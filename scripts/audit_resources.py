#!/usr/bin/env python3
"""Inventory unused images, broken manifest paths and orphan detail records; never delete."""
import json
import re
from data_reports import ROOT,datasets,write

def main():
    references=set();stable=set();detail_refs=set()
    for _,games in datasets():
        for game in games:
            stable.add(game['stableId'])
            if game.get('image'):references.add(game['image'])
            if game.get('detailPath'):detail_refs.add(game['detailPath'])
    publishers=json.loads((ROOT/'data/publishers.json').read_text())
    for publisher in publishers.get('publishers',[]):
        if publisher.get('image'):references.add(publisher['image'])
    designers=json.loads((ROOT/'data/designers.json').read_text())
    for designer in designers.get('designers',{}).values():
        if designer.get('image'):references.add(designer['image'])
    for path in [ROOT/'index.html',ROOT/'essen.html',ROOT/'styles.css']:
        references.update(re.findall(r'assets/[^\s"\'<>\)]+',path.read_text()))
    images={p.relative_to(ROOT).as_posix() for p in (ROOT/'assets').rglob('*') if p.is_file()}
    manifest=json.loads((ROOT/'data/cover-manifest.json').read_text())
    broken=[{'key':key,'image':entry.get('image')} for key,entry in manifest.items() if entry.get('status')=='ok' and not (ROOT/(entry.get('image') or '__missing__')).is_file()]
    orphan=[]
    for path in (ROOT/'data/details').rglob('*.json'):
        records=json.loads(path.read_text())
        orphan.extend({'path':path.relative_to(ROOT).as_posix(),'stableId':key} for key in records if key not in stable)
    write('resources.json',{'schemaVersion':1,'unusedImages':sorted(images-references),'missingReferencedImages':sorted(p for p in references if not (ROOT/p).is_file()),'brokenManifestEntries':broken,'orphanDetails':orphan,'unreferencedDetailFiles':sorted(p.relative_to(ROOT).as_posix() for p in (ROOT/'data/details').rglob('*.json') if p.relative_to(ROOT).as_posix() not in detail_refs),'policy':'Report only; no files deleted.'})
if __name__=='__main__':main()
