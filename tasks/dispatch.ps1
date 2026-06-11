# dispatch.ps1 — 派工腳本（軍師 → OpenCode CLI 士兵）
# 用法：
#   單一任務：  .\tasks\dispatch.ps1 -Job "rebuild-index-matthew"
#   平行派工：  .\tasks\dispatch.ps1 -Job "unit1","unit2","unit3" -Parallel
#   指定模型：  .\tasks\dispatch.ps1 -Job "ocr-images" -Model "nvidia/kimi-2.6"
#
# 前提：tasks/<Job>/plan.md 已由軍師寫好。
# 模型 ID 請先用 `opencode models` 確認實際名稱。

param(
    [Parameter(Mandatory = $true)]
    [string[]]$Job,

    [string]$Model = "nvidia/deepseek-v4-flash",

    [switch]$Parallel
)

$Root = Split-Path -Parent $PSScriptRoot   # repo 根目錄

function Invoke-Soldier {
    param([string]$JobName, [string]$ModelId, [string]$RepoRoot)

    $JobDir  = Join-Path $RepoRoot "tasks\$JobName"
    $PlanMd  = Join-Path $JobDir "plan.md"
    $LogTxt  = Join-Path $JobDir "log.txt"

    if (-not (Test-Path $PlanMd)) {
        Write-Error "找不到計畫書：$PlanMd（軍師要先寫 plan.md）"
        return
    }

    $Prompt = "讀取 tasks/$JobName/plan.md 並完整執行。" +
              "完成後把結果摘要寫入 tasks/$JobName/result.md（50 行以內：完成的檔案清單、跳過或異常的項目、一句話總結）。" +
              "不要詢問確認，直接執行。不要輸出完整檔案內容。"

    Write-Host "[$JobName] 派工中（model: $ModelId）→ log: tasks/$JobName/log.txt"

    # 士兵完整輸出落地到 log.txt，軍師不讀；軍師只讀 result.md
    Push-Location $RepoRoot
    opencode run $Prompt -m $ModelId *> $LogTxt
    Pop-Location

    $ResultMd = Join-Path $JobDir "result.md"
    if (Test-Path $ResultMd) {
        Write-Host "[$JobName] ✅ 完成，result.md 已產出"
    } else {
        Write-Warning "[$JobName] ⚠️ 沒有 result.md，請檢查 log.txt 尾端"
    }
}

if ($Parallel -and $Job.Count -gt 1) {
    # 平行出工（建議上限 7，免費 API 有 rate limit，人多要排隊）
    if ($Job.Count -gt 7) { Write-Warning "超過 7 個平行任務，免費額度可能塞車" }
    $UseThreadJob = Get-Command Start-ThreadJob -ErrorAction SilentlyContinue
    $Jobs = foreach ($j in $Job) {
        if ($UseThreadJob) {
            Start-ThreadJob -ScriptBlock ${function:Invoke-Soldier} -ArgumentList $j, $Model, $Root
        } else {
            # Windows PowerShell 5.1 沒有 Start-ThreadJob，退回 Start-Job
            Start-Job -ScriptBlock ${function:Invoke-Soldier} -ArgumentList $j, $Model, $Root
        }
    }
    $Jobs | Wait-Job | Receive-Job
    $Jobs | Remove-Job
} else {
    foreach ($j in $Job) {
        Invoke-Soldier -JobName $j -ModelId $Model -RepoRoot $Root
    }
}

Write-Host ""
Write-Host "=== 驗收提示（軍師執行）==="
Write-Host "1. type tasks\<job>\result.md     # 只讀摘要"
Write-Host "2. git diff --stat                # 只看改動範圍"
Write-Host "3. hugo --buildFuture             # 建置驗證"
