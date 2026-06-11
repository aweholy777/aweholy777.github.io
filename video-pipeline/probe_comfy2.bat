@echo off
set OUT=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_probe2.txt
echo === probe2 === > "%OUT%"
for %%D in (C D E F H I J K P) do (
  if exist "%%D:\" (
    echo [drive %%D root comfy dirs] >> "%OUT%"
    dir %%D:\ /b /ad 2>nul | findstr /i comfy >> "%OUT%"
  )
)
echo. >> "%OUT%"
for %%D in (C D E F H I J K P) do (
  if exist "%%D:\Comfy\" (
    echo [%%D:\Comfy contents] >> "%OUT%"
    dir "%%D:\Comfy" /b >> "%OUT%" 2>&1
  )
)
echo. >> "%OUT%"
echo [APPDATA comfy-ish] >> "%OUT%"
dir "%APPDATA%" /b 2>nul | findstr /i comfy >> "%OUT%"
echo [LOCALAPPDATA comfy-ish] >> "%OUT%"
dir "%LOCALAPPDATA%" /b 2>nul | findstr /i comfy >> "%OUT%"
echo. >> "%OUT%"
if exist "%APPDATA%\Comfy\" (
  echo [APPDATA\Comfy files] >> "%OUT%"
  dir "%APPDATA%\Comfy" /b >> "%OUT%" 2>&1
  if exist "%APPDATA%\Comfy\config.json" type "%APPDATA%\Comfy\config.json" >> "%OUT%" 2>&1
  if exist "%APPDATA%\Comfy\extra_models_config.yaml" type "%APPDATA%\Comfy\extra_models_config.yaml" >> "%OUT%" 2>&1
)
echo DONE >> "%OUT%"
