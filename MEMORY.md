# Picture Animator — Working Memory

## Purpose

Picture Animator is a local Windows desktop app for turning a sequence of pictures into a shareable animation/video. A user can give each picture its own duration and transition, place styled text labels on individual frames, preview the result, save the complete editable project, and export it as MP4, WebM, or GIF.

The main user requirement is simple: the app must do what the user asks without silently changing labels, losing label settings, shrinking the preview, freezing during export, or making the user work around an app limitation.

## Current architecture

- `app.py` is the entire Tkinter application.
- Pillow handles loading pictures and drawing labels.
- FFmpeg performs video export.
- A project is a portable `.paanim` ZIP file. Version 2 stores project metadata in `project.json` and each source picture as a separate ZIP entry.
- `label_presets.json` is an optional local user file for saved label style presets. It is intentionally ignored by Git.
- `app.log` records errors and export activity. It is intentionally ignored by Git.
- Tests are in `tests/` and run with `python -m unittest discover -s tests -v`.

## User-facing behavior that must be preserved

- Label backgrounds are real shapes, not rectangular labels with an arrow drawn over them.
- Available shapes: Box, Right arrow, Left arrow, Up arrow, Down arrow. Arrowheads must be clearly visible and leave room for centered text.
- Editing label text, color, style, or animation must never change the label's existing shape unless the user explicitly chooses a preset action that includes shapes.
- Label controls include text, shape, font, text color, background color, outline, opacity, rotation, size, animation, animation duration, and appearance delay. Color selection uses a picker; the user should not need to type color codes.
- Label animation choices are None, Fade in/out, Slide left/right, Pop, Pulse, Bounce, Wiggle, and Typewriter.
- Each frame can have independent duration and transition settings. “Apply timing to selected” applies only to the selected frame.
- The frame list has a scrollbar.
- The right-side controls must stay compact so the preview panel does not become too narrow.
- Label actions (Add/Delete) and preset actions (Save/Apply) are grouped into menus to conserve control-panel space.
- Playback must visibly update the preview as the playhead moves.
- Save/Open must preserve every label field on every frame, including animation, duration, and delay.

## Completed work

- Fixed frame duplication.
- Implemented proper shaped arrow labels and lengthened the arrow tips.
- Added label animation controls and rendering.
- Added color pickers for label colors.
- Added compact menus for label and preset actions.
- Added frame-list scrolling and protected the preview width.
- Improved video export: unchanged full-resolution frames are rendered once as timed stills instead of repeatedly copied through a raw-video pipe; FFmpeg expands them at the chosen FPS. MP4 uses H.264 CRF 17 for high-quality detailed pictures. Exports run in the background, progress is shown, audio looping is bounded, FFmpeg stderr is drained, and export cancellation/cleanup is handled. Encoding writes to a temporary `.partial.mp4` and replaces the requested file only after successful completion, so an interrupted export cannot leave a zero-byte final MP4.
- Added project-version-2 storage, image cache management, Undo, automatic `.bak` save backups, preset application across matching/all labels, and error logging.
- Hardened loading of older or hand-edited projects by normalizing missing label fields.
- Fixed blank read-only controls after opening a project.
- Fixed apparent “missing settings”: selecting a frame or reaching a frame while playback now selects that frame’s first label rather than clearing selection and blanking the label editor.
- Removed the unreliable pre-rendered preview playback path. Playback now renders directly on the Tk thread each tick, which restores visible preview updates.

## Important recent verification

On 2026-11-03, the full automated suite passed (14 tests). It covers duplication, export streaming, label shapes and animations, color picker behavior, preset behavior, save persistence of animation settings, label selection across frames, and playback redraw calls. A live Tk canvas check also confirmed that playback advances the timeline and creates a preview image.

## Known context / future care

- The direct playback renderer favors reliable visible playback over pre-rendering every frame. Do not reintroduce background preview rendering without proving it cannot leave a moving timeline with a frozen canvas.
- Projects can contain several labels on one frame. Frame selection intentionally selects the first label; the user can click another label in the preview to edit it.
- The `app.log` file should be checked first when a GUI action fails without an on-screen error.
- FFmpeg is looked up first at `~/ffmpeg.exe`, then on `PATH`.
- Preserve unrelated untracked files, especially `.github/`, unless the user explicitly asks to include or change them.
