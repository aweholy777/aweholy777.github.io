# 生成加速 A/B 測試結果（2026-06-17）

測試片：01-25 旁白前 ~800 字，音訊 150.9 秒（2.5 分），**所有 config 共用同一段**。
方法：同長度、一次只改一項，跑 `tasks/gen-speedup/run_one.py`，計時寫入 `_results.csv`。

## 數字

| 設定 | 耗時 | ratio（運算秒/影片秒） | 相對 BASE 加速 |
|---|---|---|---|
| BASE（25fps） | 35.7 分 | 14.21 | 1.00x |
| **fps20** | 28.1 分 | 11.16 | **1.27x** |
| **fps16** | 22.7 分 | 9.03 | **1.57x** |
| fp8_fast | ❌ 失敗 | — | 與 lightx2v LoRA 不相容（`fp8_fast is not supported with unmerged LoRAs`） |

- **fp8_fast**：本管線用未合併的 lightx2v 加速 LoRA，ComfyUI 直接報錯不支援 → **用不了**，淘汰。
- **TeaCache**：依軍師指示本輪略過（只測 fps20/fps16）。

## 畫質判定（需肉眼）
降 fps **不影響每一格的畫質**，只影響「動態平滑度」（每秒格數變少）。
靜態講道頭像對平滑度較不敏感，但 16fps 是否可接受需軍師看片決定。
- 測試片：`tasks/gen-speedup/_out/base.mp4`（25fps）、`fps20.mp4`、`fps16.mp4`（皆為純 InfiniteTalk 輸出，未燒字幕，僅供比動態平滑度與嘴型）。

## 建議
- **fps20**：穩健選擇，**1.27x（35.7→28.1 分）**，平滑度幾乎無感差異。
- **fps16**：**1.57x（35.7→22.7 分）**，加速明顯，但平滑度略降，需看片確認可接受。
- 換算整批：6 篇 ~12.5h → fps20 約 9.8h、fps16 約 8h。

## 如何採用（軍師決定 fps 後）
改 production workflow `video-pipeline/workflows/wanvideo_2_1_14B_I2V_InfiniteTalk_example_03.json`：
- `MultiTalkWav2VecEmbeds` 的 `fps`、`VHS_VideoCombine` 的 `frame_rate` 同改為選定值（20 或 16）。
- （`run_one.py` 的 `mutate()` 已有「找值替換」邏輯可參考。）

## 結論（2026-06-17 定案）：全部不採用，維持原設定 25fps

軍師看片後判定 **fps20 與 fps16 都出現「口型與聲音不同步」**——InfiniteTalk 的嘴型生成是綁 25fps 的，
改 fps 會破壞 lip-sync。因此 **fps 不是可用的加速槓桿**，維持 **25fps 不變**。
- fp8_fast：與 lightx2v LoRA 不相容（淘汰）。
- fps20/fps16：加速有（1.27x／1.57x）但**畫質不過關（嘴音不同步）→ 淘汰**。
- production workflow 全程未被改動，無需還原。

**未來若要再榨速度**：TeaCache（本輪未測）是最大潛在來源；或 SageAttention 2.x（需 Blackwell wheel）。
**不要再回頭試降 fps**（已證實會破壞 InfiniteTalk lip-sync）。

## 狀態
- [x] BASE / fps20 / fps16 實測
- [x] fp8_fast（淘汰：LoRA 不相容）
- [x] 軍師看片：fps20/fps16 嘴音不同步 → 全部淘汰，維持 25fps
- [x] production workflow 維持原樣（未動）
