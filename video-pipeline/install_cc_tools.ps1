$ErrorActionPreference = "Continue"
$Log = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_cc_tools.txt"
$Repo = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io"
$Claude = "$env:USERPROFILE\.claude"
"install start $(Get-Date -Format HH:mm:ss)" | Out-File $Log -Encoding utf8
function L($t) { $t | Out-File $Log -Append -Encoding utf8 }

# [1] backup settings
Copy-Item "$Claude\settings.json" "$Claude\settings.json.bak-cctools" -Force
L "[1] settings backed up"

# [2] statusline: locate folder by wildcard (avoid Chinese literals)
$slDir = Get-ChildItem $Repo -Directory | Where-Object { $_.Name -match "statusline" } | Select-Object -First 1
Copy-Item (Join-Path $slDir.FullName "statusline-command.sh") "$Claude\statusline-command.sh" -Force
Copy-Item "$Repo\video-pipeline\_new_settings.json" "$Claude\settings.json" -Force
L ("[2] statusline installed from: " + $slDir.Name)

# [3] ccc skill
$cccDir = Get-ChildItem $Repo -Directory | Where-Object { $_.Name -like "ccc*" } | Select-Object -First 1
$dst = "$Claude\skills\ccc-switch"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item (Join-Path $cccDir.FullName "*") $dst -Recurse -Force
L ("[3] ccc skill copied from: " + $cccDir.Name)
L ("    files: " + ((Get-ChildItem "$dst\scripts" | Measure-Object).Count) + " scripts")

# [4] fzf
if (-not (Get-Command fzf -ErrorAction SilentlyContinue)) {
    L "[4] installing fzf via winget..."
    winget install --id junegunn.fzf -e --accept-source-agreements --accept-package-agreements 2>&1 |
        Select-Object -Last 3 | ForEach-Object { L ("    " + $_) }
} else { L "[4] fzf already present" }

# [5] ccc install.sh via Git Bash
$gitbash = "C:\Program Files\Git\bin\bash.exe"
$links = "$env:LOCALAPPDATA\Microsoft\WinGet\Links"
$out = & $gitbash -lc "export PATH=`"$($links -replace '\\','/' -replace 'C:','/c'):`$PATH`"; bash ~/.claude/skills/ccc-switch/scripts/install.sh" 2>&1
$out | ForEach-Object { L ("    " + $_) }

# [6] env var + statusline test
setx CLAUDE_CONFIG_DIR_2 "$env:USERPROFILE\.claude-2" | Out-Null
L "[6] CLAUDE_CONFIG_DIR_2 set"
L "===== statusline test ====="
$json = '{"model":{"display_name":"deepseek-v4-pro"},"workspace":{"current_dir":"C:/Users/aweholy"},"context_window":{"used_percentage":42}}'
$test = $json | & $gitbash "$Claude\statusline-command.sh" 2>&1
$test | Select-Object -First 4 | ForEach-Object { L $_.ToString() }
L ("DONE " + (Get-Date -Format HH:mm:ss))
Write-Host "install finished - see log"
