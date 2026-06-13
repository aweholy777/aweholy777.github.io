# morning_3060.ps1 — 3060 晨間同步 + 檢查
# 發布是自動的：push 到 main 由 GitHub Actions（deploy.yml）建置部署。
# 本腳本不發布，只做：同步 5090 昨晚成果 → 看信箱 → 列新上傳 → 本機建置檢查。

$repo = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io"
Set-Location $repo

Write-Host "== 同步 5090 昨晚成果 ==" -ForegroundColor Cyan
$before = (git rev-parse HEAD).Trim()
git pull --rebase --autostash
$after = (git rev-parse HEAD).Trim()

Write-Host "`n== 5090 昨晚（自上次同步以來）的 commit ==" -ForegroundColor Cyan
if ($before -eq $after) { Write-Host "（無新 commit）" } else { git log --oneline "$before..$after" }

Write-Host "`n== 信箱：5090 -> 3060 最新訊息（注意有無 BLOCKED）==" -ForegroundColor Cyan
Get-Content "$repo\tasks\handoff\5090-to-3060.md" -TotalCount 14 -Encoding UTF8

Write-Host "`n== 昨晚新上傳的 YouTube（yt_uploaded.csv 末 5 列）==" -ForegroundColor Cyan
Get-Content "$repo\video-pipeline\yt_uploaded.csv" -Tail 5 -Encoding UTF8

Write-Host "`n== 本機 Hugo 建置檢查（可選；Actions 已自動部署）==" -ForegroundColor Cyan
if (Get-Command hugo -ErrorAction SilentlyContinue) {
    hugo --buildFuture --quiet
    if ($LASTEXITCODE -eq 0) { Write-Host "Hugo 建置 OK" -ForegroundColor Green }
    else { Write-Host "Hugo 建置有錯，請檢查上方訊息" -ForegroundColor Red }
} else {
    Write-Host "(本機沒有 hugo，略過；GitHub Actions 仍會建置並部署)"
}

Write-Host "`n發布為自動：push 到 main 後由 GitHub Actions 部署。" -ForegroundColor Green
Write-Host "  部署狀態：https://github.com/aweholy777/aweholy777.github.io/actions"
Write-Host "  網站    ：https://cmtc.tw/"
