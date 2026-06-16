# 加速測試結果（2026-06-15 測；2026-06-16 更正數字）

## 結論：BlockSwap 40→0 = **約 1.15 倍加速（快 ~15%）**，免費、畫質不變，已採用並保留

> ⚠️ **更正**：初版 result 寫「1.81x」是**錯的**——測試腳本拿 13 分鐘的測試片(01-20)
> 去比 8 分鐘的基準片(01-16)，但「每秒影片的運算量(ratio)」會隨影片長度下降，
> 跨長度比較把加速灌水。用**同長度**重比才是對的：

- 01-16（8:25 / 505s，**blockswap=40**）→ **135.1 分**
- 01-22（8:24 / 505s，**blockswap=0**）→ **117.1 分**
- 同長度 → **135÷117 ≈ 1.15x（快約 15%）**，2026-06-16 夜批 01-21/01-22 實測一致（ratio ~13.9）。

原因：blockswap=40 時 5090 本就用「非同步權重搬移(2 streams)」把搬移藏在運算後面，
關掉只省下沒被藏住的一小部分。真正瓶頸是 5090 的**運算本身**（14B、~240 視窗），不是記憶體搬移。

- 測試影片 01-20：已上傳 https://youtu.be/ybVnTOIcdpA，已嵌入+push（6ab1eb0）
- 生產採用：blockswap 40→0 已 commit+push（3717e4d），VRAM 峰值 ~24GB/32GB（安全）

## 重要：sageattn 沒有真的生效（這次純測 blockswap）

ComfyUI log：`ImportError: Selected attention mode not available` → fallback `Using pytorch attention`。
WanVideoWrapper 的 sageattn 模式需要 **SageAttention 2.x** 的 API，我們裝的 PyPI **v1.0.6** 不符。
所以這次的加速（修正後 ~1.15x）**完全來自 BlockSwap=0**，attention 仍是 sdpa（與本番同畫質 → 上傳無畫質風險）。

## 收尾的小例外（已處理）

腳本在「上傳成功後 git push」那步丟例外 `Applied autostash`——是 PowerShell 把 git 的
stderr 進度訊息（在 `$ErrorActionPreference='Stop'` 下）誤判成錯誤。實際上 commit 已成功，
只差 push；軍師已手動補 push（6ab1eb0 已上 main）。**腳本 git 區塊待修**（見下）。

## 待辦/建議

1. **正式採用 blockswap=0**（只改 blockswap、attention 維持 sdpa；不要設 sageattn，那只會噴 ImportError）。
   採用後整批 ~1.15x 加速（快約 15%）。
2. **腳本修正**：git 區塊在 `$ErrorActionPreference='Stop'` 下會被 git 的 stderr 噴錯——
   未來若再用 run_test.ps1，需在 git 區塊暫時改 `Continue` 或改用判退出碼方式。
3. **（選配）SageAttention 2.x**：可在 blockswap=0 之上再疊 ~1.3x，但需 Blackwell/cu130 預編譯 wheel，
   風險較高；blockswap=0 已是大頭，v2 屬之後的加碼。

## 狀態
- [x] 套件安裝、煙霧測試、完整測試
- [x] 測得 blockswap=0 → 實際 ~1.15x（初版誤算 1.81x 已更正）；測試影片已上傳+push
- [x] **使用者拍板採用**：production workflow blockswap 40→0，已 commit+push（3717e4d）
- [x] 今晚 21:00 整批自動吃到加速（blockswap 每次提交 workflow 時讀取，不需重啟 ComfyUI）
- [x] 測試排程 QT-SageTest 已移除
- [ ]（選配）日後評估 SageAttention 2.x，可再疊 ~1.3x（Blackwell wheel 風險較高）
