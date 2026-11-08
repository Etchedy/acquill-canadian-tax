"""Operator-only bounded CRA ingestion. Not exposed as an MCP tool."""
import argparse
import asyncio
import json
import time
from collections import deque
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from .core import Index, Web, canonical, html_document, now

ROOT='https://www.canada.ca'
SEEDS=[
 ROOT+'/en/revenue-agency/services/tax/technical-information/income-tax/income-tax-folios-index.html',
 ROOT+'/en/revenue-agency/services/forms-publications/publications/rc4022/general-information-gst-hst-registrants.html',
 ROOT+'/en/revenue-agency/services/forms-publications/publications/t4002/t4002-1.html',
 ROOT+'/en/revenue-agency/services/forms-publications/publications/t4036/rental-income.html',
]
FOLIOS='/en/revenue-agency/services/tax/technical-information/income-tax/income-tax-folios-index/'
GUIDE='/en/revenue-agency/services/forms-publications/publications/t4002/'

async def ingest(path, max_pages=150, delay=1.0):
    index,web=Index(path),Web()
    robot_text,_=await web.get(ROOT+'/robots.txt')
    robots=RobotFileParser();robots.parse(robot_text.splitlines())
    queue=deque((url,0) for url in SEEDS);seen=set();failures=[];saved=0
    while queue and len(seen)<max_pages:
        url,depth=queue.popleft()
        try:url=canonical(url)
        except ValueError:continue
        if url in seen:continue
        seen.add(url)
        if not robots.can_fetch('AcquillCanadianTaxMCP',url):
            failures.append({'url':url,'reason':'robots_disallowed'});continue
        try:
            html,_=await web.get(url)
            title,modified,blocks=html_document(html)
            index.put(url,title,modified,blocks);saved+=1
            print(f'Indexed {saved}: {title}',flush=True)
            if depth<3:
                soup=BeautifulSoup(html,'html.parser');main=soup.find('main') or soup
                for a in main.select('a[href]'):
                    link=urljoin(url,a['href']).split('#')[0]
                    if urlsplit(link).path.startswith((FOLIOS,GUIDE)) and link.endswith('.html') and link not in seen:
                        queue.append((link,depth+1))
        except Exception as e:
            failures.append({'url':url,'reason':str(e)})
        await asyncio.sleep(max(0.5,delay))
    report={'completed_at':now(),'saved_this_run':saved,'visited':len(seen),'queued_remaining':len(queue),
            'coverage':index.coverage(),'failures':failures,'seeds':SEEDS}
    with open(path+'.ingestion.json','w') as f:json.dump(report,f,indent=2)
    return report

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--db',default='data/cra.sqlite3');parser.add_argument('--max-pages',type=int,default=150)
    args=parser.parse_args()
    if not 1<=args.max_pages<=1000:parser.error('max-pages must be 1–1000')
    print(json.dumps(asyncio.run(ingest(args.db,args.max_pages)),indent=2))
if __name__=='__main__':main()
