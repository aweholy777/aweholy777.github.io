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
2. **派工**：用 `opencode run` 把計畫書派給便宜模型執行（NVIDIA 免費 API：DeepSeek V4 Flash 一般出工、Kimi 2.6 需要圖片/影片理解時）
3. **驗收**：只讀 `result.md` 和 `git diff --stat`，有疑慮才打開個別檔案

**禁止親自做的事**（這些派給士兵）：

- 批次生成或改寫 QT markdown（任何 >5 個檔案的重複性編輯）
- 重建各書卷 `_index.md` 索引
- 批次修正 front matter、圖片 URL、標點格式
- 批次寫 HTML/程式碼產出

## 派工協定

```
tasks/<任務名>/
├── plan.md      # 軍師寫：目標、規格、檔案清單、驗收標準
├── result.md    # 士兵寫：完成清單、異常、摘要（<50 行）
└── log.txt      # 士兵的完整輸出落地（軍師不讀）
```

派工指令範例（模型 ID 以 `opencode models` 實際輸出為準）：

```bash
opencode run "讀取 tasks/<任務名>/plan.md 並完整執行。完成後把結果摘要寫入 tasks/<任務名>/result.md（50 行以內：完成的檔案清單、跳過或異常的項目、一句話總結）。不要詢問確認，直接執行。" -m nvidia/deepseek-v4-flash > tasks/<任務名>/log.txt 2>&1
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
