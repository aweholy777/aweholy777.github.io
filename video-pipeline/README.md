# video-pipeline — QT 文章 → 朗讀影片

把 `content/daily-qt/` 的每篇 QT 文章做成 16:9 全文朗讀影片：
靜態背景＋台灣中文語音（Edge TTS 免費）＋同步字幕。

## 環境（一次性，在 Windows 本機）

```
pip install -r video-pipeline\requirements.txt
ffmpeg -version    # 沒有就：winget install ffmpeg
```

## 用法

```
# 單篇試做
python video-pipeline\make_video.py content\daily-qt\ntqt\2026-05-30.md --outdir video-output\ntqt

# 批次（先小量試 5 篇）
python video-pipeline\batch_make.py --src content\daily-qt\ntqt --outdir video-output\ntqt --limit 5

# 正式批次（按日期切段，可多視窗平行，各段不重疊）
python video-pipeline\batch_make.py --src content\daily-qt\otqt --outdir video-output\otqt --from 2026-01-01 --to 2026-05-31 --result tasks\qt-video-2026\result.md
```

## 重要特性

- **可中斷續跑**：已存在的 mp4 自動跳過，當機或限流後直接重跑同一指令
- **限流保護**：每篇間隔 2 秒（`--sleep` 可調），失敗自動重試一次。Edge TTS 是免費服務，平行視窗建議 ≤3
- **聲音**：預設 `zh-TW-HsiaoChenNeural`（女聲），男聲可用 `--voice zh-TW-YunJheNeural`
- **語速**：預設 +10%（`--rate +0%` 還原）
- **背景圖**：自動找 `static/images/qt.jpg`，自訂用 `--bg 路徑`（建議 1920×1080）

## 規模估算（全部 3,463 篇）

單篇 10~20 分鐘音訊，產出約 15~25 MB → 全部約 60~90 GB、製作時間每篇約 2~4 分鐘
（TTS 快於即時＋ffmpeg 靜態圖很快）→ 單視窗連跑約 6~10 天，3 視窗平行約 2~4 天。
建議從最近一年開始做，確認品質再回頭補舊年份。
