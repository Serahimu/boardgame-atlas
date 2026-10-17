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

def add_relations(games):
    by_id = {g['id']: g for g in games}
    by_name = {}
    for game in games:
        by_name.setdefault(game['name'], []).append(game)
    for game in games:
        if 'parentIds' not in game:
            parents = by_name.get(game.get('parent'), []) if game.get('parent') else []
            if len(parents) > 1:
                raise ValueError('Ambiguous parent: ' + game['name'])
            game['parentIds'] = [p['id'] for p in parents]
        game.setdefault('relatedIds', [])
    for game in games:
        for parent_id in game['parentIds']:
            parent = by_id[parent_id]
            if game['id'] not in parent['relatedIds']:
                parent['relatedIds'].append(game['id'])
    for game in games:
        game['parentStableIds'] = [by_id[i]['stableId'] for i in game['parentIds']]
        game['relatedStableIds'] = [by_id[i]['stableId'] for i in game['relatedIds']]
    return games
