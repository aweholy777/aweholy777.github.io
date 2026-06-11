$Log = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_cc_finish.txt"
"finish start $(Get-Date -Format HH:mm:ss)" | Out-File $Log -Encoding utf8
function L($t) { $t | Out-File $Log -Append -Encoding utf8 }

if (-not (Get-Command fzf -ErrorAction SilentlyContinue)) {
    L "[1] installing fzf via conda..."
    conda install -y -c conda-forge fzf 2>&1 | Select-Object -Last 3 | ForEach-Object { L ("    " + $_) }
} else { L "[1] fzf already present" }
$f = Get-Command fzf -ErrorAction SilentlyContinue
L ("    fzf now: " + $(if ($f) { $f.Source } else { "STILL MISSING" }))

L "[2] run ccc install.sh"
$gitbash = "C:\Program Files\Git\bin\bash.exe"
$out = & $gitbash -lc "bash ~/.claude/skills/ccc-switch/scripts/install.sh" 2>&1
$out | ForEach-Object { L ("    " + $_) }

L "[3] verify ~/bin"
Get-ChildItem "$env:USERPROFILE\bin" -ErrorAction SilentlyContinue | ForEach-Object { L ("    " + $_.Name) }
L ("DONE " + (Get-Date -Format HH:mm:ss))
Write-Host "finish done - see log"
