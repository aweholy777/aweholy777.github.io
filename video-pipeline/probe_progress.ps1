$OutFile = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_progress.txt"
$r = New-Object System.Collections.Generic.List[string]
$M = "C:\Users\aweholy\ComfyUI-Shared\models"

$r.Add("===== model files now =====")
foreach ($sub in @("diffusion_models", "text_encoders", "vae", "clip_vision")) {
    Get-ChildItem (Join-Path $M $sub) -File -ErrorAction SilentlyContinue | ForEach-Object {
        $r.Add(("{0,8:N1} MB  {1}\{2}" -f ($_.Length/1MB), $sub, $_.Name))
    }
}

$r.Add("===== setup log tail =====")
$log = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_setup_log.txt"
Get-Content $log -Tail 6 | ForEach-Object { $r.Add($_) }

$r.Add("===== example_workflows (infinitetalk) =====")
$ew = "C:\Users\aweholy\ComfyUI-Installs\ComfyUI\ComfyUI\custom_nodes\ComfyUI-WanVideoWrapper\example_workflows"
Get-ChildItem $ew -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "talk|Talk" } | ForEach-Object { $r.Add("  " + $_.Name) }

$r.Add(("time: " + (Get-Date -Format "HH:mm:ss")))
$r.Add("DONE")
$r | Out-File -FilePath $OutFile -Encoding utf8
