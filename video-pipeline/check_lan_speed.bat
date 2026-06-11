@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_lan_speed.txt
set KEY=%USERPROFILE%\.ssh\qt_lan_key
echo speed check > "%LOG%"
ssh -i "%KEY%" -o BatchMode=yes aweholy@192.168.68.61 "tail -c 2000 ~/comfyui_server.log | tr '\r' '\n' | tail -12" >> "%LOG%" 2>&1
echo EXIT %errorlevel% >> "%LOG%"
