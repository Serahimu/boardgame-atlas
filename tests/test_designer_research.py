"""Network-free safeguards for BGG designer identity and portrait research."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import fetch_designers


class DesignerResearchTests(unittest.TestCase):
    def test_semicolon_preserves_credentials_and_unknown_is_excluded(self):
        self.assertEqual(fetch_designers.designer_names('Rajiv, PhD; Chavi Chen'), ['Rajiv, PhD', 'Chavi Chen'])
        self.assertEqual(fetch_designers.designer_names('unknown'), [])
        self.assertEqual(fetch_designers.designer_key(' Ａlex  Müller '), 'alex müller')

    def test_link_must_match_credit_and_conflicting_people_are_flagged(self):
        names = {'alex': 'Alex'}
        games = {'1': {'keys': {'alex'}, 'url': 'game1'}, '2': {'keys': {'alex'}, 'url': 'game2'}}
        cache = {'1': {'source': 'source1', 'designers': [{'id': '10', 'name': 'Alex', 'url': 'person10'}, {'id': '99', 'name': 'Another', 'url': 'person99'}]}, '2': {'source': 'source2', 'designers': [{'id': '11', 'name': 'Alex', 'url': 'person11'}]}}
        result = fetch_designers.matches(names, games, cache)
        self.assertEqual(set(result), {'alex'})
        self.assertTrue(result['alex']['conflict'])
        self.assertEqual({entry['id'] for entry in result['alex']['candidates']}, {'10', '11'})
        self.assertEqual({entry['evidence']['gameId'] for entry in result['alex']['candidates']}, {'1', '2'})

    def test_no_image_and_mismatched_person_are_never_downloaded(self):
        match = {'id': '10', 'name': 'Alex', 'url': 'person10', 'evidence': {'gameId': '1'}}
        for item, status in [({'objectid': 10, 'objecttype': 'person', 'name': 'Alex', 'imageid': generic, 'images': {'previewthumb': 'https://cf.geekdo-images.com/generic.jpg'}}, 'no-image') for generic in ('1657689', '1657690')] + [({'objectid': 11, 'objecttype': 'person', 'name': 'Alex'}, 'error'), ({'objectid': 10, 'objecttype': 'person', 'name': 'Someone else'}, 'error')]:
            with self.subTest(item=item), patch.object(fetch_designers, 'request', return_value=json.dumps({'item': item}).encode()) as request:
                _, record = fetch_designers.profile('alex', 'Alex', match)
                self.assertEqual(record['status'], status)
                self.assertNotIn('image', record)
                self.assertEqual(request.call_count, 1)

    def test_resumed_download_does_not_publish_orphan_generic_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = root / 'assets/designers'
            assets.mkdir(parents=True)
            good = assets / '10.webp'
            orphan = assets / '11.webp'
            good.write_bytes(b'verified')
            orphan.write_bytes(b'generic left by interrupted fetch')
            with patch.object(fetch_designers, 'ROOT', root), patch.object(fetch_designers, 'ASSETS', assets):
                fetch_designers.prune_unused_images({'alex': {'status': 'ok', 'image': 'assets/designers/10.webp'}, 'bob': {'status': 'no-image'}})
            self.assertTrue(good.is_file())
            self.assertFalse(orphan.exists())

    def test_verified_bgg_profile_can_still_have_a_non_portrait_primary_image(self):
        match = {'id': '67269', 'name': 'Dan Booth', 'url': 'person67269', 'evidence': {'gameId': '1'}}
        item = {'objectid': 67269, 'objecttype': 'person', 'name': 'Dan Booth', 'imageid': '123456', 'images': {'previewthumb': 'https://cf.geekdo-images.com/game-card.jpg'}}
        with patch.object(fetch_designers, 'request', return_value=json.dumps({'item': item}).encode()) as request:
            _, record = fetch_designers.profile('dan booth', 'Dan Booth', match)
        self.assertEqual(record['status'], 'no-image')
        self.assertIn('遊戲卡片', record['reason'])
        self.assertEqual(record['imageid'], '123456')
        self.assertNotIn('image', record)
        self.assertEqual(request.call_count, 1)

    def test_reviewed_gallery_portrait_survives_primary_image_rejection(self):
        rejected = {'bggId': '67269', 'status': 'ok', 'imageid': '123'}
        self.assertIn('遊戲卡片', fetch_designers.rejected_portrait_reason(rejected))
        self.assertIsNone(fetch_designers.rejected_portrait_reason(dict(rejected, selection='gallery-portrait')))


if __name__ == '__main__':
    unittest.main()
