@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_lan_otqt.txt
set KEY=%USERPROFILE%\.ssh\qt_lan_key
echo launch otqt > "%LOG%"
ssh -i "%KEY%" -o BatchMode=yes aweholy@192.168.68.61 "cd ~/qtwork && nohup /home/aweholy/miniforge3/envs/comfyui/bin/python video-pipeline/batch_make.py --src content/daily-qt/otqt --outdir ~/qt-static-output/otqt --bg ~/qtwork/static/images/qt.jpg --font 'AR PL UMing TW' --result ~/qtwork/result-otqt.md > ~/qtwork/log-otqt.txt 2>&1 & sleep 25; pgrep -af '[b]atch_make' | wc -l; echo ---OTQT---; tail -4 ~/qtwork/log-otqt.txt" >> "%LOG%" 2>&1
echo EXIT %errorlevel% >> "%LOG%"
