@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_deploy_lan.txt
set KEY=%USERPROFILE%\.ssh\qt_lan_key
set HOST=aweholy@192.168.68.61
set SH=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\setup_lan_infinitetalk.sh
echo deploy start > "%LOG%"
scp -i "%KEY%" -o BatchMode=yes "%SH%" %HOST%:~/setup_lan_infinitetalk.sh >> "%LOG%" 2>&1
ssh -i "%KEY%" -o BatchMode=yes %HOST% "sed -i 's/\r$//' ~/setup_lan_infinitetalk.sh && nohup bash ~/setup_lan_infinitetalk.sh > ~/setup_infinitetalk.log 2>&1 & echo LAUNCHED" >> "%LOG%" 2>&1
echo EXIT_CODE %errorlevel% >> "%LOG%"
