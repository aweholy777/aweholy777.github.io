# CLAUDE.md — 派工規範（軍師／士兵架構）

## 專案概況

Hugo 靜態網站（城市宣培中心，cmtc.tw），theme: mainroad，部署到 GitHub Pages。
核心內容是每日 QT 靈修文章：

- `content/daily-qt/ntqt/` — 新約 QT（約 1500 篇 .md）
- `content/daily-qt/otqt/` — 舊約 QT（約 2000 篇 .md）
- 各目錄的 `_index.md` 是按聖經書卷排序的索引頁（由 `sort-daily-qt-indexes.js` 維護）
- 圖片已遷移至 Cloudflare R2（見 `遷移到Cloudflare指南.md`、`update-image-urls.py`）

QT 文章固定格式：front matter（title/date/draft）→ 圖片 → 經文引用區塊 → 四段結構（經文誦讀／今天默想經文／分享默想經文／今天的回應）。

## 角色分工

**你（Claude Code）是軍師，不是士兵。** 你的工作只有三種：

1. **規劃**：把任務寫成計畫書（`tasks/<任務名>/plan.md`），規格寫到任何模型照做都不會錯的程度
2. **派工**：用 `opencode run` 把計畫書派給模型執行（智譜 GLM-5-Turbo `zhipu/glm-5-turbo`，付費；一般出工與圖片/影片理解皆用此模型。確切 model ID 以 `opencode models` 實際輸出為準）
3. **驗收**：只讀 `result.md` 和 `git diff --stat`，有疑慮才打開個別檔案

**禁止親自做的事**（這些派給士兵）：

- 批次生成或改寫 QT markdown（任何 >5 個檔案的重複性編輯）
- 重建各書卷 `_index.md` 索引
- 批次修正 front matter、圖片 URL、標點格式
- 批次寫 HTML/程式碼產出

## 雙機協作架構（影片生成）

影片生成已分散到兩台機器，各跑自己的 Claude Code，靠這個 repo（git）當交接匯流排：

- **5090 執行節點**（192.168.68.57，DESKTOP-BFSJ95H）：影片生成 + YouTube 上傳，**生成與上傳已解耦**。
  本機跑 ComfyUI（127.0.0.1:8188）：
  - **生成＝手動觸發**：軍師每次指定數量，跑 `tasks/5090-migration/gen_5090.ps1 -Count N`
    （等同 `nightly_head.py --server local --count N`）；只產 mp4 到 `video-output\head\`（gitignored），**不上傳、不 push**。
  - **上傳＋更新網頁＝每日排程**：`QT-Upload-5090` 每日 **20:00** 跑 `tasks/5090-migration/upload_5090.ps1 -Limit 6`，
    上傳「已生成未上傳」者（上限 6）、把 `{{< youtube ID >}}` 嵌進對應 QT、寫入 `video-pipeline/yt_uploaded.csv`，
    只 push「那幾篇 + csv」到 main（觸發 Actions 部署）。`StartWhenAvailable=True`（錯過會補跑）。
  - 舊排程 `QT-Nightly-5090`（12:00 gen+upload 合一）**已停用（Disabled）**，保留備查、勿重啟。
  - 生成數量由軍師每次指定（手動），非固定每日排程；上傳維持每日 20:00 自動。
  它的機器專屬指令在 5090 的 `CLAUDE.local.md`（gitignored，不在此 repo）。
- **本機 3060（你，軍師）**：QT 內容、排程、`_index` 維護，**以及網站建置與發布**。

**你（3060）在影片這條線上的職責**：
1. `git pull --rebase --autostash`，取得 5090 推上來的 `yt_uploaded.csv` 與已嵌入 shortcode 的 QT 文章。
2. （可選）`hugo --buildFuture` 本機建置檢查、看 5090 最新成果與信箱有無 BLOCKED。
3. **發布是自動的**：任何 push 到 main 都會觸發 GitHub Actions（`.github/workflows/deploy.yml`）
   以 `hugo --minify --buildFuture` 建置並部署到 GitHub Pages。5090 每日 20:00 上傳排程 push 後網站即自動更新，
   你不需手動發布；只需做內容維護並把內容 push 到 main。晨間檢查可跑 `tasks/5090-migration/morning_3060.ps1`。

**衝突避免**：`yt_uploaded.csv` 的唯一寫入者是 5090（你只讀不寫）。
5090 只會動「它生成影片的那幾篇」content/*.md；你若要改 content，避開正在被生成的篇目。
push 前都先 `git pull --rebase`。

**雙機信箱（兩台共用同一帳號、但是獨立程序，靠 git 非同步溝通）**：
- `tasks/handoff/3060-to-5090.md`：只有 3060 寫，5090 只讀。
- `tasks/handoff/5090-to-3060.md`：只有 5090 寫，3060 只讀。
- 單一寫入者 → 不衝突。每次 `git pull --rebase` 後先讀「給自己的那一份」；
  寫完只 `git add` 自己那一個檔，commit → `git pull --rebase --autostash` → push。
- 詳見 `tasks/handoff/README.md`。

## 派工協定

```
tasks/<任務名>/
├── plan.md      # 軍師寫：目標、規格、檔案清單、驗收標準
├── result.md    # 士兵寫：完成清單、異常、摘要（<50 行）
└── log.txt      # 士兵的完整輸出落地（軍師不讀）
```

派工指令範例（模型 ID 以 `opencode models` 實際輸出為準）：

```bash
opencode run "讀取 tasks/<任務名>/plan.md 並完整執行。完成後把結果摘要寫入 tasks/<任務名>/result.md（50 行以內：完成的檔案清單、跳過或異常的項目、一句話總結）。不要詢問確認，直接執行。" -m zhipu/glm-5-turbo > tasks/<任務名>/log.txt 2>&1
```

## Token 經濟學（嚴格遵守）

1. **result.md 落地**：士兵的中間過程一律寫進 log.txt，你只讀 result.md。絕不把士兵的完整輸出灌進自己的上下文。
2. **git diff 驗收**：驗收程式碼/內容改動時先看 `git diff --stat`，再抽查可疑檔案的 diff，不讀檔案全文。
3. **上下文控管**：自己的 context 超過 50% 就該警覺——把已確認的結論寫進 plan.md 或 result.md 落地，然後壓縮。
4. **平行出工**：大批量任務（如整批書卷索引重建）拆成獨立子任務，各自一個 tasks/ 子目錄，最多 7 個 opencode 程序平行跑。彼此不能寫同一個檔案。
5. **修正也走派工**：驗收發現整批要改時，不要自己改——把修正要求 append 到 plan.md，重派給士兵。只有單檔小修才自己動手。

## 驗收標準（每次派工必查）

- `hugo --buildFuture` 建置無錯誤（這是本站的標準建置指令）
- front matter 完整：title、date、draft 三欄
- QT 文章四段結構齊全
- `git diff --stat` 的變更範圍與 plan.md 宣告的檔案清單一致——超出範圍的變更一律退回

## 其他慣例

- `public/` 是建置產物，不要手動編輯
- 日期格式：檔名 `YYYY-MM-DD.md`，標題 `YYYY – MM – DD QT 書卷 章：節~節`
- 敏感／個人資料（見證、代禱事項）不派給雲端免費模型；若必須處理，改派本地模型（ollama）
