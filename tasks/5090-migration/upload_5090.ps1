# upload_5090.ps1 — 佇列式滴傳：每小時跑一次、每次只傳 1 支（由 Task Scheduler 'QT-Upload-5090' 呼叫）
# 2026-08-21 軍師改版（取代舊的「每日 20:00 一次傳 6 支」）：
#   - 每小時跑一次，每次最多傳 1 支，避免一口氣爆量觸發 YouTube 風控。
#   - DailyCap：過去 24 小時（依 yt_uploaded.csv 時間戳）已傳滿就跳過本次，不報錯。
#   - 遇到 YouTube 配額/上傳上限錯誤（yt_publish.py exit code 2）：寫暫停旗標，
#     暫停到「現在+24h」，之後每小時的跑都直接跳過，直到旗標過期；並回報信箱一次 FYI。
#   - 分階段：第1階段 DailyCap=20/天，穩定後升 24、再穩定後最多到 30，先不要 50/100。
# 純腳本，不需 Claude Code。push 失敗才把 BLOCKED 寫進信箱給 3060。
param([int]$DailyCap = 20)

$ErrorActionPreference = "Continue"
$repo   = "C:\Users\user\qtproject"
$py     = "C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe"
$log    = "C:\Users\user\upload_5090.log"
$inbox  = "$repo\tasks\handoff\5090-to-3060.md"
$csvPath = "$repo\video-pipeline\yt_uploaded.csv"
$pauseFlag = "C:\Users\user\upload_pause.flag"

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
Log "=== 滴傳開始 (DailyCap=$DailyCap) ==="

# 1. 同步
git pull --rebase --autostash 2>&1 | Tee-Object -FilePath $log -Append

# 2. 暫停旗標檢查（碰過配額/上限錯誤，暫停 24h）
if (Test-Path $pauseFlag) {
    $pauseUntil = Get-Content $pauseFlag -Raw | ForEach-Object { $_.Trim() }
    $until = [DateTime]::Parse($pauseUntil)
    if ((Get-Date) -lt $until) {
        Log "暫停中（到 $until），本次跳過。"
        exit 0
    } else {
        Remove-Item $pauseFlag -Force
        Log "暫停旗標已過期，恢復上傳。"
    }
}

# 3. 每日上限檢查：過去 24 小時（依 csv 時間戳）已傳幾支
$last24 = 0
if (Test-Path $csvPath) {
    $rows = Import-Csv $csvPath
    $cutoff = (Get-Date).AddHours(-24)
    foreach ($r in $rows) {
        try {
            $ts = [DateTime]::Parse($r.uploaded_at)
            if ($ts -ge $cutoff) { $last24++ }
        } catch {}
    }
}
if ($last24 -ge $DailyCap) {
    Log "過去24小時已傳 $last24 支，已達 DailyCap=$DailyCap，本次跳過。"
    exit 0
}
Log "過去24小時已傳 $last24 ／ DailyCap=$DailyCap，繼續。"

# 4. 上傳 1 支（--no-push：只上傳 YouTube + 嵌入 shortcode + 寫 csv；發布由本腳本下面的 push 觸發 Actions）
Log "上傳 YouTube（本次 1 支）..."
$upOutput = & $py video-pipeline\yt_publish.py --auto --no-push --limit 1 2>&1
$upOutput | Tee-Object -FilePath $log -Append
$upExit = $LASTEXITCODE

if ($upExit -eq 2) {
    # 配額/上限錯誤：暫停 24h，回報一次 FYI
    $until = (Get-Date).AddHours(24)
    $until.ToString("o") | Set-Content -Path $pauseFlag -Encoding ascii
    Log "碰到 YouTube 配額/上限錯誤，暫停到 $until。"
    Report "FYI" "上傳滴傳碰到 YouTube 配額/上限錯誤（exit=2），已寫暫停旗標，暫停到 $until（之後每小時自動跳過，過期自動恢復）。詳見 upload_5090.log。"
    exit 0
} elseif ($upExit -ne 0) {
    Log "上傳腳本回報非零（exit=$upExit，非配額錯誤），本次無成果，留待下次重試。"
}

# 5. 只交 csv +「被嵌入 shortcode 的那幾篇」，push 回 main（push 即觸發 Actions 更新網頁）
git add video-pipeline/yt_uploaded.csv 2>&1 | Tee-Object -FilePath $log -Append
$embedded = git diff --name-only HEAD -- content/daily-qt
foreach ($f in $embedded) { if ($f) { git add -- "$f" 2>&1 | Tee-Object -FilePath $log -Append } }
$changed = git status --porcelain -- video-pipeline/yt_uploaded.csv content/daily-qt
if ($changed) {
    git commit -m "5090 upload: $(Get-Date -Format 'yyyy-MM-dd HH:mm')" 2>&1 | Tee-Object -FilePath $log -Append
    git pull --rebase --autostash 2>&1 | Tee-Object -FilePath $log -Append
    if ($LASTEXITCODE -ne 0) {
        Log "git pull --rebase 失敗（exit=$LASTEXITCODE），中止 push 以免推半套。"
        git rebase --abort 2>&1 | Out-Null
        Report "BLOCKED" "滴傳上傳 push 前 git pull --rebase 失敗（可能與 3060 衝突），成果未上 main、網頁未更新。請軍師處理 upload_5090.log。"
        exit 1
    }
    git push 2>&1 | Tee-Object -FilePath $log -Append
    if ($LASTEXITCODE -ne 0) {
        Log "git push 失敗（exit=$LASTEXITCODE）。"
        Report "BLOCKED" "滴傳上傳 git push 失敗（exit=$LASTEXITCODE），成果未上 main、網頁未更新。請軍師處理。"
    } else {
        Log "已 push 本次上傳成果（已觸發 Actions 部署網頁）"
    }
} else {
    Log "本次無新上傳（可能隊列無已生成待傳影片，或本次失敗），未 push。"
}

# 6. 歸檔：把「已上傳(在 yt_uploaded.csv)」的 mp4 從 head\ 搬到 head\old\，騰出空間。
#    搬到子目錄不影響生成/上傳：生成端 mp4 存在檢查是非遞迴直接路徑(nightly_head.py)，
#    看不到 old\；且 csv + 內嵌 shortcode 本就會擋下重生/重傳。head\old\ 由軍師(用戶)自行清空備份。
$head = "$repo\video-output\head"
$old  = "$head\old"
if (-not (Test-Path $old)) { New-Item -ItemType Directory -Path $old | Out-Null }
$uploaded = @{}
if (Test-Path $csvPath) {
    Get-Content $csvPath | Select-Object -Skip 1 | ForEach-Object {
        $md = ($_ -split ',')[0]
        if ($md -match 'daily-qt[\\/]([^\\/]+)[\\/]([^\\/.]+)\.md') { $uploaded["$($Matches[1])_$($Matches[2]).mp4"] = $true }
    }
}
$moved = 0
Get-ChildItem $head -Filter *.mp4 | Where-Object { $uploaded.ContainsKey($_.Name) } | ForEach-Object {
    Move-Item $_.FullName (Join-Path $old $_.Name) -Force
    $moved++
}
Log "歸檔已上傳 mp4 到 head\old\：$moved 部"

Log "=== 完成 ==="
