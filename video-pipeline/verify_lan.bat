@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_lan_verify.txt
set KEY=%USERPROFILE%\.ssh\qt_lan_key
echo verify start > "%LOG%"
ssh -i "%KEY%" -o BatchMode=yes aweholy@192.168.68.61 "pgrep -af main.py; echo ---; tail -8 ~/comfyui_server.log 2>/dev/null; echo ---; curl -s -m 5 http://127.0.0.1:8188/system_stats | head -c 300" >> "%LOG%" 2>&1
echo. >> "%LOG%"
echo EXIT %errorlevel% >> "%LOG%"
