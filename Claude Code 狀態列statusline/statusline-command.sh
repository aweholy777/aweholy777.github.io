#!/usr/bin/env bash
# ~/.claude/statusline-command.sh
# Claude Code status line — dual-account quota + context bar + git info

# 加值：4 色漸層 context bar / Git 分支 + 增刪 / 最後訊息時間（per-session）

input=$(cat)

# --- 解析欄位 ---
five_pct=$(echo    "$input" | jq -r '.rate_limits.five_hour.used_percentage  // empty')
five_reset=$(echo  "$input" | jq -r '.rate_limits.five_hour.resets_at        // empty')
week_pct=$(echo    "$input" | jq -r '.rate_limits.seven_day.used_percentage  // empty')
week_reset=$(echo  "$input" | jq -r '.rate_limits.seven_day.resets_at        // empty')
ctx_used=$(echo   "$input" | jq -r '.context_window.used_percentage         // empty')
model_name=$(echo "$input" | jq -r '.model.display_name // .model.id // ""')
effort=$(jq -r '.effortLevel // empty' "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json" 2>/dev/null)
cwd=$(echo        "$input" | jq -r '.workspace.current_dir // .cwd // ""')
session_id=$(echo "$input" | jq -r '.session_id // ""')

# --- 90% 手動交接守門員 ---
if [ -n "$session_id" ] && [ -x "$HOME/.claude/scripts/quota-handoff-guard.py" ]; then
  ( printf '%s' "$input" | "$HOME/.claude/scripts/quota-handoff-guard.py" >/dev/null 2>&1 ) &
fi

# --- 剩餘 ctx（顯示「剩多少」而非「用多少」）---
ctx_rem=""
if [ -n "$ctx_used" ]; then
  ctx_rem=$(echo "$ctx_used" | awk '{printf "%.0f", 100 - $1}')
fi

# --- 5h 剩餘 ---
five_rem=""
if [ -n "$five_pct" ]; then
  five_rem=$(echo "$five_pct" | awk '{printf "%.0f", 100 - $1}')
fi

# --- 專案名稱 ---
dir_display=$(echo "$cwd" | awk -F'/' '{print $NF}')

# --- 當前時間 ---
now=$(date "+%H:%M")

# --- 重置時間格式：5h 用 HH:MM，7d 用 M/D HH:MM ---
fmt_reset() {
  local epoch="$1"
  [ -z "$epoch" ] && echo "" && return
  date -r "$epoch" "+%H:%M" 2>/dev/null \
    || date -d "@$epoch" "+%H:%M" 2>/dev/null \
    || echo ""
}
fmt_reset_date() {
  local epoch="$1"
  [ -z "$epoch" ] && echo "" && return
  date -r "$epoch" "+%-m/%-d %H:%M" 2>/dev/null \
    || date -d "@$epoch" "%-m/%-d %H:%M" 2>/dev/null \
    || echo ""
}
five_next=$(fmt_reset "$five_reset")

# --- 顏色（ANSI 標準 + truecolor 4 色漸層）---
CYAN='\033[0;36m'
YEL='\033[0;33m'
GRN='\033[0;32m'
RED='\033[0;31m'
DIM='\033[2m'
RST='\033[0m'
# truecolor 漸層（4 段）— 用於 context bar
TC_GRN=$'\033[38;2;80;200;81m'
TC_YEL=$'\033[38;2;255;235;59m'
TC_OG=$'\033[38;2;255;152;0m'
TC_RD=$'\033[38;2;244;67;54m'

# 用量色彩：used_pct 越高越紅
color_used() {
  local v=$(echo "${1:-0}" | awk '{printf "%d", $1}')
  if   [ "$v" -ge 80 ]; then printf '%s' "$RED"
  elif [ "$v" -ge 50 ]; then printf '%s' "$YEL"
  else                        printf '%s' "$GRN"
  fi
}
# 剩餘色彩：rem_pct 越低越紅
color_rem() {
  local v=$(echo "${1:-100}" | awk '{printf "%d", $1}')
  if   [ "$v" -le 20 ]; then printf '%s' "$RED"
  elif [ "$v" -le 50 ]; then printf '%s' "$YEL"
  else                        printf '%s' "$GRN"
  fi
}

# --- 帳號偵測（由 CLAUDE_CONFIG_DIR 判斷）---
ccfg="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
case "$ccfg" in
  "$HOME/.claude")   acct_n="1"; acct_badge="①" ;;
  "$HOME/.claude-2") acct_n="2"; acct_badge="②" ;;
  *)                 acct_n="?"; acct_badge="$(basename "$ccfg")" ;;
esac

# --- 寫入本帳號 5h/7d 用量到共用快取（供另一帳號的 status line 讀）---
qdir="$HOME/.claude-quota-cache"
mkdir -p "$qdir" 2>/dev/null
if [ -n "$five_pct" ] || [ -n "$week_pct" ]; then
  printf '{"five":%s,"week":%s,"five_reset":%s,"week_reset":%s,"ts":%s}' \
    "${five_pct:-null}" "${week_pct:-null}" "${five_reset:-null}" "${week_reset:-null}" "$(date +%s)" \
    > "$qdir/$acct_n.json" 2>/dev/null || true
fi

# --- 時間進度條：實心=已過時間，空格=剩餘時間，W 格寬 ---
# time_bar <reset_epoch> <window_seconds> <W>
time_bar() {
  local reset_ep="$1" window="$2" W="${3:-8}"
  local remaining=$(( reset_ep - now_epoch ))
  [ "$remaining" -lt 0 ] && remaining=0
  [ "$remaining" -gt "$window" ] && remaining=$window
  local elapsed=$(( window - remaining ))
  local filled=$(echo "$elapsed $window $W" | awk '{f=int($1/$2*$3+0.5); if(f>$3)f=$3; print f}')
  local empty=$(( W - filled ))
  local b=""
  for i in $(seq 1 "$filled"); do b="${b}█"; done
  for i in $(seq 1 "$empty");  do b="${b}░"; done
  printf '%s' "$b"
}

# --- 雙帳號 5h+7d 純數字並排（含 reset 時間）---
now_epoch=$(date +%s)
acct_block=""
for n in 1 2; do
  if [ "$n" = "$acct_n" ]; then
    a_five="$five_pct"; a_week="$week_pct"
    a_reset="$five_reset"; a_wreset="$week_reset"; a_age=0
  else
    qf="$qdir/$n.json"
    [ -f "$qf" ] || continue
    a_five=$(jq -r '.five // empty' "$qf" 2>/dev/null)
    a_week=$(jq -r '.week // empty' "$qf" 2>/dev/null)
    a_reset=$(jq -r '.five_reset // empty' "$qf" 2>/dev/null)
    a_wreset=$(jq -r '.week_reset // empty' "$qf" 2>/dev/null)
    qts=$(jq -r '.ts // 0' "$qf" 2>/dev/null)
    a_age=$(( now_epoch - ${qts:-0} ))
  fi
  [ -z "$a_five" ] && [ -z "$a_week" ] && continue

  badge=$([ "$n" = "1" ] && echo "①" || echo "②")
  mark=""; [ "$n" = "$acct_n" ] && mark="*"
  stale=""; [ "$a_age" -gt 7200 ] && [ "$n" != "$acct_n" ] && stale="$DIM"
  a_reset_i=$(echo "${a_reset:-0}" | awk '{printf "%d", $1}')
  a_wreset_i=$(echo "${a_wreset:-0}" | awk '{printf "%d", $1}')
  a_next=$(fmt_reset "$a_reset")
  a_wnext=$(fmt_reset_date "$a_wreset")

  blk="${stale}${YEL}${badge}${mark}${RST}"

  # 5h：時間進度條（實心=已用時間，空格=剩餘時間）+ 用量% + →reset
  if [ -n "$a_five" ]; then
    if [ "$a_reset_i" -gt 0 ] && [ "$now_epoch" -ge "$a_reset_i" ]; then
      blk="${blk} ${DIM}5h${RST} ${GRN}↻${RST}"
    else
      vi=$(echo "$a_five" | awk '{printf "%d", $1}')
      c=$(color_used "$vi"); [ -n "$stale" ] && c="$DIM"
      bar=""
      [ "$a_reset_i" -gt 0 ] && bar="$(time_bar "$a_reset_i" 18000 8)"
      blk="${blk} ${DIM}5h${RST} ${stale}${bar:+${DIM}${bar}${RST} }${c}${vi}%%${RST}"
      [ -n "$a_next" ] && blk="${blk} ${DIM}→${a_next}${RST}"
    fi
  fi

  # 7d：時間進度條（7天窗口）+ 用量% + →reset日
  if [ -n "$a_week" ]; then
    wi=$(echo "$a_week" | awk '{printf "%d", $1}')
    cw=$(color_used "$wi"); [ -n "$stale" ] && cw="$DIM"
    wbar=""
    [ "$a_wreset_i" -gt 0 ] && wbar="$(time_bar "$a_wreset_i" 604800 8)"
    blk="${blk}  ${DIM}7d${RST} ${stale}${wbar:+${DIM}${wbar}${RST} }${cw}${wi}%%${RST}"
    [ -n "$a_wnext" ] && blk="${blk} ${DIM}→${a_wnext}${RST}"
  fi

  [ -n "$acct_block" ] && acct_block="${acct_block}    "
  acct_block="${acct_block}${blk}"
done

# --- 12-segment 4-color gradient bar (context usage) ---
bar12_gradient() {
  local used_pct="$1"
  [ -z "$used_pct" ] && return
  local used=$(echo "$used_pct" | awk '{printf "%d", $1}')
  local W=12
  local filled=$(( used * W / 100 ))
  [ $filled -gt $W ] && filled=$W
  local z1=$(( W / 4 )); local z2=$(( W / 2 )); local z3=$(( W * 3 / 4 ))
  local b=""
  for ((n=0; n<W; n++)); do
    if [ $n -lt $filled ]; then
      if   [ $n -lt $z1 ]; then b="${b}${TC_GRN}█"
      elif [ $n -lt $z2 ]; then b="${b}${TC_YEL}█"
      elif [ $n -lt $z3 ]; then b="${b}${TC_OG}█"
      else                      b="${b}${TC_RD}█"
      fi
    else
      b="${b}${DIM}░"
    fi
  done
  printf '%s' "${b}${RST}"
}

# --- 終端寬度 ---
cols="${COLUMNS:-$(tput cols 2>/dev/null || echo 120)}"

# ============================================================
# 寬模式（>= 80 cols）— 雙行顯示：L1 資源 / L2 工作狀態
# ============================================================
if [ "$cols" -ge 80 ]; then
  # ── L1：HH:MM ①/② dirname [model·effort]  ctx %   ① 5h % →reset  7d %    ② 5h % →reset  7d %
  L1=$(printf "${DIM}%s${RST}  ${YEL}%s${RST}  ${CYAN}%s${RST}" "$now" "$acct_badge" "$dir_display")
  if [ -n "$model_name" ]; then
    model_str="$model_name"
    [ -n "$effort" ] && model_str="${model_str}·${effort}"
    L1="${L1}$(printf "  ${DIM}[%s]${RST}" "$model_str")"
  fi

  # ctx：純數字
  if [ -n "$ctx_rem" ]; then
    c=$(color_rem "$ctx_rem")
    L1="${L1}$(printf "  ${DIM}ctx${RST} ${c}%s%%${RST}" "$ctx_rem")"
  fi

  # 雙帳號並排（reset 時間已嵌入各帳號 block）
  [ -n "$acct_block" ] && L1="${L1}$(printf "    %b" "$acct_block")"

  # 90% 交接警告
  if [ -n "$five_pct" ] && [ "$(echo "$five_pct" | awk '{printf "%d", $1}')" -ge 90 ]; then
    L1="${L1}$(printf "  ${RED}⚠ 交給Codex${RST}")"
  fi

  printf '%b\n' "$L1"

  # ── L2：📝 last_msg  ⎇ branch* +N/-N  codex info
  L2=""

  # 最後訊息時間（per-session）
  if [ -n "$session_id" ]; then
    msg_file="$HOME/.claude/last-session-msg-${session_id}"
    if [ -f "$msg_file" ]; then
      last_msg=$(cat "$msg_file" 2>/dev/null)
      [ -n "$last_msg" ] && L2="${DIM}📝 ${last_msg}${RST}"
    fi
  fi

  # Git 分支 + dirty + 增刪行數
  if git_top=$(git rev-parse --show-toplevel 2>/dev/null); then
    br=$(git branch --show-current 2>/dev/null)
    if [ -n "$br" ]; then
      dirty=""
      git diff-index --quiet HEAD -- 2>/dev/null || dirty="*"
      [ -z "$dirty" ] && [ -n "$(git ls-files --others --exclude-standard 2>/dev/null | head -1)" ] && dirty="*"
      git_block="${CYAN}⎇ ${br}${dirty}${RST}"

      stat=$(git diff --shortstat HEAD 2>/dev/null)
      ins=$(echo "$stat" | grep -oE '[0-9]+ insertion' | grep -oE '[0-9]+')
      del=$(echo "$stat" | grep -oE '[0-9]+ deletion' | grep -oE '[0-9]+')
      if [ -n "$ins" ] || [ -n "$del" ]; then
        diff_str=""
        [ -n "$ins" ] && diff_str="${GRN}+${ins}${RST}"
        [ -n "$ins" ] && [ -n "$del" ] && diff_str="${diff_str}${DIM}/${RST}"
        [ -n "$del" ] && diff_str="${diff_str}${RED}-${del}${RST}"
        git_block="${git_block} ${diff_str}"
      fi

      [ -n "$L2" ] && L2="${L2}  ${git_block}" || L2="${git_block}"
    fi
  fi

  # Codex job status（沿用既有）
  codex_info=$("${CLAUDE_CONFIG_DIR:-$HOME/.claude}/scripts/codex-statusline.sh" 2>/dev/null)
  if [ -n "$codex_info" ]; then
    [ -n "$L2" ] && L2="${L2}  ${DIM}${codex_info}${RST}" || L2="${DIM}${codex_info}${RST}"
  fi

  [ -n "$L2" ] && printf '%b\n' "$L2"

# ============================================================
# 窄模式（< 80 cols）— 單行精簡
# ============================================================
else
  printf "${DIM}%s${RST} ${CYAN}%s${RST}" "$now" "$dir_display"
  [ -n "$ctx_rem" ] && printf " ${DIM}ctx${RST}$(color_rem "$ctx_rem")%s%%${RST}" "$ctx_rem"
  [ -n "$five_next" ] && printf " ${DIM}→%s${RST}" "$five_next"
  [ -n "$acct_block" ] && printf " %b" "$acct_block"
  [ -n "$five_pct" ] && [ "$(echo "$five_pct" | awk '{printf "%d", $1}')" -ge 90 ] && printf " ${RED}!${RST}"
  printf '\n'
fi
