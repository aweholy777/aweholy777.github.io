#!/usr/bin/env bash
# setup_lan_infinitetalk.sh — 在 Ubuntu ComfyUI 主機上安裝 InfiniteTalk 全套
# 用法：在 192.168.68.61 上執行  bash setup_lan_infinitetalk.sh
set -e

# ---- 自動定位正在執行的 ComfyUI ----
PID=$(pgrep -f "main.py" | head -1 || true)
if [ -n "$PID" ]; then
    COMFY_DIR=$(readlink -f /proc/$PID/cwd)
    PY=$(readlink -f /proc/$PID/exe)
else
    echo "找不到執行中的 ComfyUI，請手動設定 COMFY_DIR 與 PY 後重跑"
    COMFY_DIR="${COMFY_DIR:?請設定 COMFY_DIR=ComfyUI 目錄}"
    PY="${PY:?請設定 PY=ComfyUI 的 python 路徑}"
fi
echo "ComfyUI 目錄: $COMFY_DIR"
echo "Python: $PY"
MODELS="$COMFY_DIR/models"
NODES="$COMFY_DIR/custom_nodes"

# ---- 1. 自訂節點 ----
cd "$NODES"
[ -d ComfyUI-WanVideoWrapper ]   || git clone --depth 1 https://github.com/kijai/ComfyUI-WanVideoWrapper
[ -d ComfyUI-VideoHelperSuite ]  || git clone --depth 1 https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite
[ -d ComfyUI-KJNodes ]           || git clone --depth 1 https://github.com/kijai/ComfyUI-KJNodes
"$PY" -m pip install -r ComfyUI-WanVideoWrapper/requirements.txt
"$PY" -m pip install -r ComfyUI-VideoHelperSuite/requirements.txt
"$PY" -m pip install -r ComfyUI-KJNodes/requirements.txt
echo "=== 節點安裝完成 ==="

# ---- 2. 模型（約 31GB，curl 可續傳） ----
HF=https://huggingface.co/Kijai/WanVideo_comfy/resolve/main
dl() { mkdir -p "$(dirname "$2")"; curl -L -C - --retry 5 -o "$2" "$1"; }

dl "$HF/Wan2_1-I2V-14B-480P_fp8_e4m3fn.safetensors" \
   "$MODELS/diffusion_models/Wan2_1-I2V-14B-480P_fp8_e4m3fn.safetensors"
dl "$HF/InfiniteTalk/Wan2_1-InfiniTetalk-Single_fp16.safetensors" \
   "$MODELS/diffusion_models/Wan2_1-InfiniTetalk-Single_fp16.safetensors"
dl "$HF/umt5-xxl-enc-fp8_e4m3fn.safetensors" \
   "$MODELS/text_encoders/umt5-xxl-enc-fp8_e4m3fn.safetensors"
dl "$HF/Wan2_1_VAE_bf16.safetensors" \
   "$MODELS/vae/Wan2_1_VAE_bf16.safetensors"
dl "$HF/Lightx2v/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors" \
   "$MODELS/loras/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors"
dl "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors" \
   "$MODELS/clip_vision/clip_vision_h.safetensors"

echo "=== 模型下載完成 ==="
echo "請重新啟動 ComfyUI 服務讓節點生效（systemctl restart comfyui 或重跑 main.py）"
echo "ALL DONE"
