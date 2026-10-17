#!/usr/bin/env python3
"""Read-only PDF inventory. Never copies PDFs or publishes local paths."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def key(name):
    return re.sub(r'\s+', ' ', name).strip().casefold()

def audit(input_dir, output_dir):
    inputs = sorted(input_dir.rglob('*.pdf'))
    outputs = sorted(output_dir.rglob('*.pdf'))
    index = {}
    for path in outputs:
        if path.stem.endswith('_CHT'):
            index.setdefault(key(path.stem[:-4]), []).append(path)
    records = []
    used = set()
    for path in inputs:
        candidates = index.get(key(path.stem), [])
        if len(candidates) == 1:
            used.add(candidates[0])
        records.append({'source': str(path), 'sourceName': path.name,
                        'status': 'matched' if len(candidates) == 1 else 'ambiguous' if candidates else 'missing',
                        'translations': [str(p) for p in candidates]})
    return {'schemaVersion': 1, 'scope': 'private-local-inventory',
            'matching': 'exact case-insensitive filename stem + _CHT; no fuzzy matching',
            'summary': {'sources': len(inputs), 'translations': len(outputs),
                        'matched': sum(r['status'] == 'matched' for r in records),
                        'missing': sum(r['status'] == 'missing' for r in records),
                        'ambiguous': sum(r['status'] == 'ambiguous' for r in records)},
            'records': records, 'unmappedTranslations': [str(p) for p in outputs if p not in used]}

def update_editorial(report, manifest, editorial):
    """Only explicit reviewed mappings may add public-safe status metadata."""
    mappings = json.loads(manifest.read_text())
    data = json.loads(editorial.read_text())
    by_name = {}
    for record in report['records']:
        by_name.setdefault(record['sourceName'], []).append(record)
    for mapping in mappings:
        if mapping.get('confirmed') is not True:
            continue
        records = by_name.get(mapping['sourceName'], [])
        if len(records) != 1 or records[0]['status'] != 'matched':
            raise ValueError('Confirmed mapping must identify one exactly matched source filename')
        stable_id = mapping['stableId']
        if not isinstance(stable_id, str) or not stable_id:
            raise ValueError('A reviewed stableId is required')
        # Local presence verifies a file exists, not translation quality or proofread status.
        entry = {'title': '本機繁中譯文（未公開）', 'scope': mapping.get('scope', '主遊戲'),
                 'status': '待校對', 'edition': mapping.get('edition', '未查證'),
                 'public': False, 'source': '經人工確認之本機精確檔名清冊',
                 'localFileVerified': True}
        existing = data.setdefault('games', {}).setdefault(stable_id, {})
        existing['translations'] = [t for t in existing.get('translations', [])
                                    if t.get('source') != entry['source']] + [entry]
    editorial.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT.parents[1] / '需要翻譯的規則書')
    parser.add_argument('--translated', type=Path, default=ROOT.parents[1] / '翻譯好的規則書')
    parser.add_argument('--report', type=Path, default=ROOT / '.private/translation-audit.json')
    parser.add_argument('--confirmed-map', type=Path, help='Explicit reviewed mapping JSON; opt-in editorial update')
    args = parser.parse_args()
    if not args.input.is_dir() or not args.translated.is_dir():
        parser.error('Both PDF directories must exist')
    # Reports may contain private absolute paths; confine them to ignored private output.
    if not args.report.resolve().is_relative_to((ROOT / '.private').resolve()):
        parser.error('Report must be inside .private/')
    report = audit(args.input, args.translated)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if args.confirmed_map:
        update_editorial(report, args.confirmed_map, ROOT / 'data/editorial.json')
    print(json.dumps(report['summary'], ensure_ascii=False))
    print('Private report: .private/' + str(args.report.relative_to(ROOT / '.private')))

if __name__ == '__main__':
    main()
