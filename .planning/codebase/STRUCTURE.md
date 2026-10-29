# Codebase Structure

**Analysis Date:** 2026-10-29

## Directory Layout

```text
picture-animator-python/
├── `app.py`                       # Entire Tkinter application and export logic
├── `requirements.txt`             # Runtime Python dependency declaration
├── `README.md`                    # Installation and workflow guidance
├── `Start Picture Animator.bat`   # Windows desktop launcher
├── `.gitignore`                   # Ignores Python bytecode
├── `__pycache__/`                 # Generated Python bytecode; not source
└── `.planning/codebase/`          # Generated codebase map
```

## Directory Purposes

**Project root:**

- Purpose: Contains all shipped application source and project metadata.
- Contains: The one Python module, launcher, dependency list, and user documentation.
- Key files: `app.py`, `README.md`, `requirements.txt`, and `Start Picture Animator.bat`.

**`__pycache__/`:**

- Purpose: Python interpreter cache.
- Generated: Yes.
- Committed: No; `.gitignore` excludes Python bytecode.

**`.planning/codebase/`:**

- Purpose: Generated analysis reference for future maintenance.
- Generated: Yes.
- Committed: Intended for project planning documentation, not executable application logic.

## Key File Locations

**Entry Points:**

- `app.py`: Creates `Animator` and starts Tkinter when invoked as a script.
- `Start Picture Animator.bat`: Windows convenience launcher referenced by `README.md`.

**Configuration:**

- `requirements.txt`: Declares the Pillow dependency.
- `app.py`: Holds app constants, FFmpeg default path, allowed fonts/shapes/transitions, and preset-file location.

**Core Logic:**

- `app.py`: UI, project editing, project archive I/O, preview rendering, and FFmpeg invocation all reside here.

**Testing:**

- No test directory, test files, or test-runner configuration is present.

## Naming Conventions

**Files:**

- Application source uses a simple lowercase module name: `app.py`.
- User-facing files use descriptive names and spaces only for the Windows launcher: `Start Picture Animator.bat`.
- Project archives use the `.paanim` extension as configured in `app.py`.

**Directories:**

- No application source-package directory exists; add one deliberately rather than creating ad-hoc root modules.

## Where to Add New Code

**New Feature:**

- Current primary implementation: `app.py`, using methods on `Animator` to preserve the existing structure.
- Tests: create a new `tests/` directory; no existing testing convention is available.

**New Component/Module:**

- Prefer creating a focused root-level module such as `project_model.py`, `renderer.py`, or `exporter.py`, then import it from `app.py`; this progressively separates the current monolith.

**Utilities:**

- Keep UI-neutral helpers in a newly created module (for example `project_io.py`) rather than further expanding `Animator` in `app.py`.

## Special Directories

**`.git/`:**

- Purpose: Git version-control metadata.
- Generated: Yes.
- Committed: No; managed by Git.

**`__pycache__/`:**

- Purpose: Compiled bytecode created by the Python runtime.
- Generated: Yes.
- Committed: No, as indicated by `.gitignore`.

---

*Structure analysis: 2026-10-29*
