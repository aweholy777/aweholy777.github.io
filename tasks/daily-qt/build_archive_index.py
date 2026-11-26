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
TITLE_RE = re.compile(
    r"QT\s*(?P<book>[\u4e00-\u9fff]+?)\s*(?P<ch1>\d+)\s*[：:]\s*(?P<v1>\d+)"
    r"\s*[∼~\-－—]\s*(?:(?P<ch2>\d+)\s*[：:]\s*)?(?P<v2>\d+)"
)


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
            m = TITLE_RE.search(title)
            if not m:
                continue
            ch2 = int(m.group("ch2")) if m.group("ch2") else int(m.group("ch1"))
            items.append({
                "date": f.stem,
                "title": title,
                "book": m.group("book"),
                "start": [int(m.group("ch1")), int(m.group("v1"))],
                "end": [ch2, int(m.group("v2"))],
                "url": f"/daily-qt/{sub}/{f.stem}/",
            })
    items.sort(key=lambda x: x["date"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(items, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(items)} 篇 → {OUT.relative_to(REPO)} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
