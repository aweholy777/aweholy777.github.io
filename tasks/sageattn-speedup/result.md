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

## [2026-06-19] STEP 2 A/B 結果：sage ≈ 1.75x 加速、畫面完整（口型待軍師看片定）

**接法修正（重要）**：KJNodes「PathchSageAttentionKJ」**不適用 WanVideoWrapper**——它吃/吐通用 `MODEL`，但 `WanVideoSampler.model` 是 `WANVIDEOMODEL`，接上去 `/prompt` 報 HTTP 400 return_type_mismatch。
- 正解：設 **`WanVideoModelLoader.attention_mode = sageattn`**（該 loader 的選項含 sdpa/flash_attn_2/3/**sageattn**/sageattn_3/radial_sage/…）。這正是 2026-06-15 那輪 1.0.6 失敗的同一條路，現在 sage 2.2 補上即生效。
- harness `run_sage.py` 已改為設 loader attention_mode（非插節點），pre-flight 驗證 loader.attention_mode=sageattn。

**A/B（隔離 8189、同一 3 分鐘片 150.9s、單一變因＝attention_mode）**：
| 版本 | attention_mode | 耗時 | ratio |
|---|---|---|---|
| base | sdpa | **35.7 分** | 14.20 |
| sage | sageattn | **20.4 分** | 8.09 |

→ **加速 ≈ 1.75x（快約 43%）**，優於 3060 估的 30-40%。
- 完整性：兩片時長皆 00:02:30.89（sage 未截斷）、皆有 aac 音訊；sage 版抽影格畫面乾淨（主播/背景正常，無黑屏/糊化/變形）。樣片在 `_out/base.mp4`、`_out/sage_sageattn.mp4`（gitignored）。
- **口型同步＝硬門檻，待軍師看片判定**。口型完好才採用＝把正式 workflow 的 `WanVideoModelLoader.attention_mode` 由 sdpa 改 sageattn，並在正式 system python 補裝 sage 2.2（目前正式仍 1.0.6，未動）。

**若採用，正式切換清單（尚未執行，等軍師拍板）**：
1. 正式 system python `pip install` 同一顆 sage 2.2 wheel（取代 1.0.6）。
2. 正式 workflow `wanvideo_2_1_14B_I2V_InfiniteTalk_example_03.json` 的 `WanVideoModelLoader.attention_mode`：sdpa → sageattn。
3. 跑 1 篇真實全長 QT 驗證口型＋耗時，再開大量生成。

## [2026-06-19] STEP 3 定案：軍師看片 OK → **正式採用，已切換放量**

軍師看 A/B sage 片判定**口型 OK → 採用**，並追加「主播頭部搖頭幅度有時過大，稍微減少」。正式切換三項全做：

1. **正式 system python 補裝 sage 2.2**：`pip install --no-deps --force-reinstall` 同顆 ziggyxp wheel，取代 1.0.6 →
   現 `pip show` = 2.2.0、`sageattn_qk_int8_pv_fp16_cuda` 在；torch 仍 2.12（未動）。
2. **正式 workflow 改兩處**（`wanvideo_2_1_14B_I2V_InfiniteTalk_example_03.json`，`--server local` 走的就是這支）：
   - `WanVideoModelLoader.attention_mode`：sdpa → **sageattn**。
   - `MultiTalkWav2VecEmbeds.audio_scale`：1 → **0.8**（減頭部晃動；audio_scale 是 audio 驅動動作強度主旋鈕，0.8 仍保得住口型）。
3. **全長驗證**（2026-02-14，下一篇進度、不重覆）：耗時 **43.4 分**（8196 frames＝5:27.84 影片、114 窗；按 A/B 1.75x 反推 sdpa 全長約 76 分，省 ~33 分）。
   無 fallback 報錯＝sage 真生效；影片 1920x1080/25fps、aac 音訊在、畫面乾淨、字幕正常；連續影格頭部晃動明顯收斂。
   **軍師看片判定口型 OK＋頭部晃動滿意 → 定案放量。**

**現況：正式環境已全面切到 sage 2.2 + sageattn + audio_scale 0.8，往後生成都吃加速＋減晃動。** 02-14 那篇進待上傳池，由每日 20:00 排程上傳。

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
