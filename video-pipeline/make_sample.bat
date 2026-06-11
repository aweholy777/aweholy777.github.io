@echo off
cd /d "%~dp0.."
echo ============================================
echo  QT Video Sample - voice: zh-TW-HsiaoChen
echo ============================================
echo.
echo [1/3] Checking Python and ffmpeg...
python --version
if errorlevel 1 (echo ERROR: Python not found && pause && exit /b 1)
ffmpeg -version >nul 2>&1
if errorlevel 1 (echo ERROR: ffmpeg not found. Run: winget install ffmpeg && pause && exit /b 1)
echo.
echo [2/3] Installing edge-tts...
pip install -r video-pipeline\requirements.txt --quiet
echo.
echo [3/3] Making sample video (1-3 minutes, please wait)...
python video-pipeline\make_video.py content\daily-qt\ntqt\2026-05-30.md --outdir video-output\ntqt
echo.
if exist video-output\ntqt\2026-05-30.mp4 (
    echo SUCCESS: video-output\ntqt\2026-05-30.mp4
) else (
    echo FAILED: see error above
)
pause
