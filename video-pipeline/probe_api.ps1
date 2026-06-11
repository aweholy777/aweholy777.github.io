$OutFile = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_api.txt"
$r = New-Object System.Collections.Generic.List[string]

foreach ($port in @(8000, 8188, 8080)) {
    try {
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:$port/system_stats" -TimeoutSec 5
        $r.Add("PORT $port OK comfyui=" + $resp.system.comfyui_version + " vram_total=" + $resp.devices[0].vram_total)
    } catch { $r.Add("PORT $port no") }
}

$M = "C:\Users\aweholy\ComfyUI-Shared\models"
foreach ($sub in @("diffusion_models", "text_encoders", "vae", "clip_vision", "loras")) {
    Get-ChildItem (Join-Path $M $sub) -File -ErrorAction SilentlyContinue | ForEach-Object {
        $r.Add(("{0,9:N1} MB  {1}\{2}" -f ($_.Length/1MB), $sub, $_.Name))
    }
}
$log = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_setup_log.txt"
Get-Content $log -Tail 3 | ForEach-Object { $r.Add("LOG: " + $_) }
$llog = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_lora_log.txt"
if (Test-Path $llog) { Get-Content $llog -Tail 2 | ForEach-Object { $r.Add("LORA: " + $_) } }
$r.Add(("time: " + (Get-Date -Format "HH:mm:ss")))
$r | Out-File -FilePath $OutFile -Encoding utf8
