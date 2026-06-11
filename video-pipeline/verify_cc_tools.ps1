$OutFile = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_cc_verify.txt"
$r = New-Object System.Collections.Generic.List[string]
$cd = "$env:USERPROFILE\.claude"

$r.Add("statusline.sh: " + (Test-Path "$cd\statusline-command.sh"))
$r.Add("settings.bak : " + (Test-Path "$cd\settings.json.bak-cctools"))
$sj = Get-Content "$cd\settings.json" -Raw
$r.Add("settings has statusLine: " + ($sj -match "statusLine"))
$r.Add("settings has deepseek  : " + ($sj -match "deepseek"))
$r.Add("skill SKILL.md: " + (Test-Path "$cd\skills\ccc-switch\SKILL.md"))
$r.Add("skill scripts : " + ((Get-ChildItem "$cd\skills\ccc-switch\scripts" -ErrorAction SilentlyContinue | Measure-Object).Count))
$r.Add("bin dir: " + (Test-Path "$env:USERPROFILE\bin"))
Get-ChildItem "$env:USERPROFILE\bin" -ErrorAction SilentlyContinue | ForEach-Object { $r.Add("  bin: " + $_.Name) }
$f = Get-Command fzf -ErrorAction SilentlyContinue
$r.Add("fzf: " + $(if ($f) { $f.Source } else { "not found" }))
$r.Add("CLAUDE_CONFIG_DIR_2 (user env): " + [Environment]::GetEnvironmentVariable("CLAUDE_CONFIG_DIR_2", "User"))

$r.Add("===== statusline test =====")
$json = '{"model":{"display_name":"deepseek-v4-pro"},"workspace":{"current_dir":"C:/Users/aweholy/Desktop/clone2026010/aweholy777.github.io"},"context_window":{"used_percentage":42}}'
try {
    $out = $json | & "C:\Program Files\Git\bin\bash.exe" "$cd\statusline-command.sh" 2>&1
    $out | Select-Object -First 4 | ForEach-Object { $r.Add($_.ToString()) }
} catch { $r.Add("statusline FAILED: " + $_.Exception.Message) }
$r.Add("done " + (Get-Date -Format "HH:mm:ss"))
$r | Out-File $OutFile -Encoding utf8
