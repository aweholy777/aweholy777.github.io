@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_git_merge.txt
cd /d "%~dp0.."
echo === safe merge start === > "%LOG%"

echo [0] backup branch at current HEAD >> "%LOG%"
git branch -f qt-autopush-backup HEAD >> "%LOG%" 2>&1
git rev-parse HEAD >> "%LOG%" 2>&1

echo [1] stash all (incl untracked) >> "%LOG%"
git stash push -u -m qt-autopush >> "%LOG%" 2>&1

echo [2] status after stash (should be ~0) >> "%LOG%"
git status -s | find /c /v "" >> "%LOG%" 2>&1

echo [3] fast-forward to origin/main >> "%LOG%"
git merge --ff-only origin/main >> "%LOG%" 2>&1
echo merge_exit=%errorlevel% >> "%LOG%"

echo [4] HEAD now >> "%LOG%"
git log --oneline -2 >> "%LOG%" 2>&1

echo [5] stash list (still there) >> "%LOG%"
git stash list >> "%LOG%" 2>&1
echo === phase1 done === >> "%LOG%"
