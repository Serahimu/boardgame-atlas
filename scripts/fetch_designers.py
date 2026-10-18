#!/usr/bin/env python3
"""Resolve credited designers through BGG game credits and cache profile portraits.

Network research is deliberately separate from the deterministic workbook/site build.
Resume by rerunning; --retry-errors retries failed requests, never guesses identities.
"""
import argparse
import io
import json
import re
import unicodedata
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'data/designer-game-links.json'
RESEARCH = ROOT / 'data/designer-research.json'
ASSETS = ROOT / 'assets/designers'


def request(url, metadata=False):
    # Optional network/image dependencies are unnecessary for offline safety tests.
    from fetch_covers import request as fetch
    return fetch(url, metadata=metadata)
GENERIC_IMAGES = {'', '0', '1657689', '1657690'}
# README documents this corrected identity; keep source data untouched here.
GAME_CORRECTIONS = {('324590', 'Worms: The Board Game'): '397788'}
REJECTED_PORTRAITS = {
    '149442': 'BGG 主要圖片為 APEX Ideenschmiede 品牌標誌，未提供人物照片',
    '67269': 'BGG 主要圖片為 Cool Agent 遊戲卡片，並非設計師照片',
    '117012': 'BGG 主要圖片為 W3D 立方標誌，未提供人物照片',
    '155544': 'BGG 主要圖片為黃色骰子，並非設計師照片',
    '174187': 'BGG 主要圖片為 Del Sur 品牌文字標誌，未提供人物照片',
    '175075': 'BGG 主要圖片為 Ibuink 品牌標誌，未提供人物照片',
    '133336': 'BGG 主要圖片為抽象品牌標誌，未提供人物照片',
    '80428': 'BGG 主要圖片為遊戲標誌，並非 Mike Ibeji 人物照片',
    '102313': 'BGG 主要圖片為 Prospero Hall 工作室文字標誌，未提供人物照片',
    '147289': 'BGG 主要圖片為版畫場景，並非設計師照片',
    '80626': 'BGG 主要圖片為遊戲盒封面，並非 Ronald Villaver 人物照片',
    '139031': 'BGG 主要圖片為怪物標誌，未提供 Terri Vellmann 人物照片',
    '68452': 'BGG 主要圖片為公司標誌，未提供 Mandy Tong 人物照片',
}


def rejected_portrait_reason(record):
    # A separately reviewed gallery portrait may replace a rejected primary image.
    if record.get('selection') == 'gallery-portrait':
        return None
    return REJECTED_PORTRAITS.get(str(record.get('bggId', '')))


def designer_key(name):
    return ' '.join(unicodedata.normalize('NFKC', str(name)).lower().split())


def designer_names(value):
    text = str(value or '')
    parts = re.split(r'[;；]' if re.search(r'[;；]', text) else r'[,、]', text)
    missing = re.compile(r'^(?:BGG\s*未.*|未(?:標示|提供|公開)|不適用|unknown|uncredited|\(uncredited\)|n/a|-)$', re.I)
    return [name.strip() for name in parts if name.strip() and not missing.match(name.strip())]


def save(path, data):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    tmp.replace(path)


def load(path):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def prune_unused_images(research):
    referenced = {record.get('image') for record in research.values() if record.get('status') == 'ok'}
    for path in ASSETS.glob('*.webp'):
        if path.relative_to(ROOT).as_posix() not in referenced:
            path.unlink()


def game_links(game_id):
    url = f'https://api.geekdo.com/api/geekitems?objectid={game_id}&objecttype=thing'
    try:
        item = json.loads(request(url, metadata=True))['item']
        assert str(item['objectid']) == str(game_id), 'BGG returned a different game'
        links = [dict(id=str(link['objectid']), name=link['name'], url=link.get('canonical_link') or 'https://boardgamegeek.com' + link['href']) for link in item.get('links', {}).get('boardgamedesigner', []) if link.get('objecttype') == 'person']
        return str(game_id), dict(status='ok', gameName=item.get('name'), designers=links, source=url, checked=date.today().isoformat())
    except Exception as error:
        return str(game_id), dict(status='error', source=url, error=str(error), checked=date.today().isoformat())


def matches(names, games, cache):
    found = {}
    for game_id, game in games.items():
        record = cache.get(game_id, {})
        for link in record.get('designers', []):
            key = designer_key(link['name'])
            if key in game['keys'] and key in names:
                candidate = dict(link, evidence=dict(gameId=game_id, gameUrl=game['url'], metadataUrl=record['source']))
                if game.get('originalGameId'):
                    candidate['evidence']['originalGameId'] = game['originalGameId']
                if key not in found:
                    found[key] = dict(candidate, candidates=[candidate])
                elif found[key]['id'] != link['id']:
                    # Conflicting exact-name identities must be reviewed, not picked.
                    found[key]['conflict'] = True
                    if link['id'] not in {entry['id'] for entry in found[key]['candidates']}:
                        found[key]['candidates'].append(candidate)
    return found


def profile(key, name, match):
    bgg_id = match['id']
    url = f'https://api.geekdo.com/api/geekitems?objectid={bgg_id}&objecttype=person'
    record = dict(name=name, bggId=bgg_id, bggName=match['name'], bggUrl=match['url'], metadataUrl=url, checked=date.today().isoformat(), evidence=match['evidence'])
    if match['evidence'].get('originalGameId'):
        record['reason'] = f"原始遊戲 ID {match['evidence']['originalGameId']} 已依 README 已核對更正為 {match['evidence']['gameId']}，以正確遊戲署名確認設計師身分"
    try:
        item = json.loads(request(url, metadata=True))['item']
        assert str(item['objectid']) == bgg_id and item['objecttype'] == 'person', 'BGG returned a different person'
        assert designer_key(item['name']) == key, 'BGG profile name differs from the credited name'
        record['bggName'] = item['name']
        image_id = str(item.get('imageid') or '')
        image_url = item.get('images', {}).get('previewthumb') or item.get('imageurl')
        record['imageid'] = image_id
        if bgg_id in REJECTED_PORTRAITS:
            return key, dict(record, status='no-image', reason=REJECTED_PORTRAITS[bgg_id])
        if not image_url or image_id in GENERIC_IMAGES:
            reason = 'BGG 設計師個人頁尚未提供主要照片'
            if record.get('reason'):
                reason = record['reason'] + '；' + reason
            return key, dict(record, status='no-image', reason=reason)
        assert image_url.startswith('https://cf.geekdo-images.com/'), 'Unexpected image host'
        from PIL import Image, ImageOps
        picture = ImageOps.exif_transpose(Image.open(io.BytesIO(request(image_url))))
        picture.load()
        assert min(picture.size) > 10, 'Invalid image dimensions'
        picture.thumbnail((400, 400), Image.Resampling.LANCZOS)
        if picture.mode not in ('RGB', 'RGBA'):
            picture = picture.convert('RGBA' if 'transparency' in picture.info else 'RGB')
        picture.save(ASSETS / f'{bgg_id}.webp', 'WEBP', quality=88, method=6)
        return key, dict(record, status='ok', sourceUrl=image_url, image=f'assets/designers/{bgg_id}.webp', width=picture.width, height=picture.height)
    except Exception as error:
        return key, dict(record, status='error', error=str(error))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--retry-errors', action='store_true')
    args = parser.parse_args()
    names, games = {}, {}
    for file in ('catalog.json', 'essen.json'):
        for game in load(ROOT / 'data' / file):
            if game.get('kind') == '佔位項目':
                continue
            keys = set()
            for name in designer_names(game.get('designer')):
                key = designer_key(name)
                names.setdefault(key, name)
                keys.add(key)
            if game.get('bggid') and keys:
                gid = str(game['bggid'])
                original_id = gid
                gid = GAME_CORRECTIONS.get((gid, game['name']), gid)
                if gid in games:
                    games[gid]['keys'].update(keys)
                else:
                    games[gid] = dict(url=game['url'] if gid == original_id else f'https://boardgamegeek.com/boardgame/{gid}', keys=keys)
                    if gid != original_id:
                        games[gid]['originalGameId'] = original_id
    cache, research = load(CACHE), load(RESEARCH)
    ASSETS.mkdir(parents=True, exist_ok=True)
    for record in research.values():
        rejected_reason = rejected_portrait_reason(record)
        if record.get('status') == 'ok' and (str(record.get('imageid', '')) in GENERIC_IMAGES or rejected_reason):
            path = ROOT / record.get('image', '')
            if path.parent == ASSETS and path.is_file():
                path.unlink()
            record.update(status='no-image', reason=rejected_reason or 'BGG 設計師個人頁使用通用缺圖圖示')
            for field in ('image', 'sourceUrl', 'width', 'height'):
                record.pop(field, None)
    print(f'Researching {len(names)} designer names across {len(games)} games.', flush=True)
    attempted = set(cache) if not args.retry_errors else {key for key, value in cache.items() if value.get('status') == 'ok'}
    while True:
        resolved = matches(names, games, cache)
        missing = set(names) - set(resolved)
        # A greedy cover avoids requesting every expansion and duplicate credit.
        selected, covered = [], set()
        candidates = [(len(game['keys'] & missing), gid) for gid, game in games.items() if gid not in attempted]
        for _, gid in sorted(candidates, reverse=True):
            if (games[gid]['keys'] & missing) - covered:
                selected.append(gid)
                covered.update(games[gid]['keys'] & missing)
        if not selected:
            break
        print(f'Fetching {len(selected)} game credit pages; {len(resolved)} names resolved.', flush=True)
        with ThreadPoolExecutor(max_workers=24) as pool:
            futures = [pool.submit(game_links, gid) for gid in selected]
            for count, future in enumerate(as_completed(futures), 1):
                gid, record = future.result()
                cache[gid] = record
                attempted.add(gid)
                if count % 30 == 0 or count == len(selected):
                    save(CACHE, cache)
                    print(f'Game credits {count}/{len(selected)}; {dict(Counter(v["status"] for v in cache.values()))}', flush=True)
    resolved = matches(names, games, cache)
    pending = []
    for key, name in names.items():
        match = resolved.get(key)
        if not match or match.get('conflict'):
            reason = '未在對應 BGG 遊戲頁找到完全相符的設計師署名'
            if match:
                reason = '同名設計師對應不同 BGG 身分，需人工確認：' + '；'.join(f"person {entry['id']}（遊戲 {entry['evidence']['gameId']}）" for entry in match['candidates'])
            else:
                evidence = []
                for gid, game in games.items():
                    if key in game['keys'] and gid in cache:
                        credits = '、'.join(link['name'] for link in cache[gid].get('designers', [])) or cache[gid].get('error', '未提供署名')
                        evidence.append(f'遊戲 {gid} 目前署名：{credits}')
                if evidence:
                    reason += '；' + '；'.join(evidence)
            research[key] = dict(name=name, status='unmatched', checked=date.today().isoformat(), reason=reason)
            if match:
                research[key]['candidates'] = match['candidates']
            continue
        existing = research.get(key, {})
        if existing.get('bggId') == match['id'] and match['evidence'].get('originalGameId'):
            original_id = match['evidence']['originalGameId']
            existing['evidence'] = match['evidence']
            if original_id not in existing.get('reason', ''):
                correction = f"原始遊戲 ID {original_id} 已依 README 已核對更正為 {match['evidence']['gameId']}，以正確遊戲署名確認設計師身分"
                existing['reason'] = correction + ('；' + existing['reason'] if existing.get('reason') else '')
        if existing.get('status') == 'ok' and existing.get('bggId') == match['id'] and (ROOT / existing.get('image', '')).is_file():
            continue
        if existing.get('status') == 'no-image' and existing.get('bggId') == match['id']:
            continue
        if existing.get('status') == 'error' and not args.retry_errors:
            continue
        pending.append((key, name, match))
    save(RESEARCH, research)
    print(f'Fetching {len(pending)} verified designer profiles.', flush=True)
    with ThreadPoolExecutor(max_workers=24) as pool:
        futures = [pool.submit(profile, *entry) for entry in pending]
        for count, future in enumerate(as_completed(futures), 1):
            key, record = future.result()
            research[key] = record
            if count % 30 == 0 or count == len(pending):
                save(RESEARCH, research)
                print(f'Designer profiles {count}/{len(pending)}; {dict(Counter(v["status"] for v in research.values()))}', flush=True)
    save(RESEARCH, research)
    prune_unused_images(research)
    print(f'Finished: {dict(Counter(research[key]["status"] for key in names))}', flush=True)


if __name__ == '__main__':
    main()
