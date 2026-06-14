@echo off
cd /d "%~dp0.."
REM 5090 鐵律：上傳一律 --no-push，網站發布留給 3060（見 CLAUDE.local.md）
python video-pipeline\yt_publish.py --auto --no-push --privacy public >> video-pipeline\yt_upload_log.txt 2>&1
