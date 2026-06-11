@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_lan_restart.txt
set KEY=%USERPROFILE%\.ssh\qt_lan_key
set SH=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\restart_comfy.sh
echo restart start > "%LOG%"
scp -i "%KEY%" -o BatchMode=yes "%SH%" aweholy@192.168.68.61:~/restart_comfy.sh >> "%LOG%" 2>&1
ssh -i "%KEY%" -o BatchMode=yes aweholy@192.168.68.61 "sed -i 's/\r$//' ~/restart_comfy.sh && bash ~/restart_comfy.sh" >> "%LOG%" 2>&1
echo EXIT %errorlevel% >> "%LOG%"
