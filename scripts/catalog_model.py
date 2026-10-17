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

def split_values(value):
    text = str(value or '')
    if not text or re.search(r'未標示|未公開|未有|未提供|未獨立|不適用', text):
        return []
    # A semicolon-delimited source may contain commas inside a mechanism name.
    separator = r'[;；]' if re.search(r'[;；]', text) else r'[,、]'
    return [v.strip() for v in re.split(separator, text) if v.strip()]

def add_structure(games):
    for game in games:
        game['people'] = {role: [{'id': role + ':' + hashlib.sha256(normalized(n).encode()).hexdigest()[:16], 'name': n} for n in split_values(game.get(field))] for role, field in [('designers', 'designer'), ('artists', 'artist')]}
        game['tags'] = {}
        for field in ['type', 'category', 'mechanism']:
            originals = split_values(game.get(field))
            translated = split_values(game.get(field + 'Zh'))
            game['tags'][field] = [{'id': field + ':' + hashlib.sha256(normalized(n).encode()).hexdigest()[:16], 'name': n, 'nameZh': translated[i] if len(translated) == len(originals) else None} for i, n in enumerate(originals)]
    return games

def number(value):
    try:
        result = float(value)
        return result if result == result and abs(result) != float('inf') else None
    except (ValueError, TypeError):
        return None

def value_range(value):
    text = unicodedata.normalize('NFKC', str(value or '')).strip()
    match = re.fullmatch(r'(\d+)(?:\s*[–—−-]\s*(\d+))?(?:\s*(?:Min|min|分鐘))?\+?', text)
    return {'min': int(match[1]), 'max': int(match[2] or match[1]), 'openEnded': text.endswith('+')} if match else None

def add_metrics(games):
    for game in games:
        metrics = {'players': value_range(game.get('players')), 'minutes': value_range(game.get('time')), 'rating': number(game.get('rating')), 'weight': number(game.get('weight')), 'year': number(game.get('year'))}
        game['metrics'] = metrics
        game['missingValues'] = {k: str(game.get({'minutes': 'time'}.get(k, k)) or 'source_not_provided') for k, v in metrics.items() if v is None}
    return games

def add_release(games):
    for game in games:
        raw = str(game.get('release') or '')
        match = re.match(r'^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?', raw)
        date = '-'.join(v for v in match.groups() if v) if match else None
        game['releaseInfo'] = {'date': date, 'precision': ('day' if match[3] else 'month' if match[2] else 'year') if match else 'unknown', 'status': 'unreleased' if re.search(r'未發行|未上市|unreleased', raw + str(game.get('edition') or ''), re.I) else 'unknown', 'raw': raw, 'checkedAt': str(game.get('checked') or '')[:10] or None}
    return games
