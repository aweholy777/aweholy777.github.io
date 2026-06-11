# 計畫書：qt-video — QT 文章批次製作朗讀影片

> 軍師（Claude Code）已寫好 pipeline（`video-pipeline/`），士兵（OpenCode）負責執行批次與回報。
> 本任務**不需要 LLM 生成內容**，士兵的工作是跑腳本、監控、處理異常、寫 result.md。

## 目標

`content/daily-qt/`（ntqt 約 1,496 篇＋otqt 約 1,967 篇）每篇產出一支 16:9 全文朗讀
mp4（靜態背景＋zh-TW 語音＋同步字幕），存到 `video-output/<ntqt|otqt>/<檔名>.mp4`。

## 階段執行（嚴格按順序）

### 階段 0：環境（一次性）
```
pip install -r video-pipeline\requirements.txt
ffmpeg -version
```

### 階段 1：試做 3 篇（必須先過這關）
```
python video-pipeline\batch_make.py --src content\daily-qt\ntqt --outdir video-output\ntqt --limit 3 --result tasks\qt-video\result.md
```
**停下來等軍師／站長驗收樣片**（聲音、語速、字幕、畫面）後才進入階段 2。

### 階段 2：最近一年（2025-06-01 之後，ntqt＋otqt）
```
python video-pipeline\batch_make.py --src content\daily-qt\ntqt --outdir video-output\ntqt --from 2025-06-01 --result tasks\qt-video\result-ntqt-recent.md
python video-pipeline\batch_make.py --src content\daily-qt\otqt --outdir video-output\otqt --from 2025-06-01 --result tasks\qt-video\result-otqt-recent.md
```

### 階段 3：歷史回補（按年份切段，最多 3 視窗平行）
每個年份段一條指令（`--from`/`--to` 切段），不同段寫不同 result 檔。
Edge TTS 是免費服務，**平行不要超過 3 個視窗**，每篇間隔 2 秒（內建）。

## 士兵的異常處理規則

1. 單篇失敗：腳本已自動重試一次，仍失敗就記錄在 result.md，**不要自己改文章內容**
2. 連續 5 篇以上失敗：停止批次，在 result.md 寫明最後錯誤訊息，等軍師裁決
3. 解析警告（內文過短等）：照常列在 result.md 警告區，不要修檔案
4. 中斷／當機：直接重跑同一指令（已存在的 mp4 自動跳過）

## 驗收標準（軍師查核）

- result.md 的「完成＋跳過」數 = 該段日期範圍的文章數
- 抽查 3 支 mp4：能播放、長度 >3 分鐘、有聲音、字幕同步、無亂碼
- `video-output/` 不得進 git（.gitignore 已設）
- 失敗清單 <2%，超過則退回查原因

## 規模與時程估算

全部約 3,463 篇 × 15~25 MB ≈ 60~90 GB 硬碟空間（先確認 D 槽夠）。
單篇製作 2~4 分鐘，單視窗連跑約 6~10 天，3 視窗平行約 2~4 天。

## 數位主播模式（mode=head，2026-06-10 新增）

旁白規則已改：不念開頭經文引用，只念「今天的經文進度是：…」後直接從「今天默想經文」開始。
全片由 `video-pipeline/assets/presenter.png` 的人物以 InfiniteTalk 嘴型同步講述。

### 階段 H0：ComfyUI 準備（站長手動，一次性）
1. ComfyUI Manager 安裝 **ComfyUI-WanVideoWrapper**（含 InfiniteTalk）與 **VideoHelperSuite**
2. 下載模型：Wan2.1-I2V-14B-**480P 量化版**（12GB VRAM 必須用量化）、InfiniteTalk 權重、wav2vec2
3. 載入 InfiniteTalk 官方範例工作流，用 presenter.png＋任一段短 mp3 手動跑通
4. 工作流「匯出 (API)」→ 存成 `video-pipeline/workflows/infinitetalk_api.json`

### 階段 H1 實測結果（2026-06-10，RTX 3060 12GB）

煙霧測試通過：6.8 秒影片耗時 15 分鐘（含載模型約 3 分鐘）。
穩定速率：**每 1 秒影片 ≈ 2 分鐘 GPU 運算**（640×368、blockswap 40、6 步＋lightx2v LoRA）。
注意：832×480 會撐爆 12GB VRAM 觸發系統記憶體回退（慢 16 倍以上），3060 必須用 640×368。

外推工期：單篇 8 分鐘全文 ≈ 16 小時 GPU；全部 3,463 篇 ≈ 6 年（不可行）。
可行範圍：混合式（開場 30 秒主播）單篇約 1 小時；或全程主播只做精選篇目（一晚一篇）。

**全文實測（2026-06-11）**：2026-05-30 篇 404 秒影片，一夜跑完（19:26→06:16，約 10.8 小時），
實際速率 1.6 分鐘運算/秒影片。人物一致性、嘴型、字幕同步全程穩定。確認「一晚一篇」可行。

### 階段 H1：單篇試做＋計時（決策關卡）
```
python video-pipeline\make_video.py content\daily-qt\ntqt\2026-05-30.md --outdir video-output\head --mode head
```
記錄總耗時。**用實測時間算總工期再決定範圍**：
單篇若 1 小時 → 全部 3,463 篇 ≈ 144 天連跑；單篇若 20 分鐘 → ≈ 48 天。
若工期不可接受，回退選項：(a) 只做最近一年；(b) 開場 30 秒主播＋內文靜態（混合式）。

### 階段 H2：批次（夜間排程，從最新往回做）
```
python video-pipeline\batch_make.py --src content\daily-qt\ntqt --outdir video-output\head-ntqt --mode head --limit 10 --result tasks\qt-video\result-head.md
```
GPU 任務一次只能跑一個視窗（ComfyUI 單佇列），不可平行。
中斷直接重跑，已存在的 mp4 自動跳過。

## 雙機架構（2026-06-11 定案）

LAN 主機 MS-S1 MAX（aweholy@192.168.68.61，SSH 金鑰 ~/.ssh/qt_lan_key）實測：
InfiniteTalk 在 ROCm 上 5.4 分/步（832×480），比 3060 慢 3~4 倍 → **不當數位主播工人**。

分工定案：
- **3060（Windows）**：InfiniteTalk 數位主播，一晚一篇（`run_head_full.bat` 模式）
- **MS-S1 MAX（Ubuntu）**：靜態版全集（CPU/ffmpeg，~35 秒/篇）＋未來的本地 LLM 士兵主機
  - 已部署 ~/qtwork（腳本＋全部文章），輸出在 ~/qt-static-output/{ntqt,otqt}
  - 兩批次並行跑全集 3,477 篇，預計 15~20 小時完成
  - 監控：`check_lan_static.bat`；重啟 ComfyUI：`restart_lan_comfy.bat`
  - 字型用 AR PL UMing TW，中斷重跑同指令即可續做

## 後續（另開任務，本任務不做）

- 上傳 YouTube（可用 youtube-upload API 批次，另寫 plan）
- 在每篇文章頁嵌入對應影片連結（批次改 md，標準士兵工作）
