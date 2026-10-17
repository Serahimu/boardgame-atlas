#!/usr/bin/env python3
"""Resolve the collections' publisher names against BGG game links and cache company images."""
import argparse
import io
import json
import re
import unicodedata
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

from PIL import Image, ImageOps
from fetch_covers import request

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/publishers.json"
CACHE = ROOT / "data/publisher-game-links.json"
ASSETS = ROOT / "assets/publishers"
# Visually reviewed: this gallery image says "Ludicatessen", not "Mango Planet".
REJECTED_LOGOS = {"59263": {"9789365"}}
# Multiple publishers, known aliases, and verified source-cell corrections.
# Legal company names containing commas stay intact.
SOURCE_NAMES = {
    "2F-Spiele, Rio Grande Games": ["2F-Spiele", "Rio Grande Games"],
    "A-games (Board Game), Arclight Games, Delta Vision Publishing, MeepleBR": ["A-games (Board Game / I)", "Arclight Games", "Delta Vision Publishing", "MeepleBR"],
    "Alion – by Dr Ø, Ludofun": ["Alion – by Dr Ø", "Ludofun"],
    # Solar Sphere's source cell contains its designers; BGG 329228 lists Dranda Games.
    "Ayden Lowther, Simon Milburn": ["Dranda Games"],
    "Dranda Games, GaGa Games, Giochix.it, Maldito Games": ["Dranda Games", "GaGa Games", "Giochix.it", "Maldito Games"],
    "Good Games Publishing, Grimspire, Hyperlixir, YOKA Games": ["Good Games Publishing", "Grimspire", "Hyperlixir", "YOKA Games"],
    "Present Is Future Games": ["Present Is Future Games (PIF GAMES)"],
}


def normalized(name):
    return "".join(c for c in unicodedata.normalize("NFKD", name).casefold() if c.isalnum())


def write(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def game_links(bggid):
    url = f"https://api.geekdo.com/api/geekitems?objectid={bggid}&objecttype=thing"
    item = json.loads(request(url, metadata=True))["item"]
    assert str(item["objectid"]) == bggid
    return {"gameId": bggid, "gameName": item["name"], "source": url, "publishers": [{"id": str(p["objectid"]), "name": p["name"], "url": p["canonical_link"]} for p in item.get("links", {}).get("boardgamepublisher", [])]}


def company_image(company):
    key = company["id"]
    source = f"https://api.geekdo.com/api/geekitems?objectid={key}&objecttype=company"
    record = {**company, "key": key, "metadataUrl": source, "checked": date.today().isoformat()}
    try:
        item = json.loads(request(source, metadata=True))["item"]
        assert str(item["objectid"]) == key and item["objecttype"] == "company"
        record.update(name=item["name"], imageid=item.get("imageid"))
        url = item.get("images", {}).get("previewthumb") or item.get("imageurl")
        if not url or str(item.get("imageid")) in ("None", "0", "1657689"):
            gallery = f"https://api.geekdo.com/api/images?ajax=1&gallery=all&nosession=1&objectid={key}&objecttype=company&pageid=1&showcount=10&sort=hot"
            record["galleryUrl"] = gallery
            candidates = json.loads(request(gallery, metadata=True)).get("images", [])
            logos = [image for image in candidates if "logo" in image.get("caption", "").casefold() and str(image.get("imageid")) != "1657689" and str(image.get("imageid")) not in REJECTED_LOGOS.get(key, set())]
            if not logos:
                return dict(record, status="no-image")
            logo = logos[0]
            url = logo["imageurl_lg"]
            record.update(imageid=logo["imageid"], imageCaption=logo["caption"], selection="gallery-logo")
        assert url.startswith("https://cf.geekdo-images.com/")
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(request(url))))
        image.load()
        assert min(image.size) > 10
        image.thumbnail((400, 400), Image.Resampling.LANCZOS)
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA" if "transparency" in image.info else "RGB")
        relative = f"assets/publishers/{key}.webp"
        image.save(ROOT / relative, "WEBP", quality=88, method=6)
        return dict(record, image=relative, sourceUrl=url, width=image.width, height=image.height, status="ok")
    except Exception as error:
        return dict(record, status="error", error=str(error))


def logo_background(path):
    with Image.open(path) as image:
        image = image.convert("RGBA")
        image.thumbnail((60, 60))
        pixels = [image.getpixel((x, y)) for y in range(image.height) for x in range(image.width)]
    visible = [p for p in pixels if p[3] > 32]
    transparent = sum(p[3] < 32 for p in pixels) / len(pixels)
    white = sum(min(p[:3]) > 210 for p in visible) / max(1, len(visible))
    return "dark" if transparent > .05 and white > .8 else "light"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, help="Process at most this many publisher names for a trial run")
    parser.add_argument("--retry-missing", action="store_true", help="Recheck companies previously without a logo")
    args = parser.parse_args()
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    games = json.loads(re.search(r'<script id="game-data" type="application/json">(.*?)</script>', html, re.S)[1]) + json.loads((ROOT / "data/essen.json").read_text(encoding="utf-8"))
    sources = {}
    representatives = defaultdict(list)
    for game in games:
        if game["kind"] == "佔位項目":
            continue
        source = (game.get("publisher") or "").strip()
        names = SOURCE_NAMES.get(source, [source]) if source and "BGG 未" not in source else ["出版社未提供"]
        sources[source] = names
        for name in names:
            key = str(game.get("bggid") or "")
            if key and key not in representatives[name]:
                representatives[name].append(key)
    names = sorted({name for group in sources.values() for name in group})
    # The original collection's WORMS ID refers to a different game with a similar name.
    # Resolve Mantic through the verified Worms: The Board Game record instead.
    representatives["Mantic Games"] = ["397788"]
    if args.limit is not None:
        names = names[:args.limit]
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    missing = {representatives[name][0] for name in names if name != "出版社未提供" and representatives[name] and representatives[name][0] not in cache}
    print(f"Resolving {len(names)} names; fetching {len(missing)} representative game records.", flush=True)
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs = {pool.submit(game_links, key): key for key in missing}
        for count, job in enumerate(as_completed(jobs), 1):
            key = jobs[job]
            try:
                cache[key] = job.result()
            except Exception as error:
                print(f"Game {key}: {error}", flush=True)
            if count % 25 == 0 or count == len(jobs):
                write(CACHE, cache)
                print(f"Game metadata {count}/{len(jobs)}", flush=True)
    known = defaultdict(dict)
    for game in cache.values():
        for publisher in game["publishers"]:
            known[normalized(publisher["name"])][publisher["id"]] = {**publisher, "matchedGameId": game["gameId"], "matchedGameName": game["gameName"]}
    existing = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {"publishers": [], "sources": {}}
    records = {p["key"]: p for p in existing["publishers"]}
    resolved = {}
    for name in names:
        candidates = known.get(normalized(name), {})
        if len(candidates) == 1:
            resolved[name] = next(iter(candidates.values()))
        else:
            # No fuzzy company-name matches: leave ambiguous entries explicit for review.
            key = "unknown" if name == "出版社未提供" else "unresolved:" + name
            records[key] = {"key": key, "name": name, "status": "unresolved" if name != "出版社未提供" else "unknown"}
            resolved[name] = {"id": key}
            if name != "出版社未提供":
                print(f"Unresolved publisher: {name}", flush=True)
    companies = {p["id"]: p for p in resolved.values() if p["id"].isdigit()}
    ASSETS.mkdir(parents=True, exist_ok=True)
    pending = [p for key, p in companies.items() if key not in records or records[key].get("status") == "error" or (args.retry_missing and records[key].get("status") == "no-image") or (records[key].get("image") and not (ROOT / records[key]["image"]).exists())]
    mapping = {source: list(dict.fromkeys(resolved[name]["id"] for name in group)) for source, group in sources.items() if all(name in resolved for name in group)}
    used = {key for group in mapping.values() for key in group}

    def save():
        for key in used:
            record = records.get(key, {})
            if record.get("image") and "imageBackground" not in record:
                record["imageBackground"] = logo_background(ROOT / record["image"])
        write(OUTPUT, {"checked": date.today().isoformat(), "sources": mapping, "publishers": [records[key] for key in sorted(used) if key in records]})

    print(f"Fetching {len(pending)} publisher images.", flush=True)
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs = [pool.submit(company_image, company) for company in pending]
        for count, job in enumerate(as_completed(jobs), 1):
            record = job.result()
            records[record["key"]] = record
            if record["status"] == "error":
                print(record["name"], record.get("error"), flush=True)
            if count % 25 == 0 or count == len(jobs):
                save()
                print(f"Publisher images {count}/{len(jobs)}", flush=True)
    save()
    from collections import Counter
    print(dict(Counter(p["status"] for p in records.values() if p["key"] in used)), flush=True)


if __name__ == "__main__":
    main()
