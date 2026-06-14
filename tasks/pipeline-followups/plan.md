# 影片管線：待辦／低急迫追蹤（2026-06-14 審核留檔）

2026-06-14 全管線審核後，高風險 7 條 + 🟢 兩項小修已處理並 push（59321b8、後續 extract ok 旗標）。
以下為**已知但低急迫**項目，記錄於此供日後或與 3060 協調再處理。**動手前先 `git pull --rebase`、並與 3060 確認**（這些多屬跨檔／命名約定改動）。

## 1. ntqt／otqt 同日同名碰撞（中；但約 1.8 年後才會發生）

**現象**：`nightly_head.build_queue()` 先排完 ntqt（約 2678 篇）才排 otqt。當 otqt 進入隊列、且某日期在 ntqt 與 otqt 都有同名 `YYYY-MM-DD.md` 時，三處會撞：
- `make_video`：`out_mp4 = outdir/(md_path.stem + ".mp4")` → `video-output/head/2026-01-15.mp4` 兩書卷共用同一檔。
- `nightly_head._done_slugs()`：dedup 只用日期 slug，一邊上傳會讓另一邊被誤判已完成。
- `yt_publish.find_md()`：mp4→md 只用日期、ntqt 優先 → 可能嵌進錯的書卷文章。

**已做的部分緩解**：ComfyUI 的 `filename_prefix` 已改成 `qt_head_<書卷>_<日期>`（含子目錄），所以**快取退路不會跨書卷誤抓**。但 out_mp4 檔名與 dedup／find_md 仍只用日期。

**建議修法（跨檔，需協調）**：把「書卷/日期」當成全管線統一 key——
- `make_video` out_mp4 改 `head/<sub>/<date>.mp4` 或 `<sub>_<date>.mp4`；
- `nightly_head._done_slugs()`／`pending()` 與 `yt_publish.find_md()`／csv 一律帶 sub；
- csv 增一欄 `sub`，dedup 用 (sub, date)。
**急迫度低**：otqt 進隊列前還有 ~2678 篇 ntqt（每晚 4 篇 ≈ 1.8 年）。

## 2. yt_publish 的 PUB_REPO 舊機路徑（低）

`yt_publish.py:34` `PUB_REPO = C:\Users\aweholy\qt-publish\...` 為舊機路徑。5090 一律 `--no-push` → 不觸發 `publish_push`；該路徑在 5090 不存在，反而當「忘了 --no-push 也不會誤推」的安全網。
**建議**：若 3060 要用發布副本流程，改成正確路徑或環境變數；否則可整段移除 `publish_push` 與 PUB_REPO（發布已交給 GitHub Actions）。**需 3060 確認發布流程現況再動。**

## 3. _spokenize_refs 誤念比例／時間（低）

`extract_text.py:40` 規則 `(\d+)：(\d+)(?![\d節])` 會把內文中的「比例 3：2」「時間 10：30」也轉成「3章2節」。QT 內文罕見此格式，影響小。
**建議**：限縮成只在像經文引用的上下文（前面有書卷名或「經」字）才轉，或維持現狀（成本/收益低）。

---

## ✅ 處理結果（2026-06-14，於 5090 執行節點）

三項全數處理完畢，改動侷限 `video-pipeline/`（4 檔，淨 -24 行），未動 content/config/網站。

**第 1 項（同日同名碰撞）——已修，但用更省的做法（未加 csv 欄）**：
書卷其實已存在於 csv 的 `md_path` 路徑裡，故改用「`<sub>/<date>`（路徑後兩段）」當跨機 dedup key，
對既有 5 筆 csv 完全相容、零 schema 遷移：
- `make_video.make_one`：out_mp4 → `<sub>_<date>.mp4`。
- `nightly_head`：新增 `_md_key()`，`_done_slugs()`→`_done_keys()` 回 `<sub>/<date>`，`pending()` 用 `(sub,slug)` 比對。
- `yt_publish`：`find_md()` 改從 `<sub>_<date>.mp4` 直接讀書卷（舊式 `<date>.mp4` 仍退回 ntqt 優先，向後相容）；
  `_md_name()`→`_md_key()`，`already_uploaded()` 用 `<sub>/<date>` 比對。
- 既有 `video-output/head/*.mp4`（2 支 ntqt）已就地改名為 `ntqt_*.mp4`，避免重生。
- 驗證：`pending()` 正確跳過 csv 內 4 篇＋改名 2 支，從 2026-01-16 起；`otqt/2026-01-14` 不再被誤判已上傳。

**第 2 項（PUB_REPO 舊機路徑）——已移除死碼**：
發布已全交 GitHub Actions（push main 即部署），`publish_push`/`PUB_REPO`/`setup_publish_clone` 流程廢棄。
整段移除 `publish_push()`、`PUB_REPO` 常數、`subprocess` import 與 main 的呼叫；
`--no-push` flag 保留為相容性 no-op（5090 既有指令不報錯）。

**第 3 項（誤念比例／時間）——已加時間詞防護**：
全語料 67,525 個「數：數」中真正的時間誤判僅 1 例（「清晨5：30」），「以及13：11」等實為經文引用。
故只在 `_spokenize_refs` 裸 X：Y 規則前加 `_TIME_CTX` 防護（清晨/早上/下午…），
不碰 67,524 個合法引用（含「 1：5 」逐節列表）。驗證：時間原樣保留、各式經文引用照常轉換。

（高風險修復與目錄清理見 commit 59321b8 與 5090-to-3060.md 同日 DONE 條目。）
