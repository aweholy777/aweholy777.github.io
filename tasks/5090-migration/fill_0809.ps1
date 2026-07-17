# fill_0809.ps1 -- watcher: after QT-GenOnce-5090 (31 parts) finishes, auto-run 1 part.
# Purpose: fill the transient-failure hole from 2026-07-05 manual interrupt:
#   Acts 20:1~12  ==  content/daily-qt/ntqt/2023-08-09.md
# Mechanism: a fresh nightly_head re-evaluates pending(); the earliest bible-order
#   passage with no mp4 is 2023-08-09, so it is generated first.
# One-shot: self-disables QT-GenFill-5090 after running. ASCII-only (PS 5.1 Big5-safe).
# Watch-phase logs to gen_fill.log (gen_5090.log is locked by the 31-run while it runs).
$ErrorActionPreference = "Continue"
$flog = "C:\Users\user\gen_fill.log"
function FLog($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  [FILL] $m" | Tee-Object -FilePath $flog -Append }

FLog "watcher started; waiting for QT-GenOnce-5090 to finish..."
# 1) wait for the main generation task to end (safety cap ~30h)
$waited = 0
while ((Get-ScheduledTask -TaskName 'QT-GenOnce-5090').State -eq 'Running' -and $waited -lt 108000) {
    Start-Sleep -Seconds 300; $waited += 300
}
FLog ("main task state=" + (Get-ScheduledTask -TaskName 'QT-GenOnce-5090').State + "; waiting for ComfyUI queue to drain...")

# 2) wait until ComfyUI queue is empty (max ~30 min)
for ($i = 0; $i -lt 60; $i++) {
    try {
        $q = Invoke-RestMethod http://127.0.0.1:8188/queue -TimeoutSec 10
        if (($q.queue_running.Count + $q.queue_pending.Count) -eq 0) { break }
    } catch {}
    Start-Sleep -Seconds 30
}

# 3) run 1 part (gen_5090.ps1 does git pull, ensures ComfyUI, runs nightly_head --count 1)
FLog "starting fill run of 1 part (expected: Acts 20:1~12 / 2023-08-09)..."
& "C:\Users\user\qtproject\tasks\5090-migration\gen_5090.ps1" -Count 1
FLog "fill run done; disabling QT-GenFill-5090 (one-shot)."

# 4) self-disable to avoid accidental future runs
try { Disable-ScheduledTask -TaskName 'QT-GenFill-5090' | Out-Null } catch {}
