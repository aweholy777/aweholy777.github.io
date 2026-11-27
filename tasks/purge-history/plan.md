# 計畫書：purge-history

> 2026-11-27 立。使用者同意「Mac 的影片傳完後（約 4 天），自動清除 GitHub 舊紀錄裡的金鑰」，
> 範圍選「金鑰＋兩張舊大圖」，Mac 選「自動停掉並重新同步（連不上就只改 GitHub 並給手動步驟）」。

## 目標

公開 repo `aweholy777/aweholy777.github.io` 的 git 歷史裡不再有任何金鑰，網站內容與網址完全不變。

## 背景與限制

- 外洩內容（都已從最新版移除，但舊 commit 仍免登入可抓）：
  - `video-pipeline/_new_settings.json`、`video-pipeline/_claude2_settings.json`（2026-06-12 `53892e85` 進 repo，06-16 只取消追蹤）
  - `tasks/handoff/5090-to-3060.md` 歷史版本中的一行 DeepSeek key（2026-06-14 起，最新版已於 `1363c6f1` 移除；key 本人已於 2026-06-16 撤銷）
- 順便移除早已刪除的兩張舊大圖 `static/images/聖經難字注音_1.jpg`、`_2.jpg`（2026-05-17 加入、07-03 刪除，約 49 MiB）
- 只能動 git 歷史；`content/`、`layouts/`、`static/` 等最新版內容一個位元組都不能變（以 HEAD 的 tree 雜湊驗證）
- 金鑰內容全程不讀、不印、不寫檔（掃描只輸出筆數）
- 必須等 Mac mini 的影片全數上傳完才做（改寫後 Mac 若再用舊歷史 rebase，可能把舊紀錄接回去）

## 做法

`python tasks/purge-history/rewrite_history.py --push`（Windows 端；`uvx git-filter-repo` 臨時執行，不裝進專案）：

1. **前置檢查**：工作目錄乾淨、本機無未推送 commit、`gh` 帳號是 `aweholy777`、遠端已含收工保險 commit `4b9a7041`、
   `data/qtvideos.json` 新舊約 `video_count == passage_count`、Mac 已 10 小時沒有新的 `mac upload:` commit
2. **備份**：`git bundle create video-output/history-backup-<日期>.bundle --all`（`video-output/` 已 gitignore）
3. **改寫**：`git clone --mirror` 到系統暫存目錄 → `uvx git-filter-repo --invert-paths` 移除 4 個路徑 +
   `--replace-text` 把歷史中所有 `sk-…`／`gh?_…`／`AIza…`／私鑰字串換成固定文字
4. **驗證**（在複本上）：HEAD 的 tree 雜湊與改寫前相同；歷史檔名清單不含那 4 個路徑；掃描所有文字 blob 無金鑰樣式
5. **推送**：確認遠端 tip 仍等於改寫前（期間沒人 push）→ `git push --force origin main` → 再以 `ls-remote` 確認
6. **本機對齊**：`git fetch` → 確認本機 main 仍停在改寫前的 tip 且工作目錄乾淨 → `git reset --hard origin/main` → `reflog expire` + `gc`
7. **Mac（最佳努力）**：`ssh` 過去 `launchctl bootout/disable` 停掉上傳排程，並 `git reset --hard origin/main`；連不上就回報

### 為什麼不在本機 repo 直接改寫

本機 00:05 的 `daily_qt_local.py` 會 `git push`。先改本機再推送，中途出錯就會變成本機與遠端兩套歷史。
在複本上做完並驗證、最後一步才推送，任何失敗都能保持原狀。

### Mac 端的保險（已於 `4b9a7041` 上線）

`tasks/mac-handover/upload_mac.sh` 開頭加了「收工檢查」：本機 `data/qtvideos.json` 顯示新舊約全數上傳、
且日期 ≥ 2026-12-01 時，直接 `exit 0`（不 pull、不 push）。檢查任何環節失敗都視為「還沒傳完」照常上傳。
所以影片傳完後 Mac 就不會再碰 git，改寫歷史時不需要先連進 Mac。

## 驗收標準

- [ ] `rewrite_history.py` 演練（不加 `--push`）通過：HEAD tree 雜湊不變、歷史無金鑰樣式
- [ ] 推送後 `git ls-remote` 的 tip 等於複本改寫後的 tip
- [ ] GitHub 歷史掃描（只輸出檔名與筆數）無金鑰樣式、無那 4 個路徑
- [ ] Cloudflare Pages 部署 `success`；`https://cmtc.tw/`、`/today-qt/`、`/search/` 回 HTTP 200
- [ ] 本機 `git status` 乾淨、`hugo.exe --minify --buildFuture` 0 錯誤
- [ ] 備份 bundle 存在於 `video-output/`

## 之後還要做的（程式做不到）

- GitHub 上的舊 commit 在強制推送（force push）後，仍可能用 SHA 直接抓到一段時間：到 <https://support.github.com/contact> 請 GitHub 清掉快取並執行 GC
- 確認一切正常後，`video-output/history-backup-*.bundle` 內含舊歷史，可自行刪除
- 本機筆記與舊交接文件裡引用的 commit SHA（2026-05-17 之後的）會失效，屬預期現象
