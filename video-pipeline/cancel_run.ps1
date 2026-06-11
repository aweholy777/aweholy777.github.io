try { Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8188/interrupt" | Out-Null } catch {}
try { Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8188/queue" -Body '{"clear":true}' -ContentType "application/json" | Out-Null } catch {}
"cancelled $(Get-Date -Format HH:mm:ss)" | Out-File "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_cancel.txt" -Encoding utf8
