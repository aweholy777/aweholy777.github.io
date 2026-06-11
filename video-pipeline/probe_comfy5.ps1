$OutFile = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_probe5.txt"
$r = New-Object System.Collections.Generic.List[string]
$root = "C:\Users\aweholy\ComfyUI-Installs\ComfyUI"

$r.Add("===== install root =====")
Get-ChildItem $root -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.PSIsContainer) { $r.Add("DIR  " + $_.Name) } else { $r.Add("FILE " + $_.Name) }
}

$r.Add("===== find python.exe (depth 3) =====")
Get-ChildItem $root -Recurse -Depth 3 -Filter "python.exe" -ErrorAction SilentlyContinue | ForEach-Object { $r.Add($_.FullName) }

$r.Add("===== custom_nodes =====")
$cn = Join-Path $root "custom_nodes"
if (Test-Path $cn) { Get-ChildItem $cn | ForEach-Object { $r.Add("  " + $_.Name) } } else { $r.Add("(no custom_nodes dir)") }

$r.Add("===== ComfyUI subdir? =====")
$inner = Join-Path $root "ComfyUI"
if (Test-Path $inner) {
    Get-ChildItem $inner -ErrorAction SilentlyContinue | Select-Object -First 25 | ForEach-Object {
        if ($_.PSIsContainer) { $r.Add("DIR  " + $_.Name) } else { $r.Add("FILE " + $_.Name) }
    }
}

$r.Add("===== shared models dirs =====")
Get-ChildItem "C:\Users\aweholy\ComfyUI-Shared\models" -Directory -ErrorAction SilentlyContinue | ForEach-Object { $r.Add("  " + $_.Name) }

$r.Add("DONE")
$r | Out-File -FilePath $OutFile -Encoding utf8
