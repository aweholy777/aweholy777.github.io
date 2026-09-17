#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""remove_yt_shortcodes.py — 移除 QT 文章底部的 {{< youtube >}} shortcode。

影片改由 /qt-video/ 影音庫集中呈現，文章頁不再內嵌。
「已上傳」判斷的權威來源是 video-pipeline/yt_uploaded.csv，移除 shortcode 不影響
跳過/重傳邏輯（本腳本會先比對每個 shortcode 是否都在 CSV 有紀錄）。

用法：
  python video-pipeline/remove_yt_shortcodes.py           # dry-run，只報告
  python video-pipeline/remove_yt_shortcodes.py --apply   # 實際寫入
"""
import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ROOT = REPO / "content" / "daily-qt"
CSV = REPO / "video-pipeline" / "yt_uploaded.csv"
YT = re.compile(r"\{\{<\s*youtube\s+([A-Za-z0-9_-]+)\s*>\}\}")


def csv_slugs():
    s = set()
    if CSV.exists():
        with CSV.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                p = (row.get("md_path") or "").replace("\\", "/")
                if p:
                    s.add(Path(p).stem)
    return s


def strip_trailing_shortcode(text):
    """移除檔尾的 youtube shortcode 及其前的空白行；保留其餘內容與行尾格式。"""
    lines = text.splitlines(keepends=True)
    changed = False
    while lines and lines[-1].strip() == "":
        lines.pop()
    while lines and YT.search(lines[-1]):
        lines.pop()
        changed = True
        while lines and lines[-1].strip() == "":
            lines.pop()
    if not changed:
        return text, False
    out = "".join(lines)
    if out and not out.endswith(("\n", "\r")):
        out += "\r\n" if "\r\n" in text else "\n"
    return out, True


def main():
    apply = "--apply" in sys.argv
    csvset = csv_slugs()
    total = changed = 0
    not_in_csv = []
    for sub in ("ntqt", "otqt"):
        for md in sorted((ROOT / sub).glob("*.md")):
            txt = md.read_text(encoding="utf-8")
            if "{{< youtube" not in txt:
                continue
            total += 1
            if md.stem not in csvset:
                not_in_csv.append(f"{sub}/{md.name}")
            new, did = strip_trailing_shortcode(txt)
            if did:
                changed += 1
                if apply:
                    md.write_text(new, encoding="utf-8", newline="")
    print(f"含 shortcode 的檔案: {total}")
    print(f"{'已移除' if apply else '可移除'}: {changed}")
    if not_in_csv:
        print(f"[警告] 有 shortcode 但不在 yt_uploaded.csv 的: {len(not_in_csv)}")
        for x in not_in_csv[:20]:
            print("   ", x)
    else:
        print("全部 shortcode 在 yt_uploaded.csv 都有紀錄（撤掉安全）。")
    if not apply:
        print("（dry-run；加 --apply 才實際寫入）")


if __name__ == "__main__":
    main()
