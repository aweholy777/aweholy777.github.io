@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_git_restore.txt
cd /d "%~dp0.."
echo === restore start === > "%LOG%"
git stash pop >> "%LOG%" 2>&1
echo pop_exit=%errorlevel% >> "%LOG%"
echo --- HEAD --- >> "%LOG%"
git log --oneline -1 >> "%LOG%" 2>&1
echo --- status count --- >> "%LOG%"
git status -s | find /c /v "" >> "%LOG%" 2>&1
echo --- stash list --- >> "%LOG%"
git stash list >> "%LOG%" 2>&1
echo --- embed still present? --- >> "%LOG%"
findstr /c:"youtube jhTdaflDIpo" content\daily-qt\ntqt\2026-05-30.md >> "%LOG%" 2>&1
echo === done === >> "%LOG%"
