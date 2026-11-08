"""Turn a CRA index built by `python -m canadian_tax_mcp.ingest` into SQL for the Cloudflare D1 database.

Only publications that are new or changed are rewritten (compared by a hash of their title, date and text);
unchanged ones only get their retrieval date updated, so a monthly refresh writes few rows (D1's free plan
allows 100,000 row writes a day). Publications missing from this crawl are kept, as the local index does.
Every statement stays under D1's 100 KB statement limit.

  python scripts/export_d1.py --db data/cra.sqlite3 --known known.json --out worker/build/cra.sql

--known is the output of `wrangler d1 execute ... --command "SELECT id, hash FROM documents" --json`
(omit it for a first, full load).
"""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

LIMIT = 90_000


def q(value):
    if value is None:
        return 'NULL'
    if isinstance(value, int):
        return str(value)
    return "'" + str(value).replace('\x00', '').replace("'", "''") + "'"


def known_hashes(path):
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    rows = []
    for part in data if isinstance(data, list) else [data]:
        rows.extend(part.get('results', []) if isinstance(part, dict) else [])
    return {r['id']: r.get('hash') for r in rows}


def export(db_path, known):
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    statements, unchanged, changed = [], [], 0
    retrieved_all = {}
    for doc in db.execute('SELECT id, url, title, modified, retrieved, blocks FROM documents ORDER BY id'):
        blocks = json.loads(doc['blocks'])
        digest = hashlib.sha256(json.dumps([doc['title'], doc['modified'], blocks], ensure_ascii=False).encode()).hexdigest()
        if known.get(doc['id']) == digest:
            unchanged.append(doc['id'])
            retrieved_all[doc['id']] = doc['retrieved']
            continue
        changed += 1
        statements.append(f"DELETE FROM blocks WHERE doc_id={q(doc['id'])};")
        statements.append('INSERT OR REPLACE INTO documents (id, url, title, modified, retrieved, hash) VALUES '
                          f"({q(doc['id'])}, {q(doc['url'])}, {q(doc['title'])}, {q(doc['modified'])}, {q(doc['retrieved'])}, {q(digest)});")
        head, rows = 'INSERT INTO blocks (doc_id, position, title, text) VALUES ', []
        for i, text in enumerate(blocks):
            row = f"({q(doc['id'])}, {i}, {q(doc['title'])}, {q(text)})"
            if rows and len(head) + sum(len(r) + 2 for r in rows) + len(row) > LIMIT:
                statements.append(head + ', '.join(rows) + ';')
                rows = []
            rows.append(row)
        if rows:
            statements.append(head + ', '.join(rows) + ';')
    # Unchanged publications were checked again in this crawl: their retrieval date moves forward.
    for doc_id, retrieved in retrieved_all.items():
        statements.append(f'UPDATE documents SET retrieved={q(retrieved)} WHERE id={q(doc_id)};')
    too_long = [s for s in statements if len(s.encode()) > 100_000]
    assert not too_long, f'{len(too_long)} statements exceed 100 KB'
    return statements, changed, len(unchanged)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--db', default='data/cra.sqlite3')
    parser.add_argument('--known')
    parser.add_argument('--out', default='worker/build/cra.sql')
    args = parser.parse_args()
    statements, changed, unchanged = export(args.db, known_hashes(args.known))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(statements) + '\n', encoding='utf-8')
    print(json.dumps({'changed_documents': changed, 'unchanged_documents': unchanged, 'statements': len(statements), 'out': str(out)}))


if __name__ == '__main__':
    main()
