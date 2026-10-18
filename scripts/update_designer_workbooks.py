#!/usr/bin/env python3
"""Opt-in source update: append an Artifact Tool-authored designer input sheet.

Original sheet XML, styles, media, links and other package parts remain byte-for-byte
intact. Only workbook sheet registration changes. Research is a separate network job.
"""
import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile
from build_designers import COLUMNS, SHEET, designer_key, designer_names
from workbook import game_rows

ROOT = Path(__file__).resolve().parents[1]
M = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
P = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
NS = {'m': M}


def xml_bytes(element, default_namespace=None):
    # OPC package metadata requires its root namespace as the default namespace.
    ET.register_namespace('x', M)
    ET.register_namespace('r', R)
    if default_namespace:
        ET.register_namespace('', default_namespace)
    return ET.tostring(element, encoding='utf-8', xml_declaration=True)


def source_names(path, essen=False):
    names = {}
    for game in game_rows(path, essen):
        if game.get('項目類型') == '佔位項目':
            continue
        for name in designer_names(game.get('設計師', '')):
            key = designer_key(name)
            if key:
                names.setdefault(key, name)
    return names


def worksheet_styles(original):
    """Reuse the supplied workbook's actual header/body/date styles unchanged."""
    styles = ET.fromstring(original['xl/styles.xml'])
    xfs = list(styles.find('m:cellXfs', NS))
    formats = {int(n.get('numFmtId')): n.get('formatCode') for n in styles.findall('m:numFmts/m:numFmt', NS)}
    dates = [str(i) for i, xf in enumerate(xfs) if formats.get(int(xf.get('numFmtId', 0))) == 'yyyy-mm-dd']
    sheet = ET.fromstring(original['xl/worksheets/sheet1.xml'])
    cells = {cell.get('r'): cell for cell in sheet.findall('m:sheetData/m:row/m:c', NS)}
    return cells['B5'].get('s', '0'), cells['A7'].get('s', '0'), dates[0] if dates else '0'


def merge_sheet(path, authored_sheet):
    """Copy authored sheet into the original package without round-tripping it."""
    with ZipFile(path) as archive:
        info = archive.infolist()
        original = {entry.filename: archive.read(entry) for entry in info}
    workbook = ET.fromstring(original['xl/workbook.xml'])
    rels = ET.fromstring(original['xl/_rels/workbook.xml.rels'])
    content = ET.fromstring(original['[Content_Types].xml'])
    sheets = workbook.find('m:sheets', NS)
    previous = next((s for s in sheets if s.get('name') == SHEET), None)
    old_filename = None
    if previous is not None:
        relation_id = previous.get(f'{{{R}}}id')
        relation = next(r for r in rels if r.get('Id') == relation_id)
        target = relation.get('Target')
        old_filename = target.lstrip('/') if target.startswith('/') else 'xl/' + target
        sheets.remove(previous)
        rels.remove(relation)
        for item in list(content):
            if item.get('PartName') == '/' + old_filename:
                content.remove(item)
    number = max([int(s.get('sheetId')) for s in sheets] + [0]) + 1
    filename = f'xl/worksheets/sheet{number}.xml'
    while filename in original and filename != old_filename:
        number += 1
        filename = f'xl/worksheets/sheet{number}.xml'
    relation_ids = {r.get('Id') for r in rels}
    relation_id = f'rIdDesigner{number}'
    while relation_id in relation_ids:
        relation_id += '_'
    ET.SubElement(sheets, f'{{{M}}}sheet', {'name': SHEET, 'sheetId': str(number), f'{{{R}}}id': relation_id})
    ET.SubElement(rels, f'{{{P}}}Relationship', {'Id': relation_id, 'Type': R + '/worksheet', 'Target': filename.removeprefix('xl/')})
    ET.SubElement(content, f'{{{CT}}}Override', {'PartName': '/' + filename, 'ContentType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml'})
    with ZipFile(authored_sheet) as authored:
        sheet = ET.fromstring(authored.read('xl/worksheets/sheet1.xml'))
        strings = list(ET.fromstring(authored.read('xl/sharedStrings.xml'))) if 'xl/sharedStrings.xml' in authored.namelist() else []
    header_style, body_style, date_style = worksheet_styles(original)
    for cell in sheet.findall('m:sheetData/m:row/m:c', NS):
        address = cell.get('r')
        cell.set('s', header_style if address.rstrip('0123456789') + '1' == address else date_style if address.startswith('J') and cell.find('m:v', NS) is not None else body_style)
        if cell.get('t') == 's':
            value = cell.find('m:v', NS)
            string = strings[int(value.text)]
            cell.remove(value)
            cell.set('t', 'inlineStr')
            inline = ET.SubElement(cell, f'{{{M}}}is')
            inline.extend(list(string))
    # An ordinary source table has filter controls and frozen identifying column/header.
    dimension = sheet.find('m:dimension', NS)
    if dimension is None:
        rows = sheet.findall('m:sheetData/m:row', NS)
        last_row = max(int(row.get('r')) for row in rows)
        dimension = ET.Element(f'{{{M}}}dimension', {'ref': f'A1:O{last_row}'})
        sheet.insert(1 if sheet.find('m:sheetPr', NS) is not None else 0, dimension)
    filter_element = ET.Element(f'{{{M}}}autoFilter', {'ref': dimension.get('ref')})
    sheet.insert(list(sheet).index(sheet.find('m:sheetData', NS)) + 1, filter_element)
    view = sheet.find('m:sheetViews/m:sheetView', NS)
    if view is not None:
        pane = view.find('m:pane', NS)
        if pane is None:
            pane = ET.Element(f'{{{M}}}pane')
            view.insert(0, pane)
        pane.attrib.update(xSplit='1', ySplit='1', topLeftCell='B2', activePane='bottomRight', state='frozen')
    updates = {
        'xl/workbook.xml': xml_bytes(workbook),
        'xl/_rels/workbook.xml.rels': xml_bytes(rels, P),
        '[Content_Types].xml': xml_bytes(content, CT),
        filename: xml_bytes(sheet),
    }
    replacement = path.with_suffix('.designer-tmp.xlsx')
    try:
        with ZipFile(replacement, 'w', compression=ZIP_DEFLATED) as output:
            for entry in info:
                if entry.filename == old_filename:
                    continue
                output.writestr(entry, updates.pop(entry.filename, original[entry.filename]))
            for name, data in updates.items():
                output.writestr(name, data)
        with ZipFile(replacement) as result:
            changed = {'xl/workbook.xml', 'xl/_rels/workbook.xml.rels', '[Content_Types].xml', old_filename}
            for name, data in original.items():
                if name not in changed and result.read(name) != data:
                    raise ValueError(f'Unexpected modified original workbook part: {name}')
        os.replace(replacement, path)
    finally:
        replacement.unlink(missing_ok=True)


def prepare_jobs(research, directory):
    from dataset_config import configured_datasets
    jobs = []
    records = research.get('designers', research)
    for config in configured_datasets():
        path = ROOT / config['source']
        rows = []
        for key, name in sorted(source_names(path, config['parser'] == 'essen').items()):
            if key not in records:
                raise ValueError(f'Missing designer research: {name}')
            record = dict(records[key], name=name, key=key)
            evidence = record.get('evidence') or {}
            record.update(evidenceGameUrl=evidence.get('gameUrl', ''), evidenceGameId=str(evidence.get('gameId') or ''), evidenceMetadataUrl=evidence.get('metadataUrl', ''))
            record['notes'] = record.get('notes') or record.get('reason') or record.get('error') or ''
            rows.append([str(record.get(field) or '') for _, field in COLUMNS])
        prefix = directory / config['id']
        jobs.append({'path': str(path), 'rows': rows, 'previewBefore': str(prefix) + '-before.png', 'previewAfter': str(prefix) + '-after.png', 'authoredSheet': str(prefix) + '-sheet.xlsx'})
    return {'headers': [header for header, _ in COLUMNS], 'jobs': jobs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--research', type=Path, default=ROOT / 'data/designer-research.json')
    parser.add_argument('--working-dir', type=Path, default=Path(tempfile.gettempdir()) / 'boardgame-designer-excel')
    parser.add_argument('--preview-only', action='store_true')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    directory = args.working_dir
    directory.mkdir(parents=True, exist_ok=True)
    runtime = Path.home() / '.cache/codex-runtimes/codex-primary-runtime/dependencies'
    modules = directory / 'node_modules'
    if modules.is_symlink() and not modules.exists():
        modules.unlink()
    if not modules.exists():
        modules.symlink_to(runtime / 'node/node_modules', target_is_directory=True)
    builder = directory / 'designer_sheet.mjs'
    shutil.copyfile(ROOT / 'scripts/designer_sheet.mjs', builder)
    if args.preview_only or args.verify_only:
        from dataset_config import configured_datasets
        payload = {'jobs': [{'path': str(ROOT / config['source']), 'previewBefore': str(directory / (config['id'] + '-before.png')), 'previewAfter': str(directory / (config['id'] + '-saved.png'))} for config in configured_datasets()]}
    else:
        payload = prepare_jobs(json.loads(args.research.read_text()), directory)
    payload_path = directory / 'payload.json'
    payload_path.write_text(json.dumps(payload, ensure_ascii=False))
    subprocess.run([str(runtime / 'node/bin/node'), str(builder), str(payload_path), 'preview' if args.preview_only else 'verify' if args.verify_only else 'author'], check=True)
    if not args.preview_only and not args.verify_only:
        for job in payload['jobs']:
            merge_sheet(Path(job['path']), Path(job['authoredSheet']))
            print(f'Updated {Path(job["path"]).name}: {len(job["rows"])} designer records; original package parts preserved')


if __name__ == '__main__':
    main()
