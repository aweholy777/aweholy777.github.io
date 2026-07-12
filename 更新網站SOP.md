# 更新網站 SOP（cmtc.tw）

> 給自己看的操作手冊。網站怎麼更新、指令怎麼用、出問題怎麼辦，看這一份就好。

## 網站怎麼運作（一句話）

原始碼放在 **GitHub**（repo：`aweholy777/aweholy777.github.io`）→ **Cloudflare Pages** 盯著它 →
**你一 push，Cloudflare 就自動建置，cmtc.tw 自動更新。** 你不用「上傳到 Cloudflare」，它自己會去 GitHub 抓。

---

## 🔧 每次更新網站，就這 5 步

1. **改檔**（新增/修改 QT 文章、改選單…任何檔）。
2. **開 PowerShell**（Windows 左下搜尋「PowerShell」→ 點開；工具會自動載入）。
3. 打這一行、按 Enter（引號裡寫這次改了什麼，隨便寫）：
   ```
   qt-push "改了什麼"
   ```
4. 它會列出要送出的檔 → **看一眼是你改的那些 → 按 Enter 確認**。
5. 看到綠字 **「已推送」= 成功**。等 **1~2 分鐘**，cmtc.tw 就更新了。

---

## 三個快捷指令（開窗即可用，不用先切資料夾）

| 指令 | 什麼時候用 |
|---|---|
| `qt-push "說明"` | 改完檔要送出、更新網站 |
| `qt-sync` | 想看 5090 最新回報 / 同步最新 |
| `qt-status` | 想知道有沒有還沒送出的東西 |

---

## 注意事項

- **不用先 `cd`**——`qt-push` 會自己跳到正確資料夾。
- 引號裡的說明**寫什麼都可以**（例：`qt-push "修正錯字"`）。
- `qt-push` 會**先列出檔案讓你確認**；清單裡若有不該送出的檔，打 `n` 取消、處理掉再重打。
- 從說明複製指令時，**只框灰底程式碼那幾行**，別把中文說明一起貼進去。

---

## 🆘 出問題怎麼辦

- **push 出現 `Permission ... denied to galilee7989`（或別的帳號）**＝ Git 認錯帳號。修：
  ```
  gh auth switch --user aweholy777
  git push
  ```
- **`index.lock` / index corrupt**：`qt-push` 已內建自動清；手動清是 `Remove-Item .git\index.lock -Force`。
- **改了看不到**：等 1~2 分鐘讓 Cloudflare 建置完，再 Ctrl+Shift+R 強制重整。

---

## 架構備忘（給未來的你/AI）

- **GitHub repo `aweholy777/aweholy777.github.io`** = 網站原始碼，**必留**（Cloudflare 靠它建置）。
- **Cloudflare Pages「cmtc」專案** = 服務 cmtc.tw，push 到 main 自動部署。網域 DNS 已搬到 Cloudflare（nameserver：phil/uma.ns.cloudflare.com）。
- **GitHub Pages（deploy.yml）** = 舊的備份鏡像，可留可停，非必要。
- **5090** = 每晚自動推影片到同一個 repo；跟你手動更新內容互不影響，都走同一條路（push → Cloudflare 自動部署）。
- 網站用 **Hugo** 產生；內容在 `content/daily-qt/`。
- 更詳細的來龍去脈見 `tasks/影片生成專案-完整脈絡.md`。
