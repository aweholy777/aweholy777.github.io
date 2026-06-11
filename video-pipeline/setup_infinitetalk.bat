@echo off
setlocal
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_setup_log.txt
set NODES=C:\Users\aweholy\ComfyUI-Installs\ComfyUI\ComfyUI\custom_nodes
set PY=C:\Users\aweholy\ComfyUI-Installs\ComfyUI\ComfyUI\.venv\Scripts\python.exe
set MODELS=C:\Users\aweholy\ComfyUI-Shared\models
set HF=https://huggingface.co/Kijai/WanVideo_comfy/resolve/main

echo === setup start %date% %time% === > "%LOG%"

REM ---------- custom nodes ----------
cd /d "%NODES%"
if not exist ComfyUI-WanVideoWrapper (
  git clone --depth 1 https://github.com/kijai/ComfyUI-WanVideoWrapper >> "%LOG%" 2>&1
)
if not exist ComfyUI-VideoHelperSuite (
  git clone --depth 1 https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite >> "%LOG%" 2>&1
)
if not exist ComfyUI-KJNodes (
  git clone --depth 1 https://github.com/kijai/ComfyUI-KJNodes >> "%LOG%" 2>&1
)
echo STEP1_NODES_CLONED %time% >> "%LOG%"

"%PY%" -m pip install -r ComfyUI-WanVideoWrapper\requirements.txt >> "%LOG%" 2>&1
"%PY%" -m pip install -r ComfyUI-VideoHelperSuite\requirements.txt >> "%LOG%" 2>&1
"%PY%" -m pip install -r ComfyUI-KJNodes\requirements.txt >> "%LOG%" 2>&1
echo STEP2_PIP_DONE %time% >> "%LOG%"

REM ---------- models (curl: resumable, retry) ----------
echo downloading main model 15.8GB... >> "%LOG%"
curl -L -sS -C - --retry 5 -o "%MODELS%\diffusion_models\Wan2_1-I2V-14B-480P_fp8_e4m3fn.safetensors" "%HF%/Wan2_1-I2V-14B-480P_fp8_e4m3fn.safetensors" >> "%LOG%" 2>&1
echo STEP3_MAIN_MODEL_DONE %time% >> "%LOG%"

echo downloading infinitetalk 5.1GB... >> "%LOG%"
curl -L -sS -C - --retry 5 -o "%MODELS%\diffusion_models\Wan2_1-InfiniTetalk-Single_fp16.safetensors" "%HF%/InfiniteTalk/Wan2_1-InfiniTetalk-Single_fp16.safetensors" >> "%LOG%" 2>&1
echo STEP4_INFINITETALK_DONE %time% >> "%LOG%"

echo downloading umt5 6.7GB... >> "%LOG%"
curl -L -sS -C - --retry 5 -o "%MODELS%\text_encoders\umt5-xxl-enc-fp8_e4m3fn.safetensors" "%HF%/umt5-xxl-enc-fp8_e4m3fn.safetensors" >> "%LOG%" 2>&1
echo STEP5_UMT5_DONE %time% >> "%LOG%"

echo downloading vae 254MB... >> "%LOG%"
curl -L -sS -C - --retry 5 -o "%MODELS%\vae\Wan2_1_VAE_bf16.safetensors" "%HF%/Wan2_1_VAE_bf16.safetensors" >> "%LOG%" 2>&1
echo STEP6_VAE_DONE %time% >> "%LOG%"

echo downloading clip_vision 1.26GB... >> "%LOG%"
curl -L -sS -C - --retry 5 -o "%MODELS%\clip_vision\open-clip-xlm-roberta-large-vit-huge-14_visual_fp16.safetensors" "%HF%/open-clip-xlm-roberta-large-vit-huge-14_visual_fp16.safetensors" >> "%LOG%" 2>&1
echo STEP7_CLIPVISION_DONE %time% >> "%LOG%"

echo ALL_DONE %time% >> "%LOG%"
