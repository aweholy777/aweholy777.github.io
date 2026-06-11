@echo off
cd /d "%~dp0.."
echo [1/2] Installing Google API libraries...
pip install --quiet google-api-python-client google-auth-oauthlib google-auth-httplib2
echo.
echo [2/2] First upload (browser will open for Google authorization)...
python video-pipeline\yt_publish.py --video video-output\head\2026-05-30.mp4 --privacy unlisted
pause
