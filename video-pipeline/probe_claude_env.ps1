$OutFile = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_claude_env.txt"
$r = New-Object System.Collections.Generic.List[string]

$cd = "$env:USERPROFILE\.claude"
$r.Add("claude_dir_exists: " + (Test-Path $cd))
if (Test-Path $cd) {
    Get-ChildItem $cd -ErrorAction SilentlyContinue | ForEach-Object { $r.Add("  " + $_.Name) }
}
$sj = Join-Path $cd "settings.json"
if (Test-Path $sj) {
    $r.Add("===== settings.json =====")
    $r.Add((Get-Content $sj -Raw))
} else { $r.Add("settings.json: MISSING") }

$r.Add("===== tools =====")
foreach ($t in @("bash", "jq", "fzf", "claude")) {
    $w = (Get-Command $t -ErrorAction SilentlyContinue)
    if ($w) { $r.Add("$t : " + $w.Source) } else { $r.Add("$t : not found") }
}
$gb = "C:\Program Files\Git\bin\bash.exe"
$r.Add("git-bash: " + (Test-Path $gb))
if (Test-Path $gb) { $r.Add((& $gb --version | Select-Object -First 1)) }

$r.Add("skills_dir: " + (Test-Path (Join-Path $cd "skills")))
$r.Add(("done " + (Get-Date -Format "HH:mm:ss")))
$r | Out-File $OutFile -Encoding utf8
