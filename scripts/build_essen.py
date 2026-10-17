#!/usr/bin/env python3
"""Export the Essen workbook to static JSON. Python standard library only."""
import json
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Essen2026_Most_Wanted_桌遊資料_完整.xlsx"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def read_rows(archive, index, strings):
    sheet = ET.fromstring(archive.read(f"xl/worksheets/sheet{index}.xml"))
    rows = []
    for row in sheet.findall("m:sheetData/m:row", NS):
        values = {}
        for cell in row:
            column = cell.attrib["r"].rstrip("0123456789")
            kind = cell.get("t")
            value = cell.findtext("m:v", default="", namespaces=NS)
            if kind == "s":
                value = strings[int(value)]
            elif kind == "inlineStr":
                value = "".join(cell.find("m:is", NS).itertext())
            values[column] = value
        if int(row.attrib["r"]) >= 6:
            rows.append(values)
    return rows


def main():
    from workbook import read_workbook, named_rows, HEADERS
    books = read_workbook(SOURCE)
    # Auxiliary sheets also locate their header by required names, not a row number.
    def auxiliary(name, width):
        rows = books[name]
        required = {'文件清單': ['BGG ID','桌遊項目名稱','文件名稱','文件類別','來源標示語言','檔名／標題辨識語言','適用範圍','下載入口／文件 URL','開啟下載','文件來源','來源頁 URL','來源標示日期','連結查核說明'], '主遊戲關聯': ['項目 BGG ID','項目名稱','項目類型','主遊戲 BGG ID','主遊戲名稱'], '原清單對照': ['原清單序號','原始桌遊項目名稱','原始 BGG 項目網址','來源頁碼','原始備註','BGG ID','項目類型','主遊戲桌遊','文件查找結果'], '整理說明': ['項目','說明']}[name]
        return [{chr(65+i): r.get(h, '') for i, h in enumerate(required)} for r in named_rows(rows, required)]
    games = [{(chr(65+i) if i < 26 else 'A'+chr(65+i-26)): r.get(h, '') for i,h in enumerate(HEADERS)} for r in named_rows(books['BGG完整清單'], HEADERS)]
    documents, relations, originals, notes = [auxiliary(n, w) for n,w in [('文件清單',13),('主遊戲關聯',5),('原清單對照',9),('整理說明',2)]]
    keys = ["name", "url", "year", "rating", "players", "type", "category", "mechanism", "time", "weight", "gallery", "designer", "artist", "publisher", "funding", "release", "edition", "version", "kind", "parent", "typeZh", "categoryZh", "mechanismZh", "documentSummary", "documentStatus", "priorityDocument", "sourceOrder", "bggid", "source", "officialSearch", "checked", "notes", "parentBggid"]
    columns = [chr(65 + i) for i in range(26)] + ["A" + chr(65 + i) for i in range(7)]
    source_rows = defaultdict(list)
    for row in originals:
        source_rows[row["F"]].append({k: row.get(c, "") for k, c in zip(["order", "name", "url", "page", "notes", "bggid", "kind", "parent", "documentStatus"], "ABCDEFGHI")})
    docs_by_game = defaultdict(list)
    for row in documents:
        docs_by_game[row["A"]].append({k: row.get(c, "") for k, c in zip(["bggid", "game", "name", "category", "language", "detectedLanguage", "scope", "url", "button", "source", "sourceUrl", "date", "notes"], "ABCDEFGHIJKLM")})
    # The workbook's gallery URLs are HTML pages, not image files.
    # Prefer verified local cover assets; retain existing embedded covers as a fallback.
    import re
    existing = json.loads((ROOT / 'data/catalog.json').read_text())
    images = {str(d["bggid"]): d["image"] for d in existing if d.get("image")}
    manifest_path = ROOT / "data/cover-manifest.json"
    covers = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    result = []
    for index, row in enumerate(games):
        game = {key: row.get(column, "") for key, column in zip(keys, columns)}
        bggid = game["bggid"]
        game.update(id=index, relatedIds=[], parentIds=[], originals=source_rows[bggid], documentCount=len(docs_by_game[bggid]))
        if bggid in images:
            game["image"] = images[bggid]
        cover = covers.get(bggid) or covers.get(game["url"])
        if cover and cover["status"] == "ok":
            assert (ROOT / cover["image"]).is_file(), f"Missing cover asset: {cover['image']}"
            game["image"] = cover["image"]
            game["imageSource"] = cover["sourceUrl"]
        elif cover and cover["status"] == "no-image":
            game.pop("image", None)
        result.append(game)
    ids = {g["bggid"] for g in result}
    assert all(r["A"] in ids and r["D"] in ids for r in relations), "Unresolved relationship"
    assert all(d["A"] in ids for d in documents), "Unresolved document"
    # Editions can share a BGG ID with their main game, and names can repeat.
    # Resolve the workbook's full relationship key, then use unique row IDs in the UI.
    parent_items = defaultdict(list)
    items = defaultdict(list)
    for game in result:
        items[(game["bggid"], game["name"], game["kind"])].append(game)
        parent_items[(game["bggid"], game["name"])].append(game)
    for row in relations:
        possible_parents = parent_items[(row["D"], row["E"])]
        assert possible_parents, f"Unresolved parent: {row}"
        parent = min(possible_parents, key=lambda g: g["kind"] != "主遊戲")
        candidates = items[(row["A"], row["B"], row["C"])]
        assert candidates, f"Unresolved item: {row}"
        for child in candidates:
            if child["id"] not in parent["relatedIds"]:
                parent["relatedIds"].append(child["id"])
            if parent["id"] not in child["parentIds"]:
                child["parentIds"].append(parent["id"])
    shards = [dict() for _ in range(32)]
    for bggid, docs in docs_by_game.items():
        if docs:
            shards[int(bggid) % 32][bggid] = docs
    for index, shard in enumerate(shards):
        write_json(ROOT / f"data/essen-documents/{index}.json", shard)
    write_json(ROOT / "data/essen.json", result)
    write_json(ROOT / "data/essen-notes.json", [{"label": r.get("A", ""), "text": r.get("B", "")} for r in notes])
    print(f"Exported {len(result)} items, {len(documents)} documents, {len(relations)} relations, {len(originals)} source rows.")
    print(dict(Counter(g["kind"] for g in result)))


if __name__ == "__main__":
    main()
