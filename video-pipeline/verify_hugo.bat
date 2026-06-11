@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_hugo_verify.txt
cd /d "%~dp0.."
echo hugo build check > "%LOG%"
hugo --buildFuture >> "%LOG%" 2>&1
echo EXIT %errorlevel% >> "%LOG%"
