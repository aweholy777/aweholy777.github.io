# Repository Operating Rules

This repository powers **cmtc.tw** (Hugo site) and, until the upload queue drains, the YouTube QT uploader.

## Read this first

**`AGENTS.md` is the single authoritative handover document.** It contains the full annotated
directory tree, what exists only on the local machine, current project state, hard rules, every
scheduled job, the daily 當日QT pipeline, the video pipeline, accounts/services, open items, and a
new-machine checklist. Read it before touching anything.

- `tasks/README.md` indexes the tooling folders.
- `更新網站SOP.md` is the human-facing manual.

There are no other handover documents. The pre-Cloudflare / dual-machine ones (`HANDOFF.md`,
`AI_HANDOVER.md`, `新機接手說明.md`, `遷移到Cloudflare指南.md`) were deleted on 2026-11-27 and only
live in git history. Anything they say about GitHub Pages, Vercel, a Windows uploader, or a
"3060 planner / 5090 executor" split is obsolete.

## Non-negotiables (summary — AGENTS.md §4 is the full list)

- Before any edit: `git pull --rebase --autostash origin main` (a Mac pushes hourly). Pull *before* `git add`.
- Before any push on Windows: `gh auth switch --user aweholy777`.
- Never `git add -A`; commit only the files you touched, by name.
- Verify with the repo-root `hugo.exe --minify --buildFuture` (pinned to 0.144.2; do not upgrade).
  Zero errors or it is not done.
- `public/`, `.venv/`, `video-output/`, `.claude/` are generated/local: never hand-edit or commit.
- Never read, print, commit, or transmit `video-pipeline/client_secret.json`,
  `video-pipeline/yt_token.json`, `video-pipeline/_new_settings.json`,
  `video-pipeline/_claude2_settings.json`, or any token/key/password.
- Do not delete files unless the user explicitly confirms.
- Reply to the user in Traditional Chinese (Taiwan usage; keep commands and tool names in English).
- Anything committed locally is pushed automatically at 00:05 by the daily-QT job — never commit
  locally what must not go public.

## Claude-specific notes

- `CLAUDE.local.md` (gitignored) holds machine-only notes; if it conflicts with `AGENTS.md`, `AGENTS.md` wins.
- Mac setup: if the sandbox cannot reach the GUI launchd domain (`Input/output error` with a valid
  plist), ask the user to run the installer from Terminal.app — do not add `sudo` or change plist
  permissions.
- Batch content edits over 5 files: write `tasks/<name>/plan.md` first (template in
  `tasks/_templates/`), then execute, and verify with `git diff --stat`.
- QT articles keep the fixed four-section structure
  (`1. 經文誦讀` → `2. 今天默想經文` → `3. 分享默想經文` → `4. 今天的回應`)
  and `title` / `date` / `draft` front matter.
