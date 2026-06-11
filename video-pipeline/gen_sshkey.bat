@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_sshkey_log.txt
set KEY=%USERPROFILE%\.ssh\qt_lan_key
if not exist "%USERPROFILE%\.ssh" mkdir "%USERPROFILE%\.ssh"
echo gen start > "%LOG%"
if not exist "%KEY%" (
    ssh-keygen -t ed25519 -f "%KEY%" -N "" -C "qt-video-pipeline" >> "%LOG%" 2>&1
) else (
    echo key already exists >> "%LOG%"
)
echo --- PUBLIC KEY --- >> "%LOG%"
type "%KEY%.pub" >> "%LOG%" 2>&1
echo DONE >> "%LOG%"
