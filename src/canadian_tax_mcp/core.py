from __future__ import annotations
import asyncio
import hashlib
import json
import re
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone, date
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, unquote
import httpx
from bs4 import BeautifulSoup

NAME = "Canadian Tax MCP by Acquill"
ALIASES = {"cca": "capital cost allowance", "itc": "input tax credit", "ccpc": "Canadian controlled private corporation", "gaar": "general anti avoidance rule", "hst": "harmonized sales tax", "gst": "goods and services tax"}
ALLOWED = {"www.canada.ca", "laws-lois.justice.gc.ca", "api.a2aj.ca"}

def now():
    return datetime.now(timezone.utc).isoformat()

def canonical(url: str) -> str:
    p = urlsplit(url)
    if p.scheme != "https" or p.hostname not in ALLOWED or p.username or p.password or p.port not in (None, 443):
        raise ValueError("Only HTTPS requests to approved public data sources are allowed")
    decoded=unquote(p.path)
    if '\\' in decoded or any(part in ('.','..') for part in decoded.split('/')):
        raise ValueError('Path traversal is not allowed')
    if p.hostname == "www.canada.ca" and not p.path.startswith(("/en/revenue-agency/", "/fr/agence-revenu/", "/robots.txt")):
        raise ValueError("Only CRA publications are supported on Canada.ca")
    return urlunsplit((p.scheme, p.netloc, p.path, p.query, ""))

def clean(text):
    return BeautifulSoup(text, "html.parser").get_text(" ", strip=True)

def html_document(html: str):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("h1") or soup.title
    title = title.get_text(" ", strip=True) if title else "Untitled publication"
    modified = soup.find("meta", attrs={"name": re.compile(r"^dcterms\.modified$", re.I)})
    modified = modified.get("content") if modified else None
    main = soup.find("main") or soup
    for el in main.select("script,style,nav,footer,.pagedetails,.wb-share,form"):
        el.decompose()
    # Preserve paragraph labels and section text, without duplicating nested lists.
    blocks = []
    for el in main.find_all(["h1", "h2", "h3", "h4", "p", "li", "tr"]):
        if el.find_parent(["li", "tr"]):
            continue
        t = el.get_text(" ", strip=True)
        if t:
            blocks.append(t)
    return title, modified, blocks or [main.get_text(" ", strip=True)]

def validate_query(query):
    query = query.strip()
    if not 2 <= len(query) <= 500:
        raise ValueError("query must contain 2–500 characters")
    return query

def expanded(query):
    additions = [v for k, v in ALIASES.items() if re.search(r"\b"+k+r"\b", query, re.I)]
    return query + (" " + " ".join(additions) if additions else "")

def validate_dates(start, end):
    for value in (start, end):
        if value:
            date.fromisoformat(value)
    if start and end and start > end:
        raise ValueError("start_date must not exceed end_date")

class UpstreamError(Exception):
    pass

class Web:
    """Bounded HTTP retrieval; no caller-selected hosts, redirects or credentials."""
    def __init__(self, transport=None):
        self.transport = transport
        self.cache = {}
        self.sem = asyncio.Semaphore(4)

    async def get(self, url, params=None, ttl=3600):
        url = canonical(url)
        self.prune_expired()
        key = (url, json.dumps(params or {}, sort_keys=True))
        item = self.cache.get(key)
        if item and time.monotonic() < item[0]:
            return item[1], item[2]
        async with self.sem:
            async with httpx.AsyncClient(timeout=30, follow_redirects=False, transport=self.transport,
                    headers={"User-Agent": "AcquillCanadianTaxMCP/0.1 (+public tax research)"}) as client:
                for attempt in range(3):
                    try:
                        async with client.stream("GET", url, params=params) as r:
                            if r.status_code in (429, 502, 503, 504) and attempt < 2:
                                await asyncio.sleep(attempt + 1)
                                continue
                            r.raise_for_status()
                            chunks, size = [], 0
                            async for chunk in r.aiter_bytes():
                                size += len(chunk)
                                if size > 12_000_000:
                                    raise UpstreamError("Document exceeds the 12 MB retrieval limit")
                                chunks.append(chunk)
                            content = b"".join(chunks).decode("utf-8", errors="replace")
                            retrieved = now()
                            while self.cache and (len(self.cache) >= 128 or sum(len(v[1]) for v in self.cache.values()) + len(content) > 24_000_000):
                                self.cache.pop(next(iter(self.cache)))
                            self.cache[key] = (time.monotonic()+ttl, content, retrieved)
                            return content, retrieved
                    except httpx.HTTPStatusError as e:
                        raise UpstreamError(f"Upstream returned HTTP {e.response.status_code}") from None
                    except httpx.RequestError:
                        if attempt < 2:
                            await asyncio.sleep(attempt+1)
                            continue
                        raise UpstreamError("Upstream request failed or timed out") from None
        raise UpstreamError("Upstream temporarily unavailable")

    def prune_expired(self):
        for key, value in list(self.cache.items()):
            if time.monotonic() >= value[0]:
                self.cache.pop(key, None)

class Index:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = str(path)
        with self.db() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS documents
              (id TEXT PRIMARY KEY, url TEXT UNIQUE, title TEXT, modified TEXT, retrieved TEXT, blocks TEXT);
              CREATE VIRTUAL TABLE IF NOT EXISTS passages USING fts5(doc_id UNINDEXED, position UNINDEXED, title, text, tokenize='unicode61');''')

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def put(self, url, title, modified, blocks):
        url = canonical(url)
        ident = "cra:"+hashlib.sha256(url.encode()).hexdigest()[:20]
        with self.db() as db:
            db.execute("DELETE FROM passages WHERE doc_id=?", (ident,))
            db.execute("INSERT OR REPLACE INTO documents VALUES (?,?,?,?,?,?)", (ident,url,title,modified,now(),json.dumps(blocks)))
            db.executemany("INSERT INTO passages VALUES (?,?,?,?)", [(ident,i,title,t) for i,t in enumerate(blocks)])
        return ident

    def get(self, ident):
        with self.db() as db:
            r = db.execute("SELECT * FROM documents WHERE id=?",(ident,)).fetchone()
            return dict(r) if r else None

    def coverage(self):
        with self.db() as db:
            r = db.execute("SELECT count(*) AS documents,min(retrieved) AS oldest_retrieval,max(retrieved) AS latest_retrieval FROM documents").fetchone()
            return {**dict(r),"scope":"Selected English CRA HTML publications; not the entire CRA website", "historical_versions":False}

    def search(self, query, limit=5, offset=0):
        words = re.findall(r"[^\W_]+",query, re.UNICODE)
        words = [w for w in words if w.lower() not in {"the","a","of","for","and","is","what","how","to","in"}]
        if not words:
            return []
        terms = ['"'+w+'"' for w in words[:30]]
        with self.db() as db:
            sql = '''SELECT d.id,d.url,d.title,d.modified,d.retrieved,p.position,p.text,bm25(passages,0,0,5,1) AS rank
                FROM passages p JOIN documents d ON d.id=p.doc_id WHERE passages MATCH ? ORDER BY rank LIMIT 500'''
            rows = db.execute(sql,(' AND '.join(terms),)).fetchall()
            # Exact term co-occurrence first, then broader recall, with document deduplication below.
            if len({r['id'] for r in rows}) < offset+limit:
                rows += db.execute(sql,(' OR '.join(terms),)).fetchall()
        seen, results = set(), []
        for r in rows:
            if r['id'] in seen:
                continue
            seen.add(r['id'])
            results.append({"id":r['id'],"title":r['title'],"source_url":r['url'],"source_type":"CRA interpretation",
                "publication_modified":r['modified'],"retrieved_at":r['retrieved'],"passage_index":int(r['position']),"excerpt":r['text'][:700]})
        return results[offset:offset+limit]

def case_passages(text):
    marks = list(re.finditer(r"(?m)^[ \t]*\[[ \t]*(\d+)[ \t]*\][ \t]*", text))
    # Report citations such as [2020] in headers are not judgment paragraphs.
    first=next((i for i,m in enumerate(marks) if int(m.group(1))==1),None)
    if first is None:
        return []
    marks=marks[first:]
    ambiguous=next((i for i,m in enumerate(marks) if int(m.group(1))!=i+1),None)
    # Quoted judgments can introduce another numbering sequence. Keep only the
    # fully delimited, unambiguous prefix; later ranges use character retrieval.
    count=len(marks) if ambiguous is None else max(0,ambiguous-1)
    return [(int(m.group(1)), text[m.start(): marks[i+1].start() if i+1 < len(marks) else len(text)].strip()) for i,m in enumerate(marks[:count])]

def window(text, start=0, budget=6000):
    if start < 0 or not 500 <= budget <= 16000:
        raise ValueError("start must be nonnegative; max_chars must be 500–16000")
    return {"text":text[start:start+budget],"start_char":start,"end_char":max(start,min(len(text),start+budget)),
            "next_start_char":start+budget if start+budget < len(text) else None,"truncated":start+budget < len(text),"total_chars":len(text)}
