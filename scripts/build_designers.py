#!/usr/bin/env python3
"""Export designer portraits from the source workbooks; never accesses the network."""
import json
import re
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from workbook import named_rows, read_workbook

ROOT = Path(__file__).resolve().parents[1]
SHEET = '設計師資料'
COLUMNS = [
    ('設計師名稱', 'name'), ('設計師索引鍵', 'key'), ('BGG 設計師 ID', 'bggId'),
    ('BGG 設計師名稱', 'bggName'), ('BGG 設計師頁 URL', 'bggUrl'),
    ('照片來源 URL', 'sourceUrl'), ('網站照片路徑', 'image'), ('BGG 圖片 ID', 'imageid'),
    ('照片查核狀態', 'status'), ('查核日期', 'checked'), ('BGG 中繼資料 URL', 'metadataUrl'),
    ('身分核對遊戲 URL', 'evidenceGameUrl'), ('身分核對遊戲 ID', 'evidenceGameId'),
    ('身分核對中繼資料 URL', 'evidenceMetadataUrl'), ('查核備註', 'notes'),
]


def designer_key(name):
    return ' '.join(unicodedata.normalize('NFKC', name).lower().split())


def designer_names(value):
    parts = re.split(r'[;；]' if re.search(r'[;；]', value) else r'[,、]', value)
    missing = r'^(?:BGG\s*未.*|未(?:標示|提供|公開)|不適用|unknown|uncredited|\(uncredited\)|n/a|-)$'
    return [part.strip() for part in parts if part.strip() and not re.match(missing, part.strip(), re.I)]


def date_text(value):
    if re.fullmatch(r'\d+(?:\.0+)?', value or ''):
        return (datetime(1899, 12, 30) + timedelta(days=float(value))).date().isoformat()
    if value and re.match(r'^\d{4}-\d{2}-\d{2}(?:T|$)', value):
        return datetime.fromisoformat(value.replace('Z', '+00:00')).date().isoformat()
    return value


def export_workbooks(paths):
    designers = {}
    for path in paths:
        sheets = read_workbook(path)
        if SHEET not in sheets:
            raise ValueError(f'{path.name}: Missing worksheet {SHEET}')
        rows = named_rows(sheets[SHEET], [header for header, _ in COLUMNS])
        seen = set()
        for row in rows:
            record = {field: row.get(header, '') for header, field in COLUMNS}
            key = record.pop('key')
            if not key or key != designer_key(record['name']) or key in seen:
                raise ValueError(f'{path.name}: Invalid or duplicate designer key {key!r}')
            seen.add(key)
            record['checked'] = date_text(record['checked'])
            record['evidence'] = {
                'gameUrl': record.pop('evidenceGameUrl'), 'gameId': record.pop('evidenceGameId'),
                'metadataUrl': record.pop('evidenceMetadataUrl'),
            }
            if record['bggId'] and not record['bggId'].isdigit():
                raise ValueError(f'{path.name}: Invalid BGG designer ID for {key}')
            if record['image']:
                if record['status'] != 'ok' or not record['bggId'] or not record['sourceUrl'].startswith('https://cf.geekdo-images.com/'):
                    raise ValueError(f'{path.name}: Unverified designer image for {key}')
                image = Path(record['image'])
                if image.is_absolute() or '..' in image.parts or image.parts[:2] != ('assets', 'designers'):
                    raise ValueError(f'{path.name}: Invalid designer image path for {key}')
            if key in designers and designers[key] != record:
                raise ValueError(f'Conflicting designer records between source workbooks: {key}')
            designers[key] = record
    return {'schemaVersion': 1, 'designers': dict(sorted(designers.items()))}


def main():
    from dataset_config import configured_datasets
    result = export_workbooks([ROOT / config['source'] for config in configured_datasets()])
    (ROOT / 'data/designers.json').write_text(json.dumps(result, ensure_ascii=False, separators=(',', ':')) + '\n')
    print(f'Exported {len(result["designers"])} designer records from source workbooks')


if __name__ == '__main__':
    main()
