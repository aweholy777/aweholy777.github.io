# -*- coding: utf-8 -*-
"""每日檢查「當日QT」GitHub Actions 排程。
成功且頁面正常 → 完全不輸出（Hermes no_agent cron 空輸出＝不通知）。
失敗／沒跑／頁面沒更新 → 輸出警示，由 cron 發訊息給使用者。
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.request

REPO = r"D:\AI成品\qtproject"
GH_FULL = r"C:\Program Files\GitHub CLI\gh.exe"
WORKFLOW = "daily-qt.yml"
LIVE = "https://cmtc.tw/today-qt/"
UA = "Mozilla/5.0 (cmtc-daily-qt-check)"


def sh(args, timeout=120):
    try:
        return subprocess.run(
            args, capture_output=True, text=True, encoding="utf-8",
            errors="replace", cwd=REPO, timeout=timeout,
        )
    except Exception:
        return None


def fetch_page() -> str:
    req = urllib.request.Request(
        LIVE + f"?cb={dt.datetime.now().timestamp()}",
        headers={"User-Agent": UA},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main() -> int:
    today = dt.datetime.now().strftime("%Y-%m-%d")

    # 1) 以線上頁面為準：有今天日期就一切正常（不論排程怎麼跑、誰補的）
    try:
        html = fetch_page()
    except Exception as e:
        print(f"⚠️ 抓不到 {LIVE}（{e}）")
        return 0

    if today in html:
        return 0  # 靜默，不通知

    # 2) 頁面沒更新 → 找原因
    dates = re.findall(r"20\d{2}-\d{2}-\d{2}", html)
    shown = max(dates) if dates else "（找不到日期）"
    print(f"❌ 今日QT頁面沒有更新（今天 {today}，頁面停在 {shown}）")
    print(LIVE)

    gh = GH_FULL if os.path.exists(GH_FULL) else "gh"
    r = sh([gh, "run", "list", "--workflow", WORKFLOW, "--limit", "1",
            "--json", "conclusion,createdAt,url,databaseId"])
    if r is None or r.returncode != 0:
        print("\n（無法查詢 GitHub Actions 排程狀態）")
        return 0
    try:
        runs = json.loads(r.stdout or "[]")
    except Exception:
        print("\n（排程狀態無法解析）")
        return 0
    if not runs:
        print("\n（查不到「每日當日QT」排程紀錄）")
        return 0

    run = runs[0]
    print(f"\n排程最新一次：{(run.get('createdAt') or '')[:10]} → {run.get('conclusion')}")
    print(run.get("url") or "")

    if run.get("conclusion") == "failure":
        lr = sh([gh, "run", "view", str(run.get("databaseId")), "--log-failed"], timeout=180)
        if lr is not None and lr.stdout:
            raw = [ln for ln in lr.stdout.splitlines() if ln.strip()]
            # 只留真正錯誤訊息，排除 git/清理雜訊
            keys = ("錯誤", "Error", "error", "Traceback", "RuntimeError",
                    "取得失敗", "HTTP Error", "raise ", 'File "')
            hits = [ln for ln in raw if any(k in ln for k in keys)]
            use = (hits[-8:] if hits else raw[-8:])
            if use:
                print("\n錯誤摘要：")
                print("\n".join(use))
    return 0


if __name__ == "__main__":
    sys.exit(main())
