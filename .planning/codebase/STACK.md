# Technology Stack

**Analysis Date:** 2026-10-29

## Languages

**Primary:**
- Python 3 (version not pinned) — the complete desktop application is implemented in `app.py`.

**Secondary:**
- Windows batch — `Start Picture Animator.bat` starts the application from its own directory.

## Runtime

**Environment:**
- CPython with the standard-library `tkinter` GUI toolkit; `app.py` instantiates `Animator(tk.Tk)` and runs its event loop.
- Windows is the supported platform: `app.py` references `C:/Windows/Fonts/...`, and the launcher is a `.bat` file.

**Package Manager:**
- pip — installation is documented in `README.md` as `pip install -r requirements.txt`.
- Lockfile: missing; `requirements.txt` contains an unbounded lower version constraint.

## Frameworks

**Core:**
- Tkinter/ttk (Python standard library) — native desktop UI, dialogs, canvas preview, and timeline controls in `app.py`.
- Pillow (`Pillow>=9.0`) — image validation, EXIF normalization, thumbnailing, label drawing, compositing, transitions, and PNG frame rendering in `app.py`.

**Testing:**
- Not detected. No test runner, test configuration, or test files are present in the repository.

**Build/Dev:**
- No build system, formatter, linter, type checker, or packaging configuration is detected.
- `Start Picture Animator.bat` is the supported local launch helper.

## Key Dependencies

**Critical:**
- `Pillow>=9.0` in `requirements.txt` — required for `PIL.Image`, `ImageTk`, `ImageDraw`, `ImageFont`, `ImageOps`, and `ImageColor` usage in `app.py`.
- FFmpeg executable — optional at launch but required by `Animator.export_mp4()` in `app.py` to encode MP4, WebM, or GIF output.

**Infrastructure:**
- Python standard library modules in `app.py`: `base64`, `io`, `json`, `math`, `os`, `pathlib`, `re`, `shutil`, `subprocess`, `tempfile`, `time`, and `zipfile`.

## Configuration

**Environment:**
- No environment-variable configuration is detected.
- FFmpeg resolution first checks `%USERPROFILE%\\ffmpeg.exe` via `Path.home() / "ffmpeg.exe"`, then searches `PATH` with `shutil.which("ffmpeg")` in `app.py`.
- Label-style presets are read from and written to `label_presets.json` alongside `app.py`; the file is optional and is not currently tracked.

**Build:**
- Dependency declaration: `requirements.txt`.
- User instructions: `README.md`.
- Launch configuration: `Start Picture Animator.bat`.

## Platform Requirements

**Development:**
- Python with Tk support, pip, and a display-capable Windows session.
- Install `Pillow>=9.0`; install FFmpeg and either place it at `%USERPROFILE%\\ffmpeg.exe` or expose it on `PATH` to test export.

**Production:**
- Local, single-user Windows desktop execution. No distributable executable or installer configuration is present.

---

*Stack analysis: 2026-10-29*
