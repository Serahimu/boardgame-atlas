#!/usr/bin/env python3
"""Cache BGG's primary game images locally. Requires Pillow and requests; resumes from its manifest."""
import argparse
import io
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

import requests
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/cover-manifest.json"
ASSETS = ROOT / "assets/covers"
RATE_LOCK = threading.Lock()
NEXT_REQUEST = 0
CONNECTIONS = threading.local()


def request(url, metadata=False):
    global NEXT_REQUEST
    if not hasattr(CONNECTIONS, "session"):
        CONNECTIONS.session = requests.Session()
        CONNECTIONS.session.headers["User-Agent"] = "Mozilla/5.0"
    for attempt in range(4):
        if metadata:
            # Limit metadata traffic across all workers, including retries.
            with RATE_LOCK:
                time.sleep(max(0, NEXT_REQUEST - time.monotonic()))
                NEXT_REQUEST = time.monotonic() + 0.15
        try:
            response = CONNECTIONS.session.get(url, timeout=45)
            response.raise_for_status()
            return response.content
        except requests.HTTPError as error:
            if error.response.status_code not in (429, 500, 502, 503, 504) or attempt == 3:
                raise
            delay = max(float(error.response.headers.get("Retry-After", 0)), 5 * (attempt + 1))
            with RATE_LOCK:
                NEXT_REQUEST = max(NEXT_REQUEST, time.monotonic() + delay)
            time.sleep(delay)


def fetch_cover(bggid):
    source = f"https://api.geekdo.com/api/geekitems?objectid={bggid}&objecttype=thing"
    try:
        item = json.loads(request(source, metadata=True))["item"]
        assert str(item["objectid"]) == bggid, "BGG returned a different game ID"
        images = item.get("images", {})
        url = images.get("previewthumb") or item.get("imageurl")
        record = {"bggid": bggid, "name": item.get("name"), "imageid": item.get("imageid"), "metadataUrl": source, "checked": date.today().isoformat()}
        # 1657689 is BGG's generic blue "NO IMAGE AVAILABLE" box.
        if not url or not item.get("imageid") or str(item.get("imageid")) in ("0", "1657689"):
            return bggid, dict(record, status="no-image", reason="BGG 未提供主要圖片或使用通用缺圖圖示")
        assert url.startswith("https://cf.geekdo-images.com/"), "Unexpected image host"
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(request(url))))
        image.load()
        assert image.width > 10 and image.height > 10, "Invalid image dimensions"
        image.thumbnail((480, 480), Image.Resampling.LANCZOS)
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA" if "transparency" in image.info else "RGB")
        path = ASSETS / f"{bggid}.webp"
        image.save(path, "WEBP", quality=85, method=6)
        return bggid, dict(record, status="ok", image=f"assets/covers/{bggid}.webp", sourceUrl=url, width=image.width, height=image.height)
    except Exception as error:
        return bggid, {"bggid": bggid, "status": "error", "metadataUrl": source, "error": str(error), "checked": date.today().isoformat()}


def save(manifest):
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    temporary = MANIFEST.with_suffix(".tmp")
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(MANIFEST)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, help="Fetch at most this many uncached IDs")
    parser.add_argument("--retry-missing", action="store_true", help="Recheck BGG items previously without images")
    args = parser.parse_args()
    games = json.loads((ROOT / "data/essen.json").read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    # Clean up caches generated before the generic BGG placeholder was identified.
    for key, record in manifest.items():
        if str(record.get("imageid")) == "1657689" and record["status"] == "ok":
            path = ROOT / record["image"]
            if path == ASSETS / f"{key}.webp" and path.exists():
                path.unlink()
            record.update(status="no-image", reason="BGG 主要圖片為通用缺圖圖示")
            record.pop("image", None)
    ASSETS.mkdir(parents=True, exist_ok=True)
    ids = sorted({g["bggid"] for g in games if g["bggid"] and g["kind"] != "佔位項目"}, key=int)
    pending = [key for key in ids if not (manifest.get(key, {}).get("status") == "ok" and (ROOT / manifest[key]["image"]).is_file()) and not (manifest.get(key, {}).get("status") == "no-image" and not args.retry_missing)]
    if args.limit is not None:
        pending = pending[:args.limit]
    print(f"Fetching {len(pending)} / {len(ids)} unique BGG IDs; keeping verified cached images.", flush=True)
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(fetch_cover, key) for key in pending]
        for completed, future in enumerate(as_completed(futures), 1):
            key, record = future.result()
            manifest[key] = record
            if record["status"] != "ok":
                print(f"{key}: {record['status']} {record.get('error', record.get('name', ''))}", flush=True)
            if completed % 25 == 0 or completed == len(pending):
                save(manifest)
                print(f"Processed {completed}/{len(pending)}; saved {sum(v['status'] == 'ok' for v in manifest.values())} covers.", flush=True)
    save(manifest)
    from collections import Counter
    print(dict(Counter(manifest[key]["status"] for key in ids if key in manifest)), flush=True)


if __name__ == "__main__":
    main()
