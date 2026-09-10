# HANDOFF.md — 專案交接說明（給接手的 AI 助理）

> 這份文件是寫給**任何**接手管理這個目錄的 AI 助理看的（不限 Claude Code——
> Codex、Cursor、opencode 等都適用）。目的是讓你一進來就搞懂：這是什麼專案、
> 現在跑到哪、誰在做什麼、有哪些雷區不要踩。
>
> 本檔與 `CLAUDE.md` / `CLAUDE.local.md` / `AGENTS.md`（gitignored）並存，
> 內容有重疊是刻意的——那三份是特定工具（Claude Code / Codex）讀取的規範檔，
> 這份是給人類與任何 AI 看的中性版本。若內容衝突，**以本檔與使用者當下的口頭指示為準**，
> 因為那幾份可能沒跟上最新變化。
>
> **2026-09-10 重要變更**：這個專案原本是「雙機協作」（3060 機器管內容/建置/發布，
> 5090 機器管影片生成/上傳），**已改成單機獨立作業**——現在只有 **5090 這一台機器**
> （`192.168.68.57`，機名 `DESKTOP-BFSJ95H`，RTX 5090）在跑，**一台包辦全部**。
> 如果你看到 repo 裡有些檔案還在講「3060」「雙機」「軍師/士兵跨機」，那是舊架構的
> 歷史文件，**只供參考背景，不要照著去等一台不存在的協作對象**。

---

## 1. 這個專案是什麼

- **城市宣培中心**（cmtc.tw）的網站，Hugo 靜態網站產生器，theme = `mainroad`，部署到 **GitHub Pages**（不是 Cloudflare Pages，雖然有一份遷移指南 `遷移到Cloudflare指南.md`，那次遷移只做了圖片存放，網站本體部署仍是 GitHub Pages）。
- Repo：`aweholy777/aweholy777.github.io`（GitHub 帳號 `aweholy777`，使用者信箱 `aweholy777@gmail.com`／`aweholy@gmail.com`）。
- **核心內容**是每天一篇的 QT（Quiet Time／靈修）文章，分兩個系列：
  - `content/daily-qt/ntqt/` — 新約 QT，檔名 `YYYY-MM-DD.md`，約 849 篇（**已全數寫完，不再新增**）
  - `content/daily-qt/otqt/` — 舊約 QT，約 1862 篇（**已全數寫完，不再新增**）
  - 兩個目錄各有一個 `_index.md`，是**按聖經書卷順序**排列的索引頁（不是按檔名的日期序），由 `content/daily-qt/sort-daily-qt-indexes.js` 維護排序。
- 每篇 QT 文章近年會再搭配一支**朗讀/講解影片**，生成後以 YouTube 短代碼嵌入文章底部（見下方「影片管線」）。
- 圖片已從本機遷移到 **Cloudflare R2**（`upload-images-to-r2.ps1`、`遷移到Cloudflare指南.md` 有細節，一般不需要再碰）。

### QT 文章固定格式（新增/修改文章務必照這格式）

```markdown
---
title: "2026 – 05 – 31 QT 哥林多前書 10：23~33"
date: 2026-05-31
draft: false
---

![](/images/qt.jpg)

> 哥林多前書 10：23~33
>
> 10：23 經文...（逐節列出，行尾兩個空白＝Markdown 強制換行）

**1. 經文誦讀**

**2. 今天默想經文**
（摘要經文）

**3. 分享默想經文**
（默想內容，可分段）

**4. 今天的回應**
（回應禱告/行動）

{{< youtube VIDEO_ID >}}
```

要點：
- 標題格式固定：`YYYY – MM – DD QT 書卷 章：節~節`（注意年月日之間是「–」不是「-」，前後有空格）。
- 檔名固定：`YYYY-MM-DD.md`（這裡用一般連字號）。
- front matter 三欄必備：`title`、`date`、`draft`。
- 正文固定四段結構，標題文字是**中文數字＋句號**、粗體：經文誦讀／今天默想經文／分享默想經文／今天的回應。
- 經文範圍常用 `~`，但 `hugo.toml` 已關閉 Markdown 刪除線擴充（`strikethrough = false`），所以**可以直接打 `~`**，不會被誤判成刪除線；歷史檔案中很多用 HTML 實體 `&#126;` 代替 `~`，兩種都會正確顯示，新寫不必刻意用實體。
- `{{< youtube ID >}}` shortcode 只在該篇已生成影片並上傳後才會出現，位置固定在**文章最下方、前面空三行**（2026-09-01 統一調整過，`yt_publish.py` 的 `embed()` 函式已固定這個位置，不要手動改回文章開頭）。

---

## 2. 現行架構：單機獨立作業（2026-09-10 起）

**只有一台機器**在管這整個專案：RTX 5090（`192.168.68.57`，`DESKTOP-BFSJ95H`）。這台機器**一手包辦**：

1. QT 內容維護、front matter／格式修正
2. 各書卷 `_index.md` 排序維護（`content/daily-qt/sort-daily-qt-indexes.js`）
3. 影片生成（ComfyUI + InfiniteTalk，見第 3 節）
4. YouTube 上傳、嵌入 `{{< youtube ID >}}` shortcode
5. `hugo --buildFuture` 本機建置檢查
6. 網站發布（push 到 `main` 觸發 GitHub Actions 自動部署，見第 5 節）

判斷方式：`$env:COMPUTERNAME` 應該回傳 `DESKTOP-BFSJ95H`，且 `C:\Users\user\ComfyUI\ComfyUI\main.py` 存在。

**舊的「3060 軍師機」角色已不存在**——不需要等另一台機器 pull/push 交接，也不需要維持雙機衝突避免規則（例如「只碰自己生成影片的那幾篇」這條限制已經沒有意義，因為現在同一台機器什麼都能碰，只要自己注意別互相干擾正在跑的批次工作）。

`tasks/handoff/`（`3060-to-5090.md`、`5090-to-3060.md`、`README.md`）是**舊雙機協作的信箱機制，已停用**，保留備查即可，不需要再往裡面寫新訊息。

---

## 3. 影片生成管線

程式碼都在 `video-pipeline/`：

- `nightly_head.py` — 生成主程式（呼叫本機 ComfyUI，`127.0.0.1:8188`，`--server local`）
- `yt_publish.py` — YouTube 上傳＋嵌入 shortcode＋寫 `yt_uploaded.csv`；單機架構下**不需要再加 `--no-push`**，上傳完直接讓它 push 完成發布即可
- `workflows/infinitetalk_lan.json` — ComfyUI workflow 定義（InfiniteTalk 對嘴生成）
- `yt_uploaded.csv` — 已上傳清單
- `client_secret.json` / `yt_token.json` — YouTube OAuth 憑證，**gitignored，絕不可進 repo**
- 更完整的操作手冊：`video-pipeline/專案報告與操作手冊.md`、`video-pipeline/README.md`、`tasks/影片生成專案-完整脈絡.md`

### 已鎖定、不要亂改的參數（曾測試過，改了會出問題）

- **25fps**：InfiniteTalk 對嘴同步用這個 fps 校準的，**降 fps 會破壞口型同步**，之前試過會壞掉，不要為了加速改 fps。
- **`audio_scale = 0.8`**：減少主播頭部晃動、同時保住口型準確度，這是實測過的甜蜜點。
- **`attention_mode = sageattn`**（SageAttention 加速）：實測約 1.75x 加速（~51 分/部），A/B 測過口型仍同步才採用，勿用 `--use-sage-attention` 旗標接法（Triton 後端會讓 Wan 輸出全黑），要用 ComfyUI-KJNodes 的「Patch Sage Attention」節點、後端 `sageattn_qk_int8_pv_fp16_cuda`。
- **主播指派規則**（`nightly_head.py` 的 `presenter_for()`）：第 1 卷（馬太福音）＝主播1、第 2 卷（馬可福音）＝主播2、**第 3 卷起一律主播1**（不再奇偶輪替）。主播2 只出現在馬可福音那段影片，其餘全部主播1。主播圖：`video-pipeline/assets/presenter.png`（主播1）、`presenter2.png`（主播2）。

### 排程（Windows 工作排程器）

- **生成＝手動觸發**：每次指定數量，跑 `tasks/5090-migration/gen_5090.ps1 -Count N`。只產生 mp4 到 `video-output\head\`（gitignored，不進 git）。
  - 也有全自動循環模式：`QT-GenLoop-5090` 排程每 15 分檢查一次，邏輯是「生 24 部→休息 1 小時→再 24 部」無限循環、重開機自動接續。要停用 `Disable-ScheduledTask -TaskName QT-GenLoop-5090`。
  - **長批次生成不要用一般背景任務（如 Claude Code 的 background bash）啟動**——那種背景任務被系統回收時會連帶砍掉 `nightly_head.py` 子行程，務必透過 Windows 排程任務（脫離終端 session）啟動，才能撐過數小時甚至數十小時的批次。
  - 排程 `QT-GenOnce-5090` 的 `ExecutionTimeLimit` 已從預設 `P1D`（24 小時，會腰斬長批次，實測約 28 部就被砍斷）改成 `PT72H`；派大批（>~28 部）前務必先確認這個設定，驗收時看 log 有沒有出現「生成結束」字樣，不要只看行程還在跑就當作沒問題。
  - **生成 log 是 UTF-16 編碼**：要監看 `gen_5090.log` 內容，PowerShell 用 `Get-Content` / `Select-String` 才讀得對；用 bash 的 `grep` 對 UTF-16 檔案比對不到東西，不要因此誤判「沒有進度」。
- **上傳＋發布＝每小時排程滴傳**：任務名 `QT-Upload-5090`，跑 `tasks/5090-migration/upload_5090.ps1`。
  - 「佇列式滴傳」：每小時整點 05 分跑一次，**每次只傳 1 支**（`yt_publish.py --auto --limit 1`），從 `yt_uploaded.csv` 時間戳算「過去 24 小時已傳幾支」，達到 `DailyCap` 就跳過本次。
  - `DailyCap` 現值：**24**（2026-08-21 上線時從 20 開始，觀察穩定後已調升；若要再調，改排程 Action 參數即可，不用改程式碼）。**不要相信「YouTube 一天只能傳 6 支」這個舊估計**——那是舊排程遺留的保守假設，已被實測推翻，真正瓶頸是頻道自身風控而非 API 配額（每支約消耗 100 點配額、每天理論上可傳上百支）。
  - **退避機制**：`yt_publish.py --auto` 遇到 HTTP 403 配額/上限錯誤時，會印 `QUOTA_LIMIT_HIT` 並 `exit 2`；`upload_5090.ps1` 偵測到後寫暫停旗標檔（暫停 24 小時），之後每小時的跑會直接跳過，24 小時後旗標過期自動恢復。
  - 成功傳 1 支後：`git add` 那篇 QT + `yt_uploaded.csv` → commit → `git pull --rebase` → push（觸發 Actions 部署，即完成發布）→ 把該支 mp4 歸檔到 `head\old\`。
  - 舊排程 `QT-Nightly-5090`（原本是每日 12:00 生成+上傳合一）已停用（Disabled），保留備查，**不要重新啟用**。
- **影片嚴格按聖經卷序生成與上傳**：一律卷序為主、日期為次，依 `tasks/progress/` 的進度表監控，不擅自跳脫順序插隊生成/上傳某一篇。
- 已生成的 mp4 累計在 `video-output\head\`（本機、gitignored，git 看不到）；刪檔只能刪「`yt_uploaded.csv` 內已標記已上傳的那些」，其餘刪了不會重生（生成很花時間，不是隨時可以重跑）。

---

## 4. 進度追蹤

- `tasks/progress/_summary.txt` — 兩系列的總覽數字（已上傳／已生成未上傳／未生成，按書卷分列）
- `tasks/progress/新約進度表.md`、`tasks/progress/舊約進度表.md` — 逐篇明細
- 這幾份檔案目前是**手動/半自動重新產生後 commit** 的快照，不是即時自動更新，讀的時候留意檔案的最後 commit 時間，跟 `yt_uploaded.csv` 的實際內容可能有些微落差（正常，重新整理一次再 commit 即可）。

### 現況快照（2026-09-10，供參考，會過期，請自行重新統計 `tasks/progress/_summary.txt` 取得最新數字）

- 新約 849 篇：已上傳 822、已生成未上傳 27（全部集中在啟示錄）、未生成 0 → **新約已全數生成完畢**，只剩啟示錄尾端待上傳。
- 舊約 1862 篇：已上傳 0（尚未輪到舊約開始上傳）、已生成未上傳 1463、未生成 399（未生成集中在以賽亞書後段～瑪拉基書，即後段先知書多數還沒生成）。

---

## 5. CI/CD 與建置

- `.github/workflows/deploy.yml`：push 到 `main` 或手動 `workflow_dispatch` 時觸發，用 `hugo --minify --buildFuture` 建置（Hugo Extended 0.144.2，Ubuntu runner 上臨時安裝），輸出 `public/` 後部署到 GitHub Pages。**這是唯一的發布機制**，本機不需要另外手動部署。
- **本地建置檢查指令**：`hugo --buildFuture`（跟 CI 一致，差在沒有 `--minify`）。這是驗收任何內容改動的標準指令，**建置 0 錯誤**才算過關。
- **本機 Hugo 安裝（2026-09-10 已處理）**：repo 根目錄放了一份 **釘死版本 0.144.2（跟 CI 完全一致）的 `hugo.exe`**（`.gitignore` 已排除，不會進 git），跑 `.\hugo.exe --buildFuture` 驗證過 0 錯誤。**故意不裝到系統 PATH／不用 winget 裝最新版**——實測過 Hugo 0.166.0（winget 目前給的版本）對 `content/daily-qt/Biblereadingtracker.html` 這種直接放原始 HTML 的內容檔會觸發更嚴格的 `security.allowContent` 政策，直接建置失敗（`access denied: "text/html" is not whitelisted`），那是版本升級帶來的新限制，不代表內容真的壞了。**做建置檢查一律用 repo 根目錄這份 `.\hugo.exe`，不要另外裝或用 PATH 上別的版本**，除非之後特地升級並同步處理這個 security 設定。
- `public/` 是建置產物，**不要手動編輯**，也不會進 git（看 `.gitignore`）。

---

## 6. 目錄地圖速查

```
qtproject/
├── content/daily-qt/
│   ├── ntqt/*.md            # 新約 QT，849 篇
│   ├── otqt/*.md            # 舊約 QT，1862 篇
│   ├── _index.md            # daily-qt 首頁
│   ├── sort-daily-qt-indexes.js  # 維護 ntqt/_index.md、otqt/_index.md 的書卷排序
│   └── announcement.md, Biblereadingtracker.html 等雜項頁面
├── video-pipeline/          # 影片生成/上傳程式
├── video-output/            # 生成的 mp4（gitignored，本機資產）
├── tasks/
│   ├── handoff/             # 舊雙機信箱機制，已停用，保留備查（見第 2 節）
│   ├── progress/            # 進度表（見第 4 節）
│   ├── 5090-migration/      # 各種 .ps1 排程腳本（gen/upload/daily_report 等）
│   └── <其他任務子目錄>/     # 過去派工任務的 plan.md / result.md / log.txt（軍師/士兵模式遺留）
├── themes/mainroad/         # Hugo 主題
├── layouts/, static/, archetypes/   # Hugo 標準目錄
├── hugo.toml                # 站台設定（baseURL=cmtc.tw、選單、markdown 選項等）
├── .github/workflows/deploy.yml    # CI/CD（唯一發布機制）
├── CLAUDE.md                # Claude Code 專案規範（派工架構＋單機作業說明）
├── CLAUDE.local.md          # （gitignored）本機（5090）專屬規範，現涵蓋全部職責
├── AGENTS.md                # （gitignored）給 Codex/opencode 讀的靜態複本，可能過期，不是唯一真相
├── 更新網站SOP.md            # 網站更新標準作業流程
├── 遷移到Cloudflare指南.md   # 圖片遷移到 R2 的說明
└── HANDOFF.md                # 本檔
```

---

## 7. 這個專案過去採用的工作模式（背景資訊，不強制延續）

`CLAUDE.md` 定義了一套「軍師／士兵」派工架構：負責的 AI（軍師）只做規劃、派工、驗收三件事，實際批次改檔案的粗活（>5 個檔案的重複性編輯、批次重建索引、批次修正格式）派給 `opencode run` 呼叫的另一個模型（智譜 GLM，付費）去做，軍師只讀 `result.md` 摘要和 `git diff --stat`，不把士兵的完整輸出灌進自己的上下文。這套跟「單機/雙機」無關，是內容批次編修的方法論，單機架構下一樣適用。

**你不一定要延續這套架構**——如果你是被指派直接管理這個目錄的 AI，你可以視自己的工具能力（有沒有能力/必要另外派工給別的模型）決定要不要用這套模式。但底下這幾條驗收標準和慣例，不管用什麼工作模式，**建議繼續遵守**：

- 改動 QT 內容或索引後，跑 `hugo --buildFuture` 確認建置無錯誤。
- front matter 三欄（title/date/draft）、正文四段結構要齊全。
- `git diff --stat` 檢查變更範圍有沒有超出預期。
- push 前一定先 `git pull --rebase`（或 `--rebase --autostash` 如果工作區有未 commit 的改動）。
- 敏感／個人資料（見證、代禱事項等）**不要派給雲端免費模型**處理；若必須自動化處理，改用本地模型（如 ollama）。

---

## 8. 常見雷區清單（都是實際踩過的坑）

1. **`.ps1` 腳本裡別放中文字元**（給 Windows PowerShell 5.1 用的）——曾經因為編碼被讀成 Big5 亂碼、解析失敗直接 `exit 1`。要嘛全 ASCII，要嘛檔案存成帶 UTF-8 BOM，寫完務必先實際跑一次驗證，不要只看語法。
2. **降 fps 加速生成 = 破壞口型同步**，已測試過淘汰，不要因為想加速又去改 fps。
3. **長時間生成任務不要用一般背景 shell 任務跑**，系統回收背景任務時會把 `nightly_head.py` 一起殺掉；要用 Windows 排程任務（脫離終端）啟動。
4. **排程的 `ExecutionTimeLimit` 預設可能腰斬長批次**——`QT-GenOnce-5090` 原本 24 小時上限，已改 72 小時；派新批次前先確認這個設定夠不夠長。
5. **`{{< youtube ID >}}` 位置固定在文章最下方、空三行**，2026-09-01 統一調整過，不要改回文章開頭。
6. **舊約上傳目前是 0**，這不是異常，是因為新約還沒完全傳完（卷序優先），舊約要等新約全部上傳完才會開始傳。
7. **「YouTube 一天只能傳 6 支」是過期資訊**，現行 `DailyCap=24`（滴傳＋自動退避機制），別照舊估計去規劃排程。
8. **主播2 只出現在馬可福音那段**，其餘全部主播1，不是奇偶輪替——這是後來改過的規則，別誤用舊邏輯。
9. **建置檢查只用 repo 根目錄的 `.\hugo.exe`（釘死 0.144.2，跟 CI 一致）**，不要裝/用 PATH 上更新版本的 hugo——0.15x 起對內容裡直接放 HTML 的檔案（如 `Biblereadingtracker.html`）會有更嚴格 security policy，會誤判成「建置壞了」。
10. **不要被舊文件裡的「3060／雙機」字樣誤導**——那是 2026-09-10 之前的架構，現在只有這台機器，不需要等交接、不需要走信箱。

---

## 9. 建議的第一步 Checklist（接手後照這個順序做）

1. `git status`、`git log --oneline -20`，了解目前 working tree 乾不乾淨、最近做了什麼。
2. 讀 `tasks/progress/_summary.txt`，掌握新約/舊約目前的生成/上傳進度。
3. 確認 `.\hugo.exe --buildFuture`（repo 根目錄，見第 5 節）能不能跑；這份 exe 是 gitignored 的本機檔案，換一台機器或重新 clone 時要重新放一份（下載 CI 用的同版本 0.144.2，不要裝更新版）。
4. 確認 ComfyUI 在跑（`Invoke-RestMethod http://127.0.0.1:8188/system_stats`），生成排程（`QT-GenLoop-5090` / `QT-GenOnce-5090`）與上傳排程（`QT-Upload-5090`）狀態是否正常（`Get-ScheduledTask` 查）。
5. 有疑問或發現本檔跟實際狀況不符（例如進度數字、排程參數已經變了），**直接更新本檔**，讓下一個接手的人（人或 AI）看到的是最新狀態，不要留著過期資訊。
