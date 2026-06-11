# tasks/ — 派工工作區

軍師（Claude Code）規劃，士兵（OpenCode CLI + NVIDIA 免費 API）出工。原則見根目錄 `CLAUDE.md`。

## 工作流程

```
1. 軍師寫計畫書      複製 _templates/plan.md → tasks/<任務名>/plan.md，填好規格
2. 派工              .\tasks\dispatch.ps1 -Job "<任務名>"
   （平行）          .\tasks\dispatch.ps1 -Job "a","b","c" -Parallel
3. 軍師驗收          只讀 tasks/<任務名>/result.md + git diff --stat
4. 要修正            把修正要求 append 進 plan.md，重派；不要自己改
5. 通過              git add / commit，刪掉或歸檔 tasks/<任務名>/
```

## 模型選擇

| 情境 | 模型 | 理由 |
|------|------|------|
| 批次寫 markdown、改格式、寫程式 | `nvidia/deepseek-v4-flash` | 免費、100 萬上下文、出工主力 |
| 需要看圖片／影片、複雜推理 | `nvidia/kimi-2.6` | 多模態，26 萬上下文 |
| 敏感資料（見證、個資、代禱） | 本地 ollama 模型 | 不上雲端 |
| 規劃、審查、架構決策 | Claude Code 本人 | 軍師親自做 |

模型 ID 以 `opencode models` 實際輸出為準。

## 注意事項

- 免費 API 有 rate limit（約 40 req/min），人多要排隊，平行上限建議 7
- 平行任務之間不可寫同一個檔案（特別是各 `_index.md`）
- `log.txt` 是士兵完整輸出的落地檔，軍師永遠不讀，只供除錯
- 本目錄已加入 .gitignore 候選——若不想把派工紀錄進版控，自行加 `tasks/` 到 .gitignore
