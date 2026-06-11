$OutFile = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_account2.txt"
$r = New-Object System.Collections.Generic.List[string]
$c2 = "$env:USERPROFILE\.claude-2"

$r.Add("claude-2 dir: " + (Test-Path $c2))
$r.Add("credentials : " + (Test-Path "$c2\.credentials.json"))

# account-2 settings: statusLine only, NO DeepSeek env (keep real Claude login)
New-Item -ItemType Directory -Force -Path $c2 | Out-Null
Copy-Item "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_claude2_settings.json" "$c2\settings.json" -Force
$r.Add("settings.json written (statusLine only, no DeepSeek)")

# sync skills by copy (more reliable than symlink on Windows)
if (Test-Path "$env:USERPROFILE\.claude\skills") {
    Copy-Item "$env:USERPROFILE\.claude\skills" $c2 -Recurse -Force
    $r.Add("skills copied to account 2")
}
$r.Add("done " + (Get-Date -Format "HH:mm:ss"))
$r | Out-File $OutFile -Encoding utf8
Write-Host "account2 setup done"
