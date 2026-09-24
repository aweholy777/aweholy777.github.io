# Mac 接手每日上傳（YouTube 滴傳）— 交接包

> 這包是給**在 Mac 上操作的 Codex / 助理**看的。專案在 Mac 的位置：`/Users/haoguozi/qtproject`
> ⚠️ **不要放在 `~/Desktop`／`~/Documents`／`~/Downloads`**：macOS 隱私保護（TCC）會讓 launchd 背景排程讀不到那裡的腳本，症狀是 `Input/output error` 或 `Operation not permitted`；放家目錄下的 `~/qtproject` 就沒事。
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
cd ~/qtproject

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

## 2.5 讓 Mac 能 push（GitHub 憑證）— 上傳成果靠這個才會上網站

上傳成功後腳本會 `commit` 並 `push` 回 `main`，**push 才會觸發 GitHub Actions 更新網頁**。
Mac 若沒有 GitHub 憑證，push 會失敗（`upload_mac.sh --check` 的「push 測試」那行會顯示 ⚠️）。

先用 `--check` 看是否已經可以；不行才需要設定：

```bash
# a) git 身分（Mac 上通常是空的，沒有它 commit 會失敗）
git config user.name "haoguozi"
git config user.email "aweholy@gmail.com"

# b) 憑證：用 SSH 金鑰（macOS 內建、不需 Homebrew／sudo，排程非互動也最穩）
#    2026-09-25 實測：這台 Mac 沒有 brew 也沒有 gh，所以走這條。
mkdir -p ~/.ssh && chmod 700 ~/.ssh
[ -f ~/.ssh/id_ed25519 ] || ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519 -C "mac-mini-qt"
cat ~/.ssh/id_ed25519.pub
#    → 把上面那行（公鑰，不是機密）貼到 GitHub → Settings → SSH and GPG keys → New SSH key
#      ⚠️ 一定要確認是貼到 aweholy777（不是另一個帳號 galilee7989），貼錯就等於沒用
ssh-keyscan -t rsa,ecdsa,ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null   # 排程非互動執行必須先做
ssh -T git@github.com          # 應顯示 Hi aweholy777!（exit code 1 是正常的）
git remote set-url origin git@github.com:aweholy777/aweholy777.github.io.git

# c) 驗證（顯示 up to date、沒有錯誤訊息就是 OK）
GIT_TERMINAL_PROMPT=0 git push --dry-run origin HEAD:main
git pull --ff-only
```

> 替代方案：**gh 裝置碼流程**（要先 `brew install gh`）——
> `gh auth login --hostname github.com --git-protocol https --web` 後 `gh auth setup-git`；

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
schtasks /change /tn "\QT-Upload-5090" /disable     # 或 PowerShell：Disable-ScheduledTask -TaskName QT-Upload-5090
```

**2026-09-25 02:45 已停用**（停用前確認下次執行 03:05、狀態由「就緒」變「已停用」）。
要交回 Windows 時：`schtasks /change /tn "\QT-Upload-5090" /enable`

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

### 進度基準（2026-09-25 交接完成時）
- 影片**全部已生成完畢**（新約 849 ＋ 舊約 1862 ＝ 2711 支）→ **沒有新影片要生成**，只有「還沒上傳的」要傳。
- 新約：**848 / 848 全數上傳完成** ✅
- 舊約：已上傳 **315 / 1862**、待傳約 **1,547 支**；每小時 1 支、每日上限 24 支 → 約 65 天
- csv 已上傳總計：**1,163 筆**
- **Mac 第一支上傳（交接驗收）**：`otqt_2025-04-28.mp4` → https://youtu.be/W6gettP1_UM
  （2026-09-25 02:50，commit `624b7934`；已確認頻道公開 RSS 只出現一次、無重複）
- 也就是說：腳本會自動從「下一支還沒傳的」接著傳，不必手動指定。

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
| 重跑 `install_mac.sh` 失敗 `A virtual environment already exists` | 已修：腳本現在偵測到既有 `.venv` 就沿用、不重建；真要重建請先 `rm -rf .venv`（會重新裝套件，約 1 分鐘） |
| `Launchctl load failed: 5: Input/output error` | macOS 13+ 的舊 `launchctl load` 在 GUI domain 已失效：改用 `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.cmtc.qtupload.plist`（新版 `install_mac.sh --load` 已自動走 bootstrap）。若換成 Terminal.app 仍失敗，多半是在 Claude/Codex 的沙盒外殼裡執行——launchctl 需要連 launchd 的 gui domain，沙盒會擋掉（症狀就是這個 I/O error） |
| 專案搬移後 `.venv/bin/python` 失效 | `uv` 的 `.venv/bin/python` 是指向 `.uv-python` 的**絕對**符號連結，搬移後會斷。新版 `install_mac.sh` 會就地重指連結並改寫 `.venv` 內舊路徑（不刪檔）；真的修不好才 `rm -rf .venv` 重建 |

---

## 9. 回滾（Mac 出事時，把上傳交回 Windows）

```bash
# 1) Mac：停掉排程
launchctl bootout gui/$(id -u)/com.cmtc.qtupload     # 舊寫法：launchctl unload ~/Library/LaunchAgents/com.cmtc.qtupload.plist
launchctl list | grep qtupload        # 應無輸出

# 2) Windows：重新啟用排程
schtasks /change /tn "\QT-Upload-5090" /enable
```

兩台共用同一個 repo 與同一份 `yt_uploaded.csv`；dedup key 是 `<子目錄>/<日期>`
（`video-pipeline/yt_publish.py` 與 `nightly_head.py` 都刻意只取路徑後兩段、不比對絕對路徑），
所以不管哪一台傳過，另一台都會正確跳過、不會重傳。

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
我在這台 Mac（/Users/haoguozi/qtproject）要接手每日 YouTube 上傳任務（原本在 Windows 跑）。

請讀 tasks/mac-handover/README.md，照第 1～4 步執行：
1) 把工作樹的行尾差異清乾淨並 git pull 到最新（清乾淨前先確認 git diff --stat 沒有實質內容差異）
2) 確認 video-pipeline/client_secret.json 與 yt_token.json 兩個憑證都在（不在就停下來告訴我）
3) 跑 bash tasks/mac-handover/install_mac.sh 建環境
4) 先 bash tasks/mac-handover/upload_mac.sh --check 檢查，再手動跑 bash tasks/mac-handover/upload_mac.sh 真的上傳 1 支

先不要啟用 launchd 排程（第 6 步），等我確認 Windows 那台已停掉再啟用。
任何一步結果和 README 預期不同（例如待傳 mp4 是 0、憑證缺失、git 有實質衝突），停下來回報，不要自行變通或硬做。
```
