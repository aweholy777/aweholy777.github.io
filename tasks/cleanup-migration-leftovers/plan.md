# 計畫書：cleanup-migration-leftovers

> 2026-11-27 全專案體檢（ZCode）的後續清理。使用者已同意「按建議直接處理」。

## 目標

把 2025-04 從舊網站（WordPress）搬過來時留下的殘留檔清掉，讓 sitemap 裡只剩真正有內容的頁面；
並把誤放在 `content/` 裡的工具腳本搬到 `tasks/`，不再被發布成公開檔案。

## 背景與限制

- 專案：Hugo 站，建置指令 `.\hugo.exe --minify --buildFuture`（0 錯誤才算通過）
- 只動下方檔案清單中的檔案，其他一律不碰
- 刪除的內容都先查證過：沒有任何頁面連向它們（`git grep` 全 repo 0 筆）

## 檔案清單

| 動作 | 路徑 | 說明 |
|------|------|------|
| 刪除 ×18 | `content/testimonies/life-stories/雲彩見證 - 城市宣培中心*.md` | 舊網站「雲彩見證」分類的分頁目錄（第 1～18 頁）。只是文章列表，裡面的連結指向已不存在的舊網址（全 404）；文章本身另有獨立檔案 |
| 刪除 | `content/testimonies/baptism/2019–11–29-2.md` | 與 `2019-11-29-2.md` 內容相同（只差兩行圖片的位置與一個多餘空格），檔名用了全形破折號 |
| 刪除 | `content/testimonies/baptism/2022–08–11.md` | 與 `2022-08-11.md` 同一篇見證，檔名用了全形破折號 |
| 刪除 | `content/bible_menu.md` | 孤兒頁（`/bible_menu/`），只有一張圖，站內沒有任何連結指向它 |
| 搬移 | `content/daily-qt/sort-daily-qt-indexes.js` → `tasks/daily-qt/sort-daily-qt-indexes.js` | 維護 `otqt/ntqt/_index.md` 書卷排序的工具腳本。放在 `content/` 會被 Hugo 發布成 `/daily-qt/sort-daily-qt-indexes.js`（公開可下載） |
| 修改 | `tasks/daily-qt/sort-daily-qt-indexes.js` | `ROOT` 從 `__dirname` 改為 `<repo>/content/daily-qt`（搬移後仍指向同一個資料夾） |
| 修改 | `hugo.toml` | 加 `disableKinds = ["taxonomy", "term"]`：站內文章沒有用分類／標籤，只會多出 `/categories/`、`/tags/` 兩個空頁 |

## 規格

- 搬移後的腳本必須產生與搬移前**完全相同**的三個 `_index.md`（在暫存副本上各跑一次比對，不在正本上跑）
- 其餘頁面的網址一個都不能變

## 驗收標準

- [x] `.\hugo.exe --minify --buildFuture` 無錯誤
- [x] sitemap 網址數 = 原本 − 23（18 分頁目錄 + 2 重複見證 + 1 孤兒頁 + 2 空分類頁），其餘網址完全一致
- [x] `public/daily-qt/sort-daily-qt-indexes.js` 不再存在
- [x] 搬移後的腳本在暫存副本輸出與搬移前一致
- [x] 變更範圍 = 上方檔案清單，無額外變更（`git diff --cached --stat`）
