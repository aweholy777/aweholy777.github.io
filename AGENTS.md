# AGENTS.md — 接手這個專案的唯一權威文件

> **寫給任何 AI 代理（Claude Code／Codex／Gemini CLI／Antigravity／opencode／pi／Cursor）看的。**
> 最後更新：2026-11-27。若本檔與其他歷史交接文件（`HANDOFF.md`、`新機接手說明.md`、`AI_HANDOVER.md`、`CLAUDE.local.md`）衝突，**一律以本檔為準**。
> 若在 Windows 主機上從 `D:\AI成品` 總目錄出發，請一併遵守 `D:\AI成品\AGENTS.md`（本資料夾內另有 gitignored 的本機 `進度.md` 與 `經驗.md` 可讀寫）。

---

## 0. 開工第一件事（照抄執行）

**PowerShell（Windows 主機 `D:\AI成品\qtproject`）：**
```powershell
cd D:\AI成品\qtproject
git pull --rebase --autostash origin main   # Mac 每小時 :05 會 push，沒先 pull 必撞
gh auth switch --user aweholy777             # push 前必切帳號（避開 galilee7989）
.\hugo.exe --minify --buildFuture            # 必須用根目錄釘死 0.144.2 的 hugo.exe
```

**Bash / Git Bash：**
```bash
cd /d/AI成品/qtproject
git pull --rebase --autostash origin main
gh auth switch --user aweholy777
/d/AI成品/qtproject/hugo.exe --minify --buildFuture
```

若本機有 `進度.md` 與 `經驗.md`，動手前先讀完；收工前更新這兩檔與 `D:\AI成品\00-AI工作規則\專案總表.md`（兩檔已加 `.gitignore`，僅留本機不推進公開 repo）。

---

## 1. 專案總覽與部署架構

| 項目 | 內容 |
|---|---|
| 網站 | <https://cmtc.tw> — 城市宣培中心（Hugo 靜態網站，theme `mainroad`） |
| Repo（Windows 主機） | `D:\AI成品\qtproject`（branch `main`） |
| Remote | `https://github.com/aweholy777/aweholy777.github.io.git` |
| 正式部署 | **Cloudflare Pages**，專案名 `cmtc`；push 到 `main` → 自動建置 → 1～3 分鐘上線 |
| CF 帳號 | `ee4d7f3e51b89be421114501fa50bf09`（Aweholy@gmail.com） |
| Hugo 版本 | **0.144.2**（CF 端環境變數 `HUGO_VERSION=0.144.2`；本機 repo 根目錄有同版 `hugo.exe`，gitignored） |
| GitHub Actions CI | `.github/workflows/deploy.yml` 已改為 `Hugo Build Check`（僅網站核心檔變動觸發，含 20 MiB 單檔警戒，不再重複部署 GitHub Pages） |

> ⚠️ `AI_HANDOVER.md`／`HANDOFF.md`／`新機接手說明.md` 等舊文件寫「GitHub Pages 部署」或「Vercel 代理」皆已**過期作廢**，不可再依其操作。

### Cloudflare Pages 兩大技術紅線（必看）
1. **單檔上限 25 MiB**：
   - `hugo.toml` 已設 `rssLimit = 50`（壓在 ~408 KB；未設時 `index.xml` 曾達 25.13 MiB 差點炸部署）。
   - 全站搜尋索引拆為 4 個分片（`index-ot1.json`、`index-ot2.json`、`index-nt.json`、`index-other.json`，單檔最大 ~10.4 MiB，`index.json` 為 manifest）。
   - CI 內建檢查：任何輸出檔 > 20 MiB 直接失敗提醒。
2. **靜態資產 4 小時快取問題**：
   - Cloudflare Pages 對 `.js`／`.css` 預設回傳 `Cache-Control: public, max-age=14400`（4 小時），而 HTML 是 `max-age=0`。
   - 因此 `layouts/_default/baseof.html`、`layouts/qt-video/list.html`、`layouts/search/list.html` 皆透過 Hugo `md5` 為自訂 CSS／JS／JSON 加上 `?v=<8碼雜湊>`；只要重跑 Hugo 就會自動換新網址，絕不可移除 `?v=`，否則改版後回訪瀏覽器會用舊 JS 配新 HTML 導致頁面空白。

---

## 2. 專案檔案地圖

| 路徑 | 用途 | 能否修改 / 注意事項 |
|---|---|---|
| `hugo.toml` | 站台設定、選單、`rssLimit = 50`、搜尋分片 `outputFormats` | 可；注意選單「讀經進度記錄表」須為 `/daily-qt/biblereadingtracker/`（不能寫 `.html`） |
| `content/today-qt.md` | **今日**的當日QT（每日自動產生） | 勿手改格式 |
| `content/daily-qt/otqt/` | 舊約 QT 文章（2,013 篇） | 可新增、**不可批次刪除** |
| `content/daily-qt/ntqt/` | 新約 QT 文章（1,495 篇） | 可新增、**不可批次刪除** |
| `content/daily-qt/Biblereadingtracker.html` | 讀經進度記錄表（編譯為 `/daily-qt/biblereadingtracker/`） | 可 |
| `content/deep-calls-deep/` | 深淵響應（文章＋影片，21 篇/頁分頁） | 可 |
| `layouts/_default/baseof.html` | 全站基底版型、SEO meta fallback、按頁條件載入專屬 CSS（含 `?v=`） | 可，改完必建置 |
| `layouts/index.json` + `index.search_*.json` + `partials/search-shard.json` | 搜尋索引 manifest 與 4 分片模板（3,715 篇） | 改動須驗證 4 分片與 `static/js/site-search.js` |
| `layouts/qt-video/list.html` + `static/js/qt-library.js` | QT 影音庫：Hugo 動態發布 `/data/qtvideos.json`，前端按書卷／分批 60 支渲染＋150ms debounce | 改動須驗證 `/qt-video/` 卡片與燈箱播放 |
| `static/qt-generator/index.html` | 自家「QT 產生器」（自動載入、選候選舊文、線上微調、複製/下載 `.md`） | 可 |
| `static/data/archive-index.json` | 典藏索引（**3,508 篇 / 66 卷正規化**） | **由 `build_archive_index.py` 產生，勿手改** |
| `functions/api/*.js` | Cloudflare Pages Functions 3 支 API | 可，**只在 CF 生效（本機預覽會 404）** |
| `tasks/daily-qt/generate_today_qt.py` | 當日QT 產生器（與網頁邏輯對齊） | 核心，改前先讀並 `--dry-run` 測試 |
| `tasks/daily-qt/build_archive_index.py` | 重建 `archive-index.json`（含書卷別名正規化） | 新增 QT 文章後必跑一次 |
| `data/qtvideos.json` | QT 影音庫資料（Mac 上傳後自動更新） | Mac 會更新，衝突時 pull |
| `video-pipeline/yt_uploaded.csv` | YouTube 上傳唯一權威紀錄 | 勿隨手編輯 |
| `static/robots.txt` | 搜尋爬蟲規則（`Sitemap: https://cmtc.tw/sitemap.xml`） | 可 |
| `public/` | Hugo 建置產物 | **gitignored，勿手改、勿 commit** |
| `進度.md`、`經驗.md` | 本機跨 AI 工作進度與踩坑紀錄（gitignored） | 僅留本機，不推進公開 repo |

---

## 3. 機器分工（別搞混）

| 角色 | 位置 | 負責項目 |
|---|---|---|
| **Windows 主機**（本機） | `D:\AI成品\qtproject` | 網站維護、建置驗證、每日 QT 自動產生與補產、影片生成（ComfyUI＋Breeze TTS＋CUDA，整套已渲染完成） |
| **Mac mini** | `192.168.68.60`，`/Users/haoguozi/qtproject` | **只負責** YouTube 滴傳：launchd `com.cmtc.qtupload`，每小時 :05 上傳 1 支（24h 上限 24） |
| **Cloudflare Pages** | 專案 `cmtc` | 建置與上線、執行 `functions/api/*.js` |

- **YouTube 上傳進度**：截至 2026-11-27 新約 `848/848` 已全數完成，舊約已上傳 `1,750/1,861`（剩約 111 支，約 4～5 天後全數傳完即可停用 Mac 的 `com.cmtc.qtupload`）。
- **不可在 Mac mini 生成影片**（TTS＋CUDA 只在 Windows）。
- **不可同時開啟 Windows 上傳器 `QT-Upload-5090` 與 Mac launchd**（會重複上傳；Windows 排程已停用）。
- Mac 端腳本細節與回滾步驟見 `tasks/mac-handover/README.md`（macOS `/bin/bash` 3.2 變數一律寫 `${VAR}`）。

---

## 4. 八條鐵則（違反就很難救）

1. **改動前先 `git pull --rebase --autostash origin main`**（Mac 每小時 :05 會 push）。
2. **push 前先 `gh auth switch --user aweholy777`**（避開另一個帳號 `galilee7989`）。
3. **禁用 `git add -A`**，只 `git add` 這次明確改動的檔案（避免誤收 Mac 更新或私密本機檔）。
4. **改完網站必跑 `.\hugo.exe --minify --buildFuture`**（0 錯誤才算通過）。
5. **憑證紅線**：`video-pipeline/client_secret.json`、`video-pipeline/yt_token.json`、`_new_settings.json`、`_claude2_settings.json` 及任何 token/key/password —— **不讀、不印、不 commit、不傳給外部服務**。
6. **不刪檔案**，除非使用者明確確認。
7. **不手改 `public/`、`.venv/`、`video-output/`、`.claude/`**。
8. **回覆使用者一律使用繁體中文**（台灣用語，指令／工具名保留英文）。

---

## 5. 當日 QT 每日自動化（`tasks/daily-qt/`）

### 執行流程（`generate_today_qt.py`）
1. 依優先序取得進度：
   - ① `https://www.duranno.tw/livinglife/index.php/daily`（僅查詢「今天」時使用；憑證缺 SKID，用 `curl` 抓；自 2026-11-22 起長期維護中，自動降級屬正常）
   - ② **CGN 中文《活潑的生命》YouTube RSS**（`channel_id=UCqUnxXxHSFb6At-njlSX9AQ`，保留近 15 天影片）
   - ③ 自家備援 `https://cmtc.tw/api/daily-reference`
2. 向信望愛 FHL（`bible.fhl.net/json/qb.php?version=unv`）以**單次範圍查詢（`sec=v1-v2`）**抓和合本經文（支援 66 卷簡稱與別名，跨章遇空章末即 `break`）。
3. 比對 `content/daily-qt/{otqt,ntqt}` 典藏（支援 `詩`→`詩篇`、`箴言書`→`箴言`、`約翰壹/貳/參書`→`約翰一/二/三書`、`詩篇73篇 1~14`、整篇詩篇、全形 `～`、冒號後空格）：
   - 優先序：`exact`（完全同範圍，多篇取最新日期）→ `cover`（最小涵蓋範圍、最新日期）→ `partial`（部分重疊，於頁首加註提醒；可加 `--no-partial` 關閉）。
4. 寫入 `content/today-qt.md` 與本機 `tasks/daily-qt/last-run.json`（gitignored）。

### 排程現況
| 排程 | 時間（台北） | 用途 |
|---|---|---|
| 本機 Hermes cron `7713df5c5e26` → `daily_qt_local.py` | **00:05** | 準時產生＋push（成功靜默，失敗才通知） |
| GitHub Actions `.github/workflows/daily-qt.yml` | `5 16 * * *` / `30 20 * * *` | 雙層備援（⚠️ GitHub schedule 實測常延遲 3.5～6.5 小時） |
| 本機 Hermes cron `72e54234771a` → `check_daily_qt.py` | **07:30** | 檢查線上 `/today-qt/` 是否已更新，異常才通知 |

### 手動補產指令
```powershell
python tasks/daily-qt/generate_today_qt.py --dry-run
python tasks/daily-qt/generate_today_qt.py --date 2026-11-27 --reference "林後4：1∼10" --archive-date 2018-03-07
```

---

## 6. 自家 `/qt-generator/` 與 Cloudflare Pages Functions

| 路徑 | 檔案 | 說明 |
|---|---|---|
| `/qt-generator/` | `static/qt-generator/index.html` | 開頁自動載入今日進度並產生；含昨天/今天/明天快捷鍵、簡稱/單節/整篇詩篇解析、最多 12 篇候選舊文切換、當日QT/典藏格式切換、2/3/4 段直接編輯與下載 `.md`、線上 `/today-qt/` 狀態列 |
| `/api/daily-reference` | `functions/api/daily-reference.js` | 今日走 duranno → CGN；歷史日期略過 duranno 直接查 CGN（近 15 天） |
| `/api/verses` | `functions/api/verses.js` | FHL 和合本單次範圍代理（支援 66 卷全名＋簡稱＋古字別名，單次上限 200 節） |
| `/api/archive-sections` | `functions/api/archive-sections.js` | 優先用 `context.env.ASSETS.fetch` 站內直讀舊文並正則抽取 2/3/4 段（支援 2016 早期長標題） |
| `/data/archive-index.json` | `static/data/archive-index.json` | 3,508 篇正規化索引；新增 QT 文章後跑 `python tasks/daily-qt/build_archive_index.py` 重建 |

---

## 7. 內容與影音規格

- QT 文章檔名 `YYYY-MM-DD.md`，標題 `YYYY – MM – DD QT 書卷 章：節~節`（注意 `hugo.toml` 已關 `strikethrough = false`，`~` 不需跳脫）。
- 固定四段：`1. 經文誦讀` → `2. 今天默想經文` → `3. 分享默想經文` → `4. 今天的回應`。
- 書卷 `_index.md` 遇重複經文只留最新一篇；文章內不嵌 YouTube shortcode（影音統一由 `/qt-video/` 呈現）。
- 影片參數（勿改）：25 fps、`audio_scale=0.8`、SageAttention、720p、BGM 0.10、`amix=...normalize=0`；字幕不加標點、句讀用半形空格、標題只留純經文；梳洗/更衣鏡頭衣著完整，只拍肩頸以上或背影。

---

## 8. 驗收標準（說「完成」之前必做）

```powershell
# 1) 本機建置 0 錯誤（帶 --minify 與實際上線一致）
.\hugo.exe --minify --buildFuture

# 2) 推送後確認 Cloudflare Pages 部署成功（將 <sha> 換成 push 的 commit）
gh api "repos/aweholy777/aweholy777.github.io/commits/<sha>/check-runs" `
  --jq '.check_runs[] | select(.name=="Cloudflare Pages") | {status,conclusion}'

# 3) 實測線上目標頁面 / API 回傳 HTTP 200 與預期內容
curl.exe -s "https://cmtc.tw/today-qt/?cb=$(Get-Random)" | Select-String -Pattern "<title>[^<]+"
```

看到 `Cloudflare Pages` 的 `"conclusion":"success"` 且線上實際內容驗證無誤，才可回報完成。

---

## 9. 常見故障排錯表

| 症狀 | 原因／處理 |
|---|---|
| push 被拒 `non-fast-forward` | Mac 剛 push → `git pull --rebase --autostash origin main` 再 push |
| push 拒絕 `Permission denied to galilee7989` | 帳號錯 → `gh auth switch --user aweholy777` |
| 改了 JS/CSS 但回訪畫面沒更新或空白 | 檢查模板是否漏加 `?v={{ printf "%.8s" (... \| md5) }}`（CF 預設快取 JS/CSS 4 小時） |
| 選單或新頁連結在線上回 404 | 獨立 `.html` 放 `content/` 會被 Hugo 編為 `/檔名/` 資料夾網址（例 `/daily-qt/biblereadingtracker/`） |
| 建置錯誤提到 `strings.TrimSpace` | 用錯 Hugo 版本，改用 repo 根目錄 `.\hugo.exe`（0.144.2） |
| `/api/*` 本機預覽回 404 | 正常，Pages Functions 只在 Cloudflare 生效 |
| 當日QT 沒更新 | 看 `generate_today_qt.py` 輸出；必要時用 `--reference`＋`--archive-date` 手動補產 |
| 索引頁順序亂 | 重跑書卷 `_index.md` 產生流程，不要手改 |

---

## 10. 批次作業與歷史文件對照

- **批次作業**：超過 5 個檔案的重複性修改，先在 `tasks/<任務名>/plan.md` 寫明目標、範圍、驗收標準再派工，驗收看 `git diff --stat`。
- **歷史背景檔**（僅供查考，內容部分過期）：`AI_HANDOVER.md`、`HANDOFF.md`、`新機接手說明.md`、`遷移到Cloudflare指南.md`、`CLAUDE.local.md`、`5090-每日備忘.md`。
- **人類操作手冊**：`更新網站SOP.md`（含 `qt-push`、`qt-sync`、`qt-status` 快捷指令說明）。
