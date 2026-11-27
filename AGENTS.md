# AGENTS.md — 接手這個專案的唯一權威文件

> **寫給任何 AI 代理（Claude Code／Codex／Gemini CLI／Antigravity／opencode／pi／Cursor／ZCode）看的。**
> 最後更新：2026-11-27（第二次全專案體檢後完整改寫：加入完整目錄樹、本機才有的檔案、所有排程總表、影片管線、帳號與服務、新機清單）。
> **本檔是唯一權威文件。** 舊的交接文件（`HANDOFF.md`、`AI_HANDOVER.md`、`新機接手說明.md`、`遷移到Cloudflare指南.md`）已於 2026-11-27 刪除，只存在於 git 歷史；裡面寫的「GitHub Pages 部署」「Vercel 代理」「3060 軍師／5090 執行雙機」「Windows 上傳器」全部**作廢**，不可再依其操作。
> 若在 Windows 主機上從 `D:\AI成品` 總目錄出發，請一併遵守 `D:\AI成品\AGENTS.md`（本資料夾內另有 gitignored 的本機 `進度.md`、`經驗.md`、`CLAUDE.local.md` 可讀寫）。

**閱讀順序**：本檔 → 本機 `進度.md`（做到哪、下一步）→ 本機 `經驗.md`（踩過的坑）→ 動手前再看你會碰到的目錄在 §2 的說明。

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
| 網站 | <https://cmtc.tw> — 城市宣培中心（Hugo 靜態網站，theme `mainroad`）。另綁 `www.cmtc.tw`、`aweholy.eu.cc`（指向同一個專案，`www` 直接服務不轉向，canonical 指向 `cmtc.tw`） |
| 規模 | 建置 3,721 頁：舊約 QT 2,013 篇、新約 QT 1,495 篇、受洗見證約 140 篇、生活故事 27 篇、深淵響應 12 篇；版控 4,281 個檔案 |
| Repo（Windows 主機） | `D:\AI成品\qtproject`（branch `main`） |
| Remote | `https://github.com/aweholy777/aweholy777.github.io.git` |
| 正式部署 | **Cloudflare Pages**，專案名 `cmtc`；push 到 `main` → 自動建置 → 1～3 分鐘上線 |
| CF 帳號 | `ee4d7f3e51b89be421114501fa50bf09`（Aweholy@gmail.com）。⚠️ 本人另有第二個 Cloudflare 帳號，本機 wrangler 登入的是那一個；進後台或用 API 動網站設定一律用上面這個帳號（專案頁：`https://dash.cloudflare.com/ee4d7f3e51b89be421114501fa50bf09/pages/view/cmtc`） |
| Hugo 版本 | **0.144.2**（CF 端環境變數 `HUGO_VERSION=0.144.2`；本機 repo 根目錄有同版 `hugo.exe`，gitignored） |
| GitHub Actions CI | `.github/workflows/deploy.yml` = `Hugo Build Check`（僅網站核心檔變動觸發，含 20 MiB 單檔警戒，不再部署 GitHub Pages） |

> 歷史交接文件已於 2026-11-27 刪除。任何提到 GitHub Pages、Vercel、3060／5090 雙機、Windows 上傳器的說法都是舊時代的，一律不適用。

### Cloudflare Pages 兩大技術紅線（必看）
1. **單檔上限 25 MiB**：
   - `hugo.toml` 已設 `rssLimit = 50`（壓在 ~408 KB；未設時 `index.xml` 曾達 25.13 MiB 差點炸部署）。
   - 全站搜尋索引拆為 4 個分片（`index-ot1.json`、`index-ot2.json`、`index-nt.json`、`index-other.json`，單檔最大 ~10.4 MiB，`index.json` 為 manifest）。
   - CI 內建檢查：任何輸出檔 > 20 MiB 直接失敗提醒。
2. **靜態資產 4 小時快取問題**：
   - Cloudflare Pages 對 `.js`／`.css` 預設回傳 `Cache-Control: public, max-age=14400`（4 小時），而 HTML 是 `max-age=0`。
   - 因此 `layouts/_default/baseof.html`、`layouts/qt-video/list.html`、`layouts/search/list.html` 皆透過 Hugo `md5` 為自訂 CSS／JS／JSON 加上 `?v=<8碼雜湊>`；只要重跑 Hugo 就會自動換新網址，絕不可移除 `?v=`，否則改版後回訪瀏覽器會用舊 JS 配新 HTML 導致頁面空白。

---

## 2. 專案目錄與檔案地圖

### 2.1 完整目錄樹（2026-11-27 實際盤點）

```
D:\AI成品\qtproject\                          ← 專案根目錄（版控 4,281 個檔案）
│
├─ 說明文件
│  ├─ AGENTS.md ………………… 本檔：唯一權威交接文件
│  ├─ CLAUDE.md ……………… 給 Claude Code 的入口（指向本檔＋鐵則摘要）
│  └─ 更新網站SOP.md ……… 給人看的操作手冊
│
├─ 網站設定
│  ├─ hugo.toml ……………… 站台設定、選單、輸出格式（搜尋分片）
│  ├─ .gitignore
│  └─ upload-images-to-r2.ps1 … 把 static/images/ 上傳到 Cloudflare R2 的一次性工具
│
├─ .github/workflows/ ……… GitHub Actions
│  ├─ deploy.yml ……………… Hugo Build Check（push 到 main 且動到網站核心檔時）
│  └─ daily-qt.yml …………… 當日QT 備援排程
│
├─ content/ …………………… 網站內容（Hugo；約 32 MB）
│  ├─ _index.md ………………… 首頁
│  ├─ today-qt.md ……………… 今日當日QT（每天 00:05 自動產生）
│  ├─ one-on-one.md ………… 一對一門訓
│  ├─ daily-qt/
│  │  ├─ _index.md …………… 每日QT 索引頁
│  │  ├─ otqt/ …………………… 舊約 QT：2,013 篇 YYYY-MM-DD.md ＋ _index.md（書卷排序索引）
│  │  ├─ ntqt/ …………………… 新約 QT：1,495 篇 ＋ _index.md
│  │  ├─ Biblereadingtracker.html … 讀經進度記錄表 → /daily-qt/biblereadingtracker/（選單用這個）
│  │  ├─ bibletracker.html ……… 同上的舊版 → /daily-qt/bibletracker/（重複，見 §14）
│  │  └─ announcement.md ………… 停更公告頁（已從選單移除，頁面仍在）
│  ├─ deep-calls-deep/ ……… 深淵響應：12 個文章檔（含草稿與重複）＋ _index.md ＋ 1 個 _index 草稿副本
│  ├─ testimonies/ …………… 雲彩見證
│  │  ├─ _index.md ……………… （空檔）
│  │  ├─ baptism/ ……………… 受洗見證：約 140 篇 ＋ _index.md（人工維護的列表）
│  │  └─ life-stories/ ……… 生活故事：27 篇 ＋ _index.md（空檔 → 頁面目前沒有列表，見 §14）
│  ├─ qt-video/_index.md …… QT 影音庫頁
│  └─ search/_index.md ……… 全站搜尋頁
│
├─ layouts/ …………………… 版型（覆寫主題；客製一律寫這裡，不要改主題）
│  ├─ _default/baseof.html … 全站基底：<head>、canonical、CSS 載入（含 ?v=）
│  ├─ _default/list.html ……… 列表頁：只顯示 _index.md 內容＋書卷目錄
│  ├─ index.html ………………… 首頁（_index.md 內容＋下方兩個連結：今日QT、生成當日QT）
│  ├─ index.json ………………… 搜尋索引 manifest
│  ├─ index.search_ot1/ot2/nt/other.json … 搜尋索引 4 分片模板
│  ├─ partials/ ………………… header、menu、logo、footer、google-search、search-shard.json
│  ├─ qt-video/list.html ……… QT 影音庫
│  ├─ search/list.html ………… 搜尋頁
│  ├─ deep-calls-deep/list.html … 深淵響應（21 篇／頁）
│  └─ shortcodes/youtube.html … 覆寫內建 YouTube shortcode
│
├─ static/ …………………… 原樣發布到網站根目錄
│  ├─ css/ ……………………… custom.css（全站）、qt-article.css、qt-index.css、qt-library.css
│  ├─ js/ ……………………… menu.js、site-search.js（全站搜尋）、qt-library.js（影音庫）
│  ├─ qt-generator/index.html … QT 產生器
│  ├─ data/archive-index.json … 典藏索引（腳本產生，勿手改）
│  ├─ daily-qt/bibletracker.html … 讀經記錄表第 3 份副本（重複，見 §14）
│  ├─ images/ …………………… 文章用圖片 382 個（40 MB）
│  ├─ img/ ……………………… 主題用 avatar.png、placeholder.png
│  └─ robots.txt、favicon.ico、apple-touch-icon.png、googled33be0e0f13982a9.html（Google Search Console 驗證檔，勿刪）
│
├─ data/ ……………………… Hugo 資料檔
│  ├─ books.json ……………… 書卷分類與簡稱（索引頁「書卷目錄」用）
│  └─ qtvideos.json …………… QT 影音庫資料（Mac 每小時上傳後更新）
│
├─ functions/api/ ………… Cloudflare Pages Functions（只在 Cloudflare 上生效）
│  └─ daily-reference.js、verses.js、archive-sections.js
│
├─ themes/mainroad/ ……… Hugo 主題（vendored，104 個檔案；2025-04-16 加入後未改動，不要改它）
├─ archetypes/default.md … Hugo `hugo new` 範本（目前沒在用）
│
├─ tasks/ …………………… 工具、腳本與任務紀錄（索引見 tasks/README.md）
│  ├─ daily-qt/ ……………… generate_today_qt.py、build_archive_index.py、daily_qt_local.py、check_daily_qt.py、sort-daily-qt-indexes.js
│  ├─ mac-handover/ ………… upload_mac.sh、install_mac.sh、com.cmtc.qtupload.plist、README.md
│  ├─ progress/ ……………… gen_progress.py、新約進度表.md、舊約進度表.md、_summary.txt
│  ├─ purge-history/ ………… rewrite_history.py、plan.md
│  ├─ cleanup-migration-leftovers/ … plan.md、result.md（2026-11-27 的清理紀錄）
│  ├─ _templates/ …………… plan.md、result.md 範本
│  └─ README.md
│
├─ video-pipeline/ ……… 影片生成與上傳腳本（見 §12）
│  ├─【上傳還在用】yt_publish.py、build_qt_library.py、yt_uploaded.csv
│  ├─【生成用，已完成】extract_text.py、make_video.py、batch_make.py（Edge TTS 版）
│  │                      comfy_talking_head.py、nightly_head.py（ComfyUI InfiniteTalk 主播版）
│  ├─ workflows/ ……………… ComfyUI 工作流（wanvideo_…example_03.json 正式版、infinitetalk_lan.json）
│  ├─ assets/ ………………… presenter.png、presenter2.png（主播輪替用圖）
│  ├─ remove_yt_shortcodes.py、make_lan_workflow.py、setup_lan_infinitetalk.sh、yt_first_run.bat、requirements.txt
│  └─ README.md（第一代流程）、專案報告與操作手冊.md（2026-06）
│
└─【本機才有、不進版控】見 §2.3：hugo.exe、.venv/、public/、resources/、video-output/（81 GB）、
   .claude/、.wrangler/、_chat-logs/、進度.md、經驗.md、CLAUDE.local.md、5090-每日備忘.md、憑證檔
```

### 2.2 常用可編輯檔案（動手前先看這張表）

| 路徑 | 用途 | 能否修改 / 注意事項 |
|---|---|---|
| `hugo.toml` | 站台設定、選單、`rssLimit = 50`、`defaultContentLanguage = "zh-tw"`（必須全小寫）、`hasCJKLanguage`、`disableKinds`、搜尋分片 `outputFormats` | 可；選單「讀經進度記錄表」須為 `/daily-qt/biblereadingtracker/`（不能寫 `.html`）；TOML 表格（`[xxx]`）一律加在所有頂層設定之後（最保險是檔尾），否則其後的頂層設定會被歸進該表格、主題整個沒載入 |
| `content/today-qt.md` | **今日**的當日QT（每日自動產生） | 勿手改格式 |
| `content/daily-qt/otqt/` | 舊約 QT 文章（2,013 篇） | 可新增、**不可批次刪除** |
| `content/daily-qt/ntqt/` | 新約 QT 文章（1,495 篇） | 可新增、**不可批次刪除** |
| `content/daily-qt/Biblereadingtracker.html` | 讀經進度記錄表（編譯為 `/daily-qt/biblereadingtracker/`） | 可 |
| `content/deep-calls-deep/` | 深淵響應（文章＋影片，21 篇/頁分頁） | 可 |
| `content/testimonies/` | 雲彩見證（`baptism/` 的 `_index.md` 是人工維護的列表；`life-stories/` 的 `_index.md` 是空的） | 可；見證屬敏感個人資料，不要丟給雲端 AI 批次處理 |
| `layouts/_default/baseof.html` | 全站基底版型、SEO meta fallback、canonical（404 頁除外）、按頁條件載入專屬 CSS（含 `?v=`） | 可，改完必建置 |
| `layouts/index.html` | 首頁：`content/_index.md` 內容＋下方兩個連結（不另加標題）：「今日QT <日期> <經文>」→ `/today-qt/`（顯示文字把文章標題開頭的「當日QT」換成「今日QT」，文章標題本身不變），以及開新分頁的「生成當日QT」→ `/qt-generator/`。這兩個連結已不在上方選單（2026-11-28 移到這裡） | 可 |
| `layouts/index.json` + `index.search_*.json` + `partials/search-shard.json` | 搜尋索引 manifest 與 4 分片模板（3,715 篇；日期以檔名為準，因 3,050 篇舊文的 front matter `date` 是搬家匯入日 2025-04-12） | 改動須驗證 4 分片與 `static/js/site-search.js`（索引在訪客輸入關鍵字後才下載，改 `render()`／`ensureShardsLoaded()` 時注意兩者會互相呼叫，要先標記載入中再 render，否則無限遞迴） |
| `layouts/qt-video/list.html` + `static/js/qt-library.js` | QT 影音庫：Hugo 動態發布 `/data/qtvideos.json`，前端按書卷／分批 60 支渲染＋150ms debounce | 改動須驗證 `/qt-video/` 卡片與燈箱播放 |
| `static/qt-generator/index.html` | 自家「QT 產生器」（自動載入、選候選舊文、線上微調、複製/下載 `.md`） | 可 |
| `static/data/archive-index.json` | 典藏索引（**3,508 篇 / 66 卷正規化**） | **由 `build_archive_index.py` 產生，勿手改** |
| `functions/api/*.js` | Cloudflare Pages Functions 3 支 API | 可，**只在 CF 生效（本機預覽會 404）** |
| `tasks/daily-qt/generate_today_qt.py` | 當日QT 產生器（與網頁邏輯對齊） | 核心，改前先讀並 `--dry-run` 測試 |
| `tasks/daily-qt/build_archive_index.py` | 重建 `archive-index.json`（含書卷別名正規化） | 新增 QT 文章後必跑一次 |
| `tasks/daily-qt/daily_qt_local.py`、`check_daily_qt.py` | 本機 Hermes cron 執行的兩支腳本（00:05 產生並 push／07:30 檢查線上），repo 內這兩份是版本控管的正本 | 可；改完要同步到 `%LOCALAPPDATA%\Hermes\scripts\`（cron 實際執行的是那裡的副本） |
| `tasks/daily-qt/sort-daily-qt-indexes.js` | 重建 `otqt/ntqt/_index.md` 的書卷排序：`node tasks/daily-qt/sort-daily-qt-indexes.js` | 不可放回 `content/`（會被 Hugo 發布成公開檔） |
| `tasks/purge-history/` | 清除 git 歷史裡外洩金鑰的工具 `rewrite_history.py` 與計畫書 `plan.md` | 預設只演練；加 `--push` 會改寫歷史並強制推送，只能在 Mac 影片全數上傳後執行 |
| `tasks/mac-handover/upload_mac.sh` | Mac 每小時執行的上傳腳本 | 改時務必保留開頭的「收工保險」；macOS `/bin/bash` 3.2，變數一律寫 `${VAR}` |
| `data/qtvideos.json` | QT 影音庫資料（Mac 上傳後自動更新） | Mac 會更新，衝突時 pull |
| `video-pipeline/yt_uploaded.csv` | YouTube 上傳唯一權威紀錄 | 勿隨手編輯 |
| `static/robots.txt` | 搜尋爬蟲規則（`Sitemap: https://cmtc.tw/sitemap.xml`） | 可 |
| `themes/mainroad/` | Hugo 主題原碼 | 不要改；客製寫在 `layouts/`、`static/css/` |

### 2.3 本機才有的檔案（不在 git 裡；換機器時看 §15）

| 路徑 | 大小 | 是什麼 | 換新電腦時 |
|---|---|---|---|
| `hugo.exe` | 54 MB | Hugo 0.144.2 extended | 從 GitHub Releases 下載 `hugo_extended_0.144.2_windows-amd64.zip`，解壓後放 repo 根目錄 |
| `.venv/` | 133 MB | uv 建的 Python 3.12 虛擬環境（`google-api-python-client`、`google-auth`、`google-auth-oauthlib`、`edge-tts`） | `uv venv .venv --python 3.12` 再 `uv pip install -r video-pipeline/requirements.txt google-api-python-client google-auth google-auth-oauthlib` |
| `public/` | 132 MB | Hugo 建置產物 | 建置自動產生；**勿手改、勿 commit** |
| `resources/`、`.hugo_build.lock` | — | Hugo 快取與建置鎖 | 自動 |
| `video-output/` | **81 GB** | 影片成品：`head/` 1,549 支、`head/old/` 1,159 支（已上傳的 YouTube 上都有） | 不需要重建；全部上傳結束後要不要刪由本人決定 |
| `video-pipeline/client_secret.json`、`yt_token.json` | — | YouTube OAuth 憑證（Mac 也有一份） | 用隨身碟／AirDrop 從舊機複製，**絕不經過對話或雲端** |
| ~~`video-pipeline/_new_settings.json`、`_claude2_settings.json`~~ | — | 舊的 Claude Code 設定快照，含金鑰；**本機檔已於 2026-11-27 刪除** | 它們仍存在 GitHub 歷史裡（`53892e85` 起），由 §11 #7 的排程清除；在那之前一樣不可讀、不可 commit |
| `video-pipeline/` 其餘 log、截圖、`.gen_*` | — | 影片生成時代的執行紀錄 | 不需要 |
| `tasks/daily-qt/last-run.json` | — | 當日QT 產生器最近一次執行紀錄 | 自動 |
| `.claude/` | 21 KB | Claude Code 本機權限設定 `settings.local.json` | 自動；**不手改** |
| `.wrangler/` | — | Cloudflare wrangler 快取（登入的是另一個帳號） | 自動 |
| `_chat-logs/` | 741 KB | Claude CLI 對話記錄備份；**含金鑰，不可分享** | 非必要 |
| `進度.md`、`經驗.md` | — | 本機工作筆記（跨 AI 共用） | 從舊機複製 |
| `CLAUDE.local.md` | — | 本機專屬事項（Claude Code 會讀；與本檔衝突時以本檔為準） | 從舊機複製 |
| `5090-每日備忘.md` | — | 舊節點備忘，已無用途（本人選擇保留） | 不需要 |
| `%LOCALAPPDATA%\Hermes\scripts\daily_qt_local.py`、`check_daily_qt.py` | — | Hermes 排程實際執行的副本（與 repo 正本相同） | 新機要重設 Hermes 排程並放腳本（§11） |

### 2.4 文件導覽（哪份現行、哪份歷史）

| 檔案 | 狀態 | 用途 |
|---|---|---|
| `AGENTS.md` | ✅ 現行（唯一權威） | 接手必讀 |
| `CLAUDE.md` | ✅ 現行 | Claude Code 的入口與鐵則摘要 |
| `更新網站SOP.md` | ✅ 現行 | 給人看的操作手冊 |
| `tasks/README.md` | ✅ 現行 | `tasks/` 各資料夾索引 |
| `tasks/mac-handover/README.md` | ✅ 現行 → 影片傳完後轉歷史 | Mac 上傳的交接步驟、回滾、bash 3.2 注意事項 |
| `tasks/purge-history/plan.md` | ✅ 現行 | 清除歷史金鑰的規格 |
| `tasks/cleanup-migration-leftovers/` | 紀錄 | 2026-11-27 清理搬家殘留的計畫與結果 |
| `video-pipeline/專案報告與操作手冊.md` | 歷史（2026-06） | 影片自動化計畫的報告；現況以 §12 為準 |
| `video-pipeline/README.md` | 部分過期 | 第一代 Edge TTS 流程說明 |
| 本機 `進度.md`、`經驗.md` | 本機（gitignored） | 跨 AI 的工作進度與踩坑紀錄；收工前要更新 |
| 本機 `CLAUDE.local.md` | 本機 | 本機專屬事項 |
| `D:\AI成品\AGENTS.md`、`D:\AI成品\00-AI工作規則\` | 上層規則 | 使用者的合作方式、通用經驗、機器清單、專案總表 |

> 已刪除、只存在 git 歷史的文件（2026-11-27）：`HANDOFF.md`、`AI_HANDOVER.md`、`新機接手說明.md`、`遷移到Cloudflare指南.md`、`tasks/handoff/`（雙機信箱）、`tasks/5090-migration/`（舊節點排程腳本與 `qt.ps1`）、`tasks/dispatch.ps1`、`tasks/工作分析報告.md`、`tasks/影片生成專案-完整脈絡.md`、影片生成加速實驗（`gen-speedup`／`sageattn-speedup`／`teacache-speedup`）、`content/.ai/`。要查考請看 git 歷史，**不要再照那些流程做**。

---

## 3. 機器分工（別搞混）

| 角色 | 位置 | 負責項目 |
|---|---|---|
| **Windows 主機**（本機） | `D:\AI成品\qtproject` | 網站維護、建置驗證、每日 QT 自動產生與補產；存放影片成品（`video-output/`，81 GB） |
| **Mac mini** | `192.168.68.60`，`/Users/haoguozi/qtproject` | **只負責** YouTube 滴傳：launchd `com.cmtc.qtupload`，每小時 :05 上傳 1 支（24h 上限 24） |
| **Cloudflare Pages** | 專案 `cmtc` | 建置與上線、執行 `functions/api/*.js` |

- **YouTube 上傳進度**：截至 2026-11-27 新約 `848/848` 已全數完成，舊約已上傳約 `1,760/1,861`（剩約 100 支，約 4 天後全數傳完）。
- **Mac 的上傳腳本已內建「收工保險」（`4b9a7041`）**：`tasks/mac-handover/upload_mac.sh` 開頭會檢查本機 `data/qtvideos.json`，新舊約全數上傳（且日期 ≥ 2026-12-01）後直接 `exit 0`，不再 pull／push。**改這支腳本時務必保留這段**，否則歷史改寫後 Mac 會用舊歷史做 rebase、把舊紀錄接回去。傳完後 Mac 的 `com.cmtc.qtupload` 可停用。
- **影片傳完後會自動清除 GitHub 歷史裡的金鑰**：ZCode 排程「Mac 的影片傳完後（約 4 天）清除 GitHub 舊紀錄裡的金鑰」於每月 1～10 號 14:30 檢查，條件成立就執行 `python tasks/purge-history/rewrite_history.py --push`（改寫歷史＋強制推送；規格見 `tasks/purge-history/plan.md`）。**做完後 2026-05-17 之後所有 commit 的 SHA 都會改變**，舊文件引用的 SHA 會失效。手動做法：先跑不帶 `--push` 的演練。
- **不可在 Mac mini 生成影片**（ComfyUI＋CUDA 只在 Windows 的 5090 節點；且影片已全部生成完畢）。
- **只有 Mac 可以上傳**。Windows 上傳器 `QT-Upload-5090` 已於 2026-09-25 停用、腳本已於 2026-11-27 刪除；兩台同時上傳會重複。
- 從 Windows **連不到 Mac**（2026-11-27 實測：`.60` 無回應、`.59` 連線被拒）。要動 Mac 上的東西，請本人在 Mac 操作，或請他開啟「遠端登入」。
- Mac 端腳本細節與回滾步驟見 `tasks/mac-handover/README.md`（macOS `/bin/bash` 3.2 變數一律寫 `${VAR}`）。

---

## 4. 十條鐵則（違反就很難救）

1. **改動前先 `git pull --rebase --autostash origin main`**（Mac 每小時 :05 會 push）。順序很重要：**先 pull → 再改檔 → 最後才 `git add`**。已經 `git add`（暫存）之後才 pull，`--autostash` 會把暫存狀態解開，接著 `git commit` 只會收到一部分檔案（2026-11-27 的 `70edb8d6` 就是這樣只收到新增檔）。若已經暫存了，就先 commit，再 `git pull --rebase`，再 push。
2. **push 前先 `gh auth switch --user aweholy777`**（避開另一個帳號 `galilee7989`）。
3. **禁用 `git add -A`**，只 `git add` 這次明確改動的檔案（避免誤收 Mac 更新或私密本機檔）。
4. **改完網站必跑 `.\hugo.exe --minify --buildFuture`**（0 錯誤才算通過）。
5. **憑證紅線**：`video-pipeline/client_secret.json`、`video-pipeline/yt_token.json`、`_new_settings.json`、`_claude2_settings.json` 及任何 token/key/password —— **不讀、不印、不 commit、不傳給外部服務**；交接文件、筆記、對話一律不貼 key。金鑰一旦進過 repo 就視為外洩：**到平台撤銷重發**＋**從歷史移除**兩件都要做，只「取消追蹤」沒有用（2026-06 的兩個 settings 檔就是這樣留在公開歷史裡）。這兩個 settings 檔的本機副本已於 2026-11-27 刪除，歷史裡的舊版本由 §11 #7 的排程清除。
6. **不刪檔案**，除非使用者明確確認。
7. **不手改 `public/`、`.venv/`、`video-output/`、`.claude/`**。
8. **回覆使用者一律使用繁體中文**（台灣用語，指令／工具名保留英文）。
9. **本機 commit 之前就要確定內容可以公開**：00:05 的 `daily_qt_local.py` 會直接 `git push origin main`，任何「已 commit 但還沒 push」的本機內容都會被它半夜自動推上線。
10. **見證、代禱事項等敏感個人資料不交給雲端 AI 批次處理**（要大量處理時用本地模型）；一般網站維護不涉及。

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

### 排程（完整總表見 §11）

| 排程 | 時間（台北） | 用途 |
|---|---|---|
| 本機 Hermes cron `7713df5c5e26` → `daily_qt_local.py` | **00:05** | 準時產生＋push（成功靜默，失敗才通知） |
| GitHub Actions `.github/workflows/daily-qt.yml` | `5 16 * * *` / `30 20 * * *` | 雙層備援（⚠️ GitHub schedule 實測常延遲 3.5～6.5 小時） |
| 本機 Hermes cron `72e54234771a` → `check_daily_qt.py` | **07:30** | 檢查線上 `/today-qt/` 是否已更新，異常才通知 |

> 兩支腳本的 repo 正本在 `tasks/daily-qt/`；cron 目前實際執行的是 `%LOCALAPPDATA%\Hermes\scripts\` 的副本（2026-11-27 兩邊內容相同）。要修改時改 repo 這份，再複製覆蓋過去（或把 cron 指向 repo 這份）。Hermes 目前是用它自己的 Python 執行（腳本只用標準庫）；較合規的做法是改用專案 `.venv` 的 Python（見 §14）。

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
- 影片參數（勿改）：25 fps、`audio_scale=0.8`、SageAttention、720p、BGM 0.10、`amix=...normalize=0`；字幕不加標點、句讀用半形空格、標題只留經文；梳洗/更衣鏡頭衣著完整，只拍肩頸以上或背影。
  （2026-06 加速實驗的結論：維持 25 fps、blockswap=0；SageAttention 採用（約 1.3×）；TeaCache 不採用。實驗檔案已刪除，僅存 git 歷史。）

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
| commit 只收到一部分檔案（`git status` 還有一堆沒提交） | 暫存之後才 `git pull --autostash`，暫存被解除 → 用 `git status --short` 看清楚，把剩下的明確 `git add` 後補一個 commit；不要 `git add -A` |
| push 拒絕 `Permission denied to galilee7989` | 帳號錯 → `gh auth switch --user aweholy777` |
| 改了 JS/CSS 但回訪畫面沒更新或空白 | 檢查模板是否漏加 `?v={{ printf "%.8s" (... \| md5) }}`（CF 預設快取 JS/CSS 4 小時） |
| 選單或新頁連結在線上回 404 | 獨立 `.html` 放 `content/` 會被 Hugo 編為 `/檔名/` 資料夾網址（例 `/daily-qt/biblereadingtracker/`） |
| 建置錯誤提到 `strings.TrimSpace` | 用錯 Hugo 版本，改用 repo 根目錄 `.\hugo.exe`（0.144.2） |
| 升級 Hugo 後建置失敗（挑 `content/` 裡的 `.html`） | Hugo 0.15x 起對直接放原始 HTML 的內容檔有更嚴的 `security.allowContent` 政策 → **不要升級**，回到 0.144.2 |
| `/api/*` 本機預覽回 404 | 正常，Pages Functions 只在 Cloudflare 生效 |
| 當日QT 沒更新 | 看 `generate_today_qt.py` 輸出；必要時用 `--reference`＋`--archive-date` 手動補產 |
| 索引頁順序亂 | 跑 `node tasks/daily-qt/sort-daily-qt-indexes.js`，不要手改（內容沒變時應輸出 `moved: 0、otItems: 1861、ntItems: 848`） |
| 全站 `lang`、行動版選單或 404 頁變回英文 | `hugo.toml` 的 `defaultContentLanguage` 被拿掉，或寫成大寫 `zh-TW`（0.144.2 會報 `does not match any language definition`）→ 改回全小寫 `zh-tw` |
| 改了 `hugo.toml` 後主題整個沒載入（`resources.Get` 回 nil） | 新增的 `[xxx]` 表格插在頂層設定中間 → 表格移到所有頂層設定之後 |
| 想讓日期以檔名為準 | 不可用 `[frontmatter] date = [":filename", …]`：實測會把 `2012-03-10-1.md` 這類檔名的網址塌縮成 `/1/`、`/2/`。搜尋索引的日期已在 `search-shard.json` 處理 |
| 搜尋結果日期全是 2025-04-12、輸入日期搜不到 | `search-shard.json` 的 `date` 被改回 `.Date` → 改回以檔名為準 |
| 打 `www.cmtc.tw` 出現 522／523 錯誤頁 | `www` 的 DNS 記錄被改回 `CNAME → cmtc.tw`，或 `www.cmtc.tw` 從 Pages 自訂網域被移除 → 到 Pages 專案 `cmtc` → 自訂網域確認 `www.cmtc.tw` 為「使用中」；DNS 的 `www` 應為 `CNAME → cmtc.pages.dev`（2026-11-27 修好；www 是直接服務網站內容，不會自動轉向 `cmtc.tw`，canonical 已指向 `cmtc.tw`） |
| `@cmtc.tw` 收不到信 | `mail.cmtc.tw` 的 Proxy 狀態必須是「僅 DNS」（信件埠 25／993 不經過 Proxy）；被改成「通過 Proxy 處理」就會退信（2026-11-27 修好） |
| 歷史裡還抓得到金鑰／舊 commit | 跑 `python tasks/purge-history/rewrite_history.py`（預設只演練），確認無誤再加 `--push`。前提是 Mac 影片已全數上傳，否則會回「[尚不執行]」 |
| Mac 的影片不再上傳了 | 先看是不是已經全部傳完（`data/qtvideos.json` 新舊約 `video_count == passage_count`）——那是腳本正常「退休」；沒傳完卻停了才需要查 Mac 上的 `~/upload_mac.log` |
| git 指令列出中文檔名變成 `\345\242…` | 加 `-c core.quotepath=false`（例 `git -c core.quotepath=false status --short`）；拿輸出跟路徑比對時務必加，否則會誤判 |
| `qt-push` 之類的快捷指令不能用 | 已於 2026-11-27 移除（指向已刪除的舊資料夾，且舊版用 `git add -A`）。請改用 `更新網站SOP.md` 的方式 |

---

## 10. 批次作業與歷史文件對照

- **批次作業**：超過 5 個檔案的重複性修改，先在 `tasks/<任務名>/plan.md` 寫明目標、範圍、驗收標準再執行（範本在 `tasks/_templates/`），驗收看 `git diff --stat`。
- **歷史文件**：舊交接文件與雙機時代的腳本、紀錄已於 2026-11-27 刪除（清單見 §2.4），只存在 git 歷史，**不要再依其操作**。
- **人類操作手冊**：`更新網站SOP.md`（請 AI 代推的流程、手動推送、換 AI 的三步驟）。

---

## 11. 所有自動化與排程（總表）

| # | 排程 | 在哪裡設定 | 時間（台北） | 做什麼 | 狀態／停用方式 |
|---|---|---|---|---|---|
| 1 | 當日QT 本機更新 | Hermes cron `7713df5c5e26`（`%LOCALAPPDATA%\Hermes\cron\jobs.json`）→ `scripts\daily_qt_local.py` | 每天 **00:05** | pull → 產生當日QT → commit → push；成功靜默、失敗才通知 | 啟用中。在 Hermes 停用該 cron |
| 2 | 當日QT 備援 | GitHub Actions `.github/workflows/daily-qt.yml` | 00:05 與 04:30 觸發（常延遲 3.5～6.5 小時） | 同上；內容沒變就跳過 commit | 啟用中。停用該 workflow |
| 3 | 當日QT 檢查 | Hermes cron `72e54234771a` → `scripts\check_daily_qt.py` | 每天 **07:30** | 檢查線上 `/today-qt/` 是否為今天；異常才通知 | 啟用中 |
| 4 | YouTube 滴傳 | Mac launchd `com.cmtc.qtupload`（plist 樣板在 `tasks/mac-handover/`） | 每小時 **:05** | 上傳 1 支 → 更新 `yt_uploaded.csv`、`data/qtvideos.json`、`tasks/progress/` → push | 啟用中；影片傳完後腳本自動退休。停用：`launchctl bootout gui/$(id -u)/com.cmtc.qtupload` |
| 5 | 網站部署 | Cloudflare Pages（GitHub 整合） | 每次 push 到 `main` | 建置 → 1～3 分鐘上線 | 啟用中 |
| 6 | 建置檢查 | GitHub Actions `.github/workflows/deploy.yml` | push 到 `main` 且動到網站核心檔 | Hugo 建置＋單檔 20 MiB 警戒 | 啟用中 |
| 7 | 清除歷史金鑰 | ZCode 排程 `automation-8ab5db00-fc24-4730-a010-8e2547789991` | 每月 1～10 號 **14:30**（首次 2026-12-01） | 檢查影片是否傳完 → `rewrite_history.py --push` → 驗證 → 回報 | 啟用中；成功一次自動停止，失敗即停止並回報 |

**已停用、不要再開**：Windows 上傳器 `QT-Upload-5090`（2026-09-25 停用，腳本已刪除）；舊 5090 節點的生成排程 `QT-Nightly-5090`／`QT-GenLoop-5090`／`QT-GenOnce-5090`／`QT-DailyReport-5090`（生成已完成，腳本已刪除）；雙機信箱派工。

---

## 12. 影片管線（生成已完成、上傳收尾中）

- **目標**：每段 QT 經文一支 16:9 全文朗讀影片（數位主播）。同一段經文有多篇文章時只做日期最新那篇，所以是「新約 848 支＋舊約 1,861 支」，不是文章總數。
- **生成**：已在 Windows 的 5090 節點（`C:\Users\user\qtproject`，ComfyUI＋InfiniteTalk）全部完成。成品在本機 `video-output/head/`（待傳區）與 `video-output/head/old/`（已傳歸檔），共約 2,700 支、81 GB，**不進 git**。本機不需要 ComfyUI。
- **上傳**：Mac mini 每小時上傳 1 支到 YouTube 頻道 `@aweholy731`，流程：`yt_publish.py --auto --no-push --limit 1` → 寫入 `video-pipeline/yt_uploaded.csv`（**唯一權威紀錄**）→ `build_qt_library.py` 產生 `data/qtvideos.json` → `tasks/progress/gen_progress.py` 更新進度表 → commit＋push。
- **網站端**：`layouts/qt-video/list.html`＋`static/js/qt-library.js` 讀 `/data/qtvideos.json` 動態渲染；文章頁不內嵌影片。
- **兩代腳本**（都在 `video-pipeline/`）：第一代 `extract_text.py`＋`make_video.py`＋`batch_make.py`（靜態背景＋Edge TTS）；第二代 `comfy_talking_head.py`＋`nightly_head.py`（ComfyUI 數位主播，實際採用）。上傳相關：`yt_publish.py`、`build_qt_library.py`、`yt_first_run.bat`（首次安裝 Google API 套件）。
- **不要做**：不要重跑生成腳本；不要同時讓兩台機器上傳；不要手改 `yt_uploaded.csv`；不要在 Mac 生成。
- **上傳全部結束後**：停用 Mac 的 launchd；`video-output/`（81 GB）要不要刪由本人決定；`tasks/mac-handover/`、`tasks/progress/` 轉為歷史。

---

## 13. 帳號與外部服務（不含任何金鑰）

| 服務 | 帳號／識別 | 用途 | 注意 |
|---|---|---|---|
| GitHub | `aweholy777`（repo owner） | `aweholy777/aweholy777.github.io` | 本機 `gh` 另登入 `galilee7989`；push 前必 `gh auth switch --user aweholy777`。本機 git 的 HTTPS 認證走 `gh auth git-credential`（跟著 gh 的作用中帳號） |
| Cloudflare | 帳號 ID `ee4d7f3e51b89be421114501fa50bf09`（Aweholy@gmail.com） | Pages 專案 `cmtc`、網域 `cmtc.tw` 的 DNS、R2 | 本機 wrangler 登入的是**另一個** Cloudflare 帳號；動網站設定一律用上面這個 |
| 網域 | `cmtc.tw`（NS：`phil`／`uma.ns.cloudflare.com`）；`www.cmtc.tw`、`aweholy.eu.cc` 也指向同一個 Pages 專案 | | `www` 直接服務、不轉向（canonical 指向 `cmtc.tw`） |
| 信箱 | `@cmtc.tw`：MX → `mail.cmtc.tw`（舊主機 a2hosting，`85.187.128.61`） | | `mail.cmtc.tw` 的 Proxy 狀態必須是「僅 DNS」 |
| YouTube | 頻道 `@aweholy731`；上傳憑證 `video-pipeline/client_secret.json`＋`yt_token.json`（本機與 Mac 各一份，不進 git） | QT 影片 | 24 小時上限 24 支；同一時間只能一台機器上傳 |
| 《活潑的生命》進度來源 | ① `duranno.tw/livinglife`（長期維護中）② CGN 中文頻道 RSS `UCqUnxXxHSFb6At-njlSX9AQ` ③ 自家 `/api/daily-reference` | 當日QT 的經文範圍 | |
| 信望愛 FHL | `bible.fhl.net/json/qb.php`（`version=unv`） | 和合本經文 | 一律單次範圍查詢 |
| Google Analytics | `G-99DBKKYEC1`（`hugo.toml`） | 流量分析 | |
| Google Search Console | 驗證檔 `static/googled33be0e0f13982a9.html`＋`baseof.html` 的 meta | 網站所有權驗證 | 勿刪 |
| Google 自訂搜尋 | `cx=c517b71dd612249d`（`layouts/partials/google-search.html`，頁尾） | 第三方搜尋框 | 站內已有 `/search/`；日後可考慮移除 |
| Google Fonts | Open Sans（`baseof.html`） | | 第三方 |
| Hermes | 本機 AI 代理；cron 在 `%LOCALAPPDATA%\Hermes\cron\jobs.json`，腳本在 `%LOCALAPPDATA%\Hermes\scripts\` | 00:05 產生、07:30 檢查 | 腳本正本在 `tasks/daily-qt/`；不手改 Hermes 目錄裡的其他東西 |
| ZCode | 排程 `automation-8ab5db00-fc24-4730-a010-8e2547789991` | 清除歷史金鑰 | 見 §11 |

---

## 14. 已知待辦與未決事項（細節與最新狀態在本機 `進度.md`）

1. 【排程中】清除 GitHub 歷史裡的金鑰（§11 #7）。做完後 2026-05-17 之後的 commit SHA 都會改變。
2. 【等影片傳完】停用 Mac launchd；`video-output/`（81 GB）是否刪除；`tasks/mac-handover/`、`tasks/progress/` 轉歷史。
3. Hermes cron 改指向 repo 內的腳本（目前跑的是 `%LOCALAPPDATA%\Hermes\scripts\` 的副本），並改用專案 `.venv` 的 Python（目前借用 Hermes 自己的 Python；使用者的規則是不借用 AI 工具自己的環境）。動 Hermes 目錄需本人同意。
4. 待本人決定的小項：
   - 選單「生活故事」點進去是空頁（`content/testimonies/life-stories/_index.md` 是空檔，沒有文章列表）
   - `www.cmtc.tw` 要不要加轉向規則自動轉到 `cmtc.tw`
   - `content/deep-calls-deep/` 的草稿與重複頁（`_index - 複製.md`、`追求生命的長進 .md`、`超前部署.md`、`生活故事 .md`）
   - 讀經記錄表有 3 份重複（`content/daily-qt/bibletracker.html`、`static/daily-qt/bibletracker.html`、`Biblereadingtracker.html`）
   - `content/daily-qt/announcement.md`（停更公告）已從選單移除，頁面是否刪除
   - `/api/daily-reference` 對上游沒有逾時也沒有快取
   - 頁尾的 Google 自訂搜尋框是否移除（站內已有 `/search/`）
   - 搜尋是否改用 Pagefind（目前 4 分片 ≤ 10.42 MiB 且已改成輸入才下載，短期無壓力）
5. 本機的 `video-pipeline/_new_settings.json`、`_claude2_settings.json` 已於 2026-11-27 刪除（本人同意）。它們的舊版本仍在 GitHub 歷史裡，由 §11 #7 的排程清除。

---

## 15. 換到新電腦的接手檢查清單

1. 裝好：git、GitHub CLI（`gh auth login` 登入 `aweholy777`）、uv、Python 3.12+、Node.js（跑 `sort-daily-qt-indexes.js`）。
2. `git clone https://github.com/aweholy777/aweholy777.github.io.git` 到 `D:\AI成品\qtproject`。
3. 下載 `hugo_extended_0.144.2_windows-amd64.zip`，把 `hugo.exe` 放在 repo 根目錄（已 gitignore）。**不要用 winget 裝 Hugo**（見 §9）。
4. 跑 `.\hugo.exe --minify --buildFuture`，確認 0 錯誤、約 3,700 頁。
5. 從舊機複製本機筆記：`進度.md`、`經驗.md`、`CLAUDE.local.md`（都 gitignored）。
6. （還在上傳期間才需要）建 `.venv`（§2.3）；用隨身碟／AirDrop 複製 `video-pipeline/client_secret.json`、`yt_token.json`，**絕不經過對話或雲端**。
7. 重設每日 QT 排程：把 `tasks/daily-qt/daily_qt_local.py`、`check_daily_qt.py` 放到 Hermes 的 scripts 目錄，建兩個 cron（00:05、07:30，`no_agent`，失敗才通知）。
8. 讀完本檔與本機筆記，回報你理解的現況，等使用者確認後再動手。
