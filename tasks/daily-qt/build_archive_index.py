#!/usr/bin/env python3
"""產生 static/data/archive-index.json（給 /qt-generator/ 前端比對舊文章用）。

用法：python tasks/daily-qt/build_archive_index.py
典藏文章新增後重跑一次即可。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CONTENT = REPO / "content" / "daily-qt"
OUT = REPO / "static" / "data" / "archive-index.json"

BOOK_ALIASES = {
    "詩": "詩篇",
    "箴言書": "箴言",
    "約翰壹書": "約翰一書",
    "約翰貳書": "約翰二書",
    "約翰參書": "約翰三書",
}

TITLE_RE = re.compile(
    r"QT\s*(?P<book>[\u4e00-\u9fff]+?)\s*(?P<ch1>\d+)\s*(?:[：:]|篇)\s*(?P<v1>\d+)"
    r"\s*[∼~\-－—～]\s*(?:(?P<ch2>\d+)\s*[：:]\s*)?(?P<v2>\d+)\s*節?"
)
PSALM_WHOLE_RE = re.compile(r"QT\s*(?P<book>詩篇|詩)\s*(?P<ch1>\d+)\s*篇\s*$")


def parse_title_range(title: str):
    m = TITLE_RE.search(title)
    if m:
        book = BOOK_ALIASES.get(m.group("book"), m.group("book"))
        ch1, v1 = int(m.group("ch1")), int(m.group("v1"))
        ch2 = int(m.group("ch2")) if m.group("ch2") else ch1
        v2 = int(m.group("v2"))
        return book, [ch1, v1], [ch2, v2]
    mp = PSALM_WHOLE_RE.search(title)
    if mp:
        ch1 = int(mp.group("ch1"))
        return "詩篇", [ch1, 1], [ch1, 200]
    return None


def main() -> int:
    items = []
    for sub in ("otqt", "ntqt"):
        d = CONTENT / sub
        if not d.exists():
            continue
        for f in sorted(d.glob("*.md")):
            if f.stem.startswith("_"):
                continue
            try:
                with f.open(encoding="utf-8", errors="replace") as fh:
                    head = [next(fh) for _ in range(6)]
            except (StopIteration, OSError):
                continue
            title = ""
            for line in head:
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip('"')
                    break
            parsed = parse_title_range(title)
            if not parsed:
                continue
            book, start, end = parsed
            items.append({
                "date": f.stem,
                "title": title,
                "book": book,
                "start": start,
                "end": end,
                "url": f"/daily-qt/{sub}/{f.stem}/",
            })
    items.sort(key=lambda x: x["date"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(items, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(items)} 篇 → {OUT.relative_to(REPO)} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
