$OutFile = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_probe3.txt"
$r = New-Object System.Collections.Generic.List[string]
$r.Add("=== probe3 (PowerShell UTF8) ===")

# F 槽整合包
$bundle = Get-ChildItem "F:\" -Directory | Where-Object { $_.Name -like "comfyui*" }
foreach ($b in $bundle) {
    $r.Add("[bundle] " + $b.FullName)
    Get-ChildItem $b.FullName -Directory -ErrorAction SilentlyContinue | ForEach-Object { $r.Add("  DIR " + $_.Name) }
    Get-ChildItem $b.FullName -File -ErrorAction SilentlyContinue | Select-Object -First 15 | ForEach-Object { $r.Add("  FILE " + $_.Name) }
    # 找內層 ComfyUI
    $inner = Get-ChildItem $b.FullName -Directory -Recurse -Depth 2 -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq "custom_nodes" -or $_.Name -eq "models" }
    foreach ($i in $inner) {
        $r.Add("  FOUND " + $i.FullName)
        Get-ChildItem $i.FullName -ErrorAction SilentlyContinue | Select-Object -First 30 | ForEach-Object { $r.Add("    - " + $_.Name) }
    }
}

# Comfy Desktop 設定
$cd = Join-Path $env:APPDATA "Comfy Desktop"
if (Test-Path $cd) {
    $r.Add("[Comfy Desktop appdata]")
    Get-ChildItem $cd -ErrorAction SilentlyContinue | ForEach-Object { $r.Add("  " + $_.Name) }
    $cfg = Join-Path $cd "config.json"
    if (Test-Path $cfg) { $r.Add("[config.json]"); $r.Add((Get-Content $cfg -Raw)) }
    $yml = Join-Path $cd "extra_models_config.yaml"
    if (Test-Path $yml) { $r.Add("[extra_models_config.yaml]"); $r.Add((Get-Content $yml -Raw)) }
}
$r.Add("DONE")
$r | Out-File -FilePath $OutFile -Encoding utf8
