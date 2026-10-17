"""Source-backed names must survive the generated public catalogue."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class NameOverrides(unittest.TestCase):
    def assert_source_provenance(self, source, checksum, verified, checked, nature, base=None):
        self.assertTrue(nature, 'Missing source name type')
        self.assertRegex(checked or '', r'^\d{4}-\d{2}-\d{2}$')
        self.assertIs(verified, True, 'Local source must explicitly record completed verification')
        self.assertRegex(checksum or '', r'^[a-f0-9]{64}$', 'Missing checked source SHA-256 evidence')
        self.assertFalse(Path(source.split('#')[0]).is_absolute())
        self.assertNotIn('..',Path(source.split('#')[0]).parts)
        path=(base or ROOT.parent.parent)/source.split('#')[0]
        if path.exists():
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),checksum,'Local evidence changed since verification: '+source)
        # CI does not possess private PDFs: required reviewed provenance above is
        # the release evidence. The source file itself must never be published.

    def test_detached_checkout_requires_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)
            self.assert_source_provenance('private/source.pdf','a'*64,True,'2026-10-18','本機規則檔名',base)
            for checksum,verified in [('',True),('bad',True),('a'*64,False)]:
                with self.assertRaises(AssertionError):
                    self.assert_source_provenance('private/source.pdf',checksum,verified,'2026-10-18','本機規則檔名',base)
            (base/'source.pdf').write_bytes(b'changed')
            with self.assertRaises(AssertionError):
                self.assert_source_provenance('source.pdf','a'*64,True,'2026-10-18','本機規則檔名',base)

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
                if not fields['nameZhSource'].startswith('https:'):
                    self.assert_source_provenance(fields['nameZhSource'],fields.get('nameZhSourceSha256'),fields.get('nameZhSourceVerified'),fields.get('nameChecked'),fields['nameZhType'])
            if fields.get('aliases'):
                self.assertTrue(fields['aliasSources']);aliased.append(game)
                for item in fields['aliasSources']:
                    if not item['source'].startswith('https:'):
                        self.assert_source_provenance(item['source'],item.get('sourceSha256'),item.get('sourceVerified'),item.get('checked'),item.get('type'))
        self.assertGreaterEqual(len(named),6)
        self.assertGreaterEqual(len(aliased),10)
        self.assertEqual(next(g for g in named if g['name']=='Excalibur')['nameZh'],'王者之劍')
        self.assertIn('AFFO',next(g for g in aliased if g['name']=='A Feast for Odin')['aliases'])
if __name__=='__main__':unittest.main()
