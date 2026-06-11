#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nightly_head.py — 每晚自動生成一篇數位主播影片

生產順序（2026-06-11 規則）：
1. 依照聖經書卷順序：新約（ntqt/_index.md 從馬太福音 1 章起）→ 全部做完才換舊約
2. 同一段經文有多篇（不同年份）時，只做「日期最新」的那篇
3. 已生成的（video-output/head 有 mp4）自動跳過，一晚做一篇

用 --dry 可以只列出接下來 10 篇的隊列，不實際生成。
"""
import datetime
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))

OUTDIR = REPO / "video-output" / "head"
ENTRY = re.compile(r"^\s*-\s*\[(.+?)\s*QT\s*(.+?)\]\((\d{4}-\d{2}-\d{2})/?\)", re.M)


def norm_key(passage: str) -> str:
    """經文段落正規化：去空白、統一波浪號，作為重複判斷的 key"""
    s = re.sub(r"\s+", "", passage)
    return s.replace("～", "~").replace("〜", "~")


def build_queue():
    """回傳 [(sub, slug), ...]：新約書卷順在前、舊約在後，重複經文取日期最新"""
    queue = []
    for sub in ("ntqt", "otqt"):
        idx = REPO / "content" / "daily-qt" / sub / "_index.md"
        if not idx.exists():
            continue
        best = {}    # key -> 最新 slug（日期字串比大小）
        order = []   # key 首次出現順序 = 書卷順序
        for m in ENTRY.finditer(idx.read_text(encoding="utf-8")):
            _, passage, slug = m.groups()
            key = norm_key(passage)
            if key not in best:
                best[key] = slug
                order.append(key)
            elif slug > best[key]:
                best[key] = slug
        queue += [(sub, best[k]) for k in order]
    return queue


def pending(queue):
    for sub, slug in queue:
        md = REPO / "content" / "daily-qt" / sub / f"{slug}.md"
        if not md.exists():
            continue
        if (OUTDIR / f"{slug}.mp4").exists():
            continue
        yield sub, slug, md


if __name__ == "__main__":
    q = build_queue()
    todo = pending(q)

    if "--dry" in sys.argv:
        print(f"隊列總長 {len(q)} 篇（去重後）。接下來 10 篇：")
        for i, (sub, slug, md) in enumerate(todo):
            if i >= 10:
                break
            title = ""
            for line in md.read_text(encoding="utf-8").splitlines():
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip('"')
                    break
            print(f"  {i+1}. [{sub}] {slug}  {title}")
        sys.exit(0)

    from make_video import make_one
    for sub, slug, md in todo:
        print(f"[{datetime.datetime.now():%F %T}] 今晚生成：[{sub}] {md.name}", flush=True)
        r = make_one(md, OUTDIR, mode="head")
        print(r, flush=True)
        break
    else:
        print("沒有待生成的文章（全部完成！）")
