#!/usr/bin/env python3
"""Stage the validated public allowlist into dev:/docs for branch-based GitHub Pages."""
import json
import shutil
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    subprocess.run([sys.executable,str(ROOT/'scripts/build.py'),'--dist'],cwd=ROOT,check=True)
    source=ROOT/'dist';target=ROOT/'docs';target.mkdir(exist_ok=True)
    manifest=target/'.pages-manifest.json'
    previous=json.loads(manifest.read_text()) if manifest.exists() else []
    for name in previous:
        path=target/name
        if not path.resolve().is_relative_to(target.resolve()):raise ValueError('Unsafe Pages manifest path')
        if path.is_file():path.unlink()
    paths=[]
    for path in source.rglob('*'):
        if not path.is_file() or path.name=='.nojekyll':continue
        relative=path.relative_to(source);destination=target/relative
        destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,destination);paths.append(relative.as_posix())
    excluded=sorted(p.name for p in target.iterdir() if p.is_dir() and p.name not in ['assets','data'])
    excluded+=sorted(p.name for p in target.glob('*.md'))
    (target/'_config.yml').write_text('exclude: '+json.dumps(excluded,ensure_ascii=False)+'\n')
    manifest.write_text(json.dumps(sorted(paths),separators=(',',':'))+'\n')
    print(f'Staged {len(paths)} public files for Pages dev:/docs; source workbooks and reports excluded.')
if __name__=='__main__':main()
