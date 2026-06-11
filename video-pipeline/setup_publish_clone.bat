@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_pubclone.txt
echo clone start > "%LOG%"
if not exist "C:\Users\aweholy\qt-publish" mkdir "C:\Users\aweholy\qt-publish"
cd /d "C:\Users\aweholy\qt-publish"
if exist aweholy777.github.io (
    echo already exists, pulling >> "%LOG%"
    cd aweholy777.github.io
    git pull >> "%LOG%" 2>&1
) else (
    git clone https://github.com/aweholy777/aweholy777.github.io.git >> "%LOG%" 2>&1
    cd aweholy777.github.io
)
git log --oneline -2 >> "%LOG%" 2>&1
echo EXIT %errorlevel% >> "%LOG%"
