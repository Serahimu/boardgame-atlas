#!/usr/bin/env python3
"""Build a small document facet index without loading document shards in the browser."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def category(row):
    value=str(row.get('category',''))+' '+str(row.get('name',''))
    if any(x in value.lower() for x in ['errata','勘誤']): return '勘誤'
    if any(x in value.lower() for x in ['solo','單人','solitaire']): return '單人規則'
    if any(x in value.lower() for x in ['aid','輔助','reference','摘要']): return '玩家輔助卡'
    if any(x in value.lower() for x in ['rule','規則']): return '規則書'
    return '其他'
def main():
    facets={}
    for path in sorted((ROOT/'data/essen-documents').glob('*.json')):
        for bgg,rows in json.loads(path.read_text()).items():
            facets[bgg]={'categories':sorted({category(r) for r in rows}),'languages':sorted({str(v) for r in rows for v in [r.get('language'),r.get('detectedLanguage')] if v})}
    (ROOT/'data/document-facets.json').write_text(json.dumps(facets,ensure_ascii=False,separators=(',',':'))+'\n')
if __name__=='__main__':main()
