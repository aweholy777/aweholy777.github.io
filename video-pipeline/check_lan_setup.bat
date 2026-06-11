@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_lan_setup_status.txt
set KEY=%USERPROFILE%\.ssh\qt_lan_key
echo check start > "%LOG%"
ssh -i "%KEY%" -o BatchMode=yes aweholy@192.168.68.61 "tail -5 ~/setup_infinitetalk.log; echo ---; ls -la --block-size=M $(readlink -f /proc/$(pgrep -f main.py | head -1)/cwd)/models/diffusion_models/ 2>/dev/null | tail -5; echo ---; df -h / | tail -1" >> "%LOG%" 2>&1
echo EXIT %errorlevel% >> "%LOG%"
