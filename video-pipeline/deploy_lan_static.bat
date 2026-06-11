@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_lan_static_deploy.txt
set KEY=%USERPROFILE%\.ssh\qt_lan_key
set HOST=aweholy@192.168.68.61
set REPO=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io
echo deploy start > "%LOG%"

echo [1/3] install edge-tts... >> "%LOG%"
ssh -i "%KEY%" -o BatchMode=yes %HOST% "/home/aweholy/miniforge3/envs/comfyui/bin/python -m pip install --quiet edge-tts && echo EDGE_TTS_OK" >> "%LOG%" 2>&1

echo [2/3] transfer scripts + articles... >> "%LOG%"
cd /d "%REPO%"
tar -cf - video-pipeline/extract_text.py video-pipeline/make_video.py video-pipeline/batch_make.py hugo.toml static/images/qt.jpg content/daily-qt | ssh -i "%KEY%" -o BatchMode=yes %HOST% "mkdir -p ~/qtwork && tar -xf - -C ~/qtwork && echo TRANSFER_OK && ls ~/qtwork/content/daily-qt/ntqt | wc -l" >> "%LOG%" 2>&1

echo [3/3] launch batches... >> "%LOG%"
ssh -i "%KEY%" -o BatchMode=yes %HOST% "cd ~/qtwork && PY=/home/aweholy/miniforge3/envs/comfyui/bin/python && nohup $PY video-pipeline/batch_make.py --src content/daily-qt/ntqt --outdir ~/qt-static-output/ntqt --bg ~/qtwork/static/images/qt.jpg --font 'AR PL UMing TW' --result ~/qtwork/result-ntqt.md > ~/qtwork/log-ntqt.txt 2>&1 & nohup $PY video-pipeline/batch_make.py --src content/daily-qt/otqt --outdir ~/qt-static-output/otqt --bg ~/qtwork/static/images/qt.jpg --font 'AR PL UMing TW' --result ~/qtwork/result-otqt.md > ~/qtwork/log-otqt.txt 2>&1 & sleep 20; echo ---NTQT---; tail -4 ~/qtwork/log-ntqt.txt; echo ---OTQT---; tail -4 ~/qtwork/log-otqt.txt" >> "%LOG%" 2>&1
echo EXIT %errorlevel% >> "%LOG%"
