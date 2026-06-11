$OutFile = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_startup_result.txt"
try {
    $startup = [Environment]::GetFolderPath("Startup")
    $ws = New-Object -ComObject WScript.Shell
    $sc = $ws.CreateShortcut((Join-Path $startup "Comfy Desktop (QT).lnk"))
    $sc.TargetPath = "C:\Users\aweholy\AppData\Local\Programs\Comfy Desktop\Comfy Desktop.exe"
    $sc.Save()
    "OK shortcut at: " + (Join-Path $startup "Comfy Desktop (QT).lnk") | Out-File $OutFile -Encoding utf8
} catch {
    "FAILED: " + $_.Exception.Message | Out-File $OutFile -Encoding utf8
}
