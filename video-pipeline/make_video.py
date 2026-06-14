#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_video.py — 單篇 QT 文章 → 16:9 朗讀影片（Edge TTS + ffmpeg）

用法：
  python make_video.py content/daily-qt/ntqt/2026-05-30.md
  python make_video.py <文章.md> --outdir video-output/ntqt --voice zh-TW-HsiaoChenNeural

流程：extract_text 解析 → Edge TTS 產 mp3＋逐字時間戳 → 組 SRT 字幕 → ffmpeg 合成 mp4
輸出：<outdir>/<檔名>.mp4（已存在則跳過，可安全重跑）
"""
import argparse
import asyncio
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ffmpeg 絕對路徑：優先用 imageio_ffmpeg 內建（含 libass，不依賴 PATH），找不到才退回 PATH 的 ffmpeg
try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = "ffmpeg"

import edge_tts

from extract_text import extract

DEFAULT_VOICE = "zh-TW-HsiaoChenNeural"
DEFAULT_RATE = "+10%"          # 朗讀稍快，全文較長
MAX_CUE_CHARS = 20             # 單行字幕長度上限
SENT_BREAK = "。！？；："


def _ticks_to_srt(t: int) -> str:
    """100ns ticks → SRT 時間格式"""
    ms = t // 10_000
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1_000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def _split_cues(text: str):
    """把全文切成字幕行（滿 MAX_CUE_CHARS 或遇標點斷行）"""
    cues, buf = [], ""
    for ch in text:
        if ch == "\n":
            if buf.strip():
                cues.append(buf.strip())
            buf = ""
            continue
        buf += ch
        if len(buf) >= MAX_CUE_CHARS or ch in SENT_BREAK or ch in "，、":
            if buf.strip():
                cues.append(buf.strip())
            buf = ""
    if buf.strip():
        cues.append(buf.strip())
    return cues


def _audio_seconds(mp3_path: Path) -> float:
    # 用 FFMPEG（imageio 內建，不依賴 PATH 的 ffprobe）讀音訊時長：解析 stderr 的 Duration
    r = subprocess.run([FFMPEG, "-i", str(mp3_path), "-hide_banner"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", r.stderr)
    if not m:
        return 0.0
    h, mn, s = m.groups()
    return int(h) * 3600 + int(mn) * 60 + float(s)


async def tts_with_subs(text: str, mp3_path: Path, srt_path: Path, voice: str, rate: str):
    """Edge TTS：寫 mp3＋SRT。優先用 TTS 回傳的時間戳；
    沒有時間戳時，按音訊總長以字數比例估算（誤差約 ±1 秒，足夠同步）。"""
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    words = []  # (offset_ticks, duration_ticks, text)
    with open(mp3_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                words.append((chunk["offset"], chunk["duration"], chunk["text"]))

    cues = []
    if words:
        # 把詞合併成字幕行：滿 MAX_CUE_CHARS 或遇句末標點就斷行
        buf, start = "", None
        for off, dur, w in words:
            if start is None:
                start = off
            buf += w
            end = off + dur
            if len(buf) >= MAX_CUE_CHARS or (buf and buf[-1] in SENT_BREAK):
                cues.append((start, end, buf))
                buf, start = "", None
        if buf:
            cues.append((start, words[-1][0] + words[-1][1], buf))
    else:
        # 後備：按字數比例分配音訊總長
        total_sec = _audio_seconds(mp3_path)
        lines = _split_cues(text)
        total_chars = sum(len(c) for c in lines) or 1
        t = 0.0
        for c in lines:
            d = total_sec * len(c) / total_chars
            cues.append((int(t * 1e7), int((t + d) * 1e7), c))
            t += d

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, (st, en, txt) in enumerate(cues, 1):
            f.write(f"{i}\n{_ticks_to_srt(st)} --> {_ticks_to_srt(en)}\n{txt}\n\n")


def render(bg: Path, mp3: Path, srt: Path, title: str, out_mp4: Path, font: str):
    """ffmpeg：靜態背景 + 音訊 + 燒錄字幕 → mp4。
    在暫存目錄用相對路徑執行，避開 Windows 路徑在 subtitles 濾鏡中的跳脫地獄。"""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        shutil.copy(bg, tdp / ("bg" + bg.suffix))
        shutil.copy(mp3, tdp / "a.mp3")
        shutil.copy(srt, tdp / "s.srt")
        style = (f"FontName={font},FontSize=20,PrimaryColour=&H00FFFFFF,"
                 f"OutlineColour=&H00000000,Outline=3,Shadow=1,MarginV=40")
        style_esc = style.replace(",", r"\,")
        vf = (f"scale=1920:1080:force_original_aspect_ratio=decrease,"
              f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,"
              f"subtitles=filename=s.srt:force_style='{style_esc}'")
        cmd = [FFMPEG, "-y", "-loop", "1", "-framerate", "10",
               "-i", "bg" + bg.suffix, "-i", "a.mp3",
               "-vf", vf,
               "-c:v", "libx264", "-tune", "stillimage", "-preset", "veryfast",
               "-crf", "28", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "96k", "-shortest",
               "-metadata", f"title={title}",
               "out.mp4"]
        r = subprocess.run(cmd, cwd=td, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if r.returncode != 0:
            raise RuntimeError("ffmpeg 失敗：" + r.stderr[-800:])
        out_mp4.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(tdp / "out.mp4"), str(out_mp4))


def render_head(head_mp4: Path, mp3: Path, srt: Path, title: str,
                out_mp4: Path, font: str):
    """數位主播模式：InfiniteTalk 輸出 → 放大至 1080p＋燒字幕＋換回原始音訊"""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        shutil.copy(head_mp4, tdp / "h.mp4")
        shutil.copy(mp3, tdp / "a.mp3")
        shutil.copy(srt, tdp / "s.srt")
        style = (f"FontName={font},FontSize=20,PrimaryColour=&H00FFFFFF,"
                 f"OutlineColour=&H00000000,Outline=3,Shadow=1,MarginV=40")
        style_esc = style.replace(",", r"\,")
        vf = (f"scale=1920:1080:force_original_aspect_ratio=decrease,"
              f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,"
              f"subtitles=filename=s.srt:force_style='{style_esc}'")
        cmd = [FFMPEG, "-y", "-i", "h.mp4", "-i", "a.mp3",
               "-vf", vf, "-map", "0:v", "-map", "1:a",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-shortest",
               "-metadata", f"title={title}", "out.mp4"]
        r = subprocess.run(cmd, cwd=td, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if r.returncode != 0:
            raise RuntimeError("ffmpeg 失敗：" + r.stderr[-800:])
        out_mp4.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(tdp / "out.mp4"), str(out_mp4))


def make_one(md_path, outdir, voice=DEFAULT_VOICE, rate=DEFAULT_RATE,
             bg=None, font="Microsoft JhengHei", keep_assets=False,
             mode="static", workflow=None, server=None) -> dict:
    """回傳 {ok, out, skipped, warnings, error}"""
    md_path = Path(md_path)
    outdir = Path(outdir)
    out_mp4 = outdir / (md_path.stem + ".mp4")
    if out_mp4.exists() and out_mp4.stat().st_size > 0:
        return {"ok": True, "out": str(out_mp4), "skipped": True, "warnings": [], "error": ""}

    info = extract(md_path)
    if "可能解析失敗" in " ".join(info["warnings"]):
        return {"ok": False, "out": "", "skipped": False,
                "warnings": info["warnings"], "error": "解析失敗，需人工檢查"}

    # 主播模式預設用 assets/presenter.png 當人物圖
    if mode == "head" and bg is None:
        cand = Path(__file__).parent / "assets" / "presenter.png"
        if cand.exists():
            bg = cand
    # 背景圖：優先用參數指定，否則用 repo 預設 qt 圖
    if bg is None:
        repo = md_path.resolve()
        while repo.parent != repo and not (repo / "hugo.toml").exists():
            repo = repo.parent
        for cand in ["static/images/qt.jpg", "static/images/021.jpg"]:
            if (repo / cand).exists():
                bg = repo / cand
                break
    if bg is None or not Path(bg).exists():
        return {"ok": False, "out": "", "skipped": False, "warnings": [],
                "error": "找不到背景圖，請用 --bg 指定"}

    work = outdir / "_assets" / md_path.stem
    work.mkdir(parents=True, exist_ok=True)
    # 音檔以「書卷_日期」唯一命名（不可固定為 audio.mp3）：ComfyUI 的 filename_prefix 依此 stem 而定。
    # 固定名或僅用日期會讓不同篇（含 ntqt/otqt 同日同名）prefix 相同，導致快取退路誤抓別篇舊輸出。
    slug = f"{md_path.parent.name}_{md_path.stem}"
    mp3, srt = work / (slug + ".mp3"), work / "subs.srt"
    try:
        asyncio.run(tts_with_subs(info["narration"], mp3, srt, voice, rate))
        if mode == "head":
            from comfy_talking_head import generate
            head_mp4 = work / "head.mp4"
            generate(bg, mp3, workflow, head_mp4, server=server)
            render_head(head_mp4, mp3, srt, info["title"], out_mp4, font)
        else:
            render(Path(bg), mp3, srt, info["title"], out_mp4, font)
    except Exception as e:
        return {"ok": False, "out": "", "skipped": False,
                "warnings": info["warnings"], "error": f"生成失敗：{type(e).__name__}: {e}"}
    finally:
        if not keep_assets:
            shutil.rmtree(work, ignore_errors=True)

    return {"ok": True, "out": str(out_mp4), "skipped": False,
            "warnings": info["warnings"], "error": ""}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("md")
    ap.add_argument("--outdir", default="video-output")
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    ap.add_argument("--rate", default=DEFAULT_RATE)
    ap.add_argument("--bg", default=None)
    ap.add_argument("--font", default="Microsoft JhengHei")
    ap.add_argument("--keep-assets", action="store_true")
    ap.add_argument("--mode", choices=["static", "head"], default="static",
                    help="static=靜態背景；head=ComfyUI InfiniteTalk 數位主播")
    ap.add_argument("--workflow", default=None, help="InfiniteTalk API 工作流 json")
    ap.add_argument("--server", default=None, help="local / lan / 完整URL")
    a = ap.parse_args()
    res = make_one(a.md, a.outdir, a.voice, a.rate, a.bg, a.font, a.keep_assets,
                   a.mode, a.workflow, a.server)
    print(res)
    sys.exit(0 if res["ok"] else 1)
