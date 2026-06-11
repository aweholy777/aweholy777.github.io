@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_ssh_test.txt
echo test start > "%LOG%"
ssh -i "%USERPROFILE%\.ssh\qt_lan_key" -o BatchMode=yes -o ConnectTimeout=8 aweholy@192.168.68.61 "echo SSH_OK; whoami; uname -a; df -h / | tail -1" >> "%LOG%" 2>&1
echo EXIT_CODE %errorlevel% >> "%LOG%"
