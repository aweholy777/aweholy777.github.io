# daily_report.ps1 — 每日 09:00 進度日報：本機檢查後 prepend 到 5090→3060 信箱並 push。
# 由排程 QT-DailyReport-5090 觸發。本檔須存成 UTF-8 BOM（含中文），PS5.1 才不會亂碼。
$ErrorActionPreference = "Continue"
$repo    = "C:\Users\user\qtproject"
$py      = "C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe"
$mailbox = "$repo\tasks\handoff\5090-to-3060.md"
$ntTable = "$repo\tasks\progress\新約進度表.md"
$genlog  = "C:\Users\user\gen_5090.log"
$looplog = "C:\Users\user\gen_loop.log"
Set-Location $repo
Remove-Item "$repo\.git\index.lock" -Force -ErrorAction SilentlyContinue

# 1) 同步 + 重算進度
git pull --rebase --autostash 2>&1 | Out-Null
& $py tasks\progress\gen_progress.py 2>&1 | Out-Null

# 2) 讀進度表（UTF-8）：frontier + 計數
$lines = Get-Content $ntTable -Encoding UTF8
$fl = ($lines | Where-Object { $_ -like '*未生成*' } | Select-Object -First 1)
if ($fl) { $c = $fl -split '\|'; $frontier = (($c[2].Trim() -replace '&#126;','~') + '（' + $c[3].Trim() + '）') } else { $frontier = '新約全部已生成' }
$genWait  = @($lines | Where-Object { $_ -like '*已生成未上傳*' }).Count
$uploaded = @($lines | Where-Object { $_ -like '*已上傳*' }).Count

# 3) 健康檢查
$loop = (Get-ScheduledTask -TaskName 'QT-GenLoop-5090' -ErrorAction SilentlyContinue).State
$gen  = (Get-ScheduledTask -TaskName 'QT-GenOnce-5090' -ErrorAction SilentlyContinue).State
$comfy = $false
try { Invoke-RestMethod http://127.0.0.1:8188/system_stats -TimeoutSec 8 | Out-Null; $comfy = $true } catch {}
$tail = @(Get-Content $genlog -Tail 40 -ErrorAction SilentlyContinue)   # UTF-16：不指定 encoding
$lastLine = ($tail | Select-Object -Last 1)
$lastTs = $null
foreach ($ln in $tail) { if ($ln -match '(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)') { try { $lastTs = [datetime]::ParseExact($matches[1],'yyyy-MM-dd HH:mm:ss',$null) } catch {} } }

# 4) 異常判定
$problems = @()
if ($loop -eq 'Disabled') { $problems += '自動循環 QT-GenLoop-5090 已停用' }
if (-not $comfy -and $gen -eq 'Running') { $problems += 'ComfyUI 無回應但批次顯示執行中' }
if ($gen -eq 'Running' -and $lastTs -and ((Get-Date) - $lastTs).TotalHours -gt 2.5) {
    $problems += ('批次可能卡住：gen log 已 ' + [int]((Get-Date) - $lastTs).TotalMinutes + ' 分鐘無新輸出')
}
if ($problems.Count -eq 0) { $status = '無異常' } else { $status = ($problems -join '；') }
$comfyTxt = if ($comfy) { 'OK' } else { '無回應' }
$loopDesc = if ($gen -eq 'Running') { '生成中' } elseif ($loop -eq 'Disabled') { '已停用' } else { '休息/待機' }
$now = Get-Date -Format 'yyyy-MM-dd HH:mm'

# 5) 組報告並 prepend 到信箱最上方
$block = @"
## $now 進度日報（5090 自動）

- 生成 frontier：$frontier
- 已生成待傳：$genWait ／ 已上傳：$uploaded
- 循環：GenLoop=$loop、GenOnce=$gen（$loopDesc）、ComfyUI=$comfyTxt
- 異常：$status
- gen log 尾：$lastLine

---

"@
$existing = if (Test-Path $mailbox) { Get-Content $mailbox -Raw -Encoding UTF8 } else { '' }
Set-Content -Path $mailbox -Value ($block + $existing) -Encoding UTF8

# 6) 只 push 信箱這一個檔（5090 專屬可寫）
git add tasks/handoff/5090-to-3060.md 2>&1 | Out-Null
git commit -m "5090 daily report $now" 2>&1 | Out-Null
git pull --rebase --autostash 2>&1 | Out-Null
git push 2>&1 | Out-Null
