"""Compare the Worker's page extraction with the Python server's on live pages (run with the Worker on :8787).
   .venv/Scripts/python.exe worker/test/compare_python.py"""
import asyncio, json, sys, urllib.request
sys.path.insert(0, 'src')
from canadian_tax_mcp.core import Index
from canadian_tax_mcp.service import Research

def worker(name, args):
    body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': name, 'arguments': args}}).encode()
    req = urllib.request.Request('http://127.0.0.1:8787/mcp', body, {'content-type': 'application/json', 'accept': 'application/json, text/event-stream'})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())['result']['structuredContent']

async def main():
    r = Research(Index('data/cra.sqlite3'))
    cases = [('get_legislation_section', {'act': a, 'section': s}, lambda a=a, s=s, **k: r.legislation(a, s, **k)) for a, s in
             [('income_tax_act', '20'), ('income_tax_act', '67.1'), ('income_tax_act', '125'), ('excise_tax_act', '169'), ('excise_tax_act', '123')]]
    for url in ['https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/rc4022/general-information-gst-hst-registrants.html',
                'https://www.canada.ca/en/revenue-agency/services/tax/technical-information/income-tax/income-tax-folios-index/series-1-individuals/folio-3-family-unit-issues/income-tax-folio-s1-f3-c2-principal-residence.html',
                'https://www.canada.ca/en/revenue-agency/services/tax/technical-information/income-tax/income-tax-folios-index/series-3-property-investments-savings-plans/series-3-property-investments-savings-plans-folio-4-capital-cost-allowance/income-tax-folio-s3-f4-c1-general-discussion-capital-cost-allowance.html',
                'https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/t4002/t4002-1.html'
                ]:
        cases.append(('get_cra_publication', {'url': url}, lambda url=url, **k: r.cra_url(url, **k)))
    bad = 0
    for name, args, py in cases:
        w, p = worker(name, {**args, 'max_chars': 16000}), await py(max_chars=16000)
        if p.get('status') != 'ok' or w.get('status') != 'ok':
            print('SKIP', args, p.get('status'), w.get('status')); continue
        full_w, full_p = w['total_chars'], p['total_chars']
        same = (w['title'], w['publication_modified'], w['text']) == (p['title'], p['publication_modified'], p['text']) and full_w == full_p
        bad += not same
        label = args.get('section') or args['url'].rsplit('/', 1)[-1][:50]
        print('SAME' if same else 'DIFF', label, f'chars py={full_p} worker={full_w}', '' if same else f"title_eq={w['title']==p['title']} mod_eq={w['publication_modified']==p['publication_modified']}")
        if not same:
            a, b = p['text'], w['text']; i = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]), min(len(a), len(b)))
            print('   py:    ', repr(a[max(0, i-80):i+120])); print('   worker:', repr(b[max(0, i-80):i+120]))
    print('differences:', bad)
asyncio.run(main())
