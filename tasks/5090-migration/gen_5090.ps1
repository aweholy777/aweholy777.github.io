# gen_5090.ps1 — 5090 手動生成影片（軍師下命令才跑；新架構 2026-06-18 起生成不再排程）
# 用法：  powershell -ExecutionPolicy Bypass -File tasks\5090-migration\gen_5090.ps1 -Count 3
# 只生成，不上傳、不 push。生成的 mp4 留在 video-output\head\（gitignored），
# 由每日 20:00 的 QT-Upload-5090（upload_5090.ps1）上傳上限 6 部並更新網頁。
# 生成依書卷輪替主播（presenter.png / presenter2.png，奇/偶卷交替；見 nightly_head.py）。
param([int]$Count = 1)

$ErrorActionPreference = "Continue"
$repo = "C:\Users\user\qtproject"
$py   = "C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe"
$log  = "C:\Users\user\gen_5090.log"

function Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $m" | Tee-Object -FilePath $log -Append }

Set-Location $repo
Log "=== 手動生成開始 (count=$Count) ==="

# 先同步，取得最新輪替邏輯與主播圖
git pull --rebase --autostash 2>&1 | Tee-Object -FilePath $log -Append

# 確認 ComfyUI（沒回應就啟動，輪詢等模型載入，最多 4 分鐘）
function Test-Comfy {
    try { Invoke-RestMethod http://127.0.0.1:8188/system_stats -TimeoutSec 10 | Out-Null; return $true }
    catch { return $false }
}
if (-not (Test-Comfy)) {
    Log "ComfyUI 未回應，啟動並輪詢等待..."
    Start-ScheduledTask -TaskName 'ComfyUI'
    for ($i = 0; $i -lt 24; $i++) { Start-Sleep 10; if (Test-Comfy) { break } }
}
if (-not (Test-Comfy)) { Log "ComfyUI 啟動失敗，中止。"; exit 1 }
Log "ComfyUI OK"

# 生成（依書卷輪替主播；--server local 用本機 ComfyUI）
Log "生成 $Count 部..."
& $py video-pipeline\nightly_head.py --server local --count $Count 2>&1 | Tee-Object -FilePath $log -Append
$genExit = $LASTEXITCODE
Log "=== 生成結束 (exit=$genExit)；mp4 待 20:00 QT-Upload-5090 上傳 ==="
