Copy-Item "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_new_settings.json" "$env:USERPROFILE\.claude\settings.json" -Force
"applied $(Get-Date -Format HH:mm:ss)" | Out-File "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_settings_applied.txt" -Encoding utf8
