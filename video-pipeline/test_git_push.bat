@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_git_test.txt
cd /d "%~dp0.."
echo git test > "%LOG%"
git add content\daily-qt\ntqt\2026-05-30.md video-pipeline\yt_uploaded.csv >> "%LOG%" 2>&1
git commit -m "auto: embed youtube video 2026-05-30" >> "%LOG%" 2>&1
git push >> "%LOG%" 2>&1
echo EXIT %errorlevel% >> "%LOG%"
