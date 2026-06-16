# 生成加速 A/B 測試 plan（5090 節點）

> 目標：在「畫質不變」前提下，找出能真正加速 InfiniteTalk 生成的設定，用**同長度 A/B、一次只改一項**量化，避免重蹈 blockswap「跨長度誤算 1.81x（實為 1.15x）」的覆轍。

## 背景（目前實測設定，取自 _last_prompt.json）
- 模型 14B fp8（`fp8_e4m3fn`）、`base_precision=fp16_fast`、attention=**sdpa**
- 取樣 6 步、**cfg=1（已無 CFG 加倍空間）**、scheduler `dpm++_sde`、shift 11
- **fps=25**、frame_window_size=81、blockswap=0（已採用）
- **無 TeaCache、torch.compile 未在實際 prompt 生效**
- 單篇 ~107–178 分（平均 ~2h），瓶頸＝運算本身（14B × 大量影格）

## 要測的槓桿（各自獨立一輪，對照同一基準）
| 代號 | 變更 | 預估 | 風險 |
|---|---|---|---|
| BASE | 現狀（對照組） | — | — |
| A | fps 25→**20**（同時改 `MultiTalkWav2VecEmbeds.fps` 與 `VHS_VideoCombine.frame_rate`） | ~1.25x | 平滑度略降 |
| A2 | fps 25→**16** | ~1.56x | 平滑度再降，要看可否接受 |
| B | 量化 `fp8_e4m3fn`→**`fp8_e4m3fn_fast`** | ~1.1–1.3x | 幾乎無感 |
| C | **加 `WanVideoTeaCache`**（先用預設門檻，例如 rel_l1 ~0.15） | ~1.3–2x | 動作/嘴型平滑度，需肉眼看 |
| D | **勝出項組合**（如 A+B+C）跑一輪確認疊加 | — | 綜合 |
| （選配）E | torch.compile 接上 | ~1.1–1.3x | 首次編譯慢、Triton/Win 風險 |
| （選配）F | SageAttention 2.x（attention sdpa→sageattn） | ~1.3x | 需 Blackwell/cu130 wheel，安裝風險高 |

## 方法（關鍵：可比、可信）
1. **固定測試輸入**：選同一篇文章，**把旁白截到約 3 分鐘**（軍師指定；旁白取前 ~800 字 ≈ 3 分音檔；所有輪次用完全相同的截斷音檔）。
   - 短片只為「快速比較」：ratio 會隨長度變，但**所有輪次同長度** → 相對加速（變更 ratio ÷ BASE ratio）有效、可排序。
   - 不要拿不同長度互比（這就是上次誤算的原因）。
2. **一次只改一項**，從 BASE 複製 workflow，用 `mutate_workflow.py`（沿用 `tasks/sageattn-speedup/` 的做法改寫）切換單一參數。
3. **每輪記錄**：總耗時、ratio（運算分鐘÷影片秒）、相對 BASE 加速倍數、VRAM 峰值、輸出 mp4 抽 2–3 張影格（含嘴型動的段落）存檔供肉眼比對。
4. **畫質判定**：BASE 與各變更的樣片並排看——嘴型同步、臉部穩定、無破圖/鬼影、字幕正常。畫質不過關的一律淘汰，不論多快。

## 執行條件（重要）
- **只在 GPU 空檔跑**：今晚批次（01-25~01-30）跑完、且在 18:00 夜批前。先確認無 `nightly_head` 程序在跑。
- 測試**不動 production workflow**；所有變更只在測試副本上，確認勝出後才正式套用並 commit。
- 測試期間不影響夜間排程（必要時測到一半要讓位給 18:00 夜批）。

## 交付（result.md）
- 表格：`設定 | 總耗時 | ratio | 相對加速 | VRAM | 畫質判定`
- 結論：建議採用哪些（單項與組合）、預估整批新加速倍數、是否值得再上選配 E/F。
- 勝出設定如何正式套用（改哪個檔的哪個參數）。

## 狀態
- [ ] 確認 GPU 空閒（夜批已完成）
- [ ] 備妥固定測試輸入（同篇、截 ~3 分／~800 字）
- [ ] BASE 基準
- [ ] A / A2（fps）
- [ ] B（fp8_fast）
- [ ] C（TeaCache）
- [ ] D（組合）
- [ ] result.md：數字＋樣片＋建議
