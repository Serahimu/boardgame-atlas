"""Designer source export and lossless worksheet-append regressions."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_designers import COLUMNS, SHEET, designer_names, export_workbooks
from update_designer_workbooks import merge_sheet, M
from workbook import read_workbook


def source_rows(**changes):
    record = {'name': 'Test Designer', 'key': 'test designer', 'bggId': '123', 'bggName': 'Test Designer', 'bggUrl': 'https://boardgamegeek.com/boardgamedesigner/123', 'sourceUrl': 'https://cf.geekdo-images.com/example.jpg', 'image': 'assets/designers/123.webp', 'imageid': '42', 'status': 'ok', 'checked': '46313', 'metadataUrl': 'https://api.geekdo.com/api/geekitems?objectid=123&objecttype=person', 'evidenceGameUrl': 'https://boardgamegeek.com/boardgame/1', 'evidenceGameId': '1', 'evidenceMetadataUrl': 'https://api.geekdo.com/api/geekitems?objectid=1&objecttype=thing'}
    record.update(changes)
    columns = {chr(65 + index): header for index, (header, _) in enumerate(COLUMNS)}
    values = {chr(65 + index): record.get(field, '') for index, (_, field) in enumerate(COLUMNS)}
    return {SHEET: [columns, values]}


class DesignerWorkbookTests(unittest.TestCase):
    def test_semicolon_credits_preserve_comma_credentials(self):
        self.assertEqual(designer_names('Rajiv V. Basaiawmoit, PhD, MBA; Taru Deva, PhD'), ['Rajiv V. Basaiawmoit, PhD, MBA', 'Taru Deva, PhD'])
        self.assertEqual(designer_names('A；B'), ['A', 'B'])
        self.assertEqual(designer_names('(Uncredited), BGG 未標示, A'), ['A'])

    def test_source_photo_provenance_and_typed_date_export(self):
        for checked in ['46313', '2026-10-18T00:00:00.000Z', '2026-10-18']:
            with self.subTest(checked=checked), patch('build_designers.read_workbook', return_value=source_rows(checked=checked)):
                record = export_workbooks([Path('book.xlsx')])['designers']['test designer']
            self.assertEqual(record['checked'], '2026-10-18')
            self.assertEqual(record['evidence']['gameId'], '1')
            self.assertEqual(record['evidence']['gameUrl'], 'https://boardgamegeek.com/boardgame/1')

    def test_unverified_image_or_path_is_rejected(self):
        for changes in [{'status': 'error'}, {'image': '../123.webp'}, {'sourceUrl': 'https://example.org/unrelated.jpg'}]:
            with self.subTest(changes=changes), patch('build_designers.read_workbook', return_value=source_rows(**changes)):
                with self.assertRaises(ValueError):
                    export_workbooks([Path('book.xlsx')])

    def test_disagreement_between_workbooks_is_rejected(self):
        with patch('build_designers.read_workbook', side_effect=[source_rows(), source_rows(bggId='456')]):
            with self.assertRaisesRegex(ValueError, 'Conflicting'):
                export_workbooks([Path('a.xlsx'), Path('b.xlsx')])

    def test_append_preserves_original_parts_and_shared_string_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'original.xlsx'
            shutil.copyfile(ROOT / 'BGG桌遊資料_完整.xlsx', path)
            with ZipFile(path) as original:
                before = {name: original.read(name) for name in original.namelist()}
            authored = Path(tmp) / 'sheet.xlsx'
            with ZipFile(authored, 'w') as output:
                output.writestr('xl/worksheets/sheet1.xml', f'<worksheet xmlns="{M}"><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c></row><row r="2"><c r="A2" t="s"><v>1</v></c></row></sheetData><pageMargins left="0.7"/></worksheet>')
                output.writestr('xl/sharedStrings.xml', f'<sst xmlns="{M}"><si><t>設計師名稱</t></si><si><t>Test Designer</t></si></sst>')
            merge_sheet(path, authored)
            changed = {'xl/workbook.xml', 'xl/_rels/workbook.xml.rels', '[Content_Types].xml'}
            with ZipFile(path) as result:
                for name, data in before.items():
                    if name not in changed and not name.endswith('/sheet2.xml'):
                        self.assertEqual(result.read(name), data, name)
            self.assertEqual(read_workbook(path)[SHEET][1]['A'], 'Test Designer')
            # Updating an existing designer tab must keep exactly one registration.
            merge_sheet(path, authored)
            self.assertEqual(list(read_workbook(path)).count(SHEET), 1)


if __name__ == '__main__':
    unittest.main()
