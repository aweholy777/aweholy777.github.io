# run_test.ps1 -- autonomous SageAttention + BlockSwap speed test for the 5090 node.
# Policy: MEASURE ONLY. Always restore the production workflow to the original
# (sdpa, blockswap=40) and leave ComfyUI UP, so the unattended 21:00 nightly batch
# is never at risk. ASCII comments only (PS5.1 Big5 parsing safety).

$ErrorActionPreference = 'Stop'
$proj    = 'C:\Users\user\qtproject'
$py      = 'C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe'
$tdir    = Join-Path $proj 'tasks\sageattn-speedup'
$mutate  = Join-Path $tdir 'mutate_workflow.py'
$log     = Join-Path $tdir 'run_test.log'
$genlog  = Join-Path $tdir 'gen.log'
$result  = Join-Path $tdir 'result.md'
$headDir = Join-Path $proj 'video-output\head'
$comfy   = 'http://127.0.0.1:8188'
$BASELINE_RATIO = 16.0   # sec of compute per sec of output video, measured from 01-16 (8100s/505s)

function Log($m) {
  $line = ('[{0}] {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m)
  Add-Content -Path $log -Value $line -Encoding UTF8
  Write-Output $line
}
function ComfyUp() {
  try { $null = Invoke-RestMethod "$comfy/system_stats" -TimeoutSec 5; return $true } catch { return $false }
}
function WaitComfy($timeoutSec) {
  $t = 0
  while ($t -lt $timeoutSec) { if (ComfyUp) { return $true }; Start-Sleep -Seconds 10; $t += 10 }
  return (ComfyUp)
}
function StopComfy() {
  # ComfyUI runs under the 'ComfyUI' scheduled task; Stop-Process gets Access Denied,
  # so stopping the TASK is the reliable kill. Port-owner kill is only a best-effort fallback.
  try { Stop-ScheduledTask -TaskName 'ComfyUI' -ErrorAction SilentlyContinue | Out-Null; Log 'stopped ComfyUI task' } catch {}
  $conns = Get-NetTCPConnection -LocalPort 8188 -State Listen -ErrorAction SilentlyContinue
  foreach ($c in $conns) { try { Stop-Process -Id $c.OwningProcess -Force } catch {} }
  Start-Sleep -Seconds 6
}
function StartComfy() {
  $hasTask = $false
  try { $null = Get-ScheduledTask -TaskName 'ComfyUI' -ErrorAction Stop; $hasTask = $true } catch {}
  if ($hasTask) {
    # clear any stale "Running" instance so a fresh Start actually launches a new process
    try { Stop-ScheduledTask -TaskName 'ComfyUI' -ErrorAction SilentlyContinue | Out-Null } catch {}
    Start-Sleep -Seconds 2
    Start-ScheduledTask -TaskName 'ComfyUI'
  }
  elseif (Test-Path 'C:\Users\user\ComfyUI\start_comfy.bat') { Start-Process -FilePath 'C:\Users\user\ComfyUI\start_comfy.bat' }
  else { Log 'WARN: no ComfyUI task and no start_comfy.bat found' }
}
function RestartComfy($timeoutSec) {
  StopComfy; StartComfy
  if (WaitComfy $timeoutSec) { Log 'ComfyUI is UP'; return $true } else { Log 'ERROR: ComfyUI did not come up'; return $false }
}

$applied = $false
$startTime = Get-Date
Log '==== sageattn speed test START ===='

try {
  # --- Guard: only run when the nightly batch is fully idle ---
  $busy = $false
  try {
    $nt = Get-ScheduledTask -TaskName 'QT-Nightly-5090' -ErrorAction Stop
    if ($nt.State -eq 'Running') { Log 'ABORT: QT-Nightly-5090 is Running'; $busy = $true }
  } catch { Log 'WARN: QT-Nightly-5090 task not found (continuing)' }
  if (-not $busy -and (ComfyUp)) {
    try {
      $q = Invoke-RestMethod "$comfy/queue" -TimeoutSec 10
      if ($q.queue_running.Count -gt 0 -or $q.queue_pending.Count -gt 0) { Log 'ABORT: ComfyUI queue is busy'; $busy = $true }
    } catch { Log 'WARN: could not read ComfyUI queue' }
  }
  if ($busy) {
    Set-Content -Path $result -Encoding UTF8 -Value @"
# SageAttention test -- ABORTED ($(Get-Date -Format 'yyyy-MM-dd HH:mm'))

The nightly batch / ComfyUI was still busy at trigger time, so the test did not run.
Production workflow was NOT touched. Re-run manually when idle:
  powershell -ExecutionPolicy Bypass -File tasks\sageattn-speedup\run_test.ps1
"@
    Log '==== ABORTED (busy) ===='
    return
  }

  # --- Apply test workflow (sageattn + blockswap 0) ---
  & $py $mutate backup; if ($LASTEXITCODE -ne 0) { throw 'backup failed' }
  & $py $mutate apply;  if ($LASTEXITCODE -ne 0) { throw 'apply failed' }
  $applied = $true
  Log (& $py $mutate show)

  # --- Restart ComfyUI so it loads sageattention (installed after it last started) ---
  if (-not (RestartComfy 360)) { throw 'ComfyUI failed to start with test workflow' }

  # --- Generate ONE article and time it ---
  Log 'generating 1 test article (nightly_head --count 1) ...'
  if (Test-Path $genlog) { Remove-Item $genlog -Force }
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  & $py (Join-Path $proj 'video-pipeline\nightly_head.py') --server local --count 1 *>> $genlog
  $genExit = $LASTEXITCODE
  $sw.Stop()
  $elapsed = [math]::Round($sw.Elapsed.TotalSeconds, 0)
  Log ("generation finished: exit=$genExit elapsed=${elapsed}s")

  # --- Inspect the produced mp4 ---
  $mp4 = Get-ChildItem (Join-Path $headDir '*.mp4') -ErrorAction SilentlyContinue |
         Where-Object { $_.LastWriteTime -gt $startTime } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  $videoSec = 0; $mp4mb = 0; $mp4name = '(none)'
  if ($mp4) {
    $mp4name = $mp4.Name; $mp4mb = [math]::Round($mp4.Length/1MB, 1)
    try {
      $videoSec = [double](& $py -c "import imageio_ffmpeg,subprocess,re; ff=imageio_ffmpeg.get_ffmpeg_exe(); o=subprocess.run([ff,'-i',r'$($mp4.FullName)'],capture_output=True,text=True,encoding='utf-8',errors='replace').stderr; m=re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)',o); print(round(int(m.group(1))*3600+int(m.group(2))*60+float(m.group(3)),1) if m else 0)")
    } catch { Log 'WARN: could not probe video duration' }
  }

  $ok = ($genExit -eq 0 -and $mp4 -and $mp4mb -gt 1)
  $ratio = if ($videoSec -gt 0) { [math]::Round($elapsed/$videoSec, 2) } else { 0 }
  $speedup = if ($ratio -gt 0) { [math]::Round($BASELINE_RATIO/$ratio, 2) } else { 0 }
  $rec = if ($ok -and $speedup -ge 1.15) { 'KEEP -- measurably faster, apply to production when supervised' }
         elseif ($ok) { 'NEUTRAL -- worked but not clearly faster; review numbers' }
         else { 'REVERT -- test failed (crash/OOM/no mp4). Stay on sdpa+blockswap40' }

  Set-Content -Path $result -Encoding UTF8 -Value @"
# SageAttention + BlockSwap speed test -- result ($(Get-Date -Format 'yyyy-MM-dd HH:mm'))

Test config:  attention sdpa -> sageattn,  blockswap 40 -> 0   (LOCAL default workflow)
Generation:   exit=$genExit   elapsed=${elapsed}s
Output mp4:   $mp4name   ${mp4mb} MB   duration=${videoSec}s
Speed ratio:  ${ratio} sec-compute / sec-video   (baseline ~${BASELINE_RATIO})
Est. speedup: ${speedup}x vs baseline

RECOMMENDATION: $rec

NOTE: Production workflow has been RESTORED to original (sdpa, blockswap=40).
Tonight's 21:00 batch runs on the known-good config. To adopt the change,
run (supervised):  python tasks\sageattn-speedup\mutate_workflow.py apply
then restart ComfyUI. Full log: tasks\sageattn-speedup\run_test.log , gen.log
"@
  Log "RESULT: ok=$ok elapsed=${elapsed}s ratio=$ratio speedup=${speedup}x -> $rec"

  # --- Disposition of the test video: GOOD -> upload (+push); NOT good -> leave parked (no delete) ---
  if ($ok -and $mp4) {
    Log 'test video is GOOD -> uploading to YouTube (targeted single file, non-interactive)'
    $pubout = & $py (Join-Path $proj 'video-pipeline\yt_publish.py') --video $mp4.FullName --auto --no-push 2>&1
    $pubout | ForEach-Object { Log ('  yt: ' + $_) }
    if (($pubout -join "`n") -match 'OK ') {
      Log 'upload OK -> committing csv + embedded article to main'
      Push-Location $proj
      try {
        git add video-pipeline/yt_uploaded.csv 2>&1 | Out-Null
        $embedded = git diff --name-only HEAD -- content/daily-qt
        foreach ($f in $embedded) { if ($f) { git add -- "$f" 2>&1 | Out-Null } }
        $changed = git status --porcelain -- video-pipeline/yt_uploaded.csv content/daily-qt
        if ($changed) {
          git commit -m ("5090 sage-test gen+upload " + (Get-Date -Format 'yyyy-MM-dd')) 2>&1 | Out-Null
          git pull --rebase --autostash 2>&1 | Out-Null
          if ($LASTEXITCODE -ne 0) { git rebase --abort 2>&1 | Out-Null; Log 'git pull --rebase failed -> aborted, NOT pushed (resolve manually)' }
          else { git push 2>&1 | Out-Null; if ($LASTEXITCODE -eq 0) { Log 'pushed test article to main' } else { Log 'git push failed (left committed locally)' } }
        } else { Log 'nothing to commit (already in csv / no embed change)' }
      } finally { Pop-Location }
      Add-Content -Path $result -Encoding UTF8 -Value "`nDISPOSITION: video was GOOD -> uploaded to YouTube + pushed to main ($mp4name)."
    } else {
      Log 'yt_publish did not return OK -> leaving mp4 parked for review'
      Add-Content -Path $result -Encoding UTF8 -Value "`nDISPOSITION: upload attempted but no OK -> mp4 left parked in video-output/head ($mp4name)."
    }
  } else {
    Log 'test video NOT good -> left parked in video-output/head (no upload, no delete)'
    Add-Content -Path $result -Encoding UTF8 -Value "`nDISPOSITION: video NOT good -> left parked in video-output/head for manual review/delete ($mp4name)."
  }
}
catch {
  Log ('EXCEPTION: ' + $_.Exception.Message)
  try {
    Set-Content -Path $result -Encoding UTF8 -Value @"
# SageAttention test -- ERROR ($(Get-Date -Format 'yyyy-MM-dd HH:mm'))

The test hit an exception: $($_.Exception.Message)
Production workflow is being restored to original. See run_test.log for details.
"@
  } catch {}
}
finally {
  if ($applied) {
    Log 'restoring production workflow to original ...'
    try { & $py $mutate restore; Log (& $py $mutate show) } catch { Log ('restore ERROR: ' + $_.Exception.Message) }
    if (RestartComfy 360) { Log 'ComfyUI UP on restored workflow' } else { Log 'CRITICAL: ComfyUI not up after restore -- 21:00 batch at risk' }
  } else {
    if (-not (ComfyUp)) { Log 'ComfyUI was down; starting it'; StartComfy; WaitComfy 360 | Out-Null }
  }
  Log '==== sageattn speed test END ===='
}
