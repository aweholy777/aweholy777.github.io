#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nightly_head.py — 每晚自動生成一篇數位主播影片

生產順序（2026-06-11 規則）：
1. 依照聖經書卷順序：新約（ntqt/_index.md 從馬太福音 1 章起）→ 全部做完才換舊約
2. 同一段經文有多篇（不同年份）時，只做「日期最新」的那篇
3. 已生成的（video-output/head 有 mp4）自動跳過，一晚做一篇

用 --dry 可以只列出接下來 10 篇的隊列，不實際生成。
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


def _md_key(path_str: str) -> str:
    """content/daily-qt/<sub>/<date>.md → '<sub>/<date>'（取路徑後兩段）。
    跨機器只比相對結構、不比 csv 絕對路徑前綴；保留書卷以免 ntqt/otqt 同日同名互相誤判。"""
    parts = path_str.strip().replace("\\", "/").rstrip("/").split("/")
    stem = parts[-1].removesuffix(".md")
    sub = parts[-2] if len(parts) >= 2 else ""
    return f"{sub}/{stem}" if sub else stem


def _done_keys():
    """已完成（已上傳/已嵌入）的 '<sub>/<date>' key 集合。"""
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
    for sub, slug in queue:
        md = REPO / "content" / "daily-qt" / sub / f"{slug}.md"
        if not md.exists():
            continue
        if (OUTDIR / f"{sub}_{slug}.mp4").exists():
            continue
        if f"{sub}/{slug}" in done:            # B: csv 已記錄（已上傳）
            continue
        if "{{< youtube" in md.read_text(encoding="utf-8"):  # B: 文章已嵌入
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

    # 解析 --count N 與 --server X（沿用簡易 sys.argv 解析，與 --dry 一致）
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
    for sub, slug, md in todo:
        if made >= count:
            break
        if attempts >= count + 3:   # 容錯上限：避免連續失敗時跑遍整個隊列
            print("連續失敗過多，今晚提前結束。", flush=True)
            break
        attempts += 1
        print(f"[{datetime.datetime.now():%F %T}] 生成 ({made+1}/{count})：[{sub}] {md.name}", flush=True)
        try:
            r = make_one(md, OUTDIR, mode="head", server=server)
            print(r, flush=True)
            if isinstance(r, dict) and r.get("ok"):
                made += 1
        except Exception as e:
            print(f"  生成失敗，跳過 {md.name}：{e}", flush=True)
    if made == 0:
        print("本次沒有成功生成（可能全部完成，或皆失敗）。", flush=True)
    else:
        print(f"本次完成 {made} 篇。", flush=True)
