#!/bin/bash
# upload_mac.sh — QT 滴傳（macOS 版，對應 Windows 的 tasks/5090-migration/upload_5090.ps1）
#
# 每小時跑一次、每次只傳 1 支影片到 YouTube，並把成果（yt_uploaded.csv、data/qtvideos.json）
# push 回 main，觸發 GitHub Actions 更新網站。
#
# ⚠️ 同一時間只能有一台機器在跑上傳（兩台同時跑會重複上傳同一支影片）。
#    由 launchd 的 com.cmtc.qtupload 每小時 :05 呼叫；安裝方式見同目錄 README.md。
#
# 用法：
#   bash tasks/mac-handover/upload_mac.sh           # 正常一趟（排程也是跑這個）
#   bash tasks/mac-handover/upload_mac.sh --check   # 只檢查環境與進度，不上傳
#
# 日誌：~/upload_mac.log

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
PY="$REPO/.venv/bin/python"
LOG="$HOME/upload_mac.log"
CSV="$REPO/video-pipeline/yt_uploaded.csv"
PAUSE_FLAG="$HOME/upload_pause.flag"
LOCK="$HOME/.qt-upload-mac.lock"
DAILY_CAP=24
RECENT_GUARD_MIN=5   # csv 顯示 N 分鐘內有上傳紀錄 → 視為另一台機器在跑，跳過（防重複）

PY3="/usr/bin/python3"
[ -x "$PY3" ] || PY3="$(command -v python3 || echo /usr/bin/python3)"

CHECK_ONLY=0
[ "${1:-}" = "--check" ] && CHECK_ONLY=1

log() { printf '%s  %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" | tee -a "$LOG"; }

# 過去 24 小時已傳幾支 + 距最近一次上傳幾分鐘（讀 csv 時間戳，純本機計算）
last24=0
lastmin=999999
if [ -f "$CSV" ]; then
  read -r last24 lastmin < <("$PY3" - "$CSV" <<'PYEOF'
import csv, sys
from datetime import datetime, timedelta
cut = datetime.now() - timedelta(hours=24)
n, last = 0, None
with open(sys.argv[1], encoding="utf-8") as f:
    for row in csv.reader(f):
        if len(row) < 4 or row[0].strip() in ("", "md_path"):
            continue
        try:
            t = datetime.fromisoformat(row[3].strip())
        except Exception:
            continue
        if t >= cut:
            n += 1
        if last is None or t > last:
            last = t
print(n, int((datetime.now() - last).total_seconds() // 60) if last else 999999)
PYEOF
  )
fi

if [ "$CHECK_ONLY" = "1" ]; then
  log "=== 檢查模式（不上傳）==="
  log "repo        : $REPO"
  log "python      : $("$PY" -V 2>&1 || echo '缺 .venv → 先跑 install_mac.sh')"
  log "git         : $(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>&1) / $(git -C "$REPO" log --oneline -1 2>&1)"
  log "工作樹 dirty: $(git -C "$REPO" status --porcelain 2>/dev/null | wc -l | tr -d ' ') 個檔案"
  log "待傳 mp4    : $(ls "$REPO/video-output/head"/*.mp4 2>/dev/null | wc -l | tr -d ' ') 支（head/）"
  log "已歸檔 mp4  : $(ls "$REPO/video-output/head/old"/*.mp4 2>/dev/null | wc -l | tr -d ' ') 支（head/old/）"
  log "csv 已上傳  : $(( $(wc -l < "$CSV" 2>/dev/null || echo 1) - 1 )) 支"
  log "憑證        : client_secret=$([ -f "$REPO/video-pipeline/client_secret.json" ] && echo 有 || echo 缺) / yt_token=$([ -f "$REPO/video-pipeline/yt_token.json" ] && echo 有 || echo 缺)"
  log "過去24小時  : $last24 支（上限 $DAILY_CAP）／最近一次 $lastmin 分鐘前"
  exit 0
fi

# 同一台機器不重入
if ! mkdir "$LOCK" 2>/dev/null; then log "上一趟還在跑，本次跳過。"; exit 0; fi
trap 'rmdir "$LOCK" 2>/dev/null' EXIT

cd "$REPO" || { log "找不到 repo：$REPO"; exit 1; }
log "=== 滴傳開始（macOS, DailyCap=$DAILY_CAP）==="

# 1. 同步（拿到最新 csv 與文章，跨機共用同一份權威清單）
git pull --rebase --autostash 2>&1 | tee -a "$LOG" | tail -2

# 2. 暫停旗標（碰到 YouTube 配額/上限錯誤就暫停 24h；內容為 unix 秒）
if [ -f "$PAUSE_FLAG" ]; then
  until_epoch="$(tr -dc '0-9' < "$PAUSE_FLAG")"
  if [ -n "$until_epoch" ] && [ "$until_epoch" -gt "$(date +%s)" ]; then
    log "暫停中（到 $(date -r "$until_epoch" '+%Y-%m-%d %H:%M')），本次跳過。"
    exit 0
  fi
  rm -f "$PAUSE_FLAG"
  log "暫停旗標已過期，恢復上傳。"
fi

# 3. 防重複保險：最近 N 分鐘內有上傳紀錄 → 可能另一台機器在跑
if [ "$lastmin" -lt "$RECENT_GUARD_MIN" ]; then
  log "最近 $lastmin 分鐘內有上傳紀錄（可能是另一台機器在跑）→ 本次跳過，避免重複上傳。"
  exit 0
fi

# 4. 每日上限（滾動 24 小時）
if [ "$last24" -ge "$DAILY_CAP" ]; then
  log "過去24小時已傳 $last24 支，已達 DailyCap=$DAILY_CAP，本次跳過。"
  exit 0
fi
log "過去24小時已傳 $last24 ／ DailyCap=$DAILY_CAP，繼續。"

# 5. 上傳 1 支（--no-push：發布由本腳本下面的 push 觸發 Actions）
log "上傳 YouTube（本次 1 支）..."
"$PY" video-pipeline/yt_publish.py --auto --no-push --limit 1 2>&1 | tee -a "$LOG"
up_exit="${PIPESTATUS[0]}"

if [ "$up_exit" = "2" ]; then
  echo $(( $(date +%s) + 86400 )) > "$PAUSE_FLAG"
  log "碰到 YouTube 配額/上限錯誤（exit=2），已寫暫停旗標，暫停 24 小時：$PAUSE_FLAG"
  exit 0
fi
if [ "$up_exit" != "0" ]; then
  log "上傳腳本回報非零（exit=$up_exit，非配額錯誤），本次無成果，留待下次重試。"
fi

# 6. 重新產生 QT 影音庫資料（data/qtvideos.json），隨本次上傳一起發布
"$PY" video-pipeline/build_qt_library.py 2>&1 | tee -a "$LOG" | tail -2

# 7. 只交 csv + 影音庫資料 push 回 main（push 即觸發 Actions 更新網頁）
git add video-pipeline/yt_uploaded.csv data/qtvideos.json >>"$LOG" 2>&1
git diff --name-only HEAD -- content/daily-qt | while IFS= read -r f; do
  [ -n "$f" ] && git add -- "$f"
done
if [ -n "$(git status --porcelain -- video-pipeline/yt_uploaded.csv data/qtvideos.json content/daily-qt)" ]; then
  git commit -m "mac upload: $(date '+%Y-%m-%d %H:%M')" >>"$LOG" 2>&1
  if git pull --rebase --autostash >>"$LOG" 2>&1; then
    if git push >>"$LOG" 2>&1; then
      log "已 push 本次上傳成果（已觸發 Actions 部署網頁）"
    else
      log "⚠️ git push 失敗，成果未上 main、網頁未更新，詳見 $LOG"
    fi
  else
    git rebase --abort >>"$LOG" 2>&1
    log "⚠️ git pull --rebase 失敗，已中止 push 以免推半套，詳見 $LOG"
  fi
else
  log "本次無新上傳（隊列沒有待傳影片，或本次失敗），未 push。"
fi

# 8. 歸檔：把「已上傳（在 csv 裡）」的 mp4 從 head/ 搬到 head/old/，騰出空間
#    head/old/ 不影響生成與上傳（生成端只掃 head/ 直屬檔案；csv 也會擋下重傳）
moved="$("$PY3" - "$CSV" "$REPO/video-output/head" <<'PYEOF'
import csv, re, shutil, sys
from pathlib import Path
keys = set()
with open(sys.argv[1], encoding="utf-8") as f:
    for row in csv.reader(f):
        if not row or not row[0]:
            continue
        m = re.search(r"daily-qt[/\\]([^/\\]+)[/\\]([^/\\]+)\.md$", row[0])
        if m:
            keys.add(f"{m.group(1)}_{m.group(2)}.mp4")
head = Path(sys.argv[2])
old = head / "old"
old.mkdir(exist_ok=True)
n = 0
for v in sorted(head.glob("*.mp4")):
    if v.name in keys:
        shutil.move(str(v), str(old / v.name))
        n += 1
print(n)
PYEOF
)"
log "歸檔已上傳 mp4 到 head/old/：${moved} 部"

# 9. 順手更新進度表（tasks/progress/_summary.txt 等）
"$PY3" tasks/progress/gen_progress.py >>"$LOG" 2>&1 && log "已更新 tasks/progress/ 進度表" || log "進度表更新失敗（不影響上傳）"

log "=== 完成 ==="
