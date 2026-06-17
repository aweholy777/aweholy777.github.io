# TeaCache 加速 A/B 測試 plan（5090 節點）

> 接續 `tasks/gen-speedup/`（fps/fp8_fast 已淘汰、維持 25fps）。文件標註 **TeaCache 是本管線最大的未測加速來源**。本輪用同一套「同長度 A/B、一次只改一項」方法量化 TeaCache 的加速與畫質代價。

## 背景（取自 gen-speedup 實測基準）
- production workflow：`video-pipeline/workflows/wanvideo_2_1_14B_I2V_InfiniteTalk_example_03.json`
- 14B fp8、base_precision fp16_fast、attention sdpa、6 步、cfg=1、dpm++_sde、shift 11、**fps=25**、blockswap=0（已採用）
- 同長度 3 分鐘測試片（文章 2026-01-25 旁白前 ~800 字）BASE：**35.7 分、ratio 14.21**（150.9s 片）
- WanVideoSampler 有空的 `cache_args` 輸入 → TeaCache 由一個輸出 `CACHEARGS` 的節點接入（新版統一 cache API；節點名隨版本而異）

## 為何 TeaCache 風險點不同於 fps
TeaCache 是「跳過相鄰時間步間變化小的計算」的快取，理論上**不改 fps、不動 InfiniteTalk 的 25fps 嘴型時基**，所以比降 fps 更可能保住 lip-sync。但門檻過高會略過太多步 → 動作/嘴型糊、鬼影。**畫質判定一樣以肉眼 lip-sync 為準，不過關一律淘汰，不論多快。**

## 要測的設定（各自獨立一輪，對照同一次 BASE）
| 代號 | 變更 | 預估 | 風險 |
|---|---|---|---|
| `base` | 現狀（**本機重跑一次當對照**，不沿用舊數字） | — | — |
| `teacache_lo` | 加 TeaCache，rel_l1 門檻 **0.15**（保守） | ~1.3x | 低，嘴型應可接受 |
| `teacache_hi` | 加 TeaCache，rel_l1 門檻 **0.25**（積極） | ~1.8–2x | 中高，需肉眼確認嘴型 |

（若 `teacache_lo` 畫質 OK 但想再榨，可加跑 `teacache_mid` 0.20；harness 支援任意門檻：`python run_one.py teacache:0.20`。）

## 方法（可比、可信）
1. **固定測試輸入**：`run_one.py` 的 `prep_input()` 從文章 2026-01-25 旁白前 800 字（≈3 分）生成 `_input/test.mp3`，所有輪次共用同一段（決定性、可重現）。
2. **一次只改一項**：harness 從 production workflow 複製副本，**只插入 TeaCache 節點**，其餘全不動（fps/blockswap/步數維持）。
3. **節點自動探測（不寫死）**：harness 執行時向本機 ComfyUI `/object_info` 找「輸出型別 = WanVideoSampler.`cache_args` 型別、名稱含 Cache/Tea」的生產節點，用其 `/object_info` 預設值建 widgets，只覆寫 rel_l1 門檻欄，接到 sampler 的 `cache_args`。→ 跨 WanVideoWrapper 版本穩。
4. **Pre-flight（省時關鍵）**：每輪在昂貴生成前，先本地跑一次 `ui_to_api` 檢查「TeaCache 節點存活於可達圖、且 sampler.cache_args 確實指向它」。失敗即中止、不浪費 30 分鐘生成。
5. **記錄**：`_results.csv`：`config,thresh,video_sec,elapsed_sec,elapsed_min,ratio`。輸出 mp4 留 `_out/`，**抽含嘴型動作的 2–3 張影格**供肉眼並排比對。

## 執行條件（重要）
- **只在 GPU 空檔跑**：18:00 夜批前、且確認無 `nightly_head` 程序在跑。測到一半若逼近 18:00 夜批，讓位給夜批。
- **不動 production workflow**：所有變更只在 `_wf/` 測試副本；確認勝出後才正式套用並 commit。
- ComfyUI 在跑（`Invoke-RestMethod http://127.0.0.1:8188/system_stats` 有回應）。

## 執行步驟（5090）
```powershell
cd C:\Users\user\qtproject\tasks\teacache-speedup
python run_one.py base          # 重跑對照基準（同機同版本）
python run_one.py teacache:0.15 # 保守
python run_one.py teacache:0.25 # 積極
# （選配）python run_one.py teacache:0.20
```

## 交付（result.md，<50 行）
- 表格：`設定 | 門檻 | 總耗時 | ratio | 相對 base 加速 | 嘴型畫質判定`
- 結論：哪個門檻畫質過關、整批新加速倍數、是否值得正式採用。
- **若採用**：production workflow 要插的節點與門檻（harness 已驗證的接線方式）；提醒 blockswap=0 與 TeaCache 可疊加。
- 一句話總結。

## 狀態
- [ ] 確認 GPU 空閒、ComfyUI 在跑
- [ ] `base` 重跑基準
- [ ] `teacache:0.15`
- [ ] `teacache:0.25`
- [ ] 肉眼看片：嘴型同步判定
- [ ] result.md：數字＋樣片＋建議；勝出才套 production
