@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_git_align.txt
cd /d "%~dp0.."
echo git align > "%LOG%"
REM mixed reset：HEAD 對齊遠端，工作目錄完全不動
git reset origin/main >> "%LOG%" 2>&1
echo --- status count after align --- >> "%LOG%"
git status -s | find /c /v "" >> "%LOG%" 2>&1
echo --- status sample --- >> "%LOG%"
git status -s > "%TEMP%\_gs.txt"
powershell -NoProfile -Command "Get-Content $env:TEMP\_gs.txt -TotalCount 20" >> "%LOG%" 2>&1
echo EXIT %errorlevel% >> "%LOG%"
