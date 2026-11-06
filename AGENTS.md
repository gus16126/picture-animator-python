# Agent Instructions — Picture Animator

## Project scope

This repository is a local Tkinter/Pillow desktop editor for creating picture animations and exporting video. The app source is currently a single file: `app.py`. Treat changes to it carefully because UI, rendering, saving, and exporting are closely connected.

Read [MEMORY.md](MEMORY.md) before modifying the app. It records the user’s product expectations and completed fixes that must not regress.

## Working rules

1. Work in this repository: `C:\Users\trans\Documents\pythonscripts\picture-animator-python`.
2. Before editing, inspect `git status --short`. Preserve existing user changes and untracked files. Do not add `.github/` unless the user explicitly requests it.
3. Use `apply_patch` for source and documentation edits.
4. Do not use destructive Git commands such as `git reset --hard` or `git checkout --` unless the user explicitly asks.
5. For a report/review request, inspect and explain first. Do not make code changes unless the user asks for a fix.
6. Keep the right control panel compact. Any layout change must preserve a usable preview width.
7. Do not silently overwrite label properties. In particular, editing text, colors, animations, or a style preset must preserve the label shape unless the user explicitly chose to apply shape settings.
8. Project save/load changes must preserve all label data across every frame. Include animation, animation duration, delay, shape, colors, opacity, rotation, position, and text.
9. Playback must redraw the visible preview as the timeline moves. Do not replace direct Tk-thread playback with a worker-thread/pre-render system unless it is thoroughly tested against a frozen preview.
10. Treat long or stuck MP4 exports as a serious defect. Keep FFmpeg pipe handling deadlock-safe and clean up its process if the app is closed mid-export.

## Verification

Run the complete test suite after changes:

```powershell
python -m unittest discover -s tests -v
```

Also run:

```powershell
git diff --check
```

For changes to preview, label editing, or persistence, perform a focused live check when practical:

- create/open a small project;
- select different frames and verify label controls remain populated;
- set an animation, Save As, reopen, and verify it remains;
- press Play and verify the preview image visibly redraws while the timeline moves.

## Project files

- `app.py` — application code.
- `tests/` — automated unit/regression tests.
- `README.md` — user-facing startup and usage instructions.
- `MEMORY.md` — product context, design decisions, and accomplishments.
- `app.log` — local runtime/export log (ignored by Git).
- `label_presets.json` — local user presets (ignored by Git).

## User communication

Lead with what was fixed or found. Explain in plain language. Avoid claiming a test proves a visual behavior unless a live GUI check was actually performed. If a running app needs a restart to use changed Python code, say so clearly.
