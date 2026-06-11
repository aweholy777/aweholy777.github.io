@echo off
cd /d "%~dp0.."
echo Full-article talking head: 2026-05-30 (estimated 16-20 hours on RTX 3060)
echo Started at %date% %time%
python video-pipeline\make_video.py content\daily-qt\ntqt\2026-05-30.md --outdir video-output\head --mode head
echo Finished at %date% %time%
if exist video-output\head\2026-05-30.mp4 (
    echo SUCCESS: video-output\head\2026-05-30.mp4
) else (
    echo FAILED: see error above
)
pause
