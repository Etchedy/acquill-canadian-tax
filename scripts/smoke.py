"""Live read-only MCP integration check; run against an already started server."""
import argparse
import asyncio
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

async def run(url):
    report={'checked_at':datetime.now(timezone.utc).isoformat(),'endpoint':url,'checks':[]}
    async with httpx.AsyncClient(timeout=120,trust_env=False) as client:
        async with streamable_http_client(url,http_client=client) as (read,write,_):
            async with ClientSession(read,write) as session:
                hello=await session.initialize()
                report['server_name']=hello.serverInfo.name
                tools=await session.list_tools()
                assert len(tools.tools)==6
                assert all(t.annotations.readOnlyHint and t.title for t in tools.tools)
                report['tools']=[t.name for t in tools.tools]
                async def call(name,args):
                    r=await session.call_tool(name,args)
                    assert not r.isError, str(r)
                    data=r.structuredContent or json.loads(r.content[0].text)
                    report['checks'].append({'tool':name,'arguments':args,'status':data.get('status','ok')})
                    return data
                coverage=await call('check_coverage',{})
                assert coverage['cra']['documents']>0,coverage
                assert coverage['cases']['status']=='ok',coverage
                report['coverage']=coverage
                search=await call('search_tax',{'query':'interest deductibility','source':'all','limit':3})
                report['source_search_counts']={s['source']:len(s['results']) for s in search['sources']}
                for s in search['sources']:
                    assert s['status']=='ok' and s['results'],s
                cra=next(s for s in search['sources'] if s['source']=='cra')['results'][0]
                passages=await call('get_cra_passages',{'document_id':cra['id'],'passage_index':cra['passage_index']})
                assert passages['status']=='ok' and passages['text']
                direct=await call('get_cra_publication',{'url':cra['source_url'],'max_chars':1000})
                assert direct['status']=='ok' and direct['text']
                for kind in ('cases','legislation'):
                    hit=next(s for s in search['sources'] if s['source']==kind)['results'][0]
                    doc=await call('get_document',{'document_id':hit['id'],'max_chars':1500})
                    assert doc['status']=='ok' and doc['text'],doc
                    assert len(doc['text'])<=1500
                    if kind=='cases':
                        numbered=await call('get_document',{'document_id':hit['id'],'paragraph_start':1,'paragraph_end':2,'max_chars':1500})
                        assert numbered['status'] in ('ok','paragraphs_not_found'),numbered
                        report['numbered_paragraph_retrieval']=numbered['status']
                law=await call('get_legislation_section',{'act':'income_tax_act','section':'20','max_chars':3000})
                assert law['status']=='ok' and 'interest' in law['text'].lower(),law
                report['official_section_url']=law['source_url']
    report['result']='PASS'
    return report

async def local_run(url):
    process=subprocess.Popen([sys.executable,'-m','canadian_tax_mcp.server'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        async with httpx.AsyncClient(trust_env=False) as client:
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError('Local MCP server exited before it was ready')
                try:
                    response=await client.get('http://127.0.0.1:8000/health')
                    if response.status_code==200:break
                except httpx.RequestError:pass
                await asyncio.sleep(0.1)
            else:raise RuntimeError('Local MCP server did not become ready')
        return await run(url)
    finally:
        process.terminate()
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:process.kill();process.wait()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:8000/mcp')
    parser.add_argument('--start-server',action='store_true',help='Launch and stop a local server for this check')
    parser.add_argument('--out',default='verification/live-smoke.json');args=parser.parse_args()
    report=asyncio.run(local_run(args.url) if args.start_server else run(args.url));Path(args.out).parent.mkdir(parents=True,exist_ok=True)
    Path(args.out).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='coverage'},indent=2))
