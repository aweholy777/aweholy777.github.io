@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_git_diag.txt
cd /d "%~dp0.."
echo git diag > "%LOG%"
tasklist /fi "imagename eq git.exe" >> "%LOG%" 2>&1
if exist .git\index.lock (
    del /f .git\index.lock >> "%LOG%" 2>&1
    echo lock deleted >> "%LOG%"
) else (
    echo no lock >> "%LOG%"
)
git fetch origin >> "%LOG%" 2>&1
echo --- remote ahead commits --- >> "%LOG%"
git log --oneline HEAD..origin/main >> "%LOG%" 2>&1
echo --- local ahead commits --- >> "%LOG%"
git log --oneline origin/main..HEAD >> "%LOG%" 2>&1
echo --- files changed in remote-ahead --- >> "%LOG%"
git diff --stat HEAD origin/main 2>nul | tail -5 >> "%LOG%" 2>&1
git diff --name-only HEAD origin/main >> "%LOG%" 2>&1
echo EXIT %errorlevel% >> "%LOG%"
