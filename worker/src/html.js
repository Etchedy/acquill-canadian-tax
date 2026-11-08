// HTML extraction for CRA and Justice Canada pages, with the same output as the Python server's
// html_document(): the title (first <h1>, else <title>), the dcterms.modified date, and the text blocks
// (h1-h4, p, li, tr not inside another li/tr) of the page's <main>, leaving out scripts, navigation,
// footers, forms and share widgets. Each text node is trimmed and joined with a space, like
// BeautifulSoup's get_text(" ", strip=True). Uses the Workers runtime's streaming HTMLRewriter.

const NAMED = {
  amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ', shy: '­', copy: '©', reg: '®', trade: '™',
  sect: '§', para: '¶', deg: '°', middot: '·', bull: '•', hellip: '…', ndash: '–', mdash: '—', lsquo: '‘', rsquo: '’',
  sbquo: '‚', ldquo: '“', rdquo: '”', laquo: '«', raquo: '»', times: '×', divide: '÷', plusmn: '±', frac12: '½',
  frac14: '¼', frac34: '¾', cent: '¢', pound: '£', euro: '€', yen: '¥', dollar: '$', percnt: '%', ensp: ' ',
  emsp: ' ', thinsp: ' ', zwnj: '‌', zwj: '‍', lrm: '‎', rlm: '‏',
  agrave: 'à', aacute: 'á', acirc: 'â', atilde: 'ã', auml: 'ä', aring: 'å', aelig: 'æ', ccedil: 'ç', egrave: 'è',
  eacute: 'é', ecirc: 'ê', euml: 'ë', igrave: 'ì', iacute: 'í', icirc: 'î', iuml: 'ï', ntilde: 'ñ', ograve: 'ò',
  oacute: 'ó', ocirc: 'ô', otilde: 'õ', ouml: 'ö', oslash: 'ø', ugrave: 'ù', uacute: 'ú', ucirc: 'û', uuml: 'ü',
  yacute: 'ý', yuml: 'ÿ', oelig: 'œ', szlig: 'ß', Agrave: 'À', Aacute: 'Á', Acirc: 'Â', Ccedil: 'Ç', Egrave: 'È',
  Eacute: 'É', Ecirc: 'Ê', Euml: 'Ë', Icirc: 'Î', Iuml: 'Ï', Ocirc: 'Ô', OElig: 'Œ', Ugrave: 'Ù', Ucirc: 'Û', Uuml: 'Ü',
};
const fromCodePoint = n => (Number.isInteger(n) && n > 0 && n <= 0x10ffff && !(n >= 0xd800 && n <= 0xdfff) ? String.fromCodePoint(n) : '�');
export const decodeEntities = s => s.replace(/&(#[xX][0-9a-fA-F]+|#\d+|[A-Za-z][A-Za-z0-9]*);/g, (m, e) =>
  e[0] === '#' ? fromCodePoint(e[1] === 'x' || e[1] === 'X' ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10)) : (NAMED[e] ?? m));

// A snippet that may hold markup (A2AJ's highlighted excerpts): its text, joined like get_text(" ", strip=True).
export const clean = html => String(html || '').split(/<[^>]*>/).map(s => decodeEntities(s).trim()).filter(Boolean).join(' ');

export async function htmlDocument(html) {
  let excluded = 0, mainDepth = 0, sawMain = false, listDepth = 0, h1Depth = 0, sawH1 = false, inTitle = false, pending = '';
  let modified = null;
  const h1Parts = [], titleParts = [], mainText = [], allText = [], order = [], open = new Set();
  const EXCLUDED = new Set(['script', 'style', 'nav', 'footer', 'form']), BLOCKS = new Set(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'tr']);
  await new HTMLRewriter()
    .on('meta', { element: el => { if (/^dcterms\.modified$/i.test(el.getAttribute('name') || '') && modified === null) modified = el.getAttribute('content'); } })
    // One handler per element: HTMLRewriter keeps only the last end-tag callback an element is given.
    .on('title,h1,main,script,style,nav,footer,form,.pagedetails,.wb-share,h2,h3,h4,p,li,tr', {
      element: el => {
        const tag = el.tagName, leave = [];
        if (tag === 'title') { inTitle = true; leave.push(() => { inTitle = false; }); }
        if (tag === 'h1' && !sawH1) { sawH1 = true; h1Depth++; leave.push(() => { h1Depth--; }); }
        if (tag === 'main' && (!sawMain || mainDepth > 0)) { sawMain = true; mainDepth++; leave.push(() => { mainDepth--; }); }
        const cls = ' ' + (el.getAttribute('class') || '') + ' ';
        if (EXCLUDED.has(tag) || cls.includes(' pagedetails ') || cls.includes(' wb-share ')) { excluded++; leave.push(() => { excluded--; }); }
        if (BLOCKS.has(tag)) {
          const list = tag === 'li' || tag === 'tr', counts = excluded === 0 && listDepth === 0;
          // An unclosed <p> ends where the next block starts, as in a browser.
          if (tag === 'p') for (const s of open) if (s.tag === 'p') open.delete(s);
          if (list) { listDepth++; leave.push(() => { listDepth--; }); }
          if (counts) { const slot = { tag, parts: [], inMain: mainDepth > 0 }; order.push(slot); open.add(slot); leave.push(() => { open.delete(slot); }); }
        }
        if (!leave.length) return;
        const done = () => { for (const f of leave.reverse()) f(); };
        try { el.onEndTag(done); } catch { done(); }
      },
    })
    .onDocument({
      text: chunk => {
        pending += chunk.text;
        if (!chunk.lastInTextNode) return;
        const s = decodeEntities(pending).trim(); pending = '';
        if (!s) return;
        if (h1Depth > 0) h1Parts.push(s);
        if (inTitle) titleParts.push(s);
        if (excluded > 0) return;
        for (const slot of open) slot.parts.push(s);
        if (mainDepth > 0) mainText.push(s);
        allText.push(s);
      },
    })
    .transform(new Response(html, { headers: { 'content-type': 'text/html; charset=utf-8' } }))
    .arrayBuffer();
  const title = h1Parts.join(' ') || titleParts.join(' ') || 'Untitled publication';
  const blocks = order.filter(s => !sawMain || s.inMain).map(s => s.parts.join(' ')).filter(Boolean);
  return { title, modified, blocks: blocks.length ? blocks : [(sawMain ? mainText : allText).join(' ')] };
}
