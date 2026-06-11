#!/usr/bin/env bash
# qt-resume.sh — MS-S1 MAX 開機自動恢復（由 crontab @reboot 呼叫）
# 1) 重啟 ComfyUI  2) 續跑靜態批次（已完成的自動跳過）
PY=/home/aweholy/miniforge3/envs/comfyui/bin/python

# ComfyUI
pkill -f '[m]ain.py' 2>/dev/null
sleep 3
cd /home/aweholy/ComfyUI
nohup $PY main.py --listen 0.0.0.0 --port 8188 > /home/aweholy/comfyui_server.log 2>&1 &

# 靜態批次（冪等：存在的 mp4 自動跳過）
sleep 10
cd /home/aweholy/qtwork
nohup $PY video-pipeline/batch_make.py --src content/daily-qt/ntqt \
  --outdir /home/aweholy/qt-static-output/ntqt \
  --bg /home/aweholy/qtwork/static/images/qt.jpg --font 'AR PL UMing TW' \
  --result /home/aweholy/qtwork/result-ntqt.md > /home/aweholy/qtwork/log-ntqt.txt 2>&1 &
nohup $PY video-pipeline/batch_make.py --src content/daily-qt/otqt \
  --outdir /home/aweholy/qt-static-output/otqt \
  --bg /home/aweholy/qtwork/static/images/qt.jpg --font 'AR PL UMing TW' \
  --result /home/aweholy/qtwork/result-otqt.md > /home/aweholy/qtwork/log-otqt.txt 2>&1 &
echo "qt-resume done $(date)" >> /home/aweholy/qt-resume.log
