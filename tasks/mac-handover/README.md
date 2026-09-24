# Mac 接手每日上傳（YouTube 滴傳）— 交接包

> 這包是給**在 Mac 上操作的 Codex / 助理**看的。專案在 Mac 的位置：`/Users/haoguozi/Desktop/qtproject`
> （Windows 那台原本在 `D:\qtproject`，同一個 GitHub repo。）

---

## 0. 先記住三條規則

1. **同一時間只能有一台機器在跑上傳。** 兩台同時跑 = 同一支影片重複上傳到 YouTube。
   所以交接時 **Windows 那台的排程一定要先停掉**（第 5 步），Mac 這邊才開排程（第 6 步）。
2. **`video-pipeline/yt_uploaded.csv` 是唯一權威清單**（已上傳哪些影片）。
   它跨機比對時只取路徑後兩段（`<書卷>/<日期>`），所以 Windows 的 `D:\...` 與 Mac 的 `/Users/...`
   都能正確比對，**不會因為換機器而重傳**。
3. **影片檔不在 git 裡**（`.gitignore` 有 `video-output/`，全部 **80.6 GB**，其中 `video-output/head/` 待傳區 **43.8 GB**）。
   內容（文章、清單、腳本）走 `git pull`；影片要靠**檔案複製**。

---

## 1. 讓 Mac 追上最新進度（清單＋文章）

Mac 上那份是**複製來的快照**，會落後。它顯示「2,876 個已修改檔案」＝ 複製時 Windows 的 **CRLF 換行**
和 git 索引裡的 LF 不一致，**不是真的改到內容**。照下面清乾淨再 pull：

```bash
cd ~/Desktop/qtproject

# 1-0 先留紀錄（不改變任何東西），並確認沒有卡在半路的合併
git status --short > ~/mac-status-before.txt
git diff --stat > ~/mac-diff-stat.txt
[ -f .git/MERGE_HEAD ] && git merge --abort

# 1-1 重要關卡：確認 2,876 筆真的只是行尾差異（忽略行尾後應為 0 insertions / 0 deletions）
git diff --ignore-space-at-eol --stat | tail -3

# 1-2 行尾正規化
git config core.autocrlf false
git config core.fileMode false
git checkout -- .                   # 用 git 索引覆蓋工作檔：CRLF 還原成 LF（沒有實質內容會遺失）
git status --porcelain | grep -v '^??' | wc -l    # 應為 0；不是 0 就停手回報

# 1-3 清掉「與遠端同名」的未追蹤檔（**移開備份，不要刪**）
mv 新機接手說明.md 新機接手說明.md.mac-old-backup 2>/dev/null || true
#     .claude/settings.local.json 為本機設定，保留不動（未追蹤不影響 pull）

# 1-4 拉取（只做快進，不產生合併提交）
git pull --ff-only
git log --oneline -3
```

> 為什麼 `git checkout -- .` 是安全的：前一步已經證明「忽略行尾」後差異為 0，
> 也就是說工作檔和索引的內容完全相同、只差 CRLF/LF；覆蓋後不會遺失任何實質內容。
> **若 1-1 出現非 0 的 insertions/deletions，就不要做 1-2，停手回報。**

驗證追上進度了：

```bash
wc -l video-pipeline/yt_uploaded.csv   # 行數要跟 Windows 端一致
tail -3 video-pipeline/yt_uploaded.csv # 應看到最新幾筆上傳時間
```

---

## 2. 憑證（不進 git，要手動複製）

需要兩個檔案放在 `video-pipeline/`：

| 檔案 | 說明 | 必要性 |
|---|---|---|
| `client_secret.json` | Google OAuth 用戶端憑證 | **必須複製** |
| `yt_token.json` | 已授權權杖（含 refresh token，可自動續期） | 複製最省事；或在 Mac 重新授權 |

從 Windows 用 **AirDrop 或隨身碟**複製過去（**不要**貼在對話視窗、也不要上傳到雲端硬碟公開連結）。

複製後確認 git 沒有要追蹤它們（`.gitignore` 已擋，正常不會出現在 `git status`）：

```bash
git status --short video-pipeline/
```

---

## 3. 建立環境（uv + venv）

```bash
xcode-select --install                          # 若沒裝過（git 需要）
curl -LsSf https://astral.sh/uv/install.sh | sh # 裝 uv（裝完重開 terminal 或 source ~/.zshrc）
bash tasks/mac-handover/install_mac.sh          # 建 .venv + 裝套件 + 寫入 launchd 排程檔
```

`install_mac.sh` 會：清掉腳本的 CRLF → 檢查 git/uv → `uv venv .venv --python 3.12` →
裝 `google-api-python-client google-auth google-auth-oauthlib` → 產生
`~/Library/LaunchAgents/com.cmtc.qtupload.plist`。

**排程預設不會被啟用**（避免交接期間兩台同時上傳）。要啟用時才加 `--load`：

```bash
bash tasks/mac-handover/install_mac.sh --load   # 交接完成、Windows 已停掉才用
```

---

## 4. 先手動測試（確認真的會傳、且不重複）

```bash
bash tasks/mac-handover/upload_mac.sh --check   # 只檢查：環境／待傳數／憑證／已上傳數
bash tasks/mac-handover/upload_mac.sh           # 真的上傳 1 支
```

驗收四項：

```bash
tail -5 ~/upload_mac.log                                  # 應出現 OK xxx.mp4 → https://youtu.be/...
tail -1 video-pipeline/yt_uploaded.csv                    # 是剛上傳的那支與時間
git log --oneline -1                                      # 應是 "mac upload: YYYY-MM-DD HH:MM"
git push                                                  # 若已自動 push 則顯示 up to date
```

再到 YouTube 頻道（@aweholy731）確認那支影片**只出現一次**（沒有重複上傳）。

---

## 5. Windows 那台要停掉（交接關鍵）

Windows 上的排程 `QT-Upload-5090` 必須停用，否則兩台會搶著傳同一支：

```powershell
Disable-ScheduledTask -TaskName QT-Upload-5090     # 或：schtasks /change /tn "QT-Upload-5090" /disable
```

（要交回 Windows 時再 `Enable-ScheduledTask -TaskName QT-Upload-5090`。）

> 保險：Mac 版腳本另外有「最近 5 分鐘內 csv 有上傳紀錄就跳過」的防重複機制，
> 就算一時忘了停 Windows，也不會同時傳出兩支。

---

## 6. 啟動 Mac 的每小時排程

`install_mac.sh` 預設**不會**啟用排程；要啟用有兩種方式：

```bash
launchctl load ~/Library/LaunchAgents/com.cmtc.qtupload.plist
# 或重跑： bash tasks/mac-handover/install_mac.sh --load
launchctl list | grep qtupload        # 看到 com.cmtc.qtupload 即成功
```

- 每小時 **:05** 自動跑一趟；Mac 睡眠時錯過的班，**喚醒後會補跑**。
- 建議把 Mac 的「系統設定 → 節能 → 防止自動睡眠」打開，讓它 24 小時跑。
- log：`~/upload_mac.log`（launchd 自己的輸出在 `~/upload_mac.launchd.log`）。

---

## 7. 之後怎麼看進度

| 想知道什麼 | 看哪裡 |
|---|---|
| 已上傳哪些（權威） | `video-pipeline/yt_uploaded.csv` |
| 一眼統計（新舊約各卷進度） | `tasks/progress/_summary.txt`（跑 `python3 tasks/progress/gen_progress.py` 更新） |
| 待傳影片 | `ls video-output/head/*.mp4 \| wc -l` |
| 這一趟發生什麼事 | `~/upload_mac.log` |

### 進度基準（2026-09-25 交接時）
- 影片**全部已生成完畢**（新約 849 ＋ 舊約 1862 ＝ 2711 支）→ **沒有新影片要生成**，只有「還沒上傳的」要傳。
- 新約：**848 / 848 全數上傳完成** ✅
- 舊約：已上傳 294、**待傳約 1567 支**；每小時 1 支、每日上限 24 支 → 約 65 天（11 月底左右）
- 也就是說：Mac 只要拿到最新 `yt_uploaded.csv`，就會自動從「下一支還沒傳的」接著傳，不必手動指定。

---

## 8. 疑難排解

| 症狀 | 原因／處理 |
|---|---|
| `--check` 顯示待傳 mp4 = 0 | Mac 這份沒複製到影片：把 Windows 的 `D:\qtproject\video-output\`（80.6 GB）複製過來 |
| 憑證缺 / `token 更新失敗` | 見第 2 步；或在 Mac 有桌面的環境跑 `python video-pipeline/yt_publish.py --video video-output/head/<某支>.mp4` 重新授權（會開瀏覽器） |
| `上傳腳本回報非零 (exit=N)` | 看 `~/upload_mac.log` 尾段；非 2 的錯誤多半是網路或 token，下一班會自動重試 |
| `exit=2`（配額/上限） | 腳本自動寫 `~/upload_pause.flag` 暫停 24h，過期自動恢復 |
| `git pull --rebase 失敗` | 多半是工作樹又被 CRLF 弄髒：`git config core.autocrlf false && git checkout -- .` 再重跑 |
| 忘了哪台在跑 | `tail -3 video-pipeline/yt_uploaded.csv`：`uploaded_at` 時間＋commit 訊息（`mac upload:` / `5090 upload:`）可看出是哪台傳的 |

---

## 附：修改這些腳本時的注意事項

- **macOS 內建 `/bin/bash` 是 3.2（2007 年版）**，變數後面若緊接中文字（例如 `$DAILY_CAP）`），
  它會把中文字的第一個位元組吃進變數名 → 噴 `unbound variable`。
  **所有變數一律寫成 `${VAR}`**，不要寫 `$VAR` 緊接非 ASCII 字元。
  修改後可用這行自我檢查（把路徑換成你的 repo）：
  ```bash
  python3 - <<'EOF'
  import re; from pathlib import Path
  for f in ["tasks/mac-handover/upload_mac.sh", "tasks/mac-handover/install_mac.sh"]:
      for i, l in enumerate(Path(f).read_text(encoding="utf-8").splitlines(), 1):
          for m in re.finditer(r"\$[A-Za-z_][A-Za-z0-9_]*", l):
              n = l[m.end():m.end()+1]
              if n and ord(n) > 127: print(f"✗ {f}:{i} {m.group(0)} → '{n}'")
  EOF
  ```
- 腳本一律用 `bash script.sh` 執行（不要 `./script.sh`）：從 Windows 複製過來時可能帶 CRLF，
  shebang 會失效；`install_mac.sh` 開頭會自動把 CR 清掉。
- 影片參數（25fps、`audio_scale=0.8`、`sageattn`）不可亂改。

---

## 附：這個交接包的檔案

| 檔案 | 用途 |
|---|---|
| `README.md` | 本文件（步驟總覽） |
| `upload_mac.sh` | macOS 版滴傳主程式（對應 Windows 的 `tasks/5090-migration/upload_5090.ps1`） |
| `install_mac.sh` | 一次性安裝：venv + 套件 + launchd 排程 |
| `com.cmtc.qtupload.plist` | launchd 排程樣板（路徑由 install_mac.sh 填入） |

---

## 附：可直接貼給 Mac 的 Codex 的指令

```
我在這台 Mac（/Users/haoguozi/Desktop/qtproject）要接手每日 YouTube 上傳任務（原本在 Windows 跑）。

請讀 tasks/mac-handover/README.md，照第 1～4 步執行：
1) 把工作樹的行尾差異清乾淨並 git pull 到最新（清乾淨前先確認 git diff --stat 沒有實質內容差異）
2) 確認 video-pipeline/client_secret.json 與 yt_token.json 兩個憑證都在（不在就停下來告訴我）
3) 跑 bash tasks/mac-handover/install_mac.sh 建環境
4) 先 bash tasks/mac-handover/upload_mac.sh --check 檢查，再手動跑 bash tasks/mac-handover/upload_mac.sh 真的上傳 1 支

先不要啟用 launchd 排程（第 6 步），等我確認 Windows 那台已停掉再啟用。
任何一步結果和 README 預期不同（例如待傳 mp4 是 0、憑證缺失、git 有實質衝突），停下來回報，不要自行變通或硬做。
```
