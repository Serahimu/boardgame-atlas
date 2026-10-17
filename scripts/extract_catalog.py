#!/usr/bin/env python3
"""One-time migration of embedded catalogue/images; safe to run repeatedly."""
import base64
import hashlib
import json
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def main():
    page = ROOT / 'index.html'
    html = page.read_text()
    match = re.search(r'<script id="game-data" type="application/json">(.*?)</script>', html, re.S)
    if not match:
        return
    games = json.loads(match[1])
    for game in games:
        value = game.get('image') or ''
        if value.startswith('data:'):
            header, encoded = value.split(',', 1)
            blob = base64.b64decode(encoded, validate=True)
            ext = 'png' if 'image/png' in header else 'jpg'
            path = Path('assets/covers/embedded') / (hashlib.sha256(blob).hexdigest()[:20] + '.' + ext)
            (ROOT / path).parent.mkdir(parents=True, exist_ok=True)
            (ROOT / path).write_bytes(blob)
            game['image'] = path.as_posix()
            game['imageSource'] = game.get('gallery') or game.get('url')
    dest = ROOT / 'data/catalog.json'
    dest.write_text(json.dumps(games, ensure_ascii=False, separators=(',', ':')) + '\n')
    page.write_text(html[:match.start()] + html[match.end():])
    print(f'Externalized {len(games)} catalogue items')
if __name__ == '__main__':
    main()
