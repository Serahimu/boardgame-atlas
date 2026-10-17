#!/usr/bin/env python3
"""Regenerate the original catalogue from its named workbook columns."""
import json
import re
from pathlib import Path
from workbook import game_rows, HEADERS
ROOT = Path(__file__).resolve().parents[1]
KEYS = ['name','url','year','rating','players','type','category','mechanism','time','weight','gallery','designer','artist','publisher','funding','release','edition','version','kind','parent','typeZh','categoryZh','mechanismZh']

def build(config):
    path = ROOT / config['listPath']
    old = json.loads(path.read_text()) if path.exists() else []
    by_key = {(g['name'], g['kind'], g.get('version') or ''): g for g in old}
    covers = json.loads((ROOT / 'data/cover-manifest.json').read_text())
    original_covers = json.loads((ROOT / 'data/catalog-cover-manifest.json').read_text())
    result = []
    for i,row in enumerate(game_rows(ROOT / config['source'])):
        game = {k: row.get(h) or None for k,h in zip(KEYS,HEADERS)}
        prior = by_key.get((game['name'],game['kind'],game.get('version') or ''), {})
        game['id'] = i
        match = re.search(r'/boardgame/(\d+)', game.get('url') or '')
        game['bggid'] = match[1] if match else None
        for key in ['image','imageSource']:
            if prior.get(key): game[key] = prior[key]
        original = original_covers.get(json.dumps([game['name'],game['kind'],game.get('version') or ''],ensure_ascii=False))
        if original:
            game['image'] = original['image']
            game['imageSource'] = original['sourceUrl']
        cover = covers.get(game['bggid']) or covers.get(game.get('url'))
        if cover and cover.get('status') == 'ok':
            game['image'] = cover['image']
            game['imageSource'] = cover['sourceUrl']
        result.append(game)
    path.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    print(f'Exported {len(result)} original catalogue items')
def main():
    from dataset_config import configured_datasets
    for config in configured_datasets():
        if config['parser']=='catalog':build(config)
if __name__ == '__main__': main()
