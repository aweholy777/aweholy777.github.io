# qt.ps1 — 3060(軍師) 常用快捷：同步讀信箱 / 一鍵推送（提交前會先列出變更讓你確認）
# 載入一次：  . .\tasks\5090-migration\qt.ps1
# 之後可用：  qt-sync          # 同步並看 5090 最新回報
#            qt-push "訊息"    # 清鎖→列出變更→你確認→commit→pull→push
#            qt-status        # 看本機與遠端差距、有無未提交
$script:QtRepo = "C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io"

function qt-sync {
    Set-Location $script:QtRepo
    Remove-Item .git\index.lock -Force -ErrorAction SilentlyContinue
    git pull --rebase --autostash
    Write-Host "`n===== 5090 -> 3060 最新回報（最新在最上）=====" -ForegroundColor Cyan
    Get-Content tasks\handoff\5090-to-3060.md -TotalCount 25 -Encoding UTF8
}

function qt-push {
    param([string]$msg = "update $(Get-Date -Format 'yyyy-MM-dd HH:mm')")
    Set-Location $script:QtRepo
    Remove-Item .git\index.lock -Force -ErrorAction SilentlyContinue
    git add -A
    Write-Host "`n== 即將提交以下變更（請看清楚有沒有不該進 repo 的檔）==" -ForegroundColor Cyan
    git status --short
    $ans = Read-Host "`n確定推送？(直接按 Enter = 是 / 輸入 n = 取消)"
    if ($ans -eq 'n' -or $ans -eq 'N') {
        Write-Host "已取消。變更仍在（未提交）。如要排除某檔，先處理再重跑 qt-push。" -ForegroundColor Yellow
        return
    }
    git commit -m "$msg"
    git pull --rebase --autostash
    if ($LASTEXITCODE -ne 0) { Write-Host "pull/rebase 出問題，先別 push，把畫面貼給 Claude。" -ForegroundColor Red; return }
    git push
    if ($LASTEXITCODE -eq 0) { Write-Host "已推送：$msg" -ForegroundColor Green }
    else { Write-Host "push 失敗，把畫面貼給 Claude。" -ForegroundColor Red }
}

function qt-status {
    Set-Location $script:QtRepo
    Remove-Item .git\index.lock -Force -ErrorAction SilentlyContinue
    $null = git fetch origin main 2>&1
    Write-Host "== 未提交的變更 ==" -ForegroundColor Cyan; git status --short
    Write-Host "== 本機 vs 遠端（左=遠端超前 右=本機超前）==" -ForegroundColor Cyan
    git rev-list --left-right --count origin/main...HEAD
}
