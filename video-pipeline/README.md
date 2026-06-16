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

## 字幕設定（make_video.py）

字幕**斷行以語意為主、標點為輔、字數只當最後防線**，並固定貼底、不擋臉。全部在 `make_video.py` 調整：

**斷行（`_split_cues`，常數在檔頭）**

| 設定 | 值 | 說明 |
|------|----|------|
| 句末標點 | `SENT_END = 。！？!?…` | 出現即斷 → 一句完整意思自成一段 |
| 停頓標點 | `CLAUSE_BREAK = ，、；：,;` | 只有當行已偏長（≥ `SOFT_CHARS`）才在此斷 |
| 軟門檻 | `SOFT_CHARS = 13` | 未達此長度的短句**保持完整**，不在逗號處硬斷 |
| 硬上限 | `HARD_CHARS = 24` | 完全沒標點的長串，最後才在此硬斷（避免折成多行擋臉） |

時間軸：edge-tts 中文回傳的是**整句時間戳**（SentenceBoundary），`tts_with_subs` 用每句的時間跨度
配合 `_split_cues` 切小段、段內按字數比例分配，所以斷行依語意、時間又貼合該句。

**版面（`render()`/`render_head()` 的 `force_style`）**

| 設定 | 值 | 說明 |
|------|----|------|
| 對齊 | `Alignment=2` | ASS 底部置中，位置固定不飄 |
| 底邊距 | `MarginV=45` | 距畫面底部高度 |
| 字級 | `FontSize=18` | 白字、黑邊 `Outline=3`、`Shadow=1` |

**調整指引**：想要字幕更短（更常單行）就調低 `SOFT_CHARS`；想讓長句更完整（容許較常兩行）就調高
`SOFT_CHARS`/`HARD_CHARS`（`HARD_CHARS` 不建議超過 ~26，會開始出現第三行擋臉）。

## 規模估算（全部 3,463 篇）

單篇 10~20 分鐘音訊，產出約 15~25 MB → 全部約 60~90 GB、製作時間每篇約 2~4 分鐘
（TTS 快於即時＋ffmpeg 靜態圖很快）→ 單視窗連跑約 6~10 天，3 視窗平行約 2~4 天。
建議從最近一年開始做，確認品質再回頭補舊年份。
