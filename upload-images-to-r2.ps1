# upload-images-to-r2.ps1
# 將 static/images/ 裡的所有圖片上傳到 Cloudflare R2
#
# 用法：
#   .\upload-images-to-r2.ps1 -BucketName "cmtc-images"
#
# 前置條件：
#   1. npm install -g wrangler
#   2. wrangler login

param(
    [Parameter(Mandatory=$true)]
    [string]$BucketName,

    [string]$ImagesFolder = ".\static\images",

    [switch]$DryRun
)

# 檢查 wrangler 是否安裝
if (-not (Get-Command wrangler -ErrorAction SilentlyContinue)) {
    Write-Error "找不到 wrangler！請先執行：npm install -g wrangler"
    exit 1
}

# 檢查圖片資料夾
if (-not (Test-Path $ImagesFolder)) {
    Write-Error "找不到圖片資料夾：$ImagesFolder"
    exit 1
}

$images = Get-ChildItem -Path $ImagesFolder -File
$total = $images.Count
$success = 0
$failed = 0
$skipped = 0

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Cloudflare R2 圖片上傳工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Bucket: $BucketName" -ForegroundColor Yellow
Write-Host "  來源資料夾: $ImagesFolder" -ForegroundColor Yellow
Write-Host "  圖片總數: $total" -ForegroundColor Yellow
if ($DryRun) {
    Write-Host "  模式: 預覽 (DryRun，不實際上傳)" -ForegroundColor Magenta
}
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 支援的圖片格式
$supportedExtensions = @('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico', '.bmp', '.avif')

$i = 0
foreach ($image in $images) {
    $i++
    $ext = $image.Extension.ToLower()

    # 跳過非圖片檔案
    if ($ext -notin $supportedExtensions) {
        Write-Host "  [$i/$total] 跳過（非圖片）：$($image.Name)" -ForegroundColor DarkGray
        $skipped++
        continue
    }

    $key = $image.Name
    $filePath = $image.FullName
    $fileSize = [math]::Round($image.Length / 1KB, 1)

    Write-Host "  [$i/$total] 上傳中：$key ($fileSize KB)" -NoNewline

    if ($DryRun) {
        Write-Host " [預覽]" -ForegroundColor Magenta
        $success++
        continue
    }

    try {
        # 使用 wrangler 上傳到 R2
        $result = wrangler r2 object put "$BucketName/$key" --file "$filePath" 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Host " ✓" -ForegroundColor Green
            $success++
        } else {
            Write-Host " ✗ 失敗" -ForegroundColor Red
            Write-Host "    錯誤：$result" -ForegroundColor Red
            $failed++
        }
    } catch {
        Write-Host " ✗ 例外錯誤" -ForegroundColor Red
        Write-Host "    $_" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  上傳完成！" -ForegroundColor Green
Write-Host "  成功：$success  失敗：$failed  跳過：$skipped" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan

if ($failed -gt 0) {
    Write-Host ""
    Write-Host "有 $failed 個檔案上傳失敗，請檢查上方錯誤訊息。" -ForegroundColor Red
    Write-Host "常見原因：" -ForegroundColor Red
    Write-Host "  - 尚未執行 wrangler login" -ForegroundColor Red
    Write-Host "  - Bucket 名稱錯誤" -ForegroundColor Red
    Write-Host "  - 網路問題" -ForegroundColor Red
}

if ($success -gt 0 -and -not $DryRun) {
    Write-Host ""
    Write-Host "圖片上傳完成！接下來請：" -ForegroundColor Green
    Write-Host "  1. 確認 R2 bucket 已開啟公開存取" -ForegroundColor Green
    Write-Host "  2. 複製您的 R2 公開網址（r2.dev 或自訂網域）" -ForegroundColor Green
    Write-Host "  3. 執行 update-image-urls.py 更新 content/ 裡的圖片路徑" -ForegroundColor Green
}
