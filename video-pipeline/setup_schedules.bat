@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_schedules.txt
set VP=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline
echo schedule setup > "%LOG%"
schtasks /create /f /tn "QT_NightlyHead" /tr "\"%VP%\nightly_head.bat\"" /sc daily /st 21:00 >> "%LOG%" 2>&1
schtasks /create /f /tn "QT_YT_Upload" /tr "\"%VP%\yt_auto_upload.bat\"" /sc daily /st 12:30 >> "%LOG%" 2>&1
schtasks /query /tn "QT_NightlyHead" /fo list | findstr /i "TaskName Status" >> "%LOG%" 2>&1
schtasks /query /tn "QT_YT_Upload" /fo list | findstr /i "TaskName Status" >> "%LOG%" 2>&1
echo EXIT %errorlevel% >> "%LOG%"
