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
    # 在信箱（只有 5090 寫）標題行之後插一則最新訊息，並單獨 push 這個檔
    $stamp = Get-Date -Format 'yyyy-MM-dd HH:mm'
    $entry = "`n## [$stamp] STATUS：$status`n$msg`n"
    $raw = Get-Content $inbox -Raw -Encoding UTF8
    $raw = $raw -replace "(?s)^(# .*?\r?\n)", "`$1$entry"
    Set-Content $inbox -Value $raw -Encoding UTF8
    git -C $repo add tasks/handoff/5090-to-3060.md 2>&1 | Out-Null
    git -C $repo commit -m "5090 信箱：$status $stamp" 2>&1 | Out-Null
    git -C $repo pull --rebase --autostash 2>&1 | Out-Null
    git -C $repo push 2>&1 | Out-Null
}

Set-Location $repo
Log "=== 夜間生成開始 (count=$Count) ==="

# 1. 同步
git pull --rebase --autostash 2>&1 | Tee-Object -FilePath $log -Append

# 2. 確認 ComfyUI（沒回應就啟動）
$up = $false
try { Invoke-RestMethod http://127.0.0.1:8188/system_stats -TimeoutSec 10 | Out-Null; $up = $true } catch {}
if (-not $up) {
    Log "ComfyUI 未回應，嘗試啟動..."
    Start-ScheduledTask -TaskName 'ComfyUI'
    Start-Sleep 40
    try { Invoke-RestMethod http://127.0.0.1:8188/system_stats -TimeoutSec 10 | Out-Null; $up = $true } catch {}
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

# 4. 上傳（不發布網站；--no-push 由 3060 負責 Hugo/Pages）
Log "上傳 YouTube..."
& $py video-pipeline\yt_publish.py --auto --no-push --limit $Count 2>&1 | Tee-Object -FilePath $log -Append

# 5. 只交 csv + 被嵌入的文章，push 回 main
git add video-pipeline/yt_uploaded.csv content/daily-qt 2>&1 | Tee-Object -FilePath $log -Append
$changed = git status --porcelain -- video-pipeline/yt_uploaded.csv content/daily-qt
if ($changed) {
    git commit -m "5090 nightly: $(Get-Date -Format 'yyyy-MM-dd')" 2>&1 | Tee-Object -FilePath $log -Append
    git pull --rebase --autostash 2>&1 | Tee-Object -FilePath $log -Append
    git push 2>&1 | Tee-Object -FilePath $log -Append
    Log "已 push 本次成果"
} else {
    Log "本次無新上傳（可能隊列已空或生成未產出），未 push。詳見上方 log。"
}
Log "=== 完成 ==="
