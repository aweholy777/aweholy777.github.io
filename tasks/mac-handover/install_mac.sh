#!/bin/bash
# install_mac.sh — 一次性安裝：Python 環境（uv）+ 產生 launchd 排程檔（每小時 :05）
#
# 用法：
#   bash tasks/mac-handover/install_mac.sh          # 只建立環境 + 寫入排程檔（**預設不啟用排程**）
#   bash tasks/mac-handover/install_mac.sh --load   # 額外啟用 launchd 排程（交接完成、Windows 已停掉才用）
#
# 為什麼預設不啟用：同一時間只能有一台機器在上傳。要等 Windows 那台的排程停掉之後才可以啟用。
# 前置：必須先完成 README 第 1 步（git pull），本檔案才會存在於工作目錄。
#
# 做完之後：先手動測試 `bash tasks/mac-handover/upload_mac.sh --check` 與 `... upload_mac.sh`，
#          確認成功、且 Windows 那台已停掉，才用 --load 啟用排程。

set -uo pipefail

DO_LOAD=0
for a in "$@"; do [ "$a" = "--load" ] && DO_LOAD=1; done
[ "${LOAD_LAUNCHD:-0}" = "1" ] && DO_LOAD=1

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
HOME_DIR="${HOME}"
PLIST="$HOME_DIR/Library/LaunchAgents/com.cmtc.qtupload.plist"

echo "== repo: $REPO"

# 0) 清掉可能被 Windows 換行（CRLF）污染的行尾——腳本本身與 upload_mac.sh
for f in "$HERE"/*.sh; do
  if grep -q $'\r' "$f" 2>/dev/null; then
    perl -i -pe 's/\r$//' "$f" && echo "   已修正行尾：$f"
  fi
done

# 1) 前置工具
command -v git >/dev/null 2>&1 || { echo "✗ 缺 git：先跑 xcode-select --install"; exit 1; }
if ! command -v uv >/dev/null 2>&1; then
  echo "✗ 缺 uv：請先執行  curl -LsSf https://astral.sh/uv/install.sh | sh  再跑一次本腳本"
  exit 1
fi

# 2) venv + 上傳所需套件（uv 會自己準備 Python 3.12）
cd "$REPO" || exit 1

# uv 的快取與 Python 下載目錄：優先用系統預設；不可寫（權限/沙盒）就改到 repo 內
pick_dir() { mkdir -p "$1" 2>/dev/null && [ -w "$1" ]; }

UV_CACHE_DIR="${UV_CACHE_DIR:-$HOME_DIR/Library/Caches/uv}"
if ! pick_dir "$UV_CACHE_DIR"; then
  echo "⚠️ uv 快取目錄不可寫：$UV_CACHE_DIR"
  ls -ldO "$HOME_DIR/.cache" "$HOME_DIR/.cache/uv" 2>&1 | sed 's/^/    /'
  UV_CACHE_DIR="$REPO/.uv-cache"
  if ! pick_dir "$UV_CACHE_DIR"; then
    echo "✗ $UV_CACHE_DIR 也不可寫。請先修權限再重跑："
    echo "    sudo chown -R \"$(id -un)\" \"$HOME_DIR/.cache\""
    echo "    sudo chflags -R nouchg \"$HOME_DIR/.cache\"      # 若 ls -lO 顯示 uchg"
    exit 1
  fi
  echo "   → 改用 repo 內的快取：$UV_CACHE_DIR"
fi
export UV_CACHE_DIR

UV_PYTHON_INSTALL_DIR="${UV_PYTHON_INSTALL_DIR:-$HOME_DIR/.local/share/uv/python}"
if ! pick_dir "$UV_PYTHON_INSTALL_DIR"; then
  UV_PYTHON_INSTALL_DIR="$REPO/.uv-python"
  pick_dir "$UV_PYTHON_INSTALL_DIR" || { echo "✗ $UV_PYTHON_INSTALL_DIR 不可寫"; exit 1; }
  echo "   → 改用 repo 內的 Python 安裝目錄：$UV_PYTHON_INSTALL_DIR"
fi
export UV_PYTHON_INSTALL_DIR
echo "== uv cache  : $UV_CACHE_DIR"
echo "== uv python : $UV_PYTHON_INSTALL_DIR"

# 已有 .venv 就沿用，不要重建（uv venv 對既有目錄會直接報錯；--load 重跑時更不該重建）
if [ -x "$REPO/.venv/bin/python" ]; then
  echo "== 已有 .venv，沿用（不重建）"
else
  echo "== 建立 .venv（Python 3.12）"
  uv venv .venv --python 3.12 || {
    echo "⚠️ 取不到 Python 3.12，改用系統 python3 建立 venv"
    uv venv .venv --python "$(command -v python3)" || exit 1
  }
fi

echo "== 安裝／確認上傳套件"
uv pip install --python "$REPO/.venv/bin/python" \
  google-api-python-client google-auth google-auth-oauthlib || exit 1
"$REPO/.venv/bin/python" -c "import googleapiclient, google.oauth2; print('   ✓ 套件可用：', googleapiclient.__name__)" || exit 1

# 3) 憑證檢查（不進 git，需手動複製，見 README 第 2 步）
for f in client_secret.json yt_token.json; do
  if [ -f "$REPO/video-pipeline/$f" ]; then
    echo "   ✓ video-pipeline/$f"
  else
    echo "   ✗ 缺 video-pipeline/${f}（見 README.md 第 2 步：從 Windows 用 AirDrop/隨身碟複製）"
  fi
done

# 4) 產生 launchd 排程檔（每小時 :05；Mac 睡著時喚醒後補跑）——預設只寫入，不啟用
mkdir -p "$HOME_DIR/Library/LaunchAgents"
sed -e "s|__REPO__|$REPO|g" -e "s|__HOME__|$HOME_DIR|g" "$HERE/com.cmtc.qtupload.plist" > "$PLIST"
echo "== 已寫入排程檔：$PLIST"

if [ "$DO_LOAD" = "1" ]; then
  launchctl unload "$PLIST" 2>/dev/null
  launchctl load "$PLIST"
  echo "== launchd 已啟用：每小時 :05 自動滴傳"
  launchctl list | grep -i qtupload || true
else
  echo "== 安全預設：排程**尚未啟用**（不會有任何自動上傳）。"
  echo "   確認 Mac 手動測試成功、且 Windows 那台排程已停掉後，再執行："
  echo "     launchctl load \"$PLIST\""
fi

echo
echo "下一步："
echo "  1) bash $HERE/upload_mac.sh --check     # 看環境、待傳數、憑證"
echo "  2) bash $HERE/upload_mac.sh             # 手動傳 1 支確認 OK"
echo "  3) 確認 Windows 那台已停掉排程（schtasks /change /tn \"QT-Upload-5090\" /disable）"
echo "  4) 啟用排程：launchctl load \"$PLIST\"（或重跑本腳本加 --load）"
echo "     之後每小時 :05 自動跑；log 在 ~/upload_mac.log"
