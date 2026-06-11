@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_lan_static_probe.txt
set KEY=%USERPROFILE%\.ssh\qt_lan_key
echo probe start > "%LOG%"
ssh -i "%KEY%" -o BatchMode=yes aweholy@192.168.68.61 "which ffmpeg && ffmpeg -version 2>/dev/null | head -1; echo ---FONT---; fc-list :lang=zh-tw family 2>/dev/null | sort -u | head -8; echo ---PY---; /home/aweholy/miniforge3/envs/comfyui/bin/python --version; echo ---CPU---; nproc; echo ---TAR---; which tar" >> "%LOG%" 2>&1
echo EXIT %errorlevel% >> "%LOG%"
