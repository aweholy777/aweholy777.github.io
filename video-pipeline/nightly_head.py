#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nightly_head.py — 每晚自動生成數位主播影片

生產規則：
1. 依聖經書卷順序：新約（ntqt）→ 全部做完才換舊約。
2. 同段經文多篇（不同年份）只做日期最新那篇。
3. 已生成 / 已上傳(csv) / 已嵌入(shortcode) 的自動跳過。
4. 主播按「書卷」輪替：第1卷=主播1(presenter.png)、第2卷=主播2(presenter2.png)、
   第3卷=主播1…（presenter2.png 不存在時退回主播1）。

--dry 列出接下來 10 篇（含書卷序與主播），不實際生成。
--count N 本次生成 N 篇；--server local/lan/5090/完整URL。
"""
import csv
import datetime
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))

OUTDIR = REPO / "video-output" / "head"
ENTRY = re.compile(r"^\s*-\s*\[(.+?)\s*QT\s*(.+?)\]\((\d{4}-\d{2}-\d{2})/?\)")
BOOK = re.compile(r"^\s*##\s+(.+?)\s*$")

P1 = HERE / "assets" / "presenter.png"
P2 = HERE / "assets" / "presenter2.png"


def presenter_for(book_seq):
    """書卷序輪替主播：奇數卷→主播1，偶數卷→主播2（presenter2 缺則退回主播1）。"""
    if book_seq % 2 == 0 and P2.exists():
        return P2
    return P1


def norm_key(passage: str) -> str:
    s = re.sub(r"\s+", "", passage)
    return s.replace("～", "~").replace("〜", "~")


def build_queue():
    """回傳 [(sub, slug, book_seq), ...]：書卷順序在前、重複經文取日期最新。
    book_seq 跨新舊約連續累計（1 起算），供主播輪替使用。"""
    items = []        # (sub, key, book_seq) 依首次出現序
    best = {}         # (sub, key) -> 最新 slug
    book_seq = 0
    for sub in ("ntqt", "otqt"):
        idx = REPO / "content" / "daily-qt" / sub / "_index.md"
        if not idx.exists():
            continue
        seen_books = set()
        for line in idx.read_text(encoding="utf-8").splitlines():
            bm = BOOK.match(line)
            if bm:
                book = bm.group(1)
                if book not in seen_books:
                    seen_books.add(book)
                    book_seq += 1
                continue
            em = ENTRY.search(line)
            if not em:
                continue
            _, passage, slug = em.groups()
            key = (sub, norm_key(passage))
            if key not in best:
                best[key] = slug
                items.append((sub, key, book_seq))
            elif slug > best[key]:
                best[key] = slug
    return [(sub, best[key], seq) for (sub, key, seq) in items]


def _md_key(path_str: str) -> str:
    """content/daily-qt/<sub>/<date>.md → '<sub>/<date>'（取路徑後兩段，跨機相容）。"""
    parts = path_str.strip().replace("\\", "/").rstrip("/").split("/")
    stem = parts[-1].removesuffix(".md")
    sub = parts[-2] if len(parts) >= 2 else ""
    return f"{sub}/{stem}" if sub else stem


def _done_keys():
    keys = set()
    csv_path = REPO / "video-pipeline" / "yt_uploaded.csv"
    if csv_path.exists():
        with open(csv_path, encoding="utf-8") as f:
            for row in csv.reader(f):
                if row and row[0] and row[0] != "md_path":
                    keys.add(_md_key(row[0]))
    return keys


def pending(queue):
    done = _done_keys()
    for sub, slug, seq in queue:
        md = REPO / "content" / "daily-qt" / sub / f"{slug}.md"
        if not md.exists():
            continue
        if (OUTDIR / f"{sub}_{slug}.mp4").exists():
            continue
        if f"{sub}/{slug}" in done:
            continue
        if "{{< youtube" in md.read_text(encoding="utf-8"):
            continue
        yield sub, slug, md, seq


if __name__ == "__main__":
    q = build_queue()
    todo = pending(q)

    if "--dry" in sys.argv:
        print(f"隊列總長 {len(q)} 篇（去重後）。接下來 10 篇：")
        for i, (sub, slug, md, seq) in enumerate(todo):
            if i >= 10:
                break
            who = "主播1" if presenter_for(seq) == P1 else "主播2"
            title = ""
            for line in md.read_text(encoding="utf-8").splitlines():
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip('"')
                    break
            print(f"  {i+1}. [{sub}] {slug}  第{seq}卷 → {who}  {title}")
        sys.exit(0)

    def _argval(flag, default=None):
        if flag in sys.argv:
            i = sys.argv.index(flag)
            if i + 1 < len(sys.argv):
                return sys.argv[i + 1]
        return default
    count = int(_argval("--count", "1"))
    server = _argval("--server", None)

    from make_video import make_one
    made = 0
    attempts = 0
    for sub, slug, md, seq in todo:
        if made >= count:
            break
        if attempts >= count + 3:
            print("連續失敗過多，今晚提前結束。", flush=True)
            break
        attempts += 1
        who = "主播1" if presenter_for(seq) == P1 else "主播2"
        print(f"[{datetime.datetime.now():%F %T}] 生成 ({made+1}/{count})：[{sub}] {md.name}  第{seq}卷 {who}", flush=True)
        try:
            r = make_one(md, OUTDIR, mode="head", server=server, bg=str(presenter_for(seq)))
            print(r, flush=True)
            if isinstance(r, dict) and r.get("ok"):
                made += 1
        except Exception as e:
            print(f"  生成失敗，跳過 {md.name}：{e}", flush=True)
    if made == 0:
        print("本次沒有成功生成（可能全部完成，或皆失敗）。", flush=True)
    else:
        print(f"本次完成 {made} 篇。", flush=True)
