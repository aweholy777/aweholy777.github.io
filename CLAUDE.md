# Repository Operating Rules

This repository powers cmtc.tw, a Hugo site with a YouTube QT video library.
The live owner is the Mac at `/Users/haoguozi/qtproject`. Read
`AI_HANDOVER.md` first for the current operating state; it takes precedence
over historical handoff documents and any Windows-specific instructions.

## Current Production Flow

- GitHub Pages deploys automatically after a push to `main`.
- `com.cmtc.qtupload` runs on this Mac at minute `05` each hour and uploads at
  most one video per run, with a rolling 24-hour cap of 24.
- `video-pipeline/yt_uploaded.csv` is the sole upload authority. Never
  casually edit it or run another machine's uploader at the same time.
- The video catalog has already been rendered. `video-output/head/` is the
  upload queue; do not regenerate or delete it without an explicit request.

## Safety Rules

- Never read, print, commit, transmit, or replace
  `video-pipeline/client_secret.json` or `video-pipeline/yt_token.json`.
- Preserve `video-output/`, `.venv/`, `.uv-python/`, and `.claude/` unless the
  user explicitly requests their removal. `public/` and `.uv-cache/` are
  generated cache and may be rebuilt.
- Before edits or a manual upload, run `git pull --rebase --autostash` unless
  a current uploader run owns the repository.
- Do not use `git add -A` for uploader maintenance. Commit only intended
  files, normally `video-pipeline/yt_uploaded.csv`, `data/qtvideos.json`, and
  regenerated progress tables.
- Do not enable a Windows uploader while the Mac launchd job is enabled.

## Content Rules

- QT source: `content/daily-qt/ntqt/` and `content/daily-qt/otqt/`.
- Every QT article needs `title`, `date`, and `draft` front matter, followed
  by the established four-section QT structure.
- Book-order indexes retain only the newest article for duplicate normalized
  passages; old article files remain available and must not be batch-deleted.
- Articles do not embed YouTube shortcodes. The central library is
  `/qt-video/`, generated from `data/qtvideos.json`.
- Preserve established production video settings: 25 fps, `audio_scale=0.8`,
  and SageAttention. Test isolated changes before altering them.

## Validation

- Run `bash tasks/mac-handover/upload_mac.sh --check` for uploader health;
  it does not upload a video.
- Run `bash -n tasks/mac-handover/upload_mac.sh` after changing the macOS
  uploader script.
- Build the Hugo site before publishing content or template changes when the
  local Hugo toolchain is available. Never hand-edit `public/`.
- Treat credentials, personal testimony, and prayer requests as sensitive;
  keep them out of logs, commits, and external prompts.

## Historical Files

`HANDOFF.md`, `新機接手說明.md`, and old Windows scripts under `tasks/` are
background material. They can describe retired 5090, 3060, or Windows flows.
For live operations, follow `AI_HANDOVER.md` and
`tasks/mac-handover/README.md` instead.
