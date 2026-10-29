# Picture Animator (Python)

A local desktop app for creating picture-by-picture animations with editable titles and arrows.

## Run

First run: the launcher installs Pillow automatically (or run `pip install -r requirements.txt` yourself). Exporting video also needs FFmpeg installed.

Double-click `Start Picture Animator.bat`, or run:

```powershell
python app.py
```

## Workflow

1. **Add pictures** — each becomes an animation frame. Set how long the selected picture stays on screen with **Frame duration**, then choose its entrance transition and duration.
2. Select a frame, then **Add label**. Drag the label in the preview and edit its text, font, shape, colours, outline, opacity, rotation, size, and appearance delay.
3. Use the playback controls beneath the preview to play or scrub through the complete timeline. Delayed labels and transitions appear as they will in the exported MP4.
4. Rename a frame in the frame list.
5. Save a selected label's appearance as a preset, then apply it to labels with the same text across every frame.
6. Save as a `.paanim` project file. It contains the pictures, durations, and labels, so it can be moved or reopened later.
7. Click **Export MP4** for a normal, shareable video. FFmpeg at `C:\Users\trans\ffmpeg.exe` is used automatically.

The project file is the source of truth. The app does not rely on browser storage.
