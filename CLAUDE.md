# Repository Operating Rules

This repository powers **cmtc.tw** (Hugo site) and the YouTube QT uploader.

## Read this first

**`AGENTS.md` is the single authoritative handover document** — current project state,
hard rules, the daily 當日QT pipeline, Cloudflare deployment, `/qt-generator/` APIs,
and the troubleshooting table. Read it before touching anything.

`AI_HANDOVER.md`, `HANDOFF.md`, `新機接手說明.md`, `CLAUDE.local.md` are **historical
background only**. Several of them wrongly claim GitHub Pages deployment; the live
deployment is **Cloudflare Pages** (project `cmtc`, `HUGO_VERSION=0.144.2`).

## Non-negotiables

- Before any edit: `git pull --rebase --autostash origin main` (a Mac pushes hourly).
- Before any push on Windows: `gh auth switch --user aweholy777`.
- Never `git add -A`; commit only the files you touched.
- Verify with the repo-root `hugo.exe --buildFuture` (pinned to 0.144.2). Zero errors or it is not done.
- `public/` is generated output — never hand-edit or commit it.
- Never read, print, commit, or transmit `video-pipeline/client_secret.json`
  or `video-pipeline/yt_token.json`.
- Do not enable the Windows uploader while the Mac launchd job
  (`com.cmtc.qtupload`, minute `05`, one video per run, 24h cap 24) is enabled.
  `video-pipeline/yt_uploaded.csv` is the sole upload authority.

## Claude-specific notes

- If the sandbox cannot reach the GUI launchd domain (`Input/output error` with a valid
  plist), ask the user to run the installer from Terminal.app — do not add `sudo`
  or change plist permissions.
- Batch content edits over 5 files: write `tasks/<name>/plan.md`, delegate, and verify
  with `git diff --stat` instead of editing file by file.
- QT articles keep the fixed four-section structure
  (`1. 經文誦讀` → `2. 今天默想經文` → `3. 分享默想經文` → `4. 今天的回應`)
  and `title` / `date` / `draft` front matter.
