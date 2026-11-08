"""Make a source-only handoff ZIP with checksums; excludes indexes, secrets and generated builds."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TOP={'README.md','HANDOFF.md','MARKETPLACES.md','DATA_SOURCES.md','RIGHTS.md','pyproject.toml',
     'Dockerfile','compose.yaml','Caddyfile','.env.example','.gitignore','.dockerignore'}
DIRS={'src','tests','scripts','assets','marketplace','verification'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True);args=parser.parse_args()
    files=[]
    for p in ROOT.rglob('*'):
        rel=p.relative_to(ROOT)
        if not p.is_file() or (rel.parts[0] not in DIRS and str(rel) not in TOP):continue
        if any(x=='__pycache__' or x.endswith('.egg-info') for x in rel.parts):continue
        if p.suffix in ('.pyc','.sqlite3','.db') or p.name=='.env':continue
        files.append((p,rel.as_posix()))
    manifest={name:hashlib.sha256(p.read_bytes()).hexdigest() for p,name in sorted(files)}
    target=Path(args.out).resolve();target.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for p,name in sorted(files):z.write(p,'canadian-tax-mcp/'+name)
        z.writestr('canadian-tax-mcp/RELEASE-MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for name,digest in manifest.items():assert hashlib.sha256(z.read('canadian-tax-mcp/'+name)).hexdigest()==digest
    print(json.dumps({'path':str(target),'files':len(files)+1,'bytes':target.stat().st_size,
                      'sha256':hashlib.sha256(target.read_bytes()).hexdigest()},indent=2))

if __name__=='__main__':main()
