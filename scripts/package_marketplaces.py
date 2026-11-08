"""Create directory materials using the publisher's real public URLs. Does not submit anything."""
import argparse
import json
import re
import shutil
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
NAME='Acquill Canadian Tax'  # OpenAI: displayName at most 30 characters, no "MCP" or "Plugin" in the name
DESCRIPTION=('Research Canadian tax using selected CRA guidance, federal legislation, and court decisions supplied by A2AJ. '
 'Search sources, read relevant passages with citations, and check coverage and freshness. '
 'CRA coverage is selected English publications; official statutory section retrieval provides current English Income Tax Act and Excise Tax Act text. '
 'A2AJ copies are unofficial. Historical-law resolution, complete coverage, and subsequent judicial treatment are not guaranteed. '
 'This connector accesses public information only; it cannot access taxpayer accounts, file returns or make payments. '
 'It supports research and does not provide individualized professional advice. No companion skill is included.')

def https(value):
    p=urlsplit(value)
    if (p.scheme!='https' or not p.hostname or p.username or p.password or p.fragment or p.query
        or p.hostname in ('localhost','example.com','example.org') or p.hostname.endswith(('.invalid','.test','.example'))):
        raise ValueError('Provide a real public HTTPS URL without credentials, query or fragment')
    return value.rstrip('/')

def build(base_url, email, endpoint=None, demo_url=None):
    base_url=https(base_url)
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):raise ValueError('A real monitored support email is required')
    endpoint=https(endpoint or base_url+'/mcp')
    review={'test_cases':json.loads((ROOT/'marketplace/review-cases.json').read_text()),
            'commerce':False,'commerce_description':'Public research tools; no purchases or payments.'}
    if demo_url:review['demo_recording_url']=https(demo_url)
    manifest={
      '$schema':'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json',
      'name':'acquill-canadian-tax','version':'0.1.0','description':DESCRIPTION,
      'author':{'name':'Acquill','email':email,'url':base_url},'homepage':base_url,
      'keywords':['canada','tax','cra','legislation','court-decisions','research'],
      'extensions':{'com.openai':{
        'interface':{
          'displayName':NAME,'shortDescription':'Canadian tax source research','longDescription':DESCRIPTION,
          'developerName':'Acquill','category':'Productivity',
          'capabilities':['Search Canadian tax sources','Read source passages','Check source coverage'],
          'websiteURL':base_url,'supportURL':base_url+'/support','privacyPolicyURL':base_url+'/privacy','termsOfServiceURL':base_url+'/terms',
          'defaultPrompt':['Find CRA guidance and tax cases about interest deductibility.',
                           'Read Income Tax Act section 20 and identify its version.',
                           'Check the courts, dates and CRA publications this connector covers.'],
          'brandColor':'#006DFD','composerIcon':'./assets/icon.png','logo':'./assets/icon.png'},
        'review':review,'publication':{'release_notes':'Initial public-source Canadian tax research connector.'}}}}
    mcp={'$schema':'https://agent-plugins.org/schemas/1.0.0/mcp.schema.json',
         'mcpServers':{'canadian-tax':{'type':'streamable-http','url':endpoint}}}
    claude={'document_type':'Submission worksheet, not an API payload','name':NAME,'publisher':'Acquill',
            'description':DESCRIPTION,'remote_mcp_url':endpoint,'transport':'Streamable HTTP','authentication':'none',
            'documentation_url':base_url+'/docs','privacy_policy_url':base_url+'/privacy','support_contact':email,
            'icon_file':'assets/icon.png','test_account':'Not applicable: no user accounts; all tools access public sources.',
            'tested_in_claude':False,'portal':'https://claude.ai/directory/manage',
            'outstanding':['Test every tool in Claude and record actual results.','Complete publisher and directory review requirements.']}
    return manifest,mcp,claude

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',required=True);parser.add_argument('--support-email',default='support@acquill.com')
    parser.add_argument('--endpoint');parser.add_argument('--demo-url');parser.add_argument('--out',default='dist/marketplaces')
    args=parser.parse_args()
    try:manifest,mcp,claude=build(args.base_url,args.support_email,args.endpoint,args.demo_url)
    except ValueError as e:parser.error(str(e))
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    target=out/'chatgpt-plugin.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('plugin.json',json.dumps(manifest,indent=2)+'\n')
        z.writestr('mcp.json',json.dumps(mcp,indent=2)+'\n')
        z.write(ROOT/'assets/icon.png','assets/icon.png')
    (out/'claude-submission.json').write_text(json.dumps(claude,indent=2)+'\n')
    shutil.copyfile(ROOT/'assets/icon.png',out/'claude-icon.png')
    print(f'Created {target} and Claude submission worksheet. No submission was made.')
    if not args.demo_url:print('Before OpenAI review: record the real working service and supply --demo-url or add the recording in the dashboard.')

if __name__=='__main__':main()
