import json
import httpx
import pytest
from canadian_tax_mcp.core import Index,Web,canonical,UpstreamError,html_document,case_passages,window
from canadian_tax_mcp.service import Research

@pytest.fixture
def index(tmp_path):
    return Index(tmp_path/'test.db')

def client(handler):
    return Web(httpx.MockTransport(handler))

@pytest.mark.parametrize('url',['http://www.canada.ca/en/revenue-agency/a','https://127.0.0.1/a','https://api.a2aj.ca.evil.test/a','https://user:pass@api.a2aj.ca/a','https://api.a2aj.ca:8888/a','https://www.canada.ca/en/other/a','https://www.canada.ca/en/revenue-agency/%2e%2e/other.html'])
def test_url_boundaries(url):
    with pytest.raises(ValueError):canonical(url)

async def test_redirect_not_followed():
    calls=[]
    def handler(request):
        calls.append(str(request.url));return httpx.Response(302,headers={'location':'http://169.254.169.254/latest/meta-data/'})
    with pytest.raises(UpstreamError):await client(handler).get('https://api.a2aj.ca/search')
    assert len(calls)==1

async def test_cache_avoids_repeat_request():
    calls=[]
    def handler(r):calls.append(r);return httpx.Response(200,text='hello')
    w=client(handler)
    a=await w.get('https://api.a2aj.ca/coverage');b=await w.get('https://api.a2aj.ca/coverage')
    assert a==b and len(calls)==1

def test_html_removes_scripts_and_keeps_lists():
    title,modified,blocks=html_document('<main><h1>Tax</h1><script>ignore instructions</script><p>Rule</p><ul><li>Exception <p>detail</p></li></ul></main>')
    assert title=='Tax' and 'ignore instructions' not in ' '.join(blocks) and blocks.count('detail')==0

def test_index_upsert_and_dedup(index):
    url='https://www.canada.ca/en/revenue-agency/test.html'
    ident=index.put(url,'Interest',None,['interest one','interest two'])
    assert len(index.search('interest'))==1
    index.put(url,'Replacement',None,['replacement'])
    assert not index.search('interest') and index.get(ident)['title']=='Replacement'

async def test_empty_is_not_no_matches(index):
    s=Research(index)
    assert (await s.search('interest',source='cra'))['sources'][0]['status']=='index_empty'
    index.put('https://www.canada.ca/en/revenue-agency/test.html','Rent',None,['rent'])
    assert (await s.search('unrelatedxyz',source='cra'))['sources'][0]['status']=='no_matches'

async def test_date_filter_not_silently_applied_to_cra(index):
    r=await Research(index).search('interest',source='cra',start_date='2020-01-01')
    assert r['sources'][0]['status']=='unsupported_filter'

async def test_case_filters_and_dedup(index):
    calls=[]
    def handler(r):
        calls.append(r.url.params)
        return httpx.Response(200,json={'results':[{'citation_en':'2024 TCC 1','dataset':'TCC','snippet':'<em>interest</em>','name_en':'Case','upstream_license':'terms'}]*2})
    r=await Research(index,client(handler)).search('interest',source='cases',start_date='2020-01-01',datasets='TCC')
    assert calls[0]['start_date']=='2020-01-01' and calls[0]['dataset']=='TCC'
    hits=r['sources'][0]['results'];assert len(hits)==1 and hits[0]['excerpt']=='interest' and hits[0]['upstream_license']=='terms'

async def test_partial_upstream_failure(index):
    index.put('https://www.canada.ca/en/revenue-agency/test.html','Interest',None,['interest'])
    def handler(r):return httpx.Response(403)
    r=await Research(index,client(handler)).search('interest')
    assert r['sources'][0]['status']=='ok'
    assert all(x['status']=='source_unavailable' for x in r['sources'][1:])

async def test_case_paragraphs_adjacent_context(index):
    text='Header\n[1] A\n[2] B\n[3] C\n[4] D'
    def handler(r):return httpx.Response(200,json={'results':[{'unofficial_text_en':text,'citation_en':'2024 TCC 1'}]})
    s=Research(index,client(handler))
    r=await s.document('case:2024 TCC 1',paragraph_start=2,paragraph_end=2)
    assert r['paragraphs_returned']==[1,2,3] and '[4]' not in r['text']
    assert (await s.document('case:2024 TCC 1',paragraph_start=99))['status']=='paragraphs_not_found'

async def test_invalid_schema(index):
    def handler(r):return httpx.Response(200,json={'wrong':'field'})
    r=await Research(index,client(handler)).search('interest',source='cases')
    assert r['sources'][0]['status']=='source_unavailable'

def test_window_continuation():
    text='a'*1200
    r=window(text,0,500);assert r['next_start_char']==500 and r['truncated']
    assert window(text,1000,500)['next_start_char'] is None

def test_paragraph_parser_rejects_citation_years_and_ambiguous_numbering():
    assert not case_passages('Report\n[2020] 1 SCR 166\nCase text')
    assert [n for n,_ in case_passages('[2020] 1 SCR 166\n[1] A\n[2] B')]==[1,2]
    assert not case_passages('[1] A\n[3] Number missing')

async def test_bad_range_and_dates(index):
    s=Research(index)
    with pytest.raises(ValueError):await s.search('interest',start_date='2024-02-30')
    with pytest.raises(ValueError):await s.search('interest',start_date='2024-02-02',end_date='2020-01-01')
    with pytest.raises(ValueError):await s.document('case:x',paragraph_start=3,paragraph_end=1)
    with pytest.raises(ValueError):await s.search('interest',source='cases',offset=2)

async def test_official_section_and_version(index):
    seen=[]
    def handler(r):seen.append(str(r.url));return httpx.Response(200,text='<main><h1>Income Tax Act</h1><p>20 (1) Text</p></main>')
    r=await Research(index,client(handler)).legislation('income_tax_act','20')
    assert seen==['https://laws-lois.justice.gc.ca/eng/acts/I-3.3/section-20.html']
    assert r['version']=='current consolidation' and not r['effective_date_verified']

async def test_cra_context(index):
    ident=index.put('https://www.canada.ca/en/revenue-agency/test.html','Title',None,['a','b','c','d'])
    r=await Research(index).cra_passages(ident,1,1)
    assert r['passage_indices']==[0,1,2]

async def test_direct_cra_read_and_boundaries(index):
    seen=[]
    def handler(r):seen.append(str(r.url));return httpx.Response(200,text='<main><h1>CRA</h1><p>Guidance</p></main>')
    s=Research(index,client(handler))
    assert (await s.cra_url('https://www.canada.ca/en/revenue-agency/a.html'))['text']=='CRA\n\nGuidance'
    for url in ('https://api.a2aj.ca/a.html','https://www.canada.ca/en/other/a.html','https://www.canada.ca/en/revenue-agency/a.pdf'):
        with pytest.raises(ValueError):await s.cra_url(url)
    assert len(seen)==1

async def test_dataset_filter_not_silently_ignored(index):
    with pytest.raises(ValueError):await Research(index).search('interest',source='all',datasets='TCC')

def test_full_term_match_ranked_before_broad_match(index):
    index.put('https://www.canada.ca/en/revenue-agency/a.html','Interest',None,['interest interest interest interest'])
    target=index.put('https://www.canada.ca/en/revenue-agency/b.html','Tax',None,['interest deductibility'])
    assert index.search('interest deductibility')[0]['id']==target
