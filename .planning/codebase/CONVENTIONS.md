# Coding Conventions

**Analysis Date:** 2026-10-29

## Naming Patterns

**Files:**
- The application is a single lowercase Python module: `app.py`.
- User-facing Windows launch behavior is kept in `Start Picture Animator.bat`.

**Functions:**
- Methods on `Animator` use lowercase `snake_case`, such as `add_pictures`, `apply_transition`, and `draw_export_label` in `app.py`.
- Event handlers are short verb-oriented names (`down`, `motion`, `up`) in `app.py`; retain them only where they are bound directly to Tkinter events.

**Variables:**
- Local variables generally use `snake_case`, including `transition_duration_value`, `local_time`, and `output_index` in `app.py`.
- UI widget instance variables use descriptive names such as `timeline_scale`, `transition_input`, and `play_button` in `app.py`.

**Types:**
- The project does not define custom classes beyond the `Animator(tk.Tk)` application class in `app.py` and has no type annotations.

## Code Style

**Formatting:**
- No formatter configuration is present in the repository. `app.py` frequently places several simple statements on one line with semicolons, for example in `Animator.__init__` and `_ui`.
- Preserve the existing standard-library-first import block followed by Pillow imports at the top of `app.py` when making localized changes.
- For new or substantially refactored code, prefer one statement per line, clear spacing around operators, and line breaks for long widget construction calls; this improves the maintainability of the single large module.

**Linting:**
- No linting configuration or linter dependency is present in `requirements.txt`.

## Import Organization

**Order:**
1. Python standard-library imports (`base64`, `json`, `pathlib`, `tkinter`) in `app.py`.
2. Third-party Pillow imports (`PIL`) in `app.py`.

**Path Aliases:**
- Not used; imports in `app.py` are direct standard-library and Pillow imports.

## Error Handling

**Patterns:**
- Expected file/image failures are handled with focused exceptions: `OSError` and `UnidentifiedImageError` around image input in `add_pictures`, `frame_image`, and `draw` in `app.py`.
- Numeric form fields retain their current model value if parsing fails, via `try`/`except ValueError` in `apply_duration`, `apply_transition`, and `apply_fields` in `app.py`.
- User-facing failures surface through `tkinter.messagebox`, notably project loading in `open_project` and FFmpeg export in `export_mp4`.
- Use narrow exception types for new expected failures. Avoid broad `except Exception` except at GUI command boundaries where an actionable dialog is shown; `open_project` and `export_mp4` are the existing boundary examples.

## Logging

**Framework:**
- No logging framework is configured in `app.py`.

**Patterns:**
- Runtime progress and success messages are displayed in the Tkinter status field (`self.status`) in methods such as `add_audio`, `save`, and `export_mp4`.
- If diagnostics are added, use Python's `logging` module instead of `print` so the GUI behavior remains unaffected.

## Comments

**When to Comment:**
- `app.py` is largely self-documenting through method names; comments are not used for routine UI or rendering code.
- Add comments only for non-obvious coordinate math, transition behavior, archive compatibility, or external-process arguments.

**Docstrings:**
- No module, class, or method docstrings are currently present in `app.py`.
- Add docstrings to any new reusable helper or a future extracted module, especially when it establishes project-file or rendering invariants.

## Function Design

**Size:**
- `Animator` methods range from tiny state helpers (`label`, `valid_color`) to large orchestration methods (`_ui`, `export_mp4`) in `app.py`.
- Keep new behavior in focused helpers where possible, then call them from Tkinter command/event methods.

**Parameters:**
- Methods accept native Tkinter event arguments where required (`pick_frame`, `down`, `motion`, `up`) and otherwise read and update state on `self`.

**Return Values:**
- UI command methods primarily mutate application state and return `None`; query helpers such as `frame_image`, `frame_duration`, and `transition_image` return computed values.

## Module Design

**Exports:**
- `app.py` is run directly through the `if __name__ == '__main__'` guard; it has no explicit public API.

**Barrel Files:**
- Not applicable to this Python application.

---

*Convention analysis: 2026-10-29*
