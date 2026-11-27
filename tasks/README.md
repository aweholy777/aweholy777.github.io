# tasks/ — 工具、腳本與各任務紀錄

> 這個資料夾放「網站本體以外」的工具與紀錄。現行流程一律以根目錄 `AGENTS.md` 為準，本檔只是索引。
> 2026-11-27：2026 年中「3060 軍師／5090 執行」雙機作業時代的腳本與紀錄已刪除（`5090-migration/` 的排程腳本、
> `handoff/` 雙機信箱、`dispatch.ps1` 派工、`工作分析報告.md` 等）；需要查考時請看 git 歷史，不要再照那些流程做。

## 現行（每天在跑）

| 資料夾 | 用途 | 注意 |
|---|---|---|
| `daily-qt/` | 每日「當日QT」：`generate_today_qt.py`（產生器）、`build_archive_index.py`（典藏索引）、`daily_qt_local.py`／`check_daily_qt.py`（本機 Hermes 排程執行的腳本正本）、`sort-daily-qt-indexes.js`（重建書卷索引排序） | 核心中的核心；改前先讀 AGENTS.md 第 5 節 |
| `mac-handover/` | Mac mini 接手 YouTube 滴傳的交接包：`upload_mac.sh`（launchd 每小時 :05 執行）、`install_mac.sh`、`README.md` | `upload_mac.sh` 開頭的「收工保險」不可移除；影片傳完後整包轉為歷史 |
| `progress/` | 影片上傳進度表（Mac 每小時上傳後用 `gen_progress.py` 更新） | 傳完後轉為歷史 |
| `purge-history/` | 清除 git 歷史裡外洩金鑰的工具 `rewrite_history.py` 與規格 `plan.md` | 預設只演練；`--push` 會改寫歷史並強制推送 |

## 範本與紀錄

| 路徑 | 用途 |
|---|---|
| `_templates/plan.md`、`_templates/result.md` | 超過 5 個檔案的批次作業，先在 `tasks/<任務名>/plan.md` 寫計畫書再做（AGENTS.md 第 10 節） |
| `cleanup-migration-leftovers/` | 2026-11-27 清理舊網站搬家殘留的計畫書與結果 |

## 歷史（僅供查考）

| 路徑 | 內容 |
|---|---|
| `gen-speedup/`、`sageattn-speedup/`、`teacache-speedup/` | 2026-06 在 5090 節點做的影片生成加速實驗（A/B 測試）。結論已寫進 AGENTS.md 第 7 節的影片參數：25 fps、SageAttention 採用、TeaCache 不採用 |
| `影片生成專案-完整脈絡.md` | 雙機時代「QT 影片自動生成」產線的來龍去脈（兩台機器怎麼分工、信箱怎麼運作），僅供了解歷史 |
