@echo off
cd /d "%~dp0.."
python video-pipeline\yt_publish.py --auto --privacy public >> video-pipeline\yt_upload_log.txt 2>&1
