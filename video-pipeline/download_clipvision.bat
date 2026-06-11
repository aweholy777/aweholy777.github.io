@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_clipvision_log.txt
set MODELS=C:\Users\aweholy\ComfyUI-Shared\models
echo clip_vision_h download start %time% > "%LOG%"
curl -L -sS -C - --retry 5 -o "%MODELS%\clip_vision\clip_vision_h.safetensors" "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors" >> "%LOG%" 2>&1
echo CLIPVISION_DONE %time% >> "%LOG%"
