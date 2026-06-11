@echo off
set LOG=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io\video-pipeline\_cc_tools.txt
set REPO=C:\Users\aweholy\Desktop\clone2026010\aweholy777.github.io
set CD=%USERPROFILE%\.claude
echo install start > "%LOG%"

echo [1/6] backup settings.json >> "%LOG%"
copy /y "%CD%\settings.json" "%CD%\settings.json.bak-cctools" >> "%LOG%" 2>&1

echo [2/6] install statusline script + settings >> "%LOG%"
copy /y "%REPO%\Claude Code 狀態列statusline\statusline-command.sh" "%CD%\statusline-command.sh" >> "%LOG%" 2>&1
copy /y "%REPO%\video-pipeline\_new_settings.json" "%CD%\settings.json" >> "%LOG%" 2>&1

echo [3/6] install ccc skill folder >> "%LOG%"
if not exist "%CD%\skills\ccc-switch" mkdir "%CD%\skills\ccc-switch"
xcopy /e /y /q "%REPO%\ccc — AI 多帳號一鍵切換工具ccc-switch\*" "%CD%\skills\ccc-switch\" >> "%LOG%" 2>&1

echo [4/6] install fzf via winget >> "%LOG%"
where fzf >nul 2>&1 || winget install --id junegunn.fzf -e --accept-source-agreements --accept-package-agreements >> "%LOG%" 2>&1

echo [5/6] run ccc install.sh via Git Bash >> "%LOG%"
"C:\Program Files\Git\bin\bash.exe" -lc "export PATH=\"$LOCALAPPDATA/Microsoft/WinGet/Links:$PATH\"; bash ~/.claude/skills/ccc-switch/scripts/install.sh" >> "%LOG%" 2>&1

echo [6/6] set CLAUDE_CONFIG_DIR_2 + test statusline >> "%LOG%"
setx CLAUDE_CONFIG_DIR_2 "%USERPROFILE%\.claude-2" >> "%LOG%" 2>&1
echo --- statusline test --- >> "%LOG%"
echo {"model":{"display_name":"test"},"workspace":{"current_dir":"%REPO:\=/%"},"context_window":{"used_percentage":42}} | "C:\Program Files\Git\bin\bash.exe" "%CD%\statusline-command.sh" >> "%LOG%" 2>&1
echo statusline_exit=%errorlevel% >> "%LOG%"
echo DONE >> "%LOG%"
