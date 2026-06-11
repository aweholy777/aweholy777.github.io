$OutFile = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_lan_models.txt"
"started $(Get-Date -Format HH:mm:ss)" | Out-File $OutFile -Encoding utf8
$base = "http://192.168.68.61:8188"
function Add-Line($t) { $t | Out-File $OutFile -Append -Encoding utf8 }

foreach ($node in @("WanVideoModelLoader", "MultiTalkModelLoader", "WanVideoVAELoader", "CLIPVisionLoader", "WanVideoLoraSelect", "WanVideoTextEncodeCached")) {
    try {
        $resp = Invoke-WebRequest -Uri "$base/object_info/$node" -TimeoutSec 10 -UseBasicParsing
        $txt = $resp.Content
        if ($txt.Length -gt 2500) { $txt = $txt.Substring(0, 2500) + "...TRUNC" }
        Add-Line ("===== " + $node + " =====")
        Add-Line $txt
    } catch { Add-Line ($node + " FAILED: " + $_.Exception.Message) }
}
Add-Line ("done " + (Get-Date -Format "HH:mm:ss"))
