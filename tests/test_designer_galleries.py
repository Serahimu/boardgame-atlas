"""Gallery research never selects an arbitrary first image or untrusted host."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import fetch_designer_galleries as galleries


class DesignerGalleryTests(unittest.TestCase):
    def test_unreviewed_people_are_not_changed_or_downloaded(self):
        record = {'bggId': '99999999', 'status': 'no-image'}
        with patch.object(galleries, 'request') as request:
            self.assertEqual(galleries.apply_reviewed({}, {'unknown': record}), 0)
        self.assertEqual(record, {'bggId': '99999999', 'status': 'no-image'})
        request.assert_not_called()

    def test_reviewed_selection_must_match_exact_image_in_person_gallery(self):
        cache = {'117012': {'bggId': '117012', 'status': 'ok', 'images': [{'imageid': '123', 'imageurl_lg': 'https://cf.geekdo-images.com/wrong.jpg'}]}}
        with patch.object(galleries, 'request') as request, self.assertRaisesRegex(AssertionError, 'absent or duplicated'):
            galleries.apply_reviewed(cache, {'dani': {'bggId': '117012', 'status': 'no-image'}})
        request.assert_not_called()

    def test_selected_portrait_must_use_bgg_image_host(self):
        cache = {'117012': {'bggId': '117012', 'status': 'ok', 'images': [{'imageid': '9848226', 'imageurl_lg': 'https://example.org/wrong.jpg'}]}}
        with patch.object(galleries, 'request') as request, self.assertRaisesRegex(AssertionError, 'Unexpected image host'):
            galleries.apply_reviewed(cache, {'dani': {'bggId': '117012', 'status': 'no-image'}})
        request.assert_not_called()

    def test_gallery_audit_includes_later_pages(self):
        first = {'pagination': {'total': 11}, 'images': [{'imageid': str(i)} for i in range(10)]}
        second = {'images': [{'imageid': '10', 'caption': 'Named person portrait'}]}
        with patch.object(galleries, 'request', side_effect=[json.dumps(first).encode(), json.dumps(second).encode()]) as request:
            key, result = galleries.gallery('1', 'Person')
        self.assertEqual(key, '1')
        self.assertEqual(len(result['images']), 11)
        self.assertIn('pageid=2&', request.call_args_list[1].args[0])

    def test_missing_portrait_audit_is_explicit_and_repeatable(self):
        research = {'a': {'bggId': '1', 'status': 'no-image', 'reason': 'No primary'}, 'b': {'bggId': '2', 'status': 'no-image'}}
        cache = {'1': {'status': 'ok', 'images': [], 'source': 'gallery1', 'checked': '2026-10-18'}, '2': {'status': 'ok', 'images': [{'caption': 'Logo'}], 'source': 'gallery2', 'checked': '2026-10-18'}}
        galleries.annotate_missing_gallery(cache, research)
        notes = {key: record['reason'] for key, record in research.items()}
        galleries.annotate_missing_gallery(cache, research)
        self.assertEqual(notes, {key: record['reason'] for key, record in research.items()})
        self.assertIn('圖庫無圖片', notes['a'])
        self.assertIn('圖庫未找到可確認人物照片', notes['b'])
        self.assertTrue(all(record['status'] == 'no-image' and 'image' not in record and 'sourceUrl' not in record for record in research.values()))


if __name__ == '__main__':
    unittest.main()
