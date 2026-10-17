import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('audit', Path(__file__).resolve().parents[1] / 'scripts/audit_translations.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class TranslationAuditTests(unittest.TestCase):
    def test_exact_missing_ambiguous_and_orphan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root/'input'; target = root/'output'
            source.mkdir(); target.mkdir(); (target/'nested').mkdir()
            for name in ['Exact.pdf', 'Missing.pdf', 'Duplicate.pdf']:
                (source/name).touch()
            for name in ['Exact_CHT.pdf', 'Duplicate_CHT.pdf', 'Orphan_CHT.pdf']:
                (target/name).touch()
            (target/'nested/Duplicate_CHT.pdf').touch()
            report = module.audit(source,target)
            self.assertEqual(report['summary'], dict(sources=3,translations=4,matched=1,missing=1,ambiguous=1))
            self.assertEqual(len(report['unmappedTranslations']),3)
    def test_public_metadata_never_contains_local_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); editorial=root/'editorial.json'; mapping=root/'map.json'
            editorial.write_text('{"games":{}}')
            mapping.write_text(json.dumps([{'confirmed':True,'sourceName':'Rules.pdf','stableId':'game:1'}]))
            report={'records':[{'sourceName':'Rules.pdf','status':'matched','source':'/private/Rules.pdf','translations':['/private/Rules_CHT.pdf']}]}
            module.update_editorial(report,mapping,editorial)
            result=editorial.read_text()
            self.assertNotIn('/private/',result)
            entry=json.loads(result)['games']['game:1']['translations'][0]
            self.assertFalse(entry['public']);self.assertEqual(entry['status'],'待校對')

if __name__=='__main__': unittest.main()
