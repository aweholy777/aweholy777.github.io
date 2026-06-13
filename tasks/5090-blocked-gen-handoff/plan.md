# 5090 影片生成阻斷 — 交接給 3060 軍師

> 來源：5090 執行節點（DESKTOP-BFSJ95H, user=`user`, RTX 5090）
> 日期：2026-06-14
> 狀態：生成失敗，已停下。未上傳、未 push、未改任何 QT/csv/config。工作樹乾淨。

## 背景

5090 依每日工作流執行「生成 1 篇 → 上傳 → push」。
- 步驟 1（git pull --rebase）✅：fast-forward 到 `8f93a1b`。
- 步驟 2（ComfyUI 存活）✅：`Start-ScheduledTask 'ComfyUI'` 後 `/system_stats` 回 `cuda:0 RTX 5090`。
- 步驟 3（`nightly_head.py --server local --count 1`）❌：兩個阻斷性問題，皆為 5090↔3060 跨機設定不一致。

---

## 問題 A — 硬編碼到 3060 的路徑，生成直接 crash

`video-pipeline/comfy_talking_head.py:22`
```python
COMFY_INPUT_DIR = Path(r"C:\Users\aweholy\ComfyUI-Shared\input")
```
- `aweholy` 是 3060 的 user；5090 是 `user`。
- 在 5090 建立此目錄 → `PermissionError [WinError 5]: 'C:\Users\aweholy'`。
- 5090 正確位置：`C:\Users\user\ComfyUI-Shared\...`。

### 修法（擇一，建議第 1）
1. 改成不依機器、可覆寫：
   ```python
   import os
   COMFY_INPUT_DIR = Path(
       os.environ.get("COMFY_INPUT_DIR")
       or (Path.home() / "ComfyUI-Shared" / "input")
   )
   ```
   兩台 `Path.home()` 各自正確（3060→aweholy、5090→user），需要時用環境變數覆寫。
2. 若 input 目錄與 workflow / extra_model_paths 綁定，改成讀同一份設定來源，別在 .py 硬編 user 名。

### 驗收
- 5090 上 `python -c "from video-pipeline.comfy_talking_head import COMFY_INPUT_DIR; print(COMFY_INPUT_DIR)"` 指向 `C:\Users\user\...`。
- 重跑生成不再出現 `C:\Users\aweholy` 的 PermissionError。

---

## 問題 B — `pending()` 會挑到「已完成」文章 → 硬跑會重複上傳

`video-pipeline/nightly_head.py` `pending()`（約第 52–59 行）判定「已完成」**只看本機 `video-output/head/{slug}.mp4` 是否存在**，不看 csv、也不看 .md 內的 `{{< youtube >}}`。

- `video-output/` 是 gitignored、不進 git；3060 生成的 mp4 不在 5090。
- 5090 本機 `video-output\head` 目前 **0 個 mp4**。
- 於是 nightly_head 從新約書卷順重頭挑，第一篇就挑到 `ntqt/2026-01-12.md`——**3060 早已上傳並嵌入**（`{{< youtube 9qg-EmHP-dw >}}`，csv uploaded_at 2026-06-12）。
- 後果：若只修問題 A 就硬跑，會生成 + 上傳一支**重複**的 YouTube 影片，再 re-embed 一篇已嵌入的文章。

### 修法
`pending()` 的「已完成」判定，除了本機 mp4，再認下列任一即視為已完成、跳過：
1. 該 `.md` 已含 `{{< youtube` shortcode；或
2. 該 slug 已出現在 `video-pipeline/yt_uploaded.csv`（用檔名 `{slug}.md` 比對，**不要比完整路徑**——csv 的 md_path 是各機器絕對路徑，跨機對不上）。

建議（1）最穩，因為 embed 是發布事實的單一真相，且與機器無關。

### 驗收
- 5090 上 `python video-pipeline/nightly_head.py --dry` 列出的隊列**不含**任何已嵌入 / 已在 csv 的篇目（例如 2026-01-12、2026-01-13、2026-05-30 應被排除）。

---

## 完成兩個修法後

3060 修完 push，5090 `git pull --rebase` 後重跑每日工作流（生成 1 篇 → `yt_publish.py --auto --no-push --limit 1` → push csv + 被嵌入那篇）。

若想讓 5090 立即出工而不等修 B：請指定一個「確定 3060 還沒做」的起始篇目，5090 手動指定生成、避開重複。

## 給 5090（士兵）的後續指令
- 在問題 A、B 修好並 pull 到之前，**不要**重跑 `nightly_head.py`／`yt_publish.py`，避免重複上傳。
