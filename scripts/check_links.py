#!/usr/bin/env python3
"""Opt-in, rate-limited source link checking. Never equates access denial with deletion."""
import argparse
import json
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from data_reports import ROOT, datasets, write

def classify(status, url=''):
    if status in (404,410):return 'broken'
    if status==401 or 'login' in url.lower() or 'signin' in url.lower():return 'login_required'
    if status==403:return 'access_restricted'
    if status==429 or status>=500:return 'temporarily_unavailable'
    if 200<=status<400:return 'accessible'
    return 'unknown'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='Allow network requests; otherwise only inventory links')
    parser.add_argument('--limit',type=int,default=20)
    parser.add_argument('--interval',type=float,default=1.0)
    args=parser.parse_args()
    if args.limit<0 or args.interval<0.5:parser.error('limit must be nonnegative; interval must be at least 0.5 seconds')
    urls=set()
    for _,games in datasets():
        for g in games:
            urls.update(v for k,v in g.items() if k in ['url','imageSource'] and isinstance(v,str) and v.startswith('https://'))
    for path in (ROOT/'data/essen-documents').glob('*.json'):
        for docs in json.loads(path.read_text()).values():
            urls.update(d['url'] for d in docs if d.get('url','').startswith('https://'))
    cachepath=ROOT/'data/reports/links.json'
    previous=json.loads(cachepath.read_text()).get('results',{}) if cachepath.exists() else {}
    results={url:previous.get(url,{'status':'unchecked','checkedAt':None}) for url in sorted(urls)}
    if args.check:
        for url in sorted(urls)[:args.limit]:
            checked=datetime.now(timezone.utc).isoformat()
            try:
                with urlopen(Request(url,headers={'User-Agent':'BoardgameAtlas-LinkAudit/1.0'},method='HEAD'),timeout=15) as response:
                    code=response.status;status=classify(code,response.url)
            except HTTPError as error:code=error.code;status=classify(code)
            except (URLError,TimeoutError,OSError):code=None;status='temporarily_unavailable'
            results[url]={'status':status,'httpStatus':code,'checkedAt':checked}
            time.sleep(args.interval)
    write('links.json',{'schemaVersion':1,'total':len(results),'results':results})
if __name__=='__main__':main()
