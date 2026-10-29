# Testing Patterns

**Analysis Date:** 2026-10-29

## Test Framework

**Runner:**
- Not detected. The repository contains no Python test files, test configuration, or CI workflow.
- Config: Not applicable.

**Assertion Library:**
- Not detected. Use the standard-library `unittest` module or add `pytest` deliberately before introducing a suite.

**Run Commands:**
```powershell
# No automated test command is currently configured.
python app.py                 # Manual GUI smoke test
```

## Test File Organization

**Location:**
- No tests exist. Add a root-level `tests/` directory for future tests, alongside `app.py`.

**Naming:**
- Use `tests/test_<feature>.py`, for example `tests/test_timing.py` and `tests/test_project_io.py`.

**Structure:**
```text
picture-animator-python/
├── app.py
└── tests/
    ├── test_project_io.py
    ├── test_timing.py
    └── test_rendering.py
```

## Test Structure

**Suite Organization:**
```python
# No existing test-suite pattern is present in this repository.
# New tests should exercise pure helpers extracted from `app.py` without creating Tk windows.
```

**Patterns:**
- Test pure data/rendering helpers separately from the GUI. Candidates in `app.py` include `frame_duration`, `transition_for`, `transition_duration_for`, `format_time`, `frame_at_time`, `valid_color`, and `shape`.
- Use a temporary directory for `.paanim` archive round trips around `save_data` and `open_project` behavior.
- Keep display-dependent tests optional or mock Tkinter/Pillow image wrappers; CI hosts may be headless.

## Mocking

**Framework:**
- Not detected. `unittest.mock` is appropriate if tests are added.

**Patterns:**
```python
# Future test pattern: mock external process/UI boundaries in `app.py`.
# Patch `subprocess.run` for `Animator.export_mp4` and file dialogs/messageboxes
# so tests assert constructed behavior without invoking FFmpeg or opening windows.
```

**What to Mock:**
- `subprocess.run` and `shutil.which` in `export_mp4` in `app.py`.
- `filedialog` and `messagebox` calls at GUI command boundaries in `app.py`.
- The Tk root only when testing methods that cannot be extracted into non-GUI helpers.

**What NOT to Mock:**
- Pillow image creation and ZIP serialization for small fixture images; these are core behavior of `app.py` and should have integration coverage.

## Fixtures and Factories

**Test Data:**
```python
# No existing fixture or factory pattern is present.
# Build tiny in-memory Pillow images and representative frame dictionaries
# matching the schema written by `Animator.save_data` in `app.py`.
```

**Location:**
- Put generated temporary media in the test temporary directory; do not commit large binary fixtures unless a regression requires one.

## Coverage

**Requirements:**
- None enforced; no coverage tooling or threshold is configured in `requirements.txt`.

**View Coverage:**
```powershell
# Not currently configured.
```

## Test Types

**Unit Tests:**
- Not present. Prioritize timing calculations, color validation, project schema defaults, label rendering geometry, and transition selection in `app.py`.

**Integration Tests:**
- Not present. Add archive save/open tests and FFmpeg command-construction tests using mocked process execution.

**E2E Tests:**
- Not used. Manual GUI smoke testing is currently the effective end-to-end verification path through `Start Picture Animator.bat` or `python app.py`.

## Common Patterns

**Async Testing:**
```python
# Not applicable: `app.py` uses Tkinter's `after` callback rather than asyncio.
```

**Error Testing:**
```python
# Future tests should supply malformed numeric values, corrupt image bytes, and
# invalid .paanim archives, then assert the safe defaults/dialog behavior in `app.py`.
```

---

*Testing analysis: 2026-10-29*
