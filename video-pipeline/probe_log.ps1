$OutFile = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_comfy_log.txt"
$r = New-Object System.Collections.Generic.List[string]
$dirs = @("C:\Users\aweholy\ComfyUI-Installs\ComfyUI\logs",
          (Join-Path $env:APPDATA "Comfy Desktop\logs"))
foreach ($d in $dirs) {
    if (Test-Path $d) {
        $f = Get-ChildItem $d -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($f) {
            $r.Add("===== " + $f.FullName + " (tail 40) =====")
            Get-Content $f.FullName -Tail 40 | ForEach-Object { $r.Add($_) }
        }
    }
}
$r.Add(("time: " + (Get-Date -Format "HH:mm:ss")))
$r | Out-File -FilePath $OutFile -Encoding utf8
