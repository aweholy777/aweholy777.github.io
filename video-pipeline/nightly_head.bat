@echo off
REM 若 ComfyUI 沒在跑，直接以無頭模式啟動（不依賴 Comfy Desktop 視窗）
powershell -NoProfile -Command "try{Invoke-RestMethod -Uri http://127.0.0.1:8188/system_stats -TimeoutSec 3 | Out-Null; exit 0}catch{exit 1}"
if errorlevel 1 (
    pushd "C:\Users\aweholy\ComfyUI-Installs\ComfyUI\ComfyUI"
    start "ComfyUI-headless" /min ".venv\Scripts\python.exe" main.py --port 8188
    popd
    timeout /t 90 /nobreak >nul
)
cd /d "%~dp0.."
python video-pipeline\nightly_head.py >> video-pipeline\nightly_head_log.txt 2>&1
