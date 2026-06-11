#!/usr/bin/env bash
# 在 MS-S1 MAX 上重啟 ComfyUI（由 restart_lan_comfy.bat 透過 ssh 呼叫）
pkill -f '[m]ain.py' 2>/dev/null
sleep 3
cd ~/ComfyUI
nohup /home/aweholy/miniforge3/envs/comfyui/bin/python main.py --listen 0.0.0.0 --port 8188 > ~/comfyui_server.log 2>&1 &
sleep 15
echo "=== process ==="
pgrep -af '[m]ain.py'
echo "=== log tail ==="
tail -8 ~/comfyui_server.log
