@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_lan_setup_status.txt
set KEY=%USERPROFILE%\.ssh\qt_lan_key
echo check2 start > "%LOG%"
ssh -i "%KEY%" -o BatchMode=yes aweholy@192.168.68.61 "grep -E 'ALL DONE|===' ~/setup_infinitetalk.log | tail -5; echo ---PROC---; cat /proc/$(pgrep -f main.py | head -1)/cmdline 2>/dev/null | tr '\0' ' '; echo; echo ---SVC---; systemctl list-units --no-pager 2>/dev/null | grep -i comfy; echo ---MODELS---; C=$(readlink -f /proc/$(pgrep -f main.py | head -1)/cwd); ls -la --block-size=M $C/models/diffusion_models/ $C/models/text_encoders/ $C/models/vae/ $C/models/clip_vision/ $C/models/loras/ 2>/dev/null | grep -v '^d\|^total\|put_'" >> "%LOG%" 2>&1
echo EXIT %errorlevel% >> "%LOG%"
