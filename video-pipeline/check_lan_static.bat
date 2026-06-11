@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_lan_static_status.txt
set KEY=%USERPROFILE%\.ssh\qt_lan_key
echo status check > "%LOG%"
ssh -i "%KEY%" -o BatchMode=yes aweholy@192.168.68.61 "pgrep -af '[b]atch_make' | head -4; echo ---NTQT log---; tail -3 ~/qtwork/log-ntqt.txt 2>/dev/null; echo ---OTQT log---; tail -3 ~/qtwork/log-otqt.txt 2>/dev/null; echo ---OUTPUT---; ls ~/qt-static-output/ntqt 2>/dev/null | wc -l; ls ~/qt-static-output/otqt 2>/dev/null | wc -l" >> "%LOG%" 2>&1
echo EXIT %errorlevel% >> "%LOG%"
