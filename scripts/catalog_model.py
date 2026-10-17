"""Versioned catalogue model. Display strings remain for backwards compatibility."""
import hashlib
import json
import re
import unicodedata

def normalized(value):
    return ' '.join(unicodedata.normalize('NFKC', str(value or '')).casefold().split())

def identity(game):
    # Edition URL distinguishes versions sharing a BGG ID; never depends on row order.
    return [str(game.get('bggid') or game.get('url') or ''), normalized(game.get('name')), game.get('kind') or '', game.get('version') or '', str(game.get('sourceOrder', '')) if game.get('kind') == '佔位項目' else '']

def add_identity(games, dataset):
    seen = set()
    for game in games:
        digest = hashlib.sha256(json.dumps(identity(game), ensure_ascii=False).encode()).hexdigest()[:20]
        game['entityId'] = 'game:' + digest
        game['stableId'] = dataset + ':' + digest
        if game['stableId'] in seen:
            raise ValueError('Duplicate item identity: ' + game['name'] + '; add distinct version URL')
        seen.add(game['stableId'])
    return games
