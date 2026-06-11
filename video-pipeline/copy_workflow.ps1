$src = "C:\Users\aweholy\ComfyUI-Installs\ComfyUI\ComfyUI\custom_nodes\ComfyUI-WanVideoWrapper\example_workflows"
$dst = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\workflows"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item (Join-Path $src "wanvideo_2_1_14B_I2V_InfiniteTalk_example_03.json") $dst -Force
"copied $(Get-Date -Format HH:mm:ss)" | Out-File (Join-Path $dst "_copy_done.txt") -Encoding utf8
