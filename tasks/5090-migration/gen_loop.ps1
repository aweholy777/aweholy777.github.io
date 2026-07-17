# gen_loop.ps1 -- autonomous generation-loop controller (reboot-safe).
# Policy: generate 24 parts (QT-GenOnce-5090), rest 60 min after it ENDS, then next 24, forever.
# Invoked by scheduled task QT-GenLoop-5090 (AtLogOn + every 15 min). Idempotent; safe to run anytime.
# Reboot-safe: state is derived from gen_5090.log markers, not from memory.
#   start marker line contains  "===" and "count="   (e.g. 2026-07-11 13:12:36  === ... (count=24) ===)
#   end   marker line contains  "===" and "exit="    (e.g. 2026-07-11 13:12:36  === ... (exit=0) ...)
# ASCII-only (PS 5.1 Big5-safe). Writes to gen_loop.log; never writes gen_5090.log (locked while a batch runs).
$ErrorActionPreference = "Continue"
$llog    = "C:\Users\user\gen_loop.log"
$genlog  = "C:\Users\user\gen_5090.log"
$RESTMIN = 60
function LL($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  [LOOP] $m" | Tee-Object -FilePath $llog -Append }

# 1) a batch already running -> let it finish
$st = (Get-ScheduledTask -TaskName 'QT-GenOnce-5090' -ErrorAction SilentlyContinue).State
if ($st -eq 'Running') { exit 0 }

# 2) derive last start/end timestamps from the tail of the gen log
$lastStart = $null; $lastEnd = $null
if (Test-Path $genlog) {
    foreach ($ln in (Get-Content $genlog -Tail 400 -ErrorAction SilentlyContinue)) {
        if ($ln -match '^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)') {
            $ts = [datetime]::ParseExact($matches[1], 'yyyy-MM-dd HH:mm:ss', $null)
            if ($ln -like '*===*count=*') { $lastStart = $ts }
            elseif ($ln -like '*===*exit=*') { $lastEnd = $ts }
        }
    }
}
$now = Get-Date

# 3) interrupted batch (started but no matching end, e.g. reboot mid-run) -> resume immediately
if ($lastStart -and (-not $lastEnd -or $lastStart -gt $lastEnd)) {
    LL ("interrupted batch detected (start=$lastStart end=$lastEnd); resuming now")
    Start-ScheduledTask -TaskName 'QT-GenOnce-5090'
    exit 0
}

# 4) clean finish -> rest RESTMIN after end, then start next
if ($lastEnd) {
    $restUntil = $lastEnd.AddMinutes($RESTMIN)
    if ($now -ge $restUntil) {
        LL ("rest done (ended $lastEnd); starting next 24-part batch")
        Start-ScheduledTask -TaskName 'QT-GenOnce-5090'
    }
    exit 0
}

# 5) cold start (no markers at all) -> begin
LL "no prior markers; cold-starting a 24-part batch"
Start-ScheduledTask -TaskName 'QT-GenOnce-5090'
exit 0
