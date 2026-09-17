#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_qt_library.py — 產生 QT 影音庫資料（data/qtvideos.json）。

來源：
  - content/daily-qt/{otqt,ntqt}/_index.md   書卷順序 + 經文條目（每條 = 一篇文章）
  - video-pipeline/yt_uploaded.csv           已上傳影片的 YouTube ID
輸出：
  - data/qtvideos.json   依新舊約書卷順序，列出各卷影片（YouTube ID、經文、日期）

Hugo 以 data file 讀取：.Site.Data.qtvideos
"""
import csv
import html
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INDEX = REPO / "content" / "daily-qt"
OUT = REPO / "data" / "qtvideos.json"
CSV = REPO / "video-pipeline" / "yt_uploaded.csv"

ENTRY = re.compile(r"^\s*-\s*\[(.+?)\s*QT\s*(.+?)\]\((\d{4}-\d{2}-\d{2})/?\)")
BOOK = re.compile(r"^\s*##\s+(.+?)\s*$")
CSVMD = re.compile(r"daily-qt[\\/](ntqt|otqt)[\\/](\d{4}-\d{2}-\d{2})\.md")

# 顯示順序：舊約 39 卷在前、新約 27 卷在後
TESTAMENTS = [("otqt", "舊約"), ("ntqt", "新約")]


def norm_key(passage: str) -> str:
    """經文去重鍵：去空白、統一波浪號（與 nightly_head 一致）。"""
    s = re.sub(r"\s+", "", passage)
    return s.replace("～", "~").replace("〜", "~")


def decode_passage(raw: str) -> str:
    """索引標題 → 可讀經文：還原 &#126; → ~，壓縮空白。"""
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()


def load_uploaded():
    """{(sub, slug): video_id}"""
    d = {}
    if not CSV.exists():
        return d
    with CSV.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            m = CSVMD.search(row.get("md_path", ""))
            if m:
                vid = (row.get("video_id") or "").strip()
                if vid:
                    d[(m.group(1), m.group(2))] = vid
    return d


def build(up):
    testaments = []
    for tid, tname in TESTAMENTS:
        idx = INDEX / tid / "_index.md"
        books = []
        cur = None
        unmatched = 0
        for line in idx.read_text(encoding="utf-8").splitlines():
            bm = BOOK.match(line)
            if bm:
                cur = {"name": bm.group(1).strip(), "total": 0, "passages": 0,
                       "videos": [], "_seen": set()}
                books.append(cur)
                continue
            if line.lstrip().startswith("- ["):
                em = ENTRY.match(line)
                if not em:
                    unmatched += 1
                    continue
                if cur is None:
                    continue
                passage = decode_passage(em.group(2))
                slug = em.group(3)
                cur["total"] += 1
                key = norm_key(passage)
                if key not in cur["_seen"]:
                    cur["_seen"].add(key)
                    cur["passages"] += 1
                yt = up.get((tid, slug))
                if yt:
                    cur["videos"].append({
                        "slug": slug,
                        "passage": passage,
                        "date": slug,
                        "yt": yt,
                    })
        for b in books:
            b.pop("_seen", None)
        video_count = sum(len(b["videos"]) for b in books)
        passage_count = sum(b["passages"] for b in books)
        testaments.append({
            "id": tid,
            "name": tname,
            "book_count": len(books),
            "video_count": video_count,
            "passage_count": passage_count,
            "books": books,
        })
        if unmatched:
            print(f"  [warn] {tid}: {unmatched} 條索引無法解析")
    # 刻意不放時間戳：內容沒變就不該產生 diff，避免上傳腳本每小時空 commit。
    return {"testaments": testaments}


def main():
    up = load_uploaded()
    data = build(up)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    total = 0
    for t in data["testaments"]:
        total += t["video_count"]
        print(f"{t['name']}: {t['book_count']} 卷, {t['video_count']} 支影片 / {t['passage_count']} 段經文")
    print(f"合計 {total} 支影片 -> {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
