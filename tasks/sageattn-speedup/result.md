# 加速測試結果（2026-06-15 測；2026-06-16 更正數字）

## [2026-06-18] STEP 1 環境探查（SageAttention 2.x 試驗；未安裝任何東西、零 GPU、正式環境未動）

**正式 ComfyUI 環境（系統 Python `…\Python313\python.exe`）：**
- torch **2.12.0+cu130**（CUDA build 13.0）、cudnn 9.20.0、python **3.13.14**
- GPU：RTX 5090，compute capability (12,0) = **sm_120（Blackwell）**，`cuda.is_available()=True`
- triton：import 版本 **3.7.0**（但無 pip metadata，疑為手動/附帶安裝）

**SageAttention 現況（決定性）：**
- 已裝，但版本 = **1.0.6 ← 與 2026-06-15 那輪失敗的同一版**。
- 只有 v1 符號（`sageattn`、`sageattn_varlen`、`attn_qk_int8_*`），**無 2.x API**（`hasattr(sageattn_qk_int8_pv_fp16_cuda)=False`）。
- 故 KJNodes「Patch Sage Attention」節點若設後端 `sageattn_qk_int8_pv_fp16_cuda`，會與上輪一樣 `ImportError: Selected attention mode not available` → fallback sdpa（不加速）。

**接線零件已就緒（缺的是 sage 2.x 本體）：**
- KJNodes 有 `PathchSageAttentionKJ` 節點，`sageattn_modes` 含 `sageattn_qk_int8_pv_fp16_cuda`／`_triton`／…（3060 指定的接法可行）。
- ComfyUI core `attention.py` 與 WanVideoWrapper 都能 `from sageattention import sageattn`。

**風險判定（修正 3060 TODO 的假設）：**
- 3060 TODO 假設的預編 wheel＝「SageAttention 2.2.0 + cu128 + PyTorch 2.11 nightly」，**與實機不符**（實機是 cu130 + torch 2.12 + py3.13 + sm120，比假設還新）。該 wheel 不能直接套。
- 要拿到可用的 SageAttention 2.x，需：① 找 **cu130 / torch2.12 / py3.13 / sm120 的預編 wheel**（待查是否存在）；或 ② 源碼編譯（需對應 CUDA toolkit，高風險）；或 ③ 降 torch 去配舊 wheel（**會動到正式環境，違反「正式環境不動」，禁止**）。
- 結論：**屬高風險路徑 → 必須走隔離環境（獨立 venv / ComfyUI 副本），正式那套完全不碰。** 與 3060 的隔離要求一致。

**STEP 1 狀態：完成。**

## [2026-06-19] STEP 2 進度：隔離環境 + sage 2.2 已可用（gamble #1 成功，免降 torch）

**隔離方式**：建 venv `C:\Users\user\sage-venv`（`--system-site-packages`：繼承系統的 ComfyUI 依賴，只在 venv 內覆蓋 sage/torch）。**system python 完全未動**（pip 明確 "Not uninstalling sageattention … outside environment"，正式仍 1.0.6）。
**wheel**：3060 指的 ziggyxp release 有 `sageattention-2.2.0+cu130.torch2.11-cp313-cp313-win_amd64.whl`（6.4MB），下載至 `C:\Users\user\sage-wheels\`。`pip install --no-deps` 進 venv。
**gamble #1（免降 torch）成功**：
- 在**繼承的 torch 2.12.0+cu130** 下 `import sageattention`＝2.2.0，`sageattn_qk_int8_pv_fp16_cuda` 等 2.x API 都在。
- **GPU 煙霧測試通過**：sageattn 在 cuda 實跑，輸出 (1,8,256,64) fp16，vs sdpa 平均差 0.00288（int8 量化正常近似）。
- → 對 torch 2.11 編的 wheel 在 2.12 可用，**不必降 torch**。triton「Failed to find CUDA」警告無害（cuda 後端用預編核心，非 triton JIT）。

**下一步（STEP 2 續，A/B 實測，耗 GPU）**：
- 用 venv python 跑**隔離 ComfyUI（port 8189）**，共用模型（extra_model_paths）。
- 在 workflow 副本接 KJNodes「Patch Sage Attention」節點（後端 `sageattn_qk_int8_pv_fp16_cuda`），**不用** `--use-sage-attention` 旗標。
- 同一篇真實 QT A/B：①口型/聲音同步（硬門檻）②加速%。口型完好且顯著才切正式。

---


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
