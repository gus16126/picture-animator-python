# Picture Animator (Python)

A local desktop app for creating picture-by-picture animations with editable titles and arrows.

## Run

Double-click `Start Picture Animator.bat`, or run:

```powershell
python app.py
```

## Workflow

1. **Add pictures** — each becomes an animation frame.
2. Select a frame, then **Add label**. Drag the label in the preview and edit its text, shape, color, size, and appearance delay.
3. Rename a frame in the frame list.
4. Save as a `.paanim` project file. It contains the pictures and labels, so it can be moved or reopened later.
5. Click **Export MP4** for a normal, shareable video. FFmpeg at `C:\Users\trans\ffmpeg.exe` is used automatically.

The project file is the source of truth. The app does not rely on browser storage.
