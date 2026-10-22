"""Preview editions keep their own routes, source rows and document collection."""
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from identity_registry import assign_identities
from workbook import HEADERS, named_rows, read_workbook


class NewGamesTests(unittest.TestCase):
    def test_repeated_preview_entries_keep_distinct_routes_and_shared_entity(self):
        registry = {'schemaVersion': 1, 'datasets': {}}
        base = {'id': 0, 'name': 'Lionwake', 'kind': '主遊戲', 'bggid': '123',
                'version': 'https://boardgamegeek.com/boardgameversion/456'}
        existing = assign_identities([dict(base)], 'essen2026', registry)[0]
        games = [dict(base, id=i, sourceEntryId=str(i + 1)) for i in range(2)]
        assign_identities(games, 'newgames2026', registry)
        self.assertEqual(len({g['stableId'] for g in games}), 2)
        self.assertEqual({g['entityId'] for g in games}, {existing['entityId']})
        before = {g['sourceEntryId']: g['stableId'] for g in games}
        reordered = [{k: v for k, v in g.items() if k not in ['stableId', 'entityId']} for g in reversed(games)]
        assign_identities(reordered, 'newgames2026', registry)
        self.assertEqual(before, {g['sourceEntryId']: g['stableId'] for g in reordered})

    def test_preview_matches_all_workbook_rows_and_edition_specific_originals(self):
        source = named_rows(read_workbook(ROOT / 'Essen2026_GeekPreview_1406_桌遊資料_完整.xlsx')['BGG完整清單'], HEADERS)
        games = json.loads((ROOT / 'data/newgames.json').read_text())
        self.assertEqual(len(games), 1406)
        self.assertEqual(len({g['stableId'] for g in games}), 1406)
        self.assertEqual(len({g['bggid'] for g in games}), 1286)
        self.assertEqual(Counter(g['bggid'] for g in games), Counter(r['BGG ID'] for r in source))
        cache = {}
        ids = {g['id'] for g in games}
        for game, row in zip(games, source):
            self.assertEqual(game['publisher'], row['出版社（第一家）'])
            self.assertTrue(set(game['parentIds'] + game['relatedIds']) <= ids)
            path = game['detailPath']
            if path not in cache: cache[path] = json.loads((ROOT / path).read_text())
            detail = cache[path][game['stableId']]
            self.assertEqual(detail['version'], row['版次來源 URL'])
            self.assertEqual(len(detail['originals']), 1)
            self.assertEqual(detail['originals'][0]['order'], row['原清單序號'])

    def test_preview_documents_and_navigation_are_published_separately(self):
        registry = json.loads((ROOT / 'data/datasets.json').read_text())['datasets']
        preview = next(c for c in registry if c['id'] == 'newgames2026')
        docs = {}
        for shard in (ROOT / preview['documentsPath']).glob('*.json'):
            docs.update(json.loads(shard.read_text()))
        self.assertEqual(sum(map(len, docs.values())), 3355)
        for game in json.loads((ROOT / preview['listPath']).read_text()):
            self.assertEqual(game['documentCount'], len(docs.get(game['bggid'], [])))
        for config in registry:
            html = (ROOT / config['page']).read_text()
            self.assertIn('href="newgames.html"', html)
            self.assertIn(f'href="{config["page"]}" aria-current="page"', html)
            self.assertIn('app.js?', html)
        self.assertEqual(preview['parser'], next(c for c in registry if c['id'] == 'essen2026')['parser'])


if __name__ == '__main__':
    unittest.main()
