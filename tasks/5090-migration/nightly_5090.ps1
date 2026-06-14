# nightly_5090.ps1 — 5090 每晚自動生成 + 上傳（由 Task Scheduler 於 21:00 呼叫）
# 純腳本，不需 Claude Code。routine 直接跑；ComfyUI 起不來才把 BLOCKED 寫進信箱給 3060。
# 角色與分工見 repo 的 CLAUDE.md / CLAUDE.local.md：5090 只生成+上傳，不發布網站。
param([int]$Count = 4)

$ErrorActionPreference = "Continue"
$repo  = "C:\Users\user\qtproject"
$py    = "C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe"
$log   = "C:\Users\user\nightly_5090.log"
$inbox = "$repo\tasks\handoff\5090-to-3060.md"

function Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $m" | Tee-Object -FilePath $log -Append }

function Report($status, $msg) {
    # 在信箱（只有 5090 寫）標題行之後插一則最新訊息，並單獨 push 這個檔。
    # 用 .NET 無 BOM UTF-8 讀寫，且 regex 容忍既有 BOM：避免 Set-Content -Encoding UTF8 加 BOM
    # 導致 ^(# ...) 失配、整則訊息（尤其 BLOCKED）靜默遺失。
    $stamp = Get-Date -Format 'yyyy-MM-dd HH:mm'
    $entry = "`n## [$stamp] STATUS：$status`n$msg`n"
    $enc = New-Object System.Text.UTF8Encoding($false)
    $raw = [System.IO.File]::ReadAllText($inbox, $enc)
    $raw = $raw -replace "(?s)^﻿?(# .*?\r?\n)", "`$1$entry"
    [System.IO.File]::WriteAllText($inbox, $raw, $enc)
    git -C $repo add tasks/handoff/5090-to-3060.md 2>&1 | Out-Null
    git -C $repo commit -m "5090 信箱：$status $stamp" 2>&1 | Out-Null
    git -C $repo pull --rebase --autostash 2>&1 | Out-Null
    git -C $repo push 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { Log "Report push 失敗（exit=$LASTEXITCODE），$status 可能未送達 3060" }
}

Set-Location $repo
Log "=== 夜間生成開始 (count=$Count) ==="

# 1. 同步
git pull --rebase --autostash 2>&1 | Tee-Object -FilePath $log -Append

# 2. 確認 ComfyUI（沒回應就啟動，輪詢等待模型載入，最多 4 分鐘）
function Test-Comfy {
    try { Invoke-RestMethod http://127.0.0.1:8188/system_stats -TimeoutSec 10 | Out-Null; return $true }
    catch { return $false }
}
$up = Test-Comfy
if (-not $up) {
    Log "ComfyUI 未回應，嘗試啟動並輪詢等待..."
    Start-ScheduledTask -TaskName 'ComfyUI'
    for ($i = 0; $i -lt 24; $i++) {
        Start-Sleep 10
        if (Test-Comfy) { $up = $true; break }
    }
}
if (-not $up) {
    Log "ComfyUI 啟動失敗，今晚中止。"
    Report "BLOCKED" "ComfyUI 無法在 5090 啟動（8188 無回應），今晚未生成。請軍師協助。"
    exit 1
}
Log "ComfyUI OK"

# 3. 生成
Log "生成 $Count 篇..."
& $py video-pipeline\nightly_head.py --server local --count $Count 2>&1 | Tee-Object -FilePath $log -Append
$genExit = $LASTEXITCODE
if ($genExit -ne 0) { Log "生成腳本回報非零（exit=$genExit），仍嘗試上傳已產出的影片。" }

# 4. 上傳（不發布網站；--no-push 由 3060 負責 Hugo/Pages）
Log "上傳 YouTube..."
& $py video-pipeline\yt_publish.py --auto --no-push --limit $Count 2>&1 | Tee-Object -FilePath $log -Append
$upExit = $LASTEXITCODE
if ($upExit -ne 0) { Log "上傳腳本回報非零（exit=$upExit）。" }

# 5. 只交 csv +「被嵌入 shortcode 的那幾篇」，push 回 main
#    精準 add：用 diff HEAD 找出被改動的 content 檔，而非整個 content/daily-qt 目錄（避免夾帶髒檔）
git add video-pipeline/yt_uploaded.csv 2>&1 | Tee-Object -FilePath $log -Append
$embedded = git diff --name-only HEAD -- content/daily-qt
foreach ($f in $embedded) { if ($f) { git add -- "$f" 2>&1 | Tee-Object -FilePath $log -Append } }
$changed = git status --porcelain -- video-pipeline/yt_uploaded.csv content/daily-qt
if ($changed) {
    git commit -m "5090 nightly: $(Get-Date -Format 'yyyy-MM-dd')" 2>&1 | Tee-Object -FilePath $log -Append
    git pull --rebase --autostash 2>&1 | Tee-Object -FilePath $log -Append
    if ($LASTEXITCODE -ne 0) {
        Log "git pull --rebase 失敗（exit=$LASTEXITCODE），中止 push 以免推半套。"
        git rebase --abort 2>&1 | Out-Null
        Report "BLOCKED" "夜間 push 前 git pull --rebase 失敗（可能與 3060 衝突），成果未上 main。請軍師處理 nightly_5090.log。"
        exit 1
    }
    git push 2>&1 | Tee-Object -FilePath $log -Append
    if ($LASTEXITCODE -ne 0) {
        Log "git push 失敗（exit=$LASTEXITCODE）。"
        Report "BLOCKED" "夜間 git push 失敗（exit=$LASTEXITCODE），成果未上 main。請軍師處理。"
    } else {
        Log "已 push 本次成果"
    }
} else {
    Log "本次無新上傳（可能隊列已空或生成未產出），未 push。詳見上方 log。"
}
if ($genExit -ne 0) {
    Report "BLOCKED" "夜間生成以非零碼結束（exit=$genExit），疑似 ComfyUI/TTS 連續失敗，今晚可能未達 $Count 篇。請軍師檢查 nightly_5090.log。"
}
Log "=== 完成 ==="
