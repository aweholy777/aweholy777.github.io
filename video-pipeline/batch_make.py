#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch_make.py — 批次製作 QT 朗讀影片（士兵執行用）

用法：
  python batch_make.py --src content/daily-qt/ntqt --outdir video-output/ntqt --limit 5
  python batch_make.py --src content/daily-qt/otqt --outdir video-output/otqt \
      --from 2026-01-01 --to 2026-05-31 --result tasks/qt-video-pilot/result.md

特性：
- 已存在的 mp4 自動跳過 → 中斷後重跑即可續做
- 每篇之間 sleep（預設 2 秒），避免 Edge TTS 限流；429/失敗自動重試一次
- 結束時寫 result.md 摘要（軍師只讀這份）＋ log 明細
"""
import argparse
import time
from datetime import datetime
from pathlib import Path

from make_video import make_one, DEFAULT_VOICE, DEFAULT_RATE


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="文章目錄，如 content/daily-qt/ntqt")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--limit", type=int, default=0, help="最多做幾篇（0=不限）")
    ap.add_argument("--from", dest="dfrom", default="", help="起始日期 YYYY-MM-DD（依檔名）")
    ap.add_argument("--to", dest="dto", default="", help="結束日期 YYYY-MM-DD（依檔名）")
    ap.add_argument("--sleep", type=float, default=2.0)
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    ap.add_argument("--rate", default=DEFAULT_RATE)
    ap.add_argument("--bg", default=None)
    ap.add_argument("--font", default="Microsoft JhengHei")
    ap.add_argument("--result", default="", help="result.md 路徑（不給則印到畫面）")
    ap.add_argument("--mode", choices=["static", "head"], default="static")
    ap.add_argument("--workflow", default=None)
    ap.add_argument("--server", default=None, help="local / lan / 完整URL（雙機分流時各開一個批次）")
    a = ap.parse_args()

    files = sorted(p for p in Path(a.src).glob("*.md") if not p.name.startswith("_"))
    if a.dfrom:
        files = [p for p in files if p.stem >= a.dfrom]
    if a.dto:
        files = [p for p in files if p.stem <= a.dto]
    if a.limit:
        files = files[: a.limit]

    done, skipped, failed, warned = [], [], [], []
    t0 = time.time()
    for i, p in enumerate(files, 1):
        try:
            r = make_one(p, a.outdir, a.voice, a.rate, a.bg, a.font,
                         mode=a.mode, workflow=a.workflow, server=a.server)
        except Exception as e:           # 重試一次（限流、網路抖動）
            time.sleep(10)
            try:
                r = make_one(p, a.outdir, a.voice, a.rate, a.bg, a.font,
                         mode=a.mode, workflow=a.workflow, server=a.server)
            except Exception as e2:
                r = {"ok": False, "skipped": False, "warnings": [], "error": str(e2)[:200]}
        tag = "skip" if r.get("skipped") else ("ok" if r["ok"] else "FAIL")
        print(f"[{i}/{len(files)}] {p.name} {tag} {r.get('error','')}", flush=True)
        if r.get("skipped"):
            skipped.append(p.name)
        elif r["ok"]:
            done.append(p.name)
            if r["warnings"]:
                warned.append(f"{p.name}: {';'.join(r['warnings'])}")
        else:
            failed.append(f"{p.name}: {r['error']}")
        if not r.get("skipped"):
            time.sleep(a.sleep)

    mins = (time.time() - t0) / 60
    lines = [
        f"# 批次結果：{a.src} → {a.outdir}",
        f"執行時間：{datetime.now():%Y-%m-%d %H:%M}，耗時 {mins:.1f} 分鐘",
        f"完成 {len(done)} 篇／跳過(已存在) {len(skipped)} 篇／失敗 {len(failed)} 篇",
        "",
        "## 失敗清單" if failed else "## 失敗清單：無",
        *failed[:30],
        "",
        "## 解析警告（需人工抽查）" if warned else "## 解析警告：無",
        *warned[:30],
        "",
        f"總結：{len(done)+len(skipped)}/{len(files)} 篇有影片。" +
        ("全部成功。" if not failed else f"{len(failed)} 篇需軍師裁決。"),
    ]
    report = "\n".join(lines)
    if a.result:
        Path(a.result).parent.mkdir(parents=True, exist_ok=True)
        Path(a.result).write_text(report, encoding="utf-8")
        print(f"\nresult 已寫入 {a.result}")
    else:
        print("\n" + report)


if __name__ == "__main__":
    main()
