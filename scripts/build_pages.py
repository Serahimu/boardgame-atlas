#!/usr/bin/env python3
"""Render both pages from one template; retain current per-page asset wiring."""
import hashlib
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    template=(ROOT/'templates/site.html').read_text()
    pages=json.loads((ROOT/'templates/pages.json').read_text())
    for filename,settings in pages.items():
        values=dict(settings)
        current=ROOT/filename
        # Asset additions made while developing the app must survive a data build.
        if current.exists():
            source=current.read_text()
            for key,pattern in [('styles',r'<link rel="stylesheet"[^>]*>'),('scripts',r'<script[^>]*src="[^"]+"[^>]*></script>')]:
                assets=re.findall(pattern,source)
                if assets:values[key]=''.join(assets)
        result=re.sub(r'\{\{(\w+)\}\}',lambda m:values[m[1]],template)
        if '{{' in result:raise ValueError('Unresolved template variable')
        def version_asset(match):
            attribute, path = match[1], match[2].split('?', 1)[0]
            resource = ROOT / path
            if not resource.is_file(): return match[0]
            digest = hashlib.sha256(resource.read_bytes()).hexdigest()[:12]
            return attribute + '="' + path + '?v=' + digest + '"'
        result=re.sub(r'(src|href)="([^"]+\.(?:js|css)(?:\?[^"]*)?)"',version_asset,result)
        current.write_text(result)
if __name__=='__main__':main()
