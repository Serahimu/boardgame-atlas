"""Source-backed names must survive the generated public catalogue."""
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class NameOverrides(unittest.TestCase):
    def test_aliases_and_names_survive_build(self):
        overrides=json.loads((ROOT/'data/overrides.json').read_text())['items']
        catalog=json.loads((ROOT/'data/catalog.json').read_text())
        by_id={g['stableId']:g for g in catalog}
        named=[]; aliased=[]
        for key,entry in overrides.items():
            if key not in by_id: continue
            fields=entry['fields']; game=by_id[key]
            for field in ['nameZh','aliases']:
                if field in fields:self.assertEqual(game[field],fields[field])
            if 'nameZh' in fields:
                self.assertTrue(fields['nameZhType']);self.assertTrue(fields['nameZhSource']);named.append(game)
            if fields.get('aliases'):
                self.assertTrue(fields['aliasSources']);aliased.append(game)
                for item in fields['aliasSources']:
                    if not item['source'].startswith('https:'):
                        self.assertTrue((ROOT.parent.parent/item['source']).exists(),item['source'])
        self.assertGreaterEqual(len(named),6)
        self.assertGreaterEqual(len(aliased),10)
        self.assertEqual(next(g for g in named if g['name']=='Excalibur')['nameZh'],'王者之劍')
        self.assertIn('AFFO',next(g for g in aliased if g['name']=='A Feast for Odin')['aliases'])
if __name__=='__main__':unittest.main()
