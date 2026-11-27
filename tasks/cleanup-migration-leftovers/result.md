# 結果：cleanup-migration-leftovers

完成於 2026-11-27（ZCode）。規格見同目錄 `plan.md`。

## 做了什麼

- 刪除 21 個搬家殘留檔：18 個舊站「雲彩見證」分頁目錄、2 個全形破折號的重複見證、1 個孤兒頁 `content/bible_menu.md`
- `sort-daily-qt-indexes.js` 從 `content/daily-qt/` 搬到 `tasks/daily-qt/`，`ROOT` 改為指向 `content/daily-qt`
- `hugo.toml` 加 `disableKinds = ["taxonomy", "term"]`（不產生空的 `/categories/`、`/tags/`）

## 驗收（實測）

- `.\hugo.exe --minify --buildFuture --cleanDestinationDir`：3,721 頁、0 錯誤
- sitemap 3,727 → 3,704，少的正好是 23 個預期網址，沒有新增任何網址
- 輸出檔 4,148 → 4,122；`public/daily-qt/sort-daily-qt-indexes.js`、`categories/`、`tags/`、`bible_menu/` 已不在輸出中
- 搬移後的腳本在暫存副本的輸出與搬移前一致（`moved: 0、otItems: 1861、ntItems: 848`，三個 `_index.md` 逐行相同）

## 一句話總結

sitemap 裡只剩下有實際內容的頁面，工具腳本不再被發布成公開檔案；被刪的檔案都還在 git 歷史裡，需要時救得回來。

## 這次沒有動的（保留給本人決定）

- `content/deep-calls-deep/` 下的草稿殘檔（`_index - 複製.md`、`追求生命的長進 .md`）與重複頁（`超前部署.md`、`生活故事 .md`）
- 讀經記錄表同時有 3 個網址（`content/daily-qt/bibletracker.html`、`static/daily-qt/bibletracker.html`、`Biblereadingtracker.html`）
- `/testimonies/life-stories/` 目前是空頁：選單「生活故事」點進去只有標題、沒有文章列表
