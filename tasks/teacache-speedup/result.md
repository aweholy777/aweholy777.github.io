# TeaCache 加速測試結果（2026-06-17）

## 結論：不採用。TeaCache 對本管線無加速、反而略慢，維持現狀（25fps + blockswap=0）。

## 數據（同一段 150.9s 測試片、同機同版本、一次只改一項）
| 設定 | rel_l1 門檻 | 耗時 | ratio | vs base |
|---|---|---|---|---|
| base | — | 35.7 分 | 14.21 | — |
| teacache_015 | 0.15 | 36.1 分 | 14.34 | **慢 0.4 分** |
| teacache_025 | 0.25 | 36.4 分 | 14.47 | **慢 0.7 分** |

連最積極的 0.25 都比 base 慢 → **TeaCache 在此是淨負，沒有任何加速可換畫質**，故畫質/lip-sync 判定不必做。

## 原因（明確、可解釋）
- 本管線只有 **6 步取樣**，且已用 **lightx2v 蒸餾 LoRA** 把步數壓到極限。
- TeaCache 原理＝相鄰時間步變化小就跳過重算；**6 步的短排程沒有冗餘步可跳**，反而多付
  「算相對 L1 距離 + 係數多項式 + 快取張量」的固定開銷 → 淨慢。
- TeaCache 是為 20–50 步長排程設計的；對蒸餾過的短排程無效（與 fp8_fast 一樣，敗在與既有蒸餾流程不相容）。

## harness（已入 repo，供日後重測）
- `run_one.py`：不寫死節點名，執行時向 `/object_info` 自動探測 cache 生產節點（測得＝`WanVideoTeaCache`，
  輸出型別 `CACHEARGS`），用預設值建 widgets、只覆寫 rel_l1 門檻，接到 `WanVideoSampler.cache_args`；
  生成前 pre-flight 驗證接線存活（本輪兩輪皆 pre-flight OK，接線正確、確實生效，只是無益）。
- 用法：`python run_one.py base | teacache:0.15 | teacache:0.25`（任意門檻 `teacache:0.20`）。
- 樣片留 `_out/`（gitignored）：base.mp4 / teacache_015.mp4 / teacache_025.mp4，各 6.6MB。

## 加速線總結（三輪測試後定案）
- **已採用**：blockswap 40→0（~1.15x）。
- **全部淘汰**：fps20/fps16（嘴音不同步）、fp8_fast（與 lightx2v 不相容）、**TeaCache（6 步蒸餾無冗餘步可跳，淨負）**。
- **唯一剩餘潛在槓桿**：SageAttention 2.x（需 Blackwell/cu130 wheel，風險高），可在 blockswap=0 上再疊 ~1.3x。
- **不要再回頭試**：降 fps、TeaCache（除非未來改回多步排程，否則 TeaCache 對 6 步蒸餾流程無意義）。

## 狀態
- [x] base 重跑基準（35.7 分，與舊測一致）
- [x] teacache:0.15 / teacache:0.25（接線驗證 OK、確實生效）
- [x] 結論：TeaCache 淨負、淘汰；production workflow 全程未動，無需還原
