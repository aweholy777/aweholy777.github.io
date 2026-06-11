@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_lora_log.txt
set MODELS=C:\Users\aweholy\ComfyUI-Shared\models
echo lora download start %time% > "%LOG%"
curl -L -sS -C - --retry 5 -o "%MODELS%\loras\lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors" "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Lightx2v/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors" >> "%LOG%" 2>&1
echo LORA_DONE %time% >> "%LOG%"
