#!/usr/bin/env python3
"""每天台北 00:05 在本機產生「當日QT」並推上 GitHub。

GitHub Actions 的 schedule 實測會延遲 3.5～6.5 小時，靠它無法準時 00:05。
本機這支腳本準時執行；GitHub 那條 cron 之後跑時會發現內容沒變而自動跳過。

輸出規則（no_agent）：成功且無變更 → 完全靜默；失敗 → 印出錯誤訊息。
"""
from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys

REPO = r"D:\AI成品\qtproject"
GH = r"C:\Program Files\GitHub CLI\gh.exe"
GEN = os.path.join(REPO, "tasks", "daily-qt", "generate_today_qt.py")


def sh(args, timeout=300):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    try:
        r = subprocess.run(args, cwd=REPO, capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace", env=env)
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT: " + " ".join(args)


def main():
    today = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=8)).strftime("%Y-%m-%d")
    rc, out, err = sh(["git", "pull", "--rebase", "--autostash", "origin", "main"], 240)
    if rc != 0:
        print("X 當日QT 本機排程失敗（git pull）：" + (err or out)[-400:])
        return 1
    rc, out, err = sh([sys.executable, GEN], 900)
    if rc != 0:
        print("X 當日QT 產生失敗（%s）：%s" % (today, (err or out)[-400:]))
        return 1
    rc, out, _ = sh(["git", "status", "--porcelain", "content/today-qt.md"], 60)
    if not out.strip():
        return 0
    sh(["git", "add", "content/today-qt.md"], 60)
    rc, out, err = sh(["git", "commit", "-m", "daily-qt: %s 當日QT 自動更新（本機 00:05）" % today], 120)
    if rc != 0:
        print("X 當日QT commit 失敗（%s）：%s" % (today, (err or out)[-400:]))
        return 1
    if os.path.exists(GH):
        sh([GH, "auth", "switch", "--user", "aweholy777"], 60)
    rc, out, err = sh(["git", "push", "origin", "main"], 240)
    if rc != 0:
        sh(["git", "pull", "--rebase", "--autostash", "origin", "main"], 240)
        rc, out, err = sh(["git", "push", "origin", "main"], 240)
    if rc != 0:
        print("X 當日QT 推送失敗（%s）：%s" % (today, (err or out)[-400:]))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
