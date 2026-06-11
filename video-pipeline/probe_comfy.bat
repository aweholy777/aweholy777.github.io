@echo off
set OUT=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_probe.txt
echo === ComfyUI environment probe === > "%OUT%"
echo. >> "%OUT%"
echo [GPU] >> "%OUT%"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader >> "%OUT%" 2>&1
echo. >> "%OUT%"
echo [free disk C] >> "%OUT%"
powershell -NoProfile -Command "Get-PSDrive -PSProvider FileSystem | Select-Object Name,@{n='FreeGB';e={[math]::Round($_.Free/1GB,1)}} | Format-Table -AutoSize" >> "%OUT%" 2>&1
echo [tools] >> "%OUT%"
git --version >> "%OUT%" 2>&1
curl --version 2>&1 | findstr /b curl >> "%OUT%"
echo. >> "%OUT%"
echo [LOCALAPPDATA Programs comfy] >> "%OUT%"
dir "%LOCALAPPDATA%\Programs" /b 2>nul | findstr /i comfy >> "%OUT%"
echo [APPDATA ComfyUI config.json] >> "%OUT%"
type "%APPDATA%\ComfyUI\config.json" >> "%OUT%" 2>&1
echo. >> "%OUT%"
echo [APPDATA ComfyUI extra_models_config.yaml] >> "%OUT%"
type "%APPDATA%\ComfyUI\extra_models_config.yaml" >> "%OUT%" 2>&1
echo. >> "%OUT%"
echo [Documents ComfyUI] >> "%OUT%"
dir "%USERPROFILE%\Documents\ComfyUI" /b >> "%OUT%" 2>&1
echo. >> "%OUT%"
echo [Documents ComfyUI custom_nodes] >> "%OUT%"
dir "%USERPROFILE%\Documents\ComfyUI\custom_nodes" /b >> "%OUT%" 2>&1
echo. >> "%OUT%"
echo [Documents ComfyUI models] >> "%OUT%"
dir "%USERPROFILE%\Documents\ComfyUI\models" /b >> "%OUT%" 2>&1
echo. >> "%OUT%"
echo [search ComfyUI dirs on all drives - shallow] >> "%OUT%"
for %%D in (C D E F) do (
  if exist %%D:\ (
    dir %%D:\ /b /ad 2>nul | findstr /i comfy >> "%OUT%"
    dir %%D:\ComfyUI\models /b >> "%OUT%" 2>nul
  )
)
echo DONE >> "%OUT%"
