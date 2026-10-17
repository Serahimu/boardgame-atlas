#!/usr/bin/env python3
"""Read-only quality diagnostics; reports never delete assets or infer missing facts."""
import argparse
import json
from pathlib import Path
from dataset_config import configured_datasets
ROOT=Path(__file__).resolve().parents[1]
def write(name,value):
    target=ROOT/'data/reports'/name;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def datasets():
    for config in configured_datasets():
        yield Path(config['listPath']).stem,json.loads((ROOT/config['listPath']).read_text())
def quality():
    report={'schemaVersion':1,'datasets':{}}
    for name,games in datasets():
        ids={g['id'] for g in games};issues=[];detail_cache={}
        for g in games:
            codes=[]
            detail_path=g.get('detailPath')
            if detail_path and detail_path not in detail_cache:detail_cache[detail_path]=json.loads((ROOT/detail_path).read_text())
            metrics=g.get('metrics') or detail_cache.get(detail_path,{}).get(g['stableId'],{}).get('metrics',{})
            if not g.get('image'):codes.append('missing_cover')
            elif not (ROOT/g['image']).is_file():codes.append('missing_cover_asset')
            if not g.get('publisher') or '未標示' in g.get('publisher',''):codes.append('missing_publisher')
            if g.get('documentCount')==0:codes.append('no_indexed_documents')
            if g.get('documentCount') is None:codes.append('documents_not_audited')
            for field,limit in [('rating',10),('weight',5)]:
                value=metrics.get(field)
                if value is not None and not 0<=value<=limit:codes.append('out_of_range_'+field)
            for field in ['players','minutes']:
                value=metrics.get(field)
                if value and (value['min']<0 or value['max']<value['min']):codes.append('invalid_'+field+'_range')
            if any(i not in ids for i in g.get('parentIds',[])+g.get('relatedIds',[])):codes.append('unresolved_relation')
            if g.get('parent') and not g.get('parentIds'):codes.append('unresolved_named_parent')
            if codes:issues.append({'stableId':g['stableId'],'name':g['name'],'issues':codes})
        report['datasets'][name]={'count':len(games),'issueCount':len(issues),'issues':issues}
    write('quality.json',report)
def diff(baseline='HEAD'):
    import subprocess
    report={'schemaVersion':1,'baseline':baseline,'datasets':{}}
    for name,games in datasets():
        result=subprocess.run(['git','show',f'{baseline}:data/{name}.json'],cwd=ROOT,capture_output=True,text=True)
        if result.returncode: raise ValueError('Baseline unavailable: '+baseline+' data/'+name+'.json')
        previous=json.loads(result.stdout)
        # Project relations to stable IDs regardless of list/detail storage format.
        for records in [previous,games]:
            by_numeric={g['id']:g.get('stableId') or str(g['id']) for g in records}
            for game in records:
                for prefix in ['parent','related']:
                    game[prefix+'StableIds']=sorted(by_numeric.get(i,str(i)) for i in game.get(prefix+'Ids',[]))
        old={g.get('stableId') or str(g['id']):g for g in previous}
        new={g.get('stableId') or str(g['id']):g for g in games}
        changed=[]
        for key in sorted(old.keys() & new.keys()):
            fields={field:{'before':old[key].get(field),'after':new[key].get(field)} for field in ['name','rating','documentCount','parentStableIds','relatedStableIds'] if old[key].get(field)!=new[key].get(field)}
            if fields:changed.append({'stableId':key,'changes':fields})
        report['datasets'][name]={'added':sorted(new.keys()-old.keys()),'removed':sorted(old.keys()-new.keys()),'changed':changed}
    write('changes.json',report)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('report',choices=['quality','diff']);parser.add_argument('--baseline',default='HEAD');args=parser.parse_args()
    diff(args.baseline) if args.report=='diff' else quality()
if __name__=='__main__':main()
