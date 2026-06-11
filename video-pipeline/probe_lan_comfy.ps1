$OutFile = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_lan_comfy.txt"
"started $(Get-Date -Format HH:mm:ss)" | Out-File $OutFile -Encoding utf8
$base = "http://192.168.68.61:8188"

function Add-Line($t) { $t | Out-File $OutFile -Append -Encoding utf8 }

try {
    $s = Invoke-RestMethod -Uri "$base/system_stats" -TimeoutSec 8
    Add-Line ("OK comfyui=" + $s.system.comfyui_version)
    Add-Line ("os=" + $s.system.os + " pytorch=" + $s.system.pytorch_version)
    foreach ($d in $s.devices) {
        Add-Line ("device=" + $d.name)
        Add-Line ("vram_total_GB=" + [math]::Round($d.vram_total / 1GB, 1) + " vram_free_GB=" + [math]::Round($d.vram_free / 1GB, 1))
    }
} catch {
    Add-Line ("system_stats FAILED: " + $_.Exception.Message)
}

foreach ($node in @("WanVideoModelLoader", "MultiTalkModelLoader", "VHS_VideoCombine", "INTConstant")) {
    try {
        $null = Invoke-RestMethod -Uri "$base/object_info/$node" -TimeoutSec 8
        Add-Line ("NODE " + $node + " : INSTALLED")
    } catch {
        Add-Line ("NODE " + $node + " : missing")
    }
}

Add-Line ("done " + (Get-Date -Format "HH:mm:ss"))
