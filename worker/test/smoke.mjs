// End-to-end check of a running Worker (local `npm run dev`, or the deployed URL):
//   node test/smoke.mjs [base-url]            default http://127.0.0.1:8787
// Calls every tool once over MCP (live CRA, Justice Canada and A2AJ), checks the error paths, the public
// pages, /health and the Origin rule. Exits non-zero on the first failure.
import assert from 'node:assert/strict';

const BASE = (process.argv[2] || 'http://127.0.0.1:8787').replace(/\/$/, '');
let id = 0;
async function rpc(method, params = {}, headers = {}) {
  const r = await fetch(BASE + '/mcp', { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json, text/event-stream', ...headers },
    body: JSON.stringify({ jsonrpc: '2.0', id: ++id, method, params }) });
  return { status: r.status, body: await r.json() };
}
async function call(name, args = {}) {
  const { status, body } = await rpc('tools/call', { name, arguments: args });
  assert.equal(status, 200, JSON.stringify(body));
  assert.ok(body.result, JSON.stringify(body));
  return body.result;
}
const ok = (label, extra = '') => console.log('ok  ', label, extra);

const init = await rpc('initialize', { protocolVersion: '2025-06-18', capabilities: {}, clientInfo: { name: 'smoke', version: '1' } });
assert.equal(init.status, 200); assert.equal(init.body.result.serverInfo.name, 'Acquill Canadian Tax'); assert.match(init.body.result.instructions, /Canadian public tax research/);
ok('initialize', init.body.result.protocolVersion);

const { body: { result: { tools } } } = await rpc('tools/list');
assert.deepEqual(tools.map(t => t.name).sort(), ['check_coverage', 'get_cra_passages', 'get_cra_publication', 'get_document', 'get_legislation_section', 'search_tax']);
for (const t of tools) {
  assert.ok(t.title, t.name + ' has a title');
  assert.equal(t.annotations.readOnlyHint, true); assert.equal(t.annotations.destructiveHint, false); assert.equal(t.annotations.openWorldHint, true);
}
ok('tools/list', tools.length + ' tools, titles and read-only hints');

const search = (await call('search_tax', { query: 'capital cost allowance class 8', source: 'all', limit: 3 })).structuredContent;
const cra = search.sources.find(s => s.source === 'cra'), cases = search.sources.find(s => s.source === 'cases'), laws = search.sources.find(s => s.source === 'legislation');
assert.equal(cra.status, 'ok'); assert.ok(cra.results.length > 0); assert.match(cra.results[0].id, /^cra:/);
assert.ok(['ok', 'no_matches'].includes(cases.status), JSON.stringify(cases)); assert.ok(['ok', 'no_matches'].includes(laws.status), JSON.stringify(laws));
ok('search_tax (all)', `cra ${cra.results.length}, cases ${cases.results.length}, legislation ${laws.results.length}`);

const hit = cra.results[0];
const doc = (await call('get_document', { document_id: hit.id, max_chars: 1000 })).structuredContent;
assert.equal(doc.status, 'ok'); assert.match(doc.text, /^\[passage 0\]/); assert.equal(doc.text.length, 1000);
ok('get_document (cra)', doc.title);

const passages = (await call('get_cra_passages', { document_id: hit.id, passage_index: hit.passage_index, count: 2 })).structuredContent;
assert.equal(passages.status, 'ok'); assert.ok(passages.passage_indices.includes(hit.passage_index));
ok('get_cra_passages', JSON.stringify(passages.passage_indices));

if (cases.results[0]) {
  const c = (await call('get_document', { document_id: cases.results[0].id, max_chars: 800 })).structuredContent;
  assert.ok(['ok', 'language_unavailable', 'not_found'].includes(c.status), JSON.stringify(c).slice(0, 300));
  ok('get_document (case)', `${c.status} ${c.citation || ''}`);
}

const section = (await call('get_legislation_section', { act: 'income_tax_act', section: '20', max_chars: 2000 })).structuredContent;
assert.equal(section.status, 'ok'); assert.match(section.text, /Deductions permitted/i); assert.ok(section.total_chars > 20000);
ok('get_legislation_section ITA 20', `${section.total_chars} chars, "${section.title}"`);

const pub = (await call('get_cra_publication', { url: 'https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/rc4022/general-information-gst-hst-registrants.html', max_chars: 1500 })).structuredContent;
assert.equal(pub.status, 'ok'); assert.match(pub.title, /GST\/HST/);
ok('get_cra_publication RC4022', pub.title);

const coverage = (await call('check_coverage')).structuredContent;
assert.ok(coverage.cra.documents >= 100); assert.ok(coverage.cases.status);
ok('check_coverage', `cra ${coverage.cra.documents} docs, cases ${coverage.cases.status}, laws ${coverage.laws.status}`);

// Wrong input is a tool error the AI can read, not a server failure.
for (const [name, args, message] of [
  ['search_tax', { query: 'x' }, /2–500 characters/],
  ['search_tax', { query: 'interest', source: 'cases', offset: 5 }, /Only CRA search supports offset/],
  ['get_document', { document_id: 'http://evil' }, /Use an exact ID/],
  ['get_cra_publication', { url: 'https://example.com/a.html' }, /Canada.ca CRA HTML/],
  ['get_cra_publication', { url: 'https://www.canada.ca/en/services/benefits.html' }, /Only CRA publications/],
  ['get_legislation_section', { act: 'income_tax_act', section: '20; drop' }, /section number/],
]) {
  const r = await call(name, args);
  assert.equal(r.isError, true, name + ' ' + JSON.stringify(r)); assert.match(r.content[0].text, message);
}
ok('error paths', '6 invalid requests rejected with readable messages');

const blocked = await rpc('tools/list', {}, { origin: 'https://evil.example' });
assert.equal(blocked.status, 403);
const claude = await rpc('tools/list', {}, { origin: 'https://claude.ai' });
assert.equal(claude.status, 200);
ok('origin rule', 'other sites refused, claude.ai accepted');

for (const [path, text] of [['/', 'Canadian tax sources'], ['/docs', 'Example prompts'], ['/privacy', 'Cloudflare'], ['/terms', 'Terms of use'], ['/support', 'support@acquill.com']]) {
  const r = await fetch(BASE + path); assert.equal(r.status, 200, path); assert.match(await r.text(), new RegExp(text));
}
assert.equal((await fetch(BASE + '/nope')).status, 404);
const health = await (await fetch(BASE + '/health')).json(); assert.equal(health.status, 'ok'); assert.equal(health.cra_index.documents, coverage.cra.documents);
assert.equal((await fetch(BASE + '/.well-known/openai-apps-challenge')).status, 404);
ok('public pages, /health, domain check (404 until a token is set)');
console.log('\nPASS', BASE);
