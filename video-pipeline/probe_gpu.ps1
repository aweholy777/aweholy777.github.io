$OutFile = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_gpu.txt"
$r = New-Object System.Collections.Generic.List[string]
$r.Add((nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,power.draw --format=csv,noheader))
$r.Add("--- 3 sec later ---")
Start-Sleep -Seconds 3
$r.Add((nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,power.draw --format=csv,noheader))
$log = "C:\Users\aweholy\ComfyUI-Installs\ComfyUI\logs\comfyui.log"
$r.Add("--- log tail 3 ---")
Get-Content $log -Tail 3 | ForEach-Object { $r.Add($_) }
$r.Add(("time: " + (Get-Date -Format "HH:mm:ss")))
$r | Out-File -FilePath $OutFile -Encoding utf8
