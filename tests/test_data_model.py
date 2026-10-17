"""Data regressions: python3 -m unittest discover -s tests -p 'test_data_model.py'."""
import copy
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from catalog_model import add_identity,add_relations,value_range,number,add_release,apply_overrides
from workbook import named_rows
from check_links import classify

class DataModelTests(unittest.TestCase):
    def test_stable_ids_survive_reorder_and_shared_bgg(self):
        games=[{'id':0,'bggid':'123','name':'Game','kind':'主遊戲','version':'https://example.org/1'}, {'id':1,'bggid':'123','name':'Game edition','kind':'新版','version':'https://example.org/2'}]
        add_identity(games,'test');before={g['id']:g['stableId'] for g in games}
        games.reverse();add_identity(games,'test')
        self.assertEqual(before,{g['id']:g['stableId'] for g in games})
        self.assertEqual(len(set(before.values())),2)
    def test_many_to_many_and_nested_relations(self):
        games=[{'id':0,'name':'A','parentIds':[]},{'id':1,'name':'B','parentIds':[]},{'id':2,'name':'C','parentIds':[0,1]},{'id':3,'name':'D','parentIds':[2]}]
        for g in games:g['stableId']=str(g['id'])
        add_relations(games)
        self.assertEqual(games[2]['parentStableIds'],['0','1'])
        self.assertEqual(games[2]['relatedStableIds'],['3'])
    def test_missing_and_partial_dates(self):
        self.assertIsNone(number('BGG 未公開'))
        self.assertIsNone(value_range('BGG 未標示'))
        self.assertEqual(value_range('40–60 Min')['max'],60)
        x=add_release([{'release':'2027-03（未發行）'}])[0]['releaseInfo']
        self.assertEqual((x['precision'],x['status']),('month','unreleased'))
    def test_named_headers_reordered_or_missing(self):
        self.assertEqual(named_rows([{'Z':'B','X':'A'},{'X':'a','Z':'b'}],['A','B']),[{'A':'a','B':'b'}])
        with self.assertRaises(ValueError):named_rows([{'A':'Wrong'}],['Required'])
    def test_override_cannot_change_identity_or_omit_source(self):
        games=[{'stableId':'a'}]
        for fields in [{'name':'changed'},{'publisher':'new'}]:
            with self.assertRaises(ValueError):apply_overrides(copy.deepcopy(games),{'schemaVersion':1,'items':{'a':{'fields':fields}}})
    def test_http_denial_is_not_broken(self):
        self.assertEqual(classify(403),'access_restricted')
        self.assertEqual(classify(404),'broken')
        self.assertEqual(classify(401),'login_required')
        self.assertEqual(classify(503),'temporarily_unavailable')
    def test_original_images_survive_rebuild(self):
        games=json.loads((ROOT/'data/catalog.json').read_text())
        self.assertGreaterEqual(sum(bool(g.get('image')) for g in games),160)
        self.assertTrue(next(g for g in games if g['name']=='A Feast for Odin')['image'])
    def test_published_details_and_relations_resolve(self):
        for name,count in [('catalog',170),('essen',3666)]:
            games=json.loads((ROOT/f'data/{name}.json').read_text());self.assertEqual(len(games),count)
            ids={g['id'] for g in games};stable={g['stableId'] for g in games};cache={}
            self.assertEqual(len(stable),count)
            for g in games:
                self.assertTrue(set(g['parentIds']+g['relatedIds'])<=ids)
                if g['detailPath'] not in cache:cache[g['detailPath']]=json.loads((ROOT/g['detailPath']).read_text())
                self.assertIn(g['stableId'],cache[g['detailPath']])
                if g.get('image'):self.assertTrue((ROOT/g['image']).is_file())
if __name__=='__main__':unittest.main()
