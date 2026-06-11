$OutFile = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_probe4.txt"
$r = New-Object System.Collections.Generic.List[string]
$cd = Join-Path $env:APPDATA "Comfy Desktop"

foreach ($f in @("installations.json", "settings.json", "shared_model_paths.yaml")) {
    $p = Join-Path $cd $f
    if (Test-Path $p) {
        $r.Add("===== $f =====")
        $r.Add((Get-Content $p -Raw))
    }
}

$r.Add("===== F bundle deep =====")
$bundles = Get-ChildItem "F:\" -Directory | Where-Object { $_.Name -like "comfyui*" }
foreach ($b in $bundles) {
    $r.Add("[bundle] " + $b.FullName)
    try {
        $items = Get-ChildItem $b.FullName -ErrorAction Stop
        foreach ($i in $items) {
            if ($i.PSIsContainer) { $r.Add("DIR  " + $i.Name) } else { $r.Add("FILE " + $i.Name) }
        }
    } catch { $r.Add("ERROR: " + $_.Exception.Message) }
}

$r.Add("DONE")
$r | Out-File -FilePath $OutFile -Encoding utf8
