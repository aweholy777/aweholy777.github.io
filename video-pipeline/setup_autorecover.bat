@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_autorecover.txt
set KEY=%USERPROFILE%\.ssh\qt_lan_key
set SH=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\qt-resume.sh
echo setup start > "%LOG%"

echo [1/2] LAN crontab... >> "%LOG%"
scp -i "%KEY%" -o BatchMode=yes "%SH%" aweholy@192.168.68.61:~/qt-resume.sh >> "%LOG%" 2>&1
ssh -i "%KEY%" -o BatchMode=yes aweholy@192.168.68.61 "sed -i 's/\r$//' ~/qt-resume.sh && chmod +x ~/qt-resume.sh && (crontab -l 2>/dev/null | grep -v 'qt-resume'; echo '@reboot sleep 40 && bash /home/aweholy/qt-resume.sh # qt-resume') | crontab - && echo CRONTAB_SET && crontab -l | tail -2" >> "%LOG%" 2>&1

echo [2/2] Windows schtask... >> "%LOG%"
schtasks /create /f /tn "QT_ComfyDesktop_AutoStart" /tr "\"C:\Users\aweholy\AppData\Local\Programs\Comfy Desktop\Comfy Desktop.exe\"" /sc onlogon >> "%LOG%" 2>&1
schtasks /query /tn "QT_ComfyDesktop_AutoStart" >> "%LOG%" 2>&1
echo EXIT %errorlevel% >> "%LOG%"
