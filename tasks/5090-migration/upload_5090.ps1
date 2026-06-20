# upload_5090.ps1 — 5090 每日 20:00 上傳 + 觸發網頁更新（由 Task Scheduler 'QT-Upload-5090' 呼叫，-Limit 6）
# 新架構（2026-06-18 軍師調整）：生成與上傳解耦。
#   - 生成：改成手動觸發（gen_5090.ps1 -Count N，軍師下命令才跑），不再每日固定排程。
#   - 上傳+更新網頁：維持排程，每天 20:00 上傳「已生成但未上傳」的影片，上限 6 部。
#     push 到 main 會自動觸發 GitHub Actions（deploy.yml）建置並部署到 GitHub Pages（= 更新網頁）。
# 純腳本，不需 Claude Code。上傳/push 失敗才把 BLOCKED 寫進信箱給 3060。
param([int]$Limit = 6)

$ErrorActionPreference = "Continue"
$repo  = "C:\Users\user\qtproject"
$py    = "C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe"
$log   = "C:\Users\user\upload_5090.log"
$inbox = "$repo\tasks\handoff\5090-to-3060.md"

function Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $m" | Tee-Object -FilePath $log -Append }

function Report($status, $msg) {
    # 在信箱（只有 5090 寫）標題行之後插一則最新訊息，並單獨 push 這個檔。
    # 無 BOM UTF-8 讀寫，regex 容忍既有 BOM，避免標題失配讓訊息靜默遺失。
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
Log "=== 每日上傳開始 (limit=$Limit) ==="

# 1. 同步
git pull --rebase --autostash 2>&1 | Tee-Object -FilePath $log -Append

# 2. 上傳（--no-push：只上傳 YouTube + 嵌入 shortcode + 寫 csv；發布由本腳本下面的 push 觸發 Actions）
Log "上傳 YouTube（上限 $Limit）..."
& $py video-pipeline\yt_publish.py --auto --no-push --limit $Limit 2>&1 | Tee-Object -FilePath $log -Append
$upExit = $LASTEXITCODE
if ($upExit -ne 0) { Log "上傳腳本回報非零（exit=$upExit）。" }

# 3. 只交 csv +「被嵌入 shortcode 的那幾篇」，push 回 main（push 即觸發 Actions 更新網頁）
git add video-pipeline/yt_uploaded.csv 2>&1 | Tee-Object -FilePath $log -Append
$embedded = git diff --name-only HEAD -- content/daily-qt
foreach ($f in $embedded) { if ($f) { git add -- "$f" 2>&1 | Tee-Object -FilePath $log -Append } }
$changed = git status --porcelain -- video-pipeline/yt_uploaded.csv content/daily-qt
if ($changed) {
    git commit -m "5090 upload: $(Get-Date -Format 'yyyy-MM-dd')" 2>&1 | Tee-Object -FilePath $log -Append
    git pull --rebase --autostash 2>&1 | Tee-Object -FilePath $log -Append
    if ($LASTEXITCODE -ne 0) {
        Log "git pull --rebase 失敗（exit=$LASTEXITCODE），中止 push 以免推半套。"
        git rebase --abort 2>&1 | Out-Null
        Report "BLOCKED" "20:00 上傳 push 前 git pull --rebase 失敗（可能與 3060 衝突），成果未上 main、網頁未更新。請軍師處理 upload_5090.log。"
        exit 1
    }
    git push 2>&1 | Tee-Object -FilePath $log -Append
    if ($LASTEXITCODE -ne 0) {
        Log "git push 失敗（exit=$LASTEXITCODE）。"
        Report "BLOCKED" "20:00 上傳 git push 失敗（exit=$LASTEXITCODE），成果未上 main、網頁未更新。請軍師處理。"
    } else {
        Log "已 push 本次上傳成果（已觸發 Actions 部署網頁）"
    }
} else {
    Log "本次無新上傳（可能隊列無已生成待傳影片），未 push。"
}

# 4. 歸檔：把「已上傳(在 yt_uploaded.csv)」的 mp4 從 head\ 搬到 head\old\，騰出空間。
#    搬到子目錄不影響生成/上傳：生成端 mp4 存在檢查是非遞迴直接路徑(nightly_head.py)，
#    看不到 old\；且 csv + 內嵌 shortcode 本就會擋下重生/重傳。head\old\ 由軍師(用戶)自行清空備份。
$head = "$repo\video-output\head"
$old  = "$head\old"
if (-not (Test-Path $old)) { New-Item -ItemType Directory -Path $old | Out-Null }
$uploaded = @{}
Get-Content "$repo\video-pipeline\yt_uploaded.csv" | Select-Object -Skip 1 | ForEach-Object {
    $md = ($_ -split ',')[0]
    if ($md -match 'daily-qt[\\/]([^\\/]+)[\\/]([^\\/.]+)\.md') { $uploaded["$($Matches[1])_$($Matches[2]).mp4"] = $true }
}
$moved = 0
Get-ChildItem $head -Filter *.mp4 | Where-Object { $uploaded.ContainsKey($_.Name) } | ForEach-Object {
    Move-Item $_.FullName (Join-Path $old $_.Name) -Force
    $moved++
}
Log "歸檔已上傳 mp4 到 head\old\：$moved 部"

Log "=== 完成 ==="
