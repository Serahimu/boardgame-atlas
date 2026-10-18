#!/usr/bin/env python3
"""Fail deployment on malformed data, missing resources, JS syntax or private translation URLs."""
import json
import re
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote,urlsplit
from dataset_config import ROOT,configured_datasets

class References(HTMLParser):
    def __init__(self):super().__init__();self.paths=[]
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if value and ((tag in ['script','img','iframe'] and key=='src') or (tag in ['link','a'] and key=='href')):
                self.paths.append(value)

def local_reference(value):
    parsed=urlsplit(value)
    return unquote(parsed.path) if not parsed.scheme and not parsed.netloc and parsed.path else None

def validate_editorial(editorial):
    for key,game in editorial.get('games',{}).items():
        for translation in game.get('translations',[]):
            url=translation.get('url')
            if translation.get('public') is not True and url:
                raise ValueError('Private translation URL must not enter public data: '+key)
            if url and not url.startswith('https://'):
                path=local_reference(url)
                if not path or path.startswith('/') or '..' in Path(path).parts:
                    raise ValueError('Unsafe public translation URL: '+key)
                if not (ROOT/path).is_file():raise ValueError('Missing public translation PDF: '+path)
            if any(translation.get(field) for field in ['localPath','privateUrl','privatePath']):
                raise ValueError('Private translation location included in public data: '+key)

def validate_designers(manifest):
    for key,person in manifest.get('designers',manifest).items():
        image=person.get('image')
        if not image:continue
        path=local_reference(image)
        if not path or '..' in Path(path).parts or not re.fullmatch(r'assets/designers/\d+\.webp',path):
            raise ValueError('Unsafe designer photo path: '+key)
        if person.get('status')!='ok' or str(person.get('bggId'))!=Path(path).stem:
            raise ValueError('Designer photo identity mismatch: '+key)
        if str(person.get('imageid')) in {'1657689','1657690'}:
            raise ValueError('Generic placeholder is not a designer photo: '+key)
        if not (ROOT/path).is_file():raise ValueError('Missing designer photo: '+path)

def main():
    for required in ['index.html','essen.html','app.js','styles.css','catalog-core.js','personal.js','enhancements.js','data/editorial.json','data/datasets.json','data/designers.json']:
        if not (ROOT/required).is_file():raise ValueError('Missing required file: '+required)
    count=0
    for path in (ROOT/'data').rglob('*.json'):
        json.loads(path.read_text());count+=1
    validate_editorial(json.loads((ROOT/'data/editorial.json').read_text()))
    validate_designers(json.loads((ROOT/'data/designers.json').read_text()))
    for filename in ['index.html','essen.html']:
        parser=References();parser.feed((ROOT/filename).read_text())
        for value in parser.paths:
            path=local_reference(value)
            if path and not (ROOT/path).is_file():raise ValueError(f'Missing {filename} resource: {path}')
    detail_cache={}
    for config in configured_datasets():
        games=json.loads((ROOT/config['listPath']).read_text());ids={g['id'] for g in games};stable={g['stableId'] for g in games}
        if len(ids)!=len(games) or len(stable)!=len(games):raise ValueError('Duplicate IDs: '+config['id'])
        for game in games:
            if not set(game.get('parentIds',[])+game.get('relatedIds',[]))<=ids:raise ValueError('Unresolved relation: '+game['stableId'])
            if game.get('image') and not (ROOT/game['image']).is_file():raise ValueError('Missing cover: '+game['image'])
            path=game.get('detailPath')
            if not path or not (ROOT/path).is_file():raise ValueError('Missing detail shard')
            if path not in detail_cache:detail_cache[path]=json.loads((ROOT/path).read_text())
            if game['stableId'] not in detail_cache[path]:raise ValueError('Missing detail record: '+game['stableId'])
    node=shutil.which('node')
    if not node:raise ValueError('Node.js required for deployment JavaScript syntax check')
    for script in ROOT.glob('*.js'):
        subprocess.run([node,'--check',str(script)],check=True,capture_output=True,text=True)
    print(f'Preflight passed: {count} JSON files, page references, catalogue IDs, detail assets, editorial privacy and JS syntax')
if __name__=='__main__':main()
