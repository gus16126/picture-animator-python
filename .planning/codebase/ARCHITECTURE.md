<!-- refreshed: 2026-10-29 -->
# Architecture

**Analysis Date:** 2026-10-29

## System Overview

```text
┌──────────────────────────────────────────────────────────┐
│ Tkinter desktop UI                                        │
│ `app.py` / `Animator._ui()`                               │
└───────────────┬──────────────────────────────────────────┘
                │ events invoke instance methods
                ▼
┌──────────────────────────────────────────────────────────┐
│ In-memory project controller and renderer                 │
│ `Animator` in `app.py`                                    │
├────────────────────┬─────────────────────────────────────┤
│ Frame/label state  │ Pillow preview & raster composition │
│ `self.frames`      │ `draw`, `transition_image`           │
└───────────────┬────┴─────────────────┬───────────────────┘
                │                      │
                ▼                      ▼
┌────────────────────────────┐  ┌──────────────────────────┐
│ `.paanim` ZIP project      │  │ temporary PNGs + FFmpeg  │
│ `save_data`, `open_project`│  │ `export_mp4`             │
└────────────────────────────┘  └──────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
| --- | --- | --- |
| `Animator` | Owns window, in-memory state, UI events, persistence, preview, and export | `app.py` |
| Frame dictionaries | Carry source image (base64), labels, duration, and transition configuration | `app.py` |
| Label dictionaries | Carry text/style, normalized position, rotation and delay | `app.py` |
| Batch launcher | Starts the GUI with the system Python installation | `Start Picture Animator.bat` |

## Pattern Overview

**Overall:** Single-module stateful desktop application (Tkinter controller/view combined with Pillow rendering).

**Key Characteristics:**

- `Animator` subclasses `tk.Tk`, so UI construction, commands, and project state share one object in `app.py`.
- Project state is a list of untyped nested dictionaries; rendering reads these dictionaries directly.
- All image output is generated locally: Pillow creates frames and `ffmpeg` encodes video.

## Layers

**UI and interaction layer:**

- Purpose: Construct widgets and translate mouse, keyboard, list, and timeline events into mutations.
- Location: `app.py` (`_ui`, `pick_frame`, `down`, `motion`, `toggle_play`).
- Depends on: `tkinter`, the `Animator` project state, and renderer methods.

**Project model and persistence layer:**

- Purpose: Maintain frames/labels and serialize a portable project archive.
- Location: `app.py` (`add_pictures`, `duplicate_frame`, `save_data`, `open_project`).
- Depends on: `json`, `zipfile`, `pathlib`, and base64 image data.

**Rendering/export layer:**

- Purpose: Decode cached images, composite labels and transitions, then create a video/GIF/WebM file.
- Location: `app.py` (`frame_image`, `draw_export_label`, `transition_image`, `export_mp4`).
- Depends on: Pillow and an external FFmpeg executable.

## Data Flow

### Project editing path

1. A user chooses images in `Animator.add_pictures()` (`app.py`); source bytes are validated with Pillow and base64-encoded into a frame dictionary.
2. Widget callbacks mutate `self.frames` and the selected label through `apply_fields`, timing controls, frame ordering, or dragging (`app.py`).
3. `draw()` resolves the current frame/transition and refreshes the Tkinter canvas (`app.py`).
4. `save_data()` stores `version`, `frames`, and the audio-path string as `project.json` in a `.paanim` ZIP (`app.py`).

### Export path

1. `export_mp4()` resolves a user-selected destination and `ffmpeg` path (`app.py`).
2. It renders every duration/FPS sample via `transition_image()` into a `TemporaryDirectory` as numbered PNG files (`app.py`).
3. `subprocess.run()` invokes FFmpeg, optionally looping the selected audio and encoding based on output suffix (`app.py`).

**State Management:**

- `self.frames`, `self.current`, `self.selected`, `self.audio_path`, and timeline properties are mutable instance state in `Animator` (`app.py`).
- The image cache (`self._img_cache`) holds decoded RGB copies keyed by each frame's base64 string (`app.py`).

## Key Abstractions

**Frame:**

- Purpose: A single timeline item with embedded source data and animation settings.
- Examples: dictionaries built by `add_pictures()` and normalized by `open_project()` in `app.py`.
- Pattern: JSON-serializable dictionary rather than a class or typed schema.

**Label:**

- Purpose: An overlay placed using `x`/`y` values normalized from 0 to 1.
- Examples: labels created by `add_label()` and painted by `draw_export_label()` in `app.py`.

## Entry Points

**Desktop application:**

- Location: `app.py` (`if __name__ == '__main__': Animator().mainloop()`).
- Triggers: `python app.py` or the launcher documented in `README.md`.
- Responsibilities: Construct the Tk root and enter Tkinter's event loop.

**Windows launcher:**

- Location: `Start Picture Animator.bat`.
- Triggers: Double-click from Windows Explorer.
- Responsibilities: Launch `app.py`; it is the documented convenience entry point in `README.md`.

## Architectural Constraints

- **Threading:** Tkinter UI, preview composition, and export all run synchronously on the UI thread in `app.py`; long exports block interaction.
- **Global state:** Module constants such as `FFMPEG`, `PRESETS_FILE`, and allowed UI tuples are defined in `app.py`; mutable project state is instance-bound.
- **Portability:** Font locations are hard-coded to `C:/Windows/Fonts/...` in `font_for_export()` (`app.py`).
- **Project fidelity:** Project image contents are embedded in `.paanim`; audio is only stored as an external path (`app.py`).

## Anti-Patterns

### God object

**What happens:** `Animator` contains UI assembly, validation, model mutations, serialization, rendering, and process execution in `app.py`.
**Why it's wrong:** Changes in one concern can unintentionally affect another and targeted testing is difficult.
**Do this instead:** Split new work into a project model/serializer, rendering service, exporter, and UI adapter while keeping `Animator` as a coordinator.

### Untyped persisted dictionaries

**What happens:** Frame and label properties are accessed by string keys throughout `app.py`.
**Why it's wrong:** Invalid or older archives can omit unexpected fields and cause runtime failures.
**Do this instead:** Validate archive data into dataclasses or explicit schema objects at the `open_project()` boundary.

## Error Handling

**Strategy:** Local recoverable errors are surfaced with Tkinter dialogs or the status text.

**Patterns:**

- Unsupported image files are collected and shown in a warning in `add_pictures()` (`app.py`).
- Image preview errors are caught in `draw()` (`app.py`).
- Project loading and FFmpeg failures display `messagebox.showerror()` from `open_project()` and `export_mp4()` (`app.py`).

## Cross-Cutting Concerns

**Logging:** No structured logging is implemented; user-facing failures are dialogs/status text in `app.py`.
**Validation:** UI fields use local coercion/clamping and color regex validation in `app.py`.
**Authentication:** Not applicable; this is a local desktop application.

---

*Architecture analysis: 2026-10-29*
