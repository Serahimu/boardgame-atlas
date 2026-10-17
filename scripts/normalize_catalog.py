#!/usr/bin/env python3
import json
from pathlib import Path
from catalog_model import add_identity, add_relations, add_structure, add_metrics, add_release, add_provenance, apply_overrides, add_filter_terms
ROOT = Path(__file__).resolve().parents[1]
def main():
    migrations = {}
    for dataset, file in [('catalog', 'catalog.json'), ('essen2026', 'essen.json')]:
        path = ROOT / 'data' / file
        raw = json.loads(path.read_text())
        for game in raw:
            if game.get('detailPath'):
                game.update(json.loads((ROOT / game['detailPath']).read_text()).get(game['stableId'], {}))
        games = add_relations(add_identity(raw, dataset))
        games = apply_overrides(games, json.loads((ROOT / 'data/overrides.json').read_text()))
        games = add_filter_terms(games)
        games = add_provenance(add_release(add_metrics(add_structure(games))), dataset)
        path.write_text(json.dumps(games, ensure_ascii=False, separators=(',', ':')) + '\n')
        migrations[dataset] = {str(g['id']): g['stableId'] for g in games}
    (ROOT / 'data/id-migrations.json').write_text(json.dumps({'schemaVersion': 1, 'datasets': migrations}, ensure_ascii=False, separators=(',', ':')) + '\n')
if __name__ == '__main__': main()
