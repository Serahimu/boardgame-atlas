#!/usr/bin/env python3
"""Audit missing-portrait BGG galleries without automatically selecting images."""
import argparse
import io
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

from fetch_designers import ROOT, ASSETS, RESEARCH, load, save, request

CACHE = ROOT / 'data/designer-gallery.json'
# Visually reviewed on 2026-10-18 against the named BGG person gallery/caption.
# These are explicit selections, never the first arbitrary gallery image.
GALLERY_PORTRAITS = {
    '101308': '6826415',  # Orlando Sá
    '103743': '8939289',  # Nils Nilsson
    '105412': '9712210',  # Jason Blake
    '110698': '7796860',  # Jindřich Pavlásek
    '117012': '9848226',  # Dani Garcia with The Voynich Puzzle
    '120207': '9789366',  # Rafael Prado
    '122438': '6138779',  # Nate Linhart
    '122520': '7375226',  # Toni López
    '122662': '9669102',  # Russ Law, personal illustrated portrait
    '148437': '7129184',  # Meng Chunlin, "Designer Photo"
    '155935': '9161943',  # Fabrice Puleo
    '157295': '9392385',  # Adrien Fenouillet
    '159736': '8015651',  # Melody Leblond
    '159982': '8045404',  # Juhana Keskinen
    '163899': '8401624',  # Jeffrey Chamberlain
    '165896': '9247020',  # Hugo Leblanc
    '166413': '8971442',  # Brad Spellman, personal cartoon avatar
    '168016': '9005742',  # Luke Allison
    '170024': '9023166',  # Florian Kumschier
    '171493': '9162409',  # Antonio Guillamó "Guilla"
    '172700': '9833168',  # Viljar Opdal Svensson
    '173362': '9405322',  # Franco Sardo
    '174982': '9734673',  # Marc-André Lavoie, identified at left
    '175344': '9627088',  # Mark William
    '176443': '9713248',  # Aleksander Østby
    '42727': '1481275',  # Named Sotirios Tsantilas interview group photo
    '8': '6170764',  # Richard Ulrich
}


def apply_reviewed(cache, research):
    changed = 0
    for record in research.values():
        person_id = str(record.get('bggId', ''))
        image_id = GALLERY_PORTRAITS.get(person_id)
        if not image_id:
            continue
        if record.get('selection') == 'gallery-portrait' and record.get('imageid') == image_id and (ROOT / record.get('image', '')).is_file():
            continue
        gallery_record = cache[person_id]
        assert gallery_record['status'] == 'ok' and gallery_record['bggId'] == person_id
        candidates = [item for item in gallery_record['images'] if str(item['imageid']) == image_id]
        assert len(candidates) == 1, f'Reviewed image {image_id} absent or duplicated in person gallery {person_id}'
        selected = candidates[0]
        url = selected['imageurl_lg']
        assert url.startswith('https://cf.geekdo-images.com/'), 'Unexpected image host'
        from PIL import Image, ImageOps
        picture = ImageOps.exif_transpose(Image.open(io.BytesIO(request(url))))
        picture.load()
        assert min(picture.size) > 10, 'Invalid portrait dimensions'
        picture.thumbnail((400, 400), Image.Resampling.LANCZOS)
        if picture.mode not in ('RGB', 'RGBA'):
            picture = picture.convert('RGBA' if 'transparency' in picture.info else 'RGB')
        ASSETS.mkdir(exist_ok=True)
        picture.save(ASSETS / f'{person_id}.webp', 'WEBP', quality=88, method=6)
        image_page = 'https://boardgamegeek.com' + selected['href']
        note = f"已目視確認 BGG 個人相簿人物照片／個人頭像；圖片說明：{selected.get('caption', '')}；相簿查核：{gallery_record['source']}；圖片頁：{image_page}"
        record.update(primaryImageId=record.get('imageid'), imageid=image_id, status='ok', image=f'assets/designers/{person_id}.webp', sourceUrl=url, width=picture.width, height=picture.height, selection='gallery-portrait', galleryUrl=gallery_record['source'], imageCaption=selected.get('caption', ''), imagePage=image_page, checked=date.today().isoformat(), reason=(record.get('reason', '') + '；' + note).lstrip('；'))
        changed += 1
        save(RESEARCH, research)
    return changed


def annotate_missing_gallery(cache, research):
    for record in research.values():
        if record.get('status') != 'no-image':
            continue
        audited = cache.get(str(record.get('bggId', '')), {})
        if audited.get('status') != 'ok':
            continue
        finding = '圖庫無圖片' if not audited.get('images') else '圖庫未找到可確認人物照片'
        note = f"BGG 個人相簿查核：{finding}；相簿來源：{audited['source']}"
        if note not in record.get('reason', ''):
            record['reason'] = (record.get('reason', '') + '；' + note).lstrip('；')
        record.update(galleryUrl=audited['source'], galleryChecked=audited['checked'])


def gallery(person_id, name):
    url = f'https://api.geekdo.com/api/images?ajax=1&gallery=all&nosession=1&objectid={person_id}&objecttype=person&pageid=1&showcount=10&sort=hot'
    record = dict(bggId=person_id, name=name, source=url, checked=date.today().isoformat())
    try:
        data = json.loads(request(url, metadata=True))
        total = int(data.get('pagination', {}).get('total', len(data.get('images', []))))
        items = list(data.get('images', []))
        for page in range(2, (total + 9) // 10 + 1):
            items.extend(json.loads(request(url.replace('pageid=1&', f'pageid={page}&'), metadata=True)).get('images', []))
        images = [{key: item.get(key) for key in ('imageid', 'caption', 'imageurl_lg', 'href')} for item in items]
        return person_id, dict(record, status='ok', total=total, images=images)
    except Exception as error:
        return person_id, dict(record, status='error', error=str(error))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply-reviewed', action='store_true', help='Download only explicitly curated portraits and update research provenance')
    args = parser.parse_args()
    research = load(ROOT / 'data/designer-research.json')
    people = {record['bggId']: record['name'] for record in research.values() if record.get('status') == 'no-image' and record.get('bggId')}
    cache = load(CACHE)
    pending = [(key, name) for key, name in people.items() if cache.get(key, {}).get('status') != 'ok' or len(cache[key].get('images', [])) < int(cache[key].get('total', 0))]
    print(f'Auditing {len(pending)} / {len(people)} missing-portrait galleries.', flush=True)
    with ThreadPoolExecutor(max_workers=24) as pool:
        futures = [pool.submit(gallery, *person) for person in pending]
        for count, future in enumerate(as_completed(futures), 1):
            key, record = future.result()
            cache[key] = record
            if count % 30 == 0 or count == len(pending):
                save(CACHE, cache)
                print(f'Galleries {count}/{len(pending)}; nonempty={sum(bool(r.get("images")) for r in cache.values())}', flush=True)
    save(CACHE, cache)
    if args.apply_reviewed:
        print(f'Applied {apply_reviewed(cache, research)} visually reviewed gallery portraits.', flush=True)
        annotate_missing_gallery(cache, research)
        save(RESEARCH, research)
    print(dict(Counter(record['status'] for record in cache.values())), flush=True)
    print(json.dumps({key: record for key, record in cache.items() if record.get('images')}, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
