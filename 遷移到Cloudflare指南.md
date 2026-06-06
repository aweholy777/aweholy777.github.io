# 遷移到 Cloudflare Pages + R2 圖床指南



browser_batch

成功了！`aweholy.eu.cc` 已成功新增為自訂網域，目前狀態為「正在初始化」。頁面顯示：

> **aweholy.eu.cc 正在架設。此作業可能最久須 48 小時才能完成 DNS 記錄更新，以供訪客瀏覽您的網站。**

實際上因為 DNS 都在 Cloudflare 管理，通常幾分鐘到幾小時就會生效，不需要等到 48 小時。

------

**目前遷移進度整理：**

✅ GitHub repo `aweholy777/aweholy777.github.io` 連結完成
✅ Cloudflare Pages 專案 `cmtc` 建立並部署成功
✅ 自訂網域 `aweholy.eu.cc` 已啟動（DNS 初始化中）
✅ GitHub Actions workflow 改為 build-only 驗證

**您現在可以透過以下網址訪問網站：**

- `https://cmtc.pages.dev`（立即可用）
- `https://aweholy.eu.cc`（等 DNS 生效後，約幾分鐘至幾小時）

------

**剩餘步驟（日後進行）：**

1. **圖片遷移到 R2**：執行 `.\upload-images-to-r2.ps1 -BucketName "cmtc-images"`
2. **更新圖片路徑**：執行 `python update-image-urls.py --r2-url "https://images.cmtc.tw"`
3. **兩年後**：虛擬主機到期時，直接在 Pages 自訂網域新增 `cmtc.tw` 即可

所有說明都在您的資料夾中的「遷移到Cloudflare指南.md」文件裡有詳細說明。











> 目標：將 Hugo 網站從 GitHub Pages 遷移到 Cloudflare Pages，並將圖片移到 Cloudflare R2 免費圖床

---

## 整體架構

```
GitHub Repo (原始碼)
    ↓ push 後自動觸發
Cloudflare Pages (自動 build Hugo + 部署)
    ↓ 網頁內容
cmtc.tw (自訂網域)

static/images/ 裡的圖片
    ↓ 手動上傳一次
Cloudflare R2 Bucket (免費 10GB)
    ↓ 公開 URL
https://images.cmtc.tw/ 或 https://pub-xxxx.r2.dev/
```

**免費額度：**
- Cloudflare Pages：無限流量、500次/月 build
- Cloudflare R2：10GB 儲存、100萬次/月讀取 免費

---

## 第一部分：設定 Cloudflare Pages

### 步驟 1：登入 Cloudflare

前往 [https://dash.cloudflare.com](https://dash.cloudflare.com)，登入您的帳號。

### 步驟 2：建立 Pages 專案

1. 左側選單點 **Workers & Pages**
2. 點 **Create application**
3. 選 **Pages** 分頁
4. 點 **Connect to Git**

### 步驟 3：連接 GitHub

1. 選擇 **GitHub**，授權 Cloudflare 存取您的帳號
2. 在 repository 列表中選擇 `aweholy777/aweholy777.github.io`（或您的 repo 名稱）
3. 點 **Begin setup**

### 步驟 4：設定 Build

填入以下設定：

| 設定項目 | 填入值 |
|---------|--------|
| Project name | `cmtc` 或自選 |
| Production branch | `main` |
| Framework preset | **Hugo** |
| Build command | `hugo --minify --buildFuture` |
| Build output directory | `public` |

**新增環境變數：**
點 **Add variable**，填入：
- 變數名稱：`HUGO_VERSION`
- 值：`0.111.3`

點 **Save and Deploy**，等待第一次 build 完成。

### 步驟 5：設定自訂網域 cmtc.tw

Build 成功後：
1. 進入剛建立的 Pages 專案
2. 點 **Custom domains** 分頁
3. 點 **Set up a custom domain**
4. 輸入 `cmtc.tw`，點 **Continue**
5. 如果您的 `cmtc.tw` 已在 Cloudflare 管理，系統會自動設定 DNS
6. 如果不在 Cloudflare，按照指示新增 CNAME 記錄到您的 DNS 供應商

---

## 第二部分：設定 Cloudflare R2 圖床

### 步驟 1：開啟 R2

1. Cloudflare Dashboard 左側選單點 **R2 Object Storage**
2. 第一次使用需要填信用卡（**不會收費**，只是驗證身份，免費額度非常寬裕）
3. 點 **Create bucket**

### 步驟 2：建立 Bucket

- Bucket name：`cmtc-images`（或自選）
- Location：選 **Asia Pacific (APAC)** 讓台灣速度更快
- 點 **Create bucket**

### 步驟 3：開啟公開存取

1. 進入剛建立的 bucket
2. 點上方 **Settings** 分頁
3. 找到 **Public access** 區塊
4. 點 **Allow Access** → 確認開啟

開啟後，您的圖片公開 URL 格式會是：
```
https://pub-xxxxxxxxxxxxxxxx.r2.dev/圖片檔名
```
（記下這個網址，後面替換路徑時會用到）

### 步驟 4（選用）：設定自訂網域 images.cmtc.tw

如果希望用更好看的網址：
1. 在 bucket 的 **Settings** 裡找 **Custom Domains**
2. 點 **Connect Domain**
3. 輸入 `images.cmtc.tw`
4. 若 cmtc.tw 在 Cloudflare 管理，DNS 會自動設定

設定後圖片網址變為：
```
https://images.cmtc.tw/圖片檔名
```

---

## 第三部分：上傳圖片到 R2

使用本資料夾中準備好的 **`upload-images-to-r2.ps1`** PowerShell 腳本。

### 前置條件：安裝 wrangler

1. 確認已安裝 Node.js（[下載](https://nodejs.org)）
2. 開啟 PowerShell，執行：
   ```powershell
   npm install -g wrangler
   ```
3. 登入 Cloudflare：
   ```powershell
   wrangler login
   ```
   （瀏覽器會開啟，授權後回到終端機）

### 執行上傳腳本

```powershell
# 進入您的 Hugo 專案根目錄
cd C:\Users\aweholy\Desktop\clone\aweholy777.github.io

# 執行上傳腳本（把 cmtc-images 換成您的 bucket 名稱）
.\upload-images-to-r2.ps1 -BucketName "cmtc-images"
```

腳本會自動上傳 `static/images/` 裡的所有 384 張圖片。

---

## 第四部分：更新內容中的圖片路徑

上傳完成後，需要把 content/ 裡所有 `/images/xxx` 改成 R2 的網址。

### 執行替換腳本

```powershell
# 使用 r2.dev 網址（把 pub-xxxx 換成您實際的值）
python update-image-urls.py --r2-url "https://pub-xxxxxxxxxxxxxxxx.r2.dev"

# 或者使用自訂網域
python update-image-urls.py --r2-url "https://images.cmtc.tw"
```

腳本會顯示修改了幾個檔案，並且可以先執行 `--dry-run` 預覽：

```powershell
python update-image-urls.py --r2-url "https://images.cmtc.tw" --dry-run
```

### 同步更新 hugo.toml 的圖片路徑

`hugo.toml` 裡 logo 的路徑也要更新（腳本不處理這個）：

開啟 `hugo.toml`，找到這行：
```toml
image = "/images/logo.png"
```
改為：
```toml
image = "https://images.cmtc.tw/logo.png"
```

---

## 第五部分：從 static/images/ 移除舊圖片

更新完路徑並確認網站正常後，可以把 `static/images/` 裡的圖片刪除，讓 repo 變小：

```powershell
# 先確認網站正常，再執行！
Remove-Item -Recurse -Force ".\static\images\*"
```

---

## 第六部分：停用 GitHub Actions 自動部署

由於改用 Cloudflare Pages，原本的 GitHub Pages 部署 workflow 已經停用（已改為只做檢查，不再部署）。

您也可以到 GitHub → Settings → Pages → 把 Source 改為 **None** 以完全停用 GitHub Pages。

---

## 驗證清單

完成以上步驟後，請確認：

- [ ] Cloudflare Pages 建置成功，可看到網站
- [ ] `cmtc.tw` 正常連到 Cloudflare Pages
- [ ] 圖片在 R2 可以公開存取（直接開圖片 URL 看看）
- [ ] 網頁上的圖片都正常顯示
- [ ] Logo 正常顯示
- [ ] Hugo build 沒有錯誤

---

## 常見問題

**Q: Cloudflare Pages build 失敗，說找不到 Hugo 版本？**
A: 確認環境變數 `HUGO_VERSION=0.111.3` 有設定。

**Q: 圖片上傳後開不了？**
A: 確認 bucket 的 Public access 有開啟。

**Q: 自訂網域設好了但網站還開不了？**
A: DNS 生效需要等 1-24 小時，可用 https://dnschecker.org 查詢進度。

**Q: R2 要收費嗎？**
A: 免費額度：10GB 儲存 + 每月 100 萬次讀取。您的 88MB 圖片遠低於上限，正常流量幾乎不會超過。
