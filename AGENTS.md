# AGENTS.md — 接手這個專案的唯一權威文件

> **寫給任何 AI 代理（Claude Code／Codex／Gemini CLI／opencode／pi／Cursor）看的。**
> 最後更新：2026-11-27。若本檔與其他交接文件（`HANDOFF.md`、`新機接手說明.md`、
> `AI_HANDOVER.md`、`CLAUDE.local.md`）衝突，**以本檔為準**；那些是歷史文件，只作背景。
> 看完請先回報你的理解，不要立刻動手。

---

## 0. 給 AI 的第一句話

進到這個 repo，先做三件事：

```bash
git pull --rebase --autostash origin main     # 先同步
gh auth switch --user aweholy777              # push 前必做（Windows）
```

然後讀完本檔再動手。**任何改動都要能跑 `hugo.exe --buildFuture` 0 錯誤。**

---

## 1. 這是什麼專案

| 項目 | 內容 |
|---|---|
| 網站 | <https://cmtc.tw> — 城市宣培中心（Hugo 靜態網站，theme `mainroad`）|
| Repo（Windows 主機）| `D:\AI成品\qtproject`（branch `main`）|
| Remote | `https://github.com/aweholy777/aweholy777.github.io.git` |
| 部署 | **Cloudflare Pages**，專案名 `cmtc`；push 到 `main` → 自動建置 → 上線 |
| CF 帳號 | `ee4d7f3e51b89be421114501fa50bf09`（Aweholy@gmail.com）|
| Hugo 版本 | **0.144.2**，由 CF 專案環境變數 `HUGO_VERSION` 決定；本機 repo 根目錄有一份釘死同版本的 `hugo.exe`（gitignored）|

⚠️ `AI_HANDOVER.md`／`CLAUDE.md` 舊版寫「GitHub Pages 部署」是**錯的**（`deploy.yml` 只是舊鏡像）。
真正上線走 Cloudflare Pages。

### 內容主體
- `content/daily-qt/ntqt/` — 新約 QT（849 篇）
- `content/daily-qt/otqt/` — 舊約 QT（1862 篇）
- `content/today-qt.md` — **今日**的當日QT（每天自動產生，勿手改格式）
- `content/deep-calls-deep/` — 深淵響應（文章＋影片，卡片式，21 篇/頁分頁）
- `data/qtvideos.json` — QT 影音庫資料，`/qt-video/` 頁由它產生

---

## 2. 這台機器與其他機器（別搞混）

| 角色 | 位置 | 負責 |
|---|---|---|
| **Windows 主機**（你現在在的地方）| `D:\AI成品\qtproject` | 網站內容、當日QT 自動產生、影片生成（ComfyUI＋Breeze TTS）、建置驗證 |
| **Mac mini** | `192.168.68.60`，`/Users/haoguozi/qtproject` | **只負責** YouTube 滴傳：launchd `com.cmtc.qtupload`，每小時 :05 上傳 1 支（24h 上限 24）|
| Cloudflare | — | 建置與部署（不用手動上傳）|

- **不要在 Mac mini 生成影片**（Breeze TTS＋CUDA 只在 Windows）。
- **不要同時開 Windows 上傳器與 Mac launchd**（會重複上傳）。Windows 的 `QT-Upload-5090` 已停用。
- `video-pipeline/yt_uploaded.csv` 是上傳的唯一權威記錄，不要隨手編輯。

---

## 3. 鐵則（破壞了就很難救）

1. **改東西前先 `git pull --rebase --autostash origin main`**。Mac 每小時會 push，常撞。
2. **push 前 `gh auth switch --user aweholy777`**，否則會用錯帳號（常見錯誤 `Permission denied to galilee7989`）。
3. **不要用 `git add -A`**。只 commit 你這次動到的檔案（Mac 的 CSV／json 可能同時在變）。
4. **改完網站必跑建置**：repo 根目錄 `hugo.exe --buildFuture`（Windows 走 bash 時用絕對路徑，
   `.\hugo.exe` 會失敗）。0 錯誤才算完成。
5. **`public/` 是產物，不要手改、不要 commit**。
6. **憑證紅線**：`video-pipeline/client_secret.json`、`video-pipeline/yt_token.json`、
   任何 token/key/password —— 不讀、不印、不 commit、不傳給外部服務。看到就跳過。
7. **不要刪檔案**，除非使用者明確確認。
8. 使用者是**繁體中文**使用者，回覆用繁中。

---

## 4. 當日QT：每天自動產生（最容易壞的地方）

### 流程
`tasks/daily-qt/generate_today_qt.py` 會：
1. 取得今日《活潑的生命》進度（三層來源，見下）
2. 依進度抓和合本經文（信望愛 FHL `bible.fhl.net/json/qb.php`，`version=unv`）
3. 比對典藏文章，找出**涵蓋**該範圍的舊文，沿用它的「分享默想經文」「今天的回應」
4. 寫入 `content/today-qt.md`

### 進度來源優先序（`get_daily_reference()`）
1. `https://www.duranno.tw/livinglife/index.php/daily` 直抓（憑證缺 SKID，**要用 curl** 不能用 requests）
2. **CGN 中文《活潑的生命》YouTube 頻道 RSS**：`channel_id=UCqUnxXxHSFb6At-njlSX9AQ`
   （標題格式 `[活潑的生命] YYYYMMDD 主題(書卷 章:節~節)`，需帶瀏覽器 UA）
3. 自家 `https://cmtc.tw/api/daily-reference`

> `duranno.tw` 從 2026-11-22 起長期「系統維護中」（`/daily` 只回約 927 bytes、含「維護中」，
> `daily_p`／`daily_n` 一律 500）。這時 **CGN 會自動接手**，是正常行為不是壞掉。

### 排程
| 排程 | 時間 | 用途 |
|---|---|---|
| Hermes cron `7713df5c5e26` → `daily_qt_local.py` | 台北 **00:05** | 本機準時產生＋push（成功靜默，失敗才通知）|
| `.github/workflows/daily-qt.yml` | `5 16 * * *`（16:05Z＝台北 00:05）| 備援 |
| 同上第二道 | `30 20 * * *` | 再一層備援 |
| Hermes cron `72e54234771a` → `check_daily_qt.py` | 台北 **07:30** | 檢查線上頁面是否已更新，異常才通知 |

⚠️ **GitHub Actions 的 schedule 實測會延遲 3.5～6.5 小時**，所以別指望它準時；
準時的是本機那條。改 cron 時記得這件事。

### 手動補產（自動掛掉時）
```bash
cd /d/AI成品/qtproject
python tasks/daily-qt/generate_today_qt.py                          # 用今天的日期
python tasks/daily-qt/generate_today_qt.py --date 2026-11-27 \
  --reference "哥林多後書4：1∼10" --archive-date 2018-03-07          # 指定日期/範圍/舊文
```
`--archive-date` 是必要的逃生口：新舊版本分段不同（例 2026 版 1:15~24 vs 2018 版 1:12~22）時，
「完全涵蓋」比對會失敗，要手動指定用哪篇。

---

## 5. `/qt-generator/`：自家版「生成當日QT」

| 路徑 | 檔案 | 說明 |
|---|---|---|
| `/qt-generator/` | `static/qt-generator/index.html` | 手動產生器：自動載入進度→抓經文→比對典藏→帶入分享→輸出 Markdown |
| `/api/daily-reference` | `functions/api/daily-reference.js` | duranno → CGN 備援；CORS `*` |
| `/api/verses` | `functions/api/verses.js` | FHL 和合本代理，一次最多 50 節 |
| `/api/archive-sections` | `functions/api/archive-sections.js` | 抓舊文的「2 默想／3 分享／4 回應」|
| `/data/archive-index.json` | `static/data/archive-index.json` | 3,473 篇典藏索引（日期/書卷/範圍/URL）|

- 這三支是 **Cloudflare Pages Functions**，只在 CF 生效；**本機 Hugo 預覽會 404**。
- 新增典藏文章後要重跑 `python tasks/daily-qt/build_archive_index.py` 更新索引。
- 2026-11-27 前的舊版是外部第三方 `index-html-clean-copy.vercel.app`（只抓 duranno，已停用），
  全站與程式都不可再引用它。

---

## 6. 內容規則

- QT 文章固定四段：`1. 經文誦讀` → `2. 今天默想經文` → `3. 分享默想經文` → `4. 今天的回應`
- front matter 至少 `title`、`date`、`draft`
- 檔名 `YYYY-MM-DD.md`；標題格式 `YYYY – MM – DD QT 書卷 章：節~節`
- 書卷順序索引 `_index.md` 遇重複經文只保留最新一篇，**舊檔不可批次刪除**
- 文章內**不要**嵌 YouTube shortcode，影音統一由 `/qt-video/` 呈現
- 字幕／標題規則（做影片時）：字幕不加標點、句讀用半形空格；《》〈〉【】（）()、破折號、刪節號保留；
  標題只留純經文，不放日期
- 影片參數（勿改）：25 fps、`audio_scale=0.8`、SageAttention、720p、BGM 0.10、`amix=...normalize=0`
- 宗教影片對裸露敏感：梳洗/更衣場景要衣著完整，只拍肩頸以上或背影

---

## 7. 驗證清單（說「完成」之前）

```bash
# 1) 建置 0 錯誤
/d/AI成品/qtproject/hugo.exe --buildFuture

# 2) 確認 Cloudflare 建置成功（用你剛 push 的 commit）
gh api repos/aweholy777/aweholy777.github.io/commits/<sha>/check-runs \
  --jq '.check_runs[] | select(.name=="Cloudflare Pages") | {status,conclusion}'

# 3) 線上真的更新了
curl -s https://cmtc.tw/today-qt/ | grep -o "<title>[^<]*"
```

看到 `{"conclusion":"success"}` 且線上內容正確，才算完成。**不要只看 push 成功就說做完。**

---

## 8. 常見故障 → 處理

| 症狀 | 原因／處理 |
|---|---|
| push 被拒 `non-fast-forward` | Mac 剛 push 過 → `git pull --rebase --autostash` 再 push |
| push 拒絕 `Permission denied to galilee7989` | 帳號錯 → `gh auth switch --user aweholy777` |
| 當日QT 沒更新 | 看 `generate_today_qt.py` 輸出；duranno 維護時應走 CGN；必要時手動補產 |
| 頁面停在昨天 | CF 建置還在跑（1~3 分鐘）或排程延遲；查 check-runs |
| 建置錯誤提到 `strings.TrimSpace` | 用錯 Hugo 版本，改用 repo 根目錄的 `hugo.exe`（0.144.2）|
| CF 建置抓錯 Hugo 版本 | Pages 專案 `cmtc` → 設定 → 變數與機密 → `HUGO_VERSION` 應為 `0.144.2` |
| `/api/*` 本機 404 | 正常，Functions 只在 Cloudflare 生效 |

---

## 9. 批次作業的方法論（內容類大改動適用）

**大原則：先寫計畫，再派工，最後驗收。** 超過 5 個檔案的重複性編輯，不要一個一個手改。

```
tasks/<任務名>/
├── plan.md      # 目標、規格、檔案清單、驗收標準
├── result.md    # 執行的回報（<50 行）
└── log.txt      # 完整輸出（不讀）
```
可用 `opencode run "讀取 tasks/<任務名>/plan.md 並完整執行…" -m <model>` 派工。
驗收看 `git diff --stat`，範圍與 plan.md 不符就退回。

---

## 10. 不要做的事

- 不要改 `public/`、`.venv/`、`video-output/`、`.claude/`（除非使用者明確要求）
- 不要重新生成整套影片目錄（已渲染完成）
- 不要啟用 Windows 上傳排程（Mac 那條在跑）
- 不要為了「比較乾淨」而批次刪除舊 QT 文章
- 不要把見證、代禱事項等個人資料丟給雲端免費模型
