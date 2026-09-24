# AI Handover: QT Website and YouTube Uploader

Read this file first when taking over this repository. It describes the live
Mac setup and overrides historical notes about the old Windows/dual-machine
workflow where they conflict. Do not read, print, commit, or transmit OAuth
credentials.

## Current State

- Repository path: `/Users/haoguozi/qtproject`
- Site: `cmtc.tw`, a Hugo static site using the `mainroad` theme and GitHub
  Pages deployment. Pushing `main` triggers the site deployment.
- Upload owner: this Mac. The old Windows scheduled task `QT-Upload-5090` was
  disabled on 2026-09-25.
- Mac scheduler: `com.cmtc.qtupload` is installed in
  `~/Library/LaunchAgents/` and runs once per hour at minute `05`.
- Upload rate: one video per run, rolling 24-hour cap of 24.
- The whole video catalog has already been generated. Do not restart video
  generation unless new QT articles are added.
- Upload counts change every hour. Treat `video-pipeline/yt_uploaded.csv` as
  the authoritative upload record; `tasks/progress/` contains derived
  snapshots only. The whole video catalog has already been generated.

## Read These Files Next

1. `CLAUDE.md`: repository-wide safety, content, and validation rules.
2. `tasks/mac-handover/README.md`: macOS uploader commands, recovery steps,
   launchd details, and rollback.
3. `video-pipeline/README.md`: video rendering and subtitle implementation.
4. `HANDOFF.md` and `新機接手說明.md`: historical background only. They may
   contain retired Windows paths and machine names; never follow them as live
   operating instructions.

`tasks/影片生成專案-完整脈絡.md` is useful background, but much of it describes
the retired dual-machine setup. Do not reactivate Windows jobs based on it.

## Daily Operation

The scheduler normally needs no help. Inspect it with:

```bash
cd /Users/haoguozi/qtproject
launchctl list | grep qtupload
tail -40 ~/upload_mac.log
tail -3 video-pipeline/yt_uploaded.csv
git status --short
```

Expected scheduler label:

```text
com.cmtc.qtupload
```

For a non-uploading health check:

```bash
bash tasks/mac-handover/upload_mac.sh --check
```

It reports the Python environment, local video queue, CSV count, credentials,
recent uploads, Git identity, Git remote, and a non-writing Git push preflight.

For a deliberate one-video manual run, use only when the Windows task remains
disabled:

```bash
bash tasks/mac-handover/upload_mac.sh
```

The uploader pulls the shared CSV, selects the next unuploaded `head/*.mp4`,
uploads one video, updates `yt_uploaded.csv` and `data/qtvideos.json`, commits
and pushes. It has a five-minute cross-machine guard and archives uploaded
files into `video-output/head/old/`.

## Scheduling and Recovery

The modern macOS command is `bootstrap`, not the legacy `launchctl load`.
The installer handles this when run from Terminal.app:

```bash
bash tasks/mac-handover/install_mac.sh --load
launchctl list | grep qtupload
```

If the job must be stopped, run:

```bash
launchctl bootout gui/$(id -u)/com.cmtc.qtupload
```

Do not enable the Windows task while the Mac job is enabled. If a rollback is
required, stop the Mac job first, then enable `QT-Upload-5090` on Windows.

Codex-style sandbox shells may be unable to access the GUI launchd domain and
can report `Input/output error` even with a valid plist. In that case, run the
installer from Terminal.app; do not change plist permissions or add `sudo`.

The repository must remain under `/Users/haoguozi/qtproject`, not Desktop,
Documents, or Downloads. macOS TCC can prevent a background job from reading
those protected directories.

## Git and Local State

- Git remote uses SSH: `git@github.com:aweholy777/aweholy777.github.io.git`.
- The Mac SSH key authenticates as `aweholy777`.
- Before edits or manual uploads, pull first:

  ```bash
  git pull --rebase --autostash
  ```

- Keep local tool settings under `.claude/` untouched unless the user
  explicitly says otherwise.
- Never commit `video-pipeline/client_secret.json`, `video-pipeline/yt_token.json`,
  `video-output/`, `.venv/`, `.uv-cache/`, or `.uv-python/`.
- The working tree may become dirty after an upload only when a derived progress
  table is regenerated. Commit only the intended files; never use a blanket
  `git add -A` for uploader maintenance.

## Python Environment

The uploader uses `.venv` with Python 3.12 and Google API packages. The venv
was rebuilt after the repository moved from Desktop. Its interpreter may use an
absolute path, so a future directory move can invalidate it.

Run the installer to repair normal path issues without deleting files:

```bash
bash tasks/mac-handover/install_mac.sh
```

If `.venv/bin/python -V` still fails after the installer attempts repair, stop
and ask before rebuilding `.venv`, because rebuilding replaces that directory.

## Critical Content and Pipeline Rules

- QT source lives in `content/daily-qt/ntqt/` and `content/daily-qt/otqt/`.
  Each article requires `title`, `date`, and `draft` front matter and the fixed
  four-section QT structure.
- New and Old Testament index pages are book-order indexes. The index builder
  retains only the most recent date for a duplicate normalized passage while
  preserving old article files.
- Articles no longer embed YouTube shortcodes. The central video library is
  `/qt-video/` and is built from `data/qtvideos.json`.
- Do not change video settings without a specific request and isolated testing:
  25 fps, `audio_scale=0.8`, and SageAttention are established production
  settings. Lowering fps breaks lip synchronization.
- `video-pipeline/yt_uploaded.csv` is the single source of truth for upload
  deduplication. Never hand-edit it casually and never delete generated videos
  that are not already represented there.

## Change Discipline

- Build/content changes should follow the detailed repository rules in
  `AGENTS.md`; repetitive work across more than five files should be planned
  and delegated through `tasks/<job>/` rather than performed blindly.
- `public/` is generated output. Do not hand-edit it.
- Use the pinned Hugo version and normal repository validation instructions
  from `AGENTS.md`/`HANDOFF.md` when changing website content.
- Treat every credential, token, personal testimony, and prayer request as
  sensitive data. Keep it out of commits, logs, and external model prompts.

## Fast Incident Triage

| Symptom | First check | Safe next action |
| --- | --- | --- |
| No recent upload | `tail -40 ~/upload_mac.log` | Run `upload_mac.sh --check`; inspect the reported pause, cap, Git, credentials, and any recovered uploader lock. |
| Queue shows zero | `ls video-output/head/*.mp4 | wc -l` | Confirm the local video archive exists; do not regenerate videos. |
| Push fails | `upload_mac.sh --check` | Confirm SSH remote and `ssh -T git@github.com`; do not replace credentials without approval. |
| Job absent | `launchctl list | grep qtupload` | Run `install_mac.sh --load` from Terminal.app. |
| Job needs emergency stop | `launchctl bootout gui/$(id -u)/com.cmtc.qtupload` | Verify it is absent before considering Windows rollback. |

This document is intentionally operational rather than historical. Update it
whenever machine ownership, scheduling, authentication, or the upload contract
changes.
