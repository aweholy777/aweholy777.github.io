# SageAttention 加速 — 交接備忘（5090 節點）

> 建立：2026-06-15。目的：把 InfiniteTalk 生成的 attention 從 `sdpa` 換成 `sageattn`，
> 不掉畫質拿到約 1.3× 加速（一晚 4 篇 → 更快或更多篇）。

## 背景（為什麼要做）

- 生成慢的真因是**影片長**：全文 InfiniteTalk，一篇 6～9 分鐘、25fps ≈ 1.2 萬幀，
  81 幀視窗滑動約 150+ 個視窗，每視窗 ~50 秒。GPU 已滿載，設定（steps=6 蒸餾、
  fp8、480p 生成）都已優化過。
- 唯一沒吃到的免費加速是 attention：workflow 寫死 `sdpa`（最慢退路），因為機器原本
  沒裝 sageattention / flash_attn / triton。

## 已完成（2026-06-15，未重啟 ComfyUI、未改 workflow、未碰生成中的 01-18）

- ✅ `pip install triton-windows` → **3.7.0.post26**（cp313），import OK
- ✅ `pip install --no-deps sageattention` → **1.0.6**（triton 後端、免編譯），import OK，`sageattn` 可呼叫
- ✅ torch 未被動到，仍 2.12.0+cu130 / CUDA 13.0 / sm_120

## 環境常數（實機）

- Python：`C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe`（3.13.14）
- torch 2.12.0+cu130，CUDA 13.0，RTX 5090（sm_120, Blackwell）
- workflow：`video-pipeline/workflows/infinitetalk_lan.json`
- 要改的節點：`WanVideoModelLoader`，第 5 個 widget = attention（目前 `sdpa`）

## 關鍵更正：本機實際用的 workflow + 真正的瓶頸

- 本機 `--server local` 實際載入的是 **`wanvideo_2_1_14B_I2V_InfiniteTalk_example_03.json`**
  （DEFAULT_WORKFLOW，`comfy_talking_head.py:48`），**不是** `infinitetalk_lan.json`（那支是 LAN 遠端用）。
- 該 workflow 的 **`WanVideoBlockSwap = 40`** —— 32GB 5090 根本不用退避 40 個 block，
  每步在 GPU↔CPU 間搬權重，**這很可能是比 attention 更大的慢因，且改成 0 是免費的**。
- attention 仍是 `sdpa`。peak VRAM 是「每 81 幀視窗」決定（與影片總長無關），
  所以單篇測試即可驗證 blockswap=0 不會 OOM。

## 已自動化（2026-06-15 設好，**今天 14:00** 自動跑；State=Ready, NextRun 06-15 14:00）

Windows 排程 **`QT-SageTest`**（一次性，今天 14:00，StartWhenAvailable）→ 跑
`tasks/sageattn-speedup/run_test.ps1`。方針 = **workflow 只計測永遠復原；測試影片用「下一個進度」那篇，好就上傳、不好就留著**：

1. 守門：批次/ComfyUI 仍忙 → 中止、不動 workflow。
2. 備份 → 套用測試版（attention→sageattn、blockswap 40→0）。
3. 重啟 ComfyUI（讓它載入新裝的 sageattention）。
4. `nightly_head --count 1` 生成「下一個進度」那篇並計時、量 mp4。
5. **影片處置**：
   - 好（exit 0 + mp4 有效 >1MB）→ `yt_publish --video <該檔> --auto --no-push` 精準上傳 +
     嵌 shortcode + 寫 csv，再 `git add csv+被嵌那篇 → commit → pull --rebase → push`（沿用 nightly 的 git 邏輯、衝突即 abort 不硬推）。
   - 不好（crash/OOM/無 mp4）→ **留在 video-output/head 不刪**，等人工檢視/刪除。
6. **finally 一律把 workflow 還原成原版（sdpa/blockswap40）、重啟 ComfyUI 並確認 UP**
   → 今晚 21:00 本番批次永遠跑在已知良好設定，留守期間產線零風險（即使測試影片用 sageattn 生成並上傳，未來生成仍回 sdpa，直到我看 result 後決定是否正式套用）。
7. 結果寫 `result.md`（speedup 倍數 + 建議 KEEP/REVERT + 上傳處置）；我下次上線讀它再決定是否正式套用 sageattn+blockswap0。

輔助檔：`mutate_workflow.py`（backup/apply/restore/show）、`run_test.log`、`gen.log`。

## 狀態
- [x] 套件安裝（triton-windows 3.7.0 / sageattention 1.0.6）
- [x] 自動測試腳本 + 排程（QT-SageTest @ 2026-06-16 14:00）
- [ ] 14:00 自動跑出 result.md（明天）
- [ ] 我讀 result → 若 KEEP 則正式套用（supervised）/ 否則維持 sdpa

## 風險／備援

- SageAttention **v1**（已裝）約 1.3×。v2（~2×）需 cu130/sm_120 預編譯 wheel，Blackwell 上
  不一定現成，風險高 → 先用穩的 v1，v2 之後再評估。
- 首次 JIT 若在 sm_120 報錯：回 `sdpa`、不影響每日產線；再查 triton-windows 對 sm_120 支援。

## 狀態
- [x] 套件安裝
- [ ] 改 workflow + 重啟 + 短測試（明天白天，批次跑完後）
- [ ] 定案 / 回退
