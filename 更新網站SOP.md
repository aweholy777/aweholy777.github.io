# 更新網站 SOP（cmtc.tw）

> 給自己看的操作手冊。網站怎麼更新、出問題怎麼辦，看這一份就好。
> 給 AI 看的完整說明（目錄結構、所有排程、規則）在 `AGENTS.md`。

## 網站怎麼運作（一句話）

原始碼放在 **GitHub**（repo：`aweholy777/aweholy777.github.io`）→ **Cloudflare Pages** 盯著它 →
**一 push 到 main，Cloudflare 就自動建置，1～3 分鐘後 cmtc.tw 更新。** 你不用「上傳到 Cloudflare」，它自己會去 GitHub 抓。

本機專案位置：`D:\AI成品\qtproject`

---

## ✅ 最省事的做法：請 AI 代勞（建議）

1. 開你的 AI（ZCode、Claude Code、codex…），確認它開在 `D:\AI成品\qtproject` 這個專案裡。
2. 第一句請它：「先讀 AGENTS.md，再跟我確認你要做什麼。」
3. 用白話說你要改什麼（例：「把選單的 OO 拿掉」「新增一篇見證，內容如下」）。
4. AI 會自己：同步最新 → 改檔 → 本機建置檢查 → 推送 → 等網站更新 → 回報結果。
5. 你只要打開網站確認。

AI 說「完成」以前，一定會做這三件事（你可以要求它出示結果）：

- 本機建置 0 錯誤
- Cloudflare 部署成功
- 線上頁面實際打開來驗過

---

## 🔧 想自己推送（需要時才用）

開 PowerShell，依序打（`<檔案>` 換成你改過的檔案，一個一個列出來）：

```powershell
cd D:\AI成品\qtproject
git pull --rebase --autostash origin main
gh auth switch --user aweholy777
git add <檔案1> <檔案2>
git commit -m "改了什麼"
git push
```

- **絕對不要打 `git add -A`**（會把不該上傳的東西一起送出去）。
- 推送後等 1～3 分鐘，網站就更新了。
- 從說明複製指令時，**只框灰底程式碼那幾行**，別把中文說明一起貼進去。

> 原本的 `qt-push`／`qt-sync`／`qt-status` 快捷指令已於 2026-11-27 移除：它指向的舊資料夾早就刪了（早就失效），而且舊版會一次送出所有變更，違反專案規則。

---

## 🆘 出問題怎麼辦

| 症狀 | 處理 |
|---|---|
| push 出現 `Permission denied to galilee7989` | 帳號錯：`gh auth switch --user aweholy777` 再 `git push` |
| push 被拒 `non-fast-forward` | Mac 剛推送過：`git pull --rebase --autostash origin main` 再 push |
| 改了看不到 | 等 1～3 分鐘讓 Cloudflare 建置完再重新整理 |
| 改壞了、想還原 | 不要自己刪檔，直接跟 AI 說 |
| 早上當日QT 沒更新 | 跟 AI 說「補產今天的當日QT」（指令見 `AGENTS.md` 第 5 節） |
| 其他 | 把畫面貼給 AI |

---

## 架構備忘

- **GitHub repo `aweholy777/aweholy777.github.io`** = 網站原始碼，**必留**（Cloudflare 靠它建置）。
- **本機 repo 路徑** = `D:\AI成品\qtproject`。
- **Cloudflare Pages「cmtc」專案** = 服務 `cmtc.tw`、`www.cmtc.tw`、`aweholy.eu.cc`，push 到 main 自動部署。網域 DNS 在 Cloudflare（nameserver：phil／uma.ns.cloudflare.com）。帳號是 **Aweholy@gmail.com**（你另有第二個 Cloudflare 帳號，別登錯）。
- **Mac mini** = 每小時 :05 自動上傳 1 支影片到 YouTube 並推回 `data/qtvideos.json`（傳完後會自動停止動作）；跟網站內容更新互不影響。
- **每日當日QT** = 這台電腦每天 00:05 自動產生並發布（07:30 另有檢查）。
- 網站用 **Hugo** 產生，內容在 `content/`。

---

## 🤖 想換別的 AI 來管這個專案

交接文件只有一份：repo 根目錄的 **`AGENTS.md`**。
（Claude Code 讀 `CLAUDE.md`，它會指到 `AGENTS.md`；Codex／Gemini／opencode 直接讀 `AGENTS.md`。）

### 三步驟

1. 在專案資料夾 `D:\AI成品\qtproject` 開你要用的 AI。
2. 第一句打：

   ```
   先讀 AGENTS.md 與本機的 進度.md、經驗.md，回報你理解的專案現況（部署方式、每日QT 流程、鐵則、目錄結構）。
   現在不要修改任何檔案。
   ```

3. 它講對了 → 再給任務。講錯了 → 把錯的地方補回 `AGENTS.md`（那是唯一權威版本）。

### 三個提醒

- **一次只讓一個 AI 改這個 repo**，兩個同時改會互相打架。
- 任何 AI 都要：`hugo.exe --minify --buildFuture` 0 錯誤、Cloudflare 部署成功、線上實測通過，才算完成（驗收清單在 `AGENTS.md` 第 8 節）。
- 換 AI 不等於換權限：憑證紅線、不亂刪檔、push 前切帳號，全部照舊。

### 這台機器已裝的 AI CLI（2026-11-27 確認）

| 指令 | 工具 |
|---|---|
| `claude` | Claude Code |
| `codex` | Codex CLI |
| `gemini` | Gemini CLI |
| `opencode` | OpenCode |
| `pi` | Pi |

（另有 ZCode 桌面版。）
