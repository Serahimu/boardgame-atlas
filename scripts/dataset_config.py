"""One registry for additional workbook collections and years."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def configured_datasets():
    registry=json.loads((ROOT/'data/datasets.json').read_text())
    if registry.get('schemaVersion')!=1:raise ValueError('Unsupported dataset registry')
    rows=registry['datasets'];ids=[row['id'] for row in rows]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate dataset identifier')
    for row in rows:
        for field in ['source','listPath']:
            if not (ROOT/row[field]).resolve().is_relative_to(ROOT):raise ValueError('Dataset path outside project')
    return rows
