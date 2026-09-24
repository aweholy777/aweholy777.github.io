#!/bin/bash
# install_mac.sh — 一次性安裝：Python 環境（uv）+ launchd 每小時排程
#
# 用法：bash tasks/mac-handover/install_mac.sh
#
# 做完之後：先手動測試 `bash tasks/mac-handover/upload_mac.sh --check` 與 `... upload_mac.sh`，
#          確認成功後才 load launchd 排程（本腳本最後會 load；不想立刻啟用就先註解掉）。

set -uo pipefail

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
echo "== 建立 .venv（Python 3.12）"
uv venv .venv --python 3.12 || exit 1
echo "== 安裝上傳套件"
uv pip install --python "$REPO/.venv/bin/python" \
  google-api-python-client google-auth google-auth-oauthlib || exit 1

# 3) 憑證檢查（不進 git，需手動複製，見 README 第 2 步）
for f in client_secret.json yt_token.json; do
  if [ -f "$REPO/video-pipeline/$f" ]; then
    echo "   ✓ video-pipeline/$f"
  else
    echo "   ✗ 缺 video-pipeline/$f（見 README.md 第 2 步：從 Windows 用 AirDrop/隨身碟複製）"
  fi
done

# 4) 安裝 launchd 排程（每小時 :05；Mac 睡著時喚醒後補跑）
mkdir -p "$HOME_DIR/Library/LaunchAgents"
sed -e "s|__REPO__|$REPO|g" -e "s|__HOME__|$HOME_DIR|g" "$HERE/com.cmtc.qtupload.plist" > "$PLIST"
launchctl unload "$PLIST" 2>/dev/null
launchctl load "$PLIST"
echo "== launchd 已載入：$PLIST"
launchctl list | grep -i qtupload || true

echo
echo "下一步："
echo "  1) bash $HERE/upload_mac.sh --check     # 看環境、待傳數、憑證"
echo "  2) bash $HERE/upload_mac.sh             # 手動傳 1 支確認 OK"
echo "  3) 確認 Windows 那台已停掉排程（schtasks /change /tn \"QT-Upload-5090\" /disable）"
echo "  4) 之後每小時 :05 會自動跑；log 在 ~/upload_mac.log"
