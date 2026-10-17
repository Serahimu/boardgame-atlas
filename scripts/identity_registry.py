"""Persistent source identity registry; names disambiguate only source-key collisions."""
import hashlib
import json
import re
import unicodedata
from collections import Counter
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

def normalized_name(value):
    return ' '.join(unicodedata.normalize('NFKC',str(value or '')).casefold().split())

def canonical_url(value):
    raw=str(value or '').strip()
    if not raw:return ''
    parts=urlsplit(raw)
    host=(parts.hostname or '').lower().removeprefix('www.')
    path=re.sub(r'/+','/',parts.path).rstrip('/')
    if host=='boardgamegeek.com':
        # BGG slug and tracking changes do not change the addressed source object.
        match=re.match(r'^/(boardgame|boardgameversion|project/link/version)/(\d+)(?:/|$)',path)
        if match:return 'https://'+host+'/'+match[1]+'/'+match[2]
    query=urlencode(sorted((k,v) for k,v in parse_qsl(parts.query) if not k.startswith('utm_') and k not in ['fbclid','gclid']))
    return urlunsplit(('https' if parts.scheme.lower() in ['http','https'] else parts.scheme.lower(),host,path,query,''))

def source_identity(game):
    raw=str(game.get('bggid') or '').strip()
    if re.fullmatch(r'\d+(?:\.0+)?',raw):source='bgg:'+str(int(float(raw)))
    else:
        match=re.search(r'/boardgame/(\d+)(?:/|$)',str(game.get('url') or ''))
        source='bgg:'+match[1] if match else canonical_url(game.get('url'))
    if not source:raise ValueError('Item has no stable source URL or BGG ID: '+str(game.get('name')))
    return json.dumps([source,game.get('kind') or '',canonical_url(game.get('version')),str(game.get('sourceOrder') or '') if game.get('kind')=='佔位項目' else ''],ensure_ascii=False,separators=(',',':'))

def assign_identities(games,dataset,registry=None):
    if registry is None:registry={'schemaVersion':1,'datasets':{}}
    if registry.get('schemaVersion')!=1:raise ValueError('Unsupported identity registry schema')
    rows=registry.setdefault('datasets',{}).setdefault(dataset,[])
    groups={}
    for entry in rows:groups.setdefault(entry['sourceKey'],[]).append(entry)
    counts=Counter(source_identity(game) for game in games)
    seen=set()
    for game in games:
        key=source_identity(game);name=normalized_name(game.get('name'));candidates=groups.get(key,[])
        matches=[entry for entry in candidates if name in entry['names']]
        if len(matches)==1:entry=matches[0]
        elif len(candidates)==1 and counts[key]==1:entry=candidates[0]
        elif len(candidates)>1 and counts[key]<=len(candidates):
            raise ValueError('Ambiguous source identity; add verified name alias to data/identity-registry.json: '+str(game.get('name')))
        else:
            discriminator=name if counts[key]>1 else ''
            digest=hashlib.sha256((key+'\n'+discriminator).encode()).hexdigest()[:20]
            # On registry creation, retain all IDs already issued to URLs/backups.
            entity=game.get('entityId')
            if not entity:
                peers=[e for entries in registry['datasets'].values() for e in entries if e['sourceKey']==key and (counts[key]==1 or name in e['names'])]
                entities={e['entityId'] for e in peers}
                entity=next(iter(entities)) if len(entities)==1 else 'game:'+digest
            entry={'sourceKey':key,'names':[name],'stableId':game.get('stableId') or dataset+':'+digest,'entityId':entity}
            rows.append(entry);groups.setdefault(key,[]).append(entry)
        if name not in entry['names']:entry['names'].append(name);entry['names'].sort()
        game['stableId']=entry['stableId'];game['entityId']=entry['entityId']
        if game['stableId'] in seen:raise ValueError('Duplicate item identity: '+str(game.get('name')))
        seen.add(game['stableId'])
    rows.sort(key=lambda entry:entry['stableId'])
    return games
