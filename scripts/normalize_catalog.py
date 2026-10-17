#!/usr/bin/env python3
import json
from pathlib import Path
from dataset_config import configured_datasets
from catalog_model import add_identity, add_relations, add_structure, add_metrics, add_release, add_provenance, apply_overrides, add_filter_terms
ROOT = Path(__file__).resolve().parents[1]
def main():
    migration_path = ROOT / 'data/id-migrations.json'
    previous_migrations = json.loads(migration_path.read_text()).get('datasets', {}) if migration_path.exists() else {}
    migrations = {}
    for config in configured_datasets():
        dataset = config['id']
        path = ROOT / config['listPath']
        raw = json.loads(path.read_text())
        for game in raw:
            if game.get('detailPath'):
                game.update(json.loads((ROOT / game['detailPath']).read_text()).get(game['stableId'], {}))
        games = add_relations(add_identity(raw, dataset))
        games = apply_overrides(games, json.loads((ROOT / 'data/overrides.json').read_text()))
        games = add_filter_terms(games)
        games = add_provenance(add_release(add_metrics(add_structure(games))), dataset)
        path.write_text(json.dumps(games, ensure_ascii=False, separators=(',', ':')) + '\n')
        migrations[dataset] = {**{str(g['id']): g['stableId'] for g in games}, **previous_migrations.get(dataset, {})}
    (ROOT / 'data/id-migrations.json').write_text(json.dumps({'schemaVersion': 1, 'datasets': migrations}, ensure_ascii=False, separators=(',', ':')) + '\n')
if __name__ == '__main__': main()
