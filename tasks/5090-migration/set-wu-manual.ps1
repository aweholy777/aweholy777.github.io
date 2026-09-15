# set-wu-manual.ps1 -- make Windows Update restart MANUAL (no auto-reboot).
# ASCII-only on purpose: PS 5.1 on this zh-TW box mis-parses Chinese as Big5.
# Must run ELEVATED (writes HKLM). Idempotent; safe to re-run.
$ErrorActionPreference = 'Stop'
$log = Join-Path $env:USERPROFILE 'wu_manual_change.log'
function L($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $m" | Tee-Object -FilePath $log -Append }

L "=== apply Windows Update manual-restart policy ==="

# 1) Legacy Windows Update AU policy: notify for download+install, never auto-reboot with a logged-on user.
$au = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU'
if (-not (Test-Path $au)) { New-Item -Path $au -Force | Out-Null }
New-ItemProperty -Path $au -Name 'NoAutoRebootWithLoggedOnUsers' -PropertyType DWord -Value 1 -Force | Out-Null
New-ItemProperty -Path $au -Name 'AUOptions'                   -PropertyType DWord -Value 2 -Force | Out-Null
New-ItemProperty -Path $au -Name 'AUPowerManagement'           -PropertyType DWord -Value 0 -Force | Out-Null
New-ItemProperty -Path $au -Name 'AutoInstallMinorUpdates'     -PropertyType DWord -Value 0 -Force | Out-Null
L "AU key  : NoAutoRebootWithLoggedOnUsers=1 AUOptions=2 AUPowerManagement=0 AutoInstallMinorUpdates=0"

# 2) UX settings: allow restart notifications, keep Active Hours as-is (20:00-14:00).
$ux = 'HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings'
if (-not (Test-Path $ux)) { New-Item -Path $ux -Force | Out-Null }
New-ItemProperty -Path $ux -Name 'RestartNotificationsAllowed2' -PropertyType DWord -Value 1 -Force | Out-Null
L "UX key  : RestartNotificationsAllowed2=1"

# 3) Verify
$v = Get-ItemProperty $au
L ("verify  : NoAutoRebootWithLoggedOnUsers=" + $v.NoAutoRebootWithLoggedOnUsers + " AUOptions=" + $v.AUOptions)
L "=== DONE ==="
