$ErrorActionPreference = 'Continue'
$LogFile = 'C:\Users\user\update_comfyui.log'
$ComfyDir = 'C:\Users\user\ComfyUI\ComfyUI'
$NodeDirs = @(
  'C:\Users\user\ComfyUI\ComfyUI\custom_nodes\ComfyUI-WanVideoWrapper',
  'C:\Users\user\ComfyUI\ComfyUI\custom_nodes\ComfyUI-VideoHelperSuite',
  'C:\Users\user\ComfyUI\ComfyUI\custom_nodes\ComfyUI-KJNodes'
)
$RepoDir = 'C:\Users\user\qtproject'
$HandoffFile = "$RepoDir\tasks\handoff\5090-to-3060.md"

function Log($msg) {
  $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $msg"
  Add-Content -Path $LogFile -Value $line
}

$genTask = Get-ScheduledTask -TaskName 'QT-GenOnce-5090' -ErrorAction SilentlyContinue
if ($genTask -and $genTask.State -eq 'Running') {
  exit 0
}

Log "batch not running, starting comfyui update"

Stop-ScheduledTask -TaskName 'ComfyUI' -ErrorAction SilentlyContinue
Start-Sleep -Seconds 10

$allClean = $true
$repos = @($ComfyDir) + $NodeDirs
foreach ($r in $repos) {
  Push-Location $r
  $dirty = git status --porcelain
  if ($dirty) {
    Log "SKIP (dirty working tree): $r"
    $allClean = $false
  } else {
    $out = git pull 2>&1
    Log "pull $r : $out"
  }
  Pop-Location
}

Start-ScheduledTask -TaskName 'ComfyUI' -ErrorAction SilentlyContinue

$ok = $false
for ($i = 0; $i -lt 18; $i++) {
  Start-Sleep -Seconds 10
  try {
    $resp = Invoke-RestMethod -Uri 'http://127.0.0.1:8188/system_stats' -TimeoutSec 5 -ErrorAction Stop
    if ($resp) { $ok = $true; break }
  } catch {}
}

if ($ok) {
  Log "comfyui restarted OK, system_stats reachable"
  Enable-ScheduledTask -TaskName 'QT-GenLoop-5090' -ErrorAction SilentlyContinue
  Log "GenLoop re-enabled"
  $lines = @(
    "",
    "---",
    "## $(Get-Date -Format 'yyyy-MM-dd HH:mm') ComfyUI update (5090 auto, requested by user 2026-08-20)",
    "",
    "- Auto update after current batch finished: core + WanVideoWrapper/VideoHelperSuite/KJNodes",
    "- all repos clean (no skipped dirty pulls): $allClean",
    "- ComfyUI restarted, system_stats OK, GenLoop re-enabled",
    "- checked MiniMax H3 (alphalab.site tutorial) per user request: general T2V/I2V+audio model, not lipsync-to-script, not adopted"
  )
  Add-Content -Path $HandoffFile -Value ($lines -join "`n")
  Push-Location $RepoDir
  git add tasks/handoff/5090-to-3060.md
  git commit -m "5090: comfyui update $(Get-Date -Format 'yyyy-MM-dd')"
  git pull --rebase --autostash
  git push
  Pop-Location
} else {
  Log "ComfyUI FAILED to come back after update, GenLoop left DISABLED for manual check"
  $lines = @(
    "",
    "---",
    "## $(Get-Date -Format 'yyyy-MM-dd HH:mm') ComfyUI update FAILED (5090 auto)",
    "",
    "- ComfyUI did not respond on system_stats after update+restart",
    "- GenLoop left DISABLED, needs manual check: $LogFile"
  )
  Add-Content -Path $HandoffFile -Value ($lines -join "`n")
  Push-Location $RepoDir
  git add tasks/handoff/5090-to-3060.md
  git commit -m "5090: comfyui update FAILED $(Get-Date -Format 'yyyy-MM-dd')"
  git pull --rebase --autostash
  git push
  Pop-Location
}

Unregister-ScheduledTask -TaskName 'QT-ComfyUpdate-5090' -Confirm:$false -ErrorAction SilentlyContinue
