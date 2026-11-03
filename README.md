# Picture Animator (Python)

A local desktop app for turning a series of pictures into an MP4 video, with editable text labels, arrows, and animations.

## Run

First run: install the dependency once with `pip install -r requirements.txt` (Pillow). Exporting video also needs FFmpeg installed.

Double-click `Start Picture Animator.bat`, or run:

```powershell
python app.py
```

## Workflow

1. **Add pictures** — each becomes a frame. Set how long it stays with **Frame duration**, and its entrance **transition** (cut, fade, slide, zoom).
2. **Add a label** to a frame. Drag it to position it, then edit its text (press Enter for a second line), font, shape (box or arrow), colours (with a colour picker), outline, opacity, rotation, size, **animation** (fade in/out, slide, pop, pulse, bounce, wiggle, typewriter), and appearance delay.
3. Play or scrub the timeline under the preview to see delayed labels, transitions, and animations exactly as they'll export.
4. **Undo** (Ctrl+Z or the Undo button) reverts label edits, frame changes, reorders, and preset applications.
5. Save a label's style as a **preset**, then apply it to matching labels — or to **all labels in every frame** — from the Preset actions menu.
6. **Save** as a `.paanim` file (pictures + labels together, portable). Saving also keeps the previous version as a `.paanim.bak` backup.
7. **Export MP4** (also WebM or GIF), optionally with an audio track that loops to fill the video. Export runs in the background with a progress readout.

## Notes

- Projects are saved in version-2 format: pictures are stored as separate entries, so saving and loading large projects is fast.
- Errors and export activity are written to `app.log` next to the app, for troubleshooting.
- Tests live in `tests/` (`python -m unittest discover -s tests`) and run automatically via GitHub Actions on every push.
