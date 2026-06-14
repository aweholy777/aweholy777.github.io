#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""yt_publish.py — 上傳 QT 影片到 YouTube ＋ 把影片嵌入對應文章

用法：
  # 上傳單支並嵌入（影片檔名 = 文章日期，自動找到對應 md）
  python video-pipeline\\yt_publish.py --video video-output\\head\\2026-05-30.mp4

  # 掃描 head 目錄，把還沒上傳的全部處理（每日排程用）
  python video-pipeline\\yt_publish.py --auto

  # 私隱設定：public（預設）/ unlisted / private
  python video-pipeline\\yt_publish.py --video ... --privacy unlisted

第一次執行會開瀏覽器要求 Google 授權（按允許一次即可）。
對照表：video-pipeline/yt_uploaded.csv（md 路徑, videoId, 網址, 時間）
"""
import argparse
import csv
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

HERE = Path(__file__).parent
REPO = HERE.parent
PUB_REPO = Path(r"C:\Users\aweholy\qt-publish\aweholy777.github.io")  # 獨立發布副本
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET = HERE / "client_secret.json"
TOKEN = HERE / "yt_token.json"
CSV_PATH = HERE / "yt_uploaded.csv"

sys.path.insert(0, str(HERE))
from extract_text import extract  # noqa: E402


def get_service(allow_interactive=True):
    """allow_interactive=False（如 --auto 夜間排程）時，憑證無效一律報錯退出，
    絕不開瀏覽器互動授權（run_local_server 會讓無人值守排程永久卡死）。"""
    creds = None
    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                raise RuntimeError(
                    f"YouTube token 更新失敗（可能已撤銷/過期/離線）：{e}。"
                    "請在有桌面的環境重新授權（yt_first_run）後再排程。") from e
        elif allow_interactive:
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
            creds = flow.run_local_server(port=0)
        else:
            raise RuntimeError(
                "YouTube 憑證無效且為非互動模式（--auto）：不開啟瀏覽器授權以免夜間排程卡死。"
                "請先手動重新授權後再排程。")
        TOKEN.write_text(creds.to_json(), encoding="utf-8")
    return build("youtube", "v3", credentials=creds)


def find_md(video_path: Path):
    """依檔名（日期）找對應文章：先 ntqt 再 otqt"""
    stem = video_path.stem
    for sub in ("ntqt", "otqt"):
        p = REPO / "content" / "daily-qt" / sub / f"{stem}.md"
        if p.exists():
            return p, sub
    return None, None


def _md_name(path_str: str) -> str:
    """取 csv 路徑欄的檔名（跨機 dedup 用，不比對絕對路徑——舊機 aweholy 與新機 user 路徑不同）"""
    return Path(path_str.strip().replace("\\", "/")).name


def already_uploaded(md_path: Path) -> bool:
    if not CSV_PATH.exists():
        return False
    target = md_path.name
    with open(CSV_PATH, encoding="utf-8") as f:
        return any(row and row[0] and _md_name(row[0]) == target for row in csv.reader(f))


def upload(yt, video_path: Path, title: str, description: str, privacy: str) -> str:
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:4900],
            "categoryId": "27",          # Education
            "defaultLanguage": "zh-TW",
        },
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(str(video_path), chunksize=8 * 1024 * 1024,
                            resumable=True, mimetype="video/mp4")
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"  上傳 {int(status.progress() * 100)}%", flush=True)
    return resp["id"]


def embed(md_path: Path, video_id: str) -> bool:
    """在文章圖片行後插入 YouTube 影片（Hugo 內建 shortcode）"""
    text = md_path.read_text(encoding="utf-8")
    if "{{< youtube" in text:
        return False  # 已嵌入過
    shortcode = f"\n{{{{< youtube {video_id} >}}}}\n"
    m = re.search(r"^!\[.*\]\(.*\)\s*$", text, re.M)
    if m:
        pos = m.end()
        text = text[:pos] + "\n" + shortcode + text[pos:]
    else:  # 沒有圖片行就插在 front matter 之後
        fm = re.match(r"^---\s*\n.*?\n---\s*\n", text, re.S)
        pos = fm.end() if fm else 0
        text = text[:pos] + shortcode + text[pos:]
    md_path.write_text(text, encoding="utf-8")
    return True


def publish_one(yt, video_path: Path, privacy: str) -> str:
    md_path, sub = find_md(video_path)
    if md_path is None:
        return f"SKIP {video_path.name}: 找不到對應文章"
    if already_uploaded(md_path):
        return f"SKIP {video_path.name}: 已上傳過"

    info = extract(md_path)
    title = info["title"] or video_path.stem
    url = f"https://cmtc.tw/daily-qt/{sub}/{video_path.stem}/"
    desc = (f"{info['spoken_title']}\n\n"
            f"全文：{url}\n\n"
            f"城市宣培中心 每日QT靈修")
    print(f"上傳 {video_path.name}：{title}", flush=True)
    vid = upload(yt, video_path, title, desc, privacy)
    did_embed = embed(md_path, vid)

    new_file = not CSV_PATH.exists()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["md_path", "video_id", "youtube_url", "uploaded_at"])
        w.writerow([str(md_path), vid, f"https://youtu.be/{vid}",
                    datetime.now().isoformat(timespec="seconds")])
        f.flush()
        os.fsync(f.fileno())   # 影片已上傳成功，務必把 csv 落地，避免下次重傳
    return (f"OK {video_path.name} → https://youtu.be/{vid}"
            + ("（已嵌入文章）" if did_embed else "（文章已有嵌入，未重複）"))


def publish_push(items):
    """在獨立發布副本內：pull → 對副本的 md 做同樣的嵌入 → commit → push。
    完全不動主資料夾的 git（那裡有未整理的變更）。
    items: [(主資料夾 md Path, video_id), ...]"""
    if not items:
        return "publish: 本次無嵌入，跳過"
    if not PUB_REPO.exists():
        return f"publish: 找不到發布副本 {PUB_REPO}（請先跑 setup_publish_clone.bat）"

    def run(*args):
        return subprocess.run(["git", *args], cwd=PUB_REPO, capture_output=True,
                              text=True, encoding="utf-8", errors="replace")

    pull = run("pull", "--ff-only")
    if pull.returncode != 0:
        return "publish: git pull 失敗：" + (pull.stderr or pull.stdout)[-300:]

    changed = []
    for md_path, vid in items:
        rel = md_path.relative_to(REPO)
        clone_md = PUB_REPO / rel
        if clone_md.exists() and embed(clone_md, vid):
            changed.append(str(rel))
            run("add", str(rel))
    if not changed:
        return "publish: 副本無需變更（可能已嵌入過）"

    msg = f"auto: embed youtube videos {datetime.now():%Y-%m-%d %H:%M}"
    c = run("commit", "-m", msg)
    if c.returncode != 0:
        return "publish: commit 失敗：" + (c.stderr or c.stdout)[-300:]
    p = run("push")
    if p.returncode != 0:
        return "publish: push 失敗：" + (p.stderr or p.stdout)[-300:]
    return f"publish: 已推送 {len(changed)} 篇 → 網站將自動部署（{msg}）"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", help="單支影片路徑")
    ap.add_argument("--auto", action="store_true",
                    help="掃描 video-output/head/*.mp4，處理未上傳的（最多 --limit 支）")
    ap.add_argument("--limit", type=int, default=5, help="auto 模式單次上限（配額保護）")
    ap.add_argument("--privacy", default="public",
                    choices=["public", "unlisted", "private"])
    ap.add_argument("--no-push", action="store_true", help="不自動 git push")
    a = ap.parse_args()

    yt = get_service(allow_interactive=not a.auto)
    embedded = []   # [(md_path, video_id)]

    def vid_of(md_path):
        target = md_path.name
        with open(CSV_PATH, encoding="utf-8") as f:
            for row in csv.reader(f):
                if row and row[0] and _md_name(row[0]) == target:
                    return row[1]
        return None

    def _is_quota(e: HttpError) -> bool:
        txt = str(e).lower()
        return getattr(e.resp, "status", None) == 403 and ("quota" in txt or "limit" in txt)

    if a.video:
        v = Path(a.video)
        try:
            msg = publish_one(yt, v, a.privacy)
        except HttpError as e:
            print(f"上傳 {v.name} 失敗（HTTP {getattr(e.resp,'status','?')}）：{e}")
            return
        print(msg)
        if msg.startswith("OK"):
            md, _ = find_md(v)
            embedded.append((md, vid_of(md)))
    elif a.auto:
        vids = sorted((REPO / "video-output" / "head").glob("*.mp4"), reverse=True)
        done = 0
        for v in vids:
            if done >= a.limit:
                break
            try:
                msg = publish_one(yt, v, a.privacy)
            except HttpError as e:
                if _is_quota(e):
                    print("YouTube 配額/上限已用盡，停止本次上傳（其餘留待下次）。", flush=True)
                    break
                print(f"上傳 {v.name} 失敗（HTTP {getattr(e.resp,'status','?')}），跳過。", flush=True)
                continue
            print(msg)
            if msg.startswith("OK"):
                md, _ = find_md(v)
                embedded.append((md, vid_of(md)))
                done += 1
    else:
        print("請指定 --video 或 --auto")
        return
    if not a.no_push:
        print(publish_push(embedded))


if __name__ == "__main__":
    main()
