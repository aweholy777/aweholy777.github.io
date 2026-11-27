#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清除 git 歷史裡外洩的金鑰：改寫 repo 歷史並強制推送（Windows 端專用）。

用法：
  python tasks/purge-history/rewrite_history.py                      # 演練：複本 → 改寫 → 驗證 → 刪除。不推送、不動本機 repo
  python tasks/purge-history/rewrite_history.py --skip-upload-check  # 演練時略過「影片已全數上傳」檢查
  python tasks/purge-history/rewrite_history.py --push               # 真正執行：檢查 → 備份 → 改寫 → 驗證 → 強制推送 → 本機對齊

為什麼在系統暫存目錄的「鏡像複本」上改寫，而不是直接改本機 repo：
  本機的 00:05 排程（tasks/daily-qt/daily_qt_local.py）會 git push。若先改寫本機、再慢慢推送，
  中途一出錯，本機與遠端就成了兩套歷史。所以先在複本上做完並驗證，最後一步才推送；
  推送成功後才讓本機 repo 對齊新歷史。任何一步失敗都會停下來，遠端與本機維持原狀。

只用到 git、uvx（臨時執行 git-filter-repo，不裝進專案）與 Python 標準庫。
金鑰內容全程不顯示、不寫入任何檔案（掃描結果只輸出筆數）。

設計與驗收見同目錄 plan.md。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BRANCH = "main"

# 要從「所有歷史」移除的檔案：2 個含金鑰的設定檔快照、2 張早已刪除的舊大圖（約 49 MiB）
REMOVE_PATHS = [
    "video-pipeline/_new_settings.json",
    "video-pipeline/_claude2_settings.json",
    "static/images/聖經難字注音_1.jpg",
    "static/images/聖經難字注音_2.jpg",
]
# 歷史內容中所有「看起來像金鑰」的字串一律以固定文字覆蓋（git-filter-repo --replace-text 規則，Python regex）
REPLACE_RULES = "\n".join([
    r"regex:\bsk-[A-Za-z0-9_-]{20,}==>[已移除的 API key]",
    r"regex:\bgh[pousr]_[A-Za-z0-9]{30,}==>[已移除的 GitHub token]",
    r"regex:\bAIza[0-9A-Za-z_-]{35}==>[已移除的 Google API key]",
    r"regex:-----BEGIN [A-Z ]*PRIVATE KEY-----==>[已移除的私鑰]",
]) + "\n"
SECRET_RES = [
    re.compile(rb"\bsk-[A-Za-z0-9_\-]{20,}"),
    re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(rb"\bAIza[0-9A-Za-z_\-]{35}\b"),
    re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]
# upload_mac.sh 的「收工保險」commit：Mac 之後的每個上傳 commit 都會包含它，代表 Mac 已拿到退休邏輯，
# 影片傳完後就不會再 pull／push（否則改寫歷史後 Mac 會用舊歷史做 rebase）。
KILLSWITCH_COMMIT = "4b9a7041"
MAC_IDLE_HOURS = 10          # 改寫前，Mac 必須已經這麼多小時沒有新的上傳 commit
MAC_HOSTS = ["haoguozi@192.168.68.60", "haoguozi@192.168.68.59"]   # 最佳努力；連不上不影響主流程
GH_USER = "aweholy777"


class NotReady(Exception):
    """條件還沒到期（影片沒傳完／Mac 還在動）：不是錯誤，等下一次再試。"""


def sh(args, cwd=None, check=True, timeout=3600) -> subprocess.CompletedProcess:
    r = subprocess.run([str(a) for a in args], cwd=None if cwd is None else str(cwd),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if check and r.returncode != 0:
        tail = (r.stderr or r.stdout or "").strip()[-500:]
        raise RuntimeError(f"指令失敗（exit {r.returncode}）：{' '.join(map(str, args))[:150]}\n{tail}")
    return r


def out(args, cwd=None) -> str:
    return sh(args, cwd=cwd).stdout.strip()


# ---------------------------------------------------------------- 檢查
def precheck(skip_upload_check: bool) -> dict:
    if out(["git", "status", "--porcelain"], REPO):
        raise RuntimeError("本機工作目錄不乾淨，請先 commit 或處理掉再執行")
    if out(["git", "rev-list", "--count", f"origin/{BRANCH}..{BRANCH}"], REPO) != "0":
        raise RuntimeError("本機 main 有還沒 push 的 commit，先處理再執行")
    sh(["git", "fetch", "origin"], REPO)
    if out(["git", "rev-list", "--count", f"origin/{BRANCH}..{BRANCH}"], REPO) != "0":
        raise RuntimeError("fetch 後本機 main 有未推送的 commit，先處理再執行")
    sh(["git", "merge-base", "--is-ancestor", KILLSWITCH_COMMIT, f"origin/{BRANCH}"], REPO)

    if not skip_upload_check:
        lib = json.loads(out(["git", "show", f"origin/{BRANCH}:data/qtvideos.json"], REPO))
        left = {t["id"]: int(t["passage_count"]) - int(t["video_count"]) for t in lib["testaments"]}
        if any(left.values()):
            raise NotReady(f"影片尚未全數上傳，剩：{left}")
        recent = out(["git", "log", f"origin/{BRANCH}", f"--since={MAC_IDLE_HOURS} hours",
                      "--format=%s", "--grep=^mac upload:"], REPO)
        if recent:
            raise NotReady(f"Mac 最近 {MAC_IDLE_HOURS} 小時內還有上傳紀錄（{recent.splitlines()[0]}），先等它收工")

    if GH_USER:
        # gh auth status 把內容印在 stderr；帳號名稱在「Active account: true」的上一行
        r = sh(["gh", "auth", "status"], check=False)
        lines = ((r.stdout or "") + (r.stderr or "")).splitlines()
        me = None
        for i, ln in enumerate(lines):
            if "Active account: true" in ln:
                for j in range(i, -1, -1):
                    m = re.search(r"account\s+(\S+)", lines[j])
                    if m:
                        me = m.group(1)
                        break
                break
        if me is None:
            raise RuntimeError("無法判讀 gh 目前的帳號，停止")
        if me != GH_USER:
            raise RuntimeError(f"gh 目前的帳號是 {me}，不是 {GH_USER}；先執行 gh auth switch --user {GH_USER}")

    return {
        "tip": out(["git", "rev-parse", f"origin/{BRANCH}"], REPO),
        "tree": out(["git", "rev-parse", f"origin/{BRANCH}^{{tree}}"], REPO),
        "url": out(["git", "remote", "get-url", "origin"], REPO),
    }


def backup() -> Path:
    """完整備份（含舊歷史）到 video-output/（該資料夾已 gitignore，只留本機）。"""
    folder = REPO / "video-output"
    folder.mkdir(exist_ok=True)
    path = folder / f"history-backup-{dt.date.today():%Y%m%d}.bundle"
    sh(["git", "bundle", "create", path, "--all"], REPO)
    sh(["git", "bundle", "verify", path], REPO)
    if path.stat().st_size < 50_000_000:
        raise RuntimeError(f"備份檔異常地小（{path.stat().st_size} bytes），停止")
    return path


# ---------------------------------------------------------------- 改寫與驗證
def rewrite_mirror(url: str, work: Path) -> tuple[Path, int]:
    mirror = work / "repo.git"
    sh(["git", "clone", "--mirror", url, mirror], timeout=3600)
    before = int(out(["git", "rev-list", "--count", "--all"], mirror))
    rules = work / "replace-rules.txt"
    rules.write_text(REPLACE_RULES, encoding="utf-8", newline="\n")
    args = ["uvx", "git-filter-repo", "--force", "--invert-paths"]
    for p in REMOVE_PATHS:
        args += ["--path", p]
    args += ["--replace-text", rules]
    sh(args, cwd=mirror, timeout=3600)
    rules.unlink(missing_ok=True)
    return mirror, before


def count_secret_hits(repo: Path) -> tuple[int, int]:
    """掃描 repo 所有版本的文字內容，回傳（含金鑰樣式的檔案版本數, 掃過的文字檔案版本數）。只回傳數字。

    git cat-file --batch 預設把「整行」當成物件名稱，而 rev-list --objects 的輸出是「SHA 路徑」，
    直接串接會全部變成 missing；所以這裡只把 SHA 餵進去。"""
    listed = out(["git", "rev-list", "--objects", "--all"], repo).split("\n")
    shas = [ln.split()[0] for ln in listed if ln.strip()]
    cat = subprocess.Popen(["git", "cat-file", "--batch"], cwd=str(repo), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    hits = scanned = 0
    try:
        for sha in shas:
            cat.stdin.write((sha + "\n").encode("ascii"))
            cat.stdin.flush()
            parts = cat.stdout.readline().split()
            if len(parts) < 3:      # missing / dangling：不該發生，略過並由下面的計數發現
                continue
            size = int(parts[2])
            data = cat.stdout.read(size)
            cat.stdout.read(1)
            if size > 6_000_000 or b"\x00" in data[:4000]:
                continue
            scanned += 1
            if any(rx.search(data) for rx in SECRET_RES):
                hits += 1
    finally:
        cat.stdin.close()
        cat.wait()
    return hits, scanned


def remove_workdir(work: Path) -> None:
    """Windows 上 git 的 pack 檔是唯讀的，shutil.rmtree 預設刪不掉。刪不乾淨只警告，不影響主流程。"""
    def force(func, path, _exc):
        try:
            os.chmod(path, stat.S_IWRITE)
        except OSError:
            pass
        func(path)
    try:
        shutil.rmtree(work, onexc=force)          # Python 3.12+
    except TypeError:
        shutil.rmtree(work, onerror=force)        # 舊版 Python
    except OSError as exc:
        print(f"警告：暫存目錄沒能完全刪除（{work}）：{exc}", file=sys.stderr)


def verify(mirror: Path, old_tree: str) -> str:
    new_tip = out(["git", "rev-parse", f"refs/heads/{BRANCH}"], mirror)
    new_tree = out(["git", "rev-parse", f"refs/heads/{BRANCH}^{{tree}}"], mirror)
    if new_tree != old_tree:
        raise RuntimeError("改寫後 HEAD 的內容與改寫前不同，停止（尚未推送）")
    names = set(out(["git", "-c", "core.quotepath=false", "log", "--all", "--format=", "--name-only"], mirror).splitlines())
    still = [p for p in REMOVE_PATHS if p in names]
    if still:
        raise RuntimeError(f"改寫後歷史裡仍有應移除的檔案：{still}（尚未推送）")
    hits, scanned = count_secret_hits(mirror)
    if scanned < 1000:
        raise RuntimeError(f"掃描異常：只掃到 {scanned} 個文字檔案版本（停止，尚未推送）")
    if hits:
        raise RuntimeError(f"改寫後歷史裡仍有 {hits} 個檔案版本含金鑰樣式（尚未推送）")
    return new_tip, hits, scanned


# ---------------------------------------------------------------- 推送與對齊
def remote_tip(url: str) -> str:
    r = sh(["git", "ls-remote", url, f"refs/heads/{BRANCH}"], REPO)
    return r.stdout.split()[0]


def push(mirror: Path, url: str, old_tip: str, new_tip: str) -> None:
    if remote_tip(url) != old_tip:
        raise RuntimeError("遠端 main 在改寫期間有了新的 commit，停止（尚未推送）；請重新執行")
    if "origin" not in out(["git", "remote"], mirror).splitlines():
        sh(["git", "remote", "add", "origin", url], mirror)
    sh(["git", "push", "--force", "origin", f"refs/heads/{BRANCH}:refs/heads/{BRANCH}"], mirror)
    if remote_tip(url) != new_tip:
        raise RuntimeError("推送後遠端 tip 與預期不符，請立即檢查")


def resync_local(old_tip: str) -> None:
    sh(["git", "fetch", "origin"], REPO)
    if out(["git", "rev-parse", BRANCH], REPO) != old_tip or out(["git", "status", "--porcelain"], REPO):
        raise RuntimeError("本機 repo 在改寫期間有變動，未自動 reset；請手動執行 git reset --hard origin/" + BRANCH)
    sh(["git", "reset", "--hard", f"origin/{BRANCH}"], REPO)
    # 清掉本機還留著的舊物件（舊歷史已備份在 bundle）
    sh(["git", "reflog", "expire", "--expire=now", "--all"], REPO)
    sh(["git", "gc", "--prune=now", "--quiet"], REPO)


def try_mac_resync() -> str:
    """最佳努力：停掉 Mac 的上傳排程，並把 Mac 上的專案對齊新歷史。連不上就回報，不影響主流程。"""
    script = (
        "launchctl bootout gui/$(id -u)/com.cmtc.qtupload 2>/dev/null; "
        "launchctl disable gui/$(id -u)/com.cmtc.qtupload 2>/dev/null; "
        "cd ~/qtproject && git status --short > ~/mac-status-before-history-rewrite.txt 2>&1; "
        "git fetch origin && git reset --hard origin/main && git log --oneline -1"
    )
    for host in MAC_HOSTS:
        r = sh(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "-o", "StrictHostKeyChecking=yes",
                host, script], check=False, timeout=120)
        if r.returncode == 0:
            return f"已透過 {host} 停掉 Mac 排程並重新同步（Mac HEAD：{r.stdout.strip().splitlines()[-1][:60] if r.stdout.strip() else '?'})"
    return "連不上 Mac（" + "、".join(MAC_HOSTS) + "），Mac 維持原狀。其上傳腳本已內建退休邏輯，不會再 pull／push；之後手動同步即可。"


# ---------------------------------------------------------------- 主流程
def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="清除 git 歷史裡外洩的金鑰")
    ap.add_argument("--push", action="store_true", help="真正推送（預設只演練）")
    ap.add_argument("--skip-upload-check", action="store_true", help="略過「影片已全數上傳」檢查（只供演練）")
    args = ap.parse_args(argv)

    try:
        info = precheck(args.skip_upload_check)
    except NotReady as e:
        print(f"[尚不執行] {e}")
        return 2

    work = Path(tempfile.mkdtemp(prefix="qt-purge-history-"))
    try:
        print(f"[1/4] 複製遠端 repo 到暫存目錄並改寫歷史…")
        mirror, before = rewrite_mirror(info["url"], work)
        print(f"[2/4] 驗證改寫結果…")
        new_tip, hits, scanned = verify(mirror, info["tree"])
        after = int(out(["git", "rev-list", "--count", "--all"], mirror))
        print(f"      commit 數 {before} -> {after}；掃描 {scanned} 個文字檔案版本，金鑰樣式 {hits} 筆")
        print(f"      改寫前 tip {info['tip'][:10]}  ->  改寫後 tip {new_tip[:10]}")
        if not args.push:
            print("[演練完成] 未推送、未動本機 repo。加 --push 才會真正執行。")
            return 0

        print(f"[3/4] 備份 -> {backup()}")
        push(mirror, info["url"], info["tip"], new_tip)
        print("      已強制推送 origin/" + BRANCH)

        print(f"[4/4] 本機 repo 對齊新歷史…")
        resync_local(info["tip"])
        print(f"      完成。Mac：{try_mac_resync()}")
        print("[完成] GitHub 歷史已清除金鑰。接下來請確認網站正常，並聯絡 GitHub Support 請他們清掉快取的舊 commit。")
        return 0
    finally:
        remove_workdir(work)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except NotReady as exc:
        print(f"[尚不執行] {exc}")
        sys.exit(2)
    except Exception as exc:  # noqa: BLE001 - 最外層統一回報，不顯示任何金鑰內容
        print(f"[失敗，已停止] {exc}", file=sys.stderr)
        sys.exit(1)
