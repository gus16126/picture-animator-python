# External Integrations

**Analysis Date:** 2026-10-29

## APIs & External Services

**Media encoding:**
- FFmpeg command-line executable — encodes rendered temporary PNG frames to MP4, WebM, or GIF in `Animator.export_mp4()` in `app.py`.
  - SDK/Client: Python `subprocess.run()`.
  - Auth: none.
- The lookup sequence in `app.py` is a user-home `ffmpeg.exe` followed by the operating-system `PATH`.

**Image processing:**
- Pillow — locally decodes input images and renders frames in `app.py`; it makes no network requests.
  - SDK/Client: `PIL` imports declared in `app.py` and installed from `requirements.txt`.
  - Auth: none.

## Data Storage

**Databases:**
- None detected.

**File Storage:**
- Local filesystem only. Input pictures are read by `Animator.add_pictures()` in `app.py` and embedded as base64 strings in project data.
- `.paanim` projects are ZIP files containing `project.json`, written atomically via a temporary sibling file in `Animator.save_data()`.
- Label presets are persisted as local JSON at `label_presets.json` next to `app.py` by `Animator.persist_presets()`.
- Selected audio remains an external filesystem path inside the project JSON; it is not embedded in `.paanim` files.

**Caching:**
- In-memory image cache only: `Animator._img_cache` in `app.py`; it is cleared for new and opened projects.

## Authentication & Identity

**Auth Provider:**
- Not applicable. The app has no accounts, login, tokens, remote services, or identity layer.

## Monitoring & Observability

**Error Tracking:**
- None detected.

**Logs:**
- None detected. User-facing feedback is provided through Tkinter status text and `messagebox` dialogs in `app.py`.

## CI/CD & Deployment

**Hosting:**
- Not applicable; `README.md` describes a local desktop workflow.

**CI Pipeline:**
- None detected; no workflow/configuration files are present.

## Environment Configuration

**Required env vars:**
- None detected.

**Secrets location:**
- No secrets or secret-management configuration is detected. `.gitignore` only excludes Python bytecode/cache artifacts.

## Webhooks & Callbacks

**Incoming:**
- None. The only callbacks are local Tkinter event bindings in `app.py`.

**Outgoing:**
- None. `app.py` does not contain network client usage.

---

*Integration audit: 2026-10-29*
