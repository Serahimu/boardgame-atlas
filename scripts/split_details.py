#!/usr/bin/env python3
"""Emit list payloads and lazily loaded detail shards keyed by stableId."""
import json
from pathlib import Path
from dataset_config import configured_datasets
ROOT = Path(__file__).resolve().parents[1]
DETAIL_FIELDS = {'originals','source','officialSearch','checked','notes','gallery','version','funding','edition','documentSummary','documentStatus','priorityDocument','parentBggid','people','tags','provenance','missingValues','dataWarnings','editorialOverride'}
def main():
    for config in configured_datasets():
        dataset=config['id']
        path=ROOT/config['listPath']
        games=json.loads(path.read_text()); shards=[{} for _ in range(32)]
        for game in games:
            index=int(game['stableId'][-2:],16)%32
            detail={key:game.pop(key) for key in list(game) if key in DETAIL_FIELDS}
            shards[index][game['stableId']]=detail
            game['detailPath']=f'data/details/{dataset}/{index}.json'
        for index,shard in enumerate(shards):
            dest=ROOT/f'data/details/{dataset}/{index}.json';dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text(json.dumps(shard,ensure_ascii=False,separators=(',',':'))+'\n')
        path.write_text(json.dumps(games,ensure_ascii=False,separators=(',',':'))+'\n')
if __name__=='__main__':main()
