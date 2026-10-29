# Codebase Concerns

**Analysis Date:** 2026-10-29

## Tech Debt

**Single, UI-coupled application class (medium):**
- Issue: `Animator` owns widget construction, mutable project state, project persistence, image rendering, timeline scheduling, and FFmpeg orchestration in one 367-line module.
- Files: `app.py`
- Impact: Small feature changes cross unrelated concerns, and core behavior cannot be exercised without constructing a Tk window.
- Fix approach: Extract a validated project model/serializer, a Pillow rendering service, and an exporter; keep `Animator` as the Tkinter adapter.

**No durable validation layer (medium):**
- Issue: UI inputs are mostly clamped when edited, but imported project values are accepted directly and defaults are filled only for some keys.
- Files: `app.py:312-322`, `app.py:328-337`
- Impact: Hand-edited, old, or corrupt `.paanim` files can leave the running application with malformed frames or labels.
- Fix approach: Validate and normalize the complete project schema before assigning `self.frames`; reject invalid projects with a specific user-facing message.

## Known Bugs

**Export completion message is inaccurate for non-MP4 targets (low):**
- Symptoms: A GIF or WebM export reports `MP4 exported`.
- Files: `app.py:340-362`
- Trigger: Select a `.gif` or `.webm` target in the export dialog.
- Workaround: Confirm the actual file extension in the chosen destination.
- Fix approach: Display a neutral message such as `Exported: {name}`.

**Audio is not portable with its project (medium):**
- Symptoms: A project can reopen without usable audio after being moved to another computer or directory.
- Files: `app.py:300`, `app.py:316`, `README.md`
- Trigger: Save a project that has audio, then move the project or remove the original audio file.
- Workaround: Re-add the audio file before exporting; absent audio is silently omitted by `app.py:356`.
- Fix approach: Embed audio in the archive, store a project-relative reference, or clearly surface a missing-audio warning on open/export.

**Malformed project state can cause downstream runtime errors (medium):**
- Symptoms: An imported frame missing `labels`, `image`, or expected label fields can fail during preview, playback, or export after the open operation.
- Files: `app.py:76-82`, `app.py:245-249`, `app.py:312-322`
- Trigger: Open a manually modified or legacy `.paanim` archive whose `project.json` does not match the current implicit schema.
- Workaround: Recreate the project using the current application.
- Fix approach: Use a versioned schema migration function that establishes every frame and label default, including `labels`.

## Security Considerations

**Unbounded archive and image decoding (high):**
- Risk: `.paanim` input is a ZIP file and images are decoded from base64 without size, count, pixel, or decompression limits. A crafted project or image can consume excessive CPU, RAM, or disk during preview/export.
- Files: `app.py:65-68`, `app.py:76-82`, `app.py:315-316`, `app.py:347-354`
- Current mitigation: `add_pictures` verifies that input is recognized as an image; project archives are never extracted to disk.
- Recommendations: Impose archive member/count/uncompressed-size limits, cap image dimensions/pixels before full decoding, cap frame count and export dimensions, and handle Pillow decompression-bomb warnings as rejection.

**Untrusted executable resolution (medium):**
- Risk: When `%USERPROFILE%\\ffmpeg.exe` is absent, the program executes the first `ffmpeg` found on `PATH`.
- Files: `app.py:11`, `app.py:342-361`
- Current mitigation: FFmpeg receives an argument list rather than shell text, so destination/audio paths are not shell-injected.
- Recommendations: Show the resolved executable path and optionally require a user-selected executable; document that users should install FFmpeg from a trusted source.

**Verbose exception disclosure (low):**
- Risk: Error dialogs expose raw ZIP, filesystem, and FFmpeg diagnostics to the user.
- Files: `app.py:322`, `app.py:363-366`
- Current mitigation: FFmpeg output is truncated to the final 3,000 characters.
- Recommendations: Present a concise default message and offer diagnostics only on demand; record sanitized details in a local log if troubleshooting is needed.

## Performance Bottlenecks

**Export materializes every frame as PNG (high):**
- Problem: Export renders all timeline samples to a temporary directory before FFmpeg begins.
- Files: `app.py:345-361`
- Cause: Work and disk scale with frame count, duration, FPS, and image dimensions. For example, long high-resolution projects can create thousands of PNGs.
- Improvement path: Estimate output count/space before export, enforce configurable limits, update progress, and stream frames to FFmpeg or use a lower-memory intermediate strategy.

**Playback and editing redraw full-resolution images on the UI thread (medium):**
- Problem: Each 30 ms playback tick composites, resizes, and converts Pillow images, then updates Tkinter synchronously.
- Files: `app.py:239-244`, `app.py:245-272`
- Cause: Rendering scales with source resolution and labels/transitions; there is no preview-sized cache or background worker.
- Improvement path: Cache scaled preview images, throttle redraws, and move long-running export work off the Tk event loop while marshaling progress back to the UI thread.

## Fragile Areas

**Project save replacement (medium):**
- Files: `app.py:297-303`
- Why fragile: The temporary file is adjacent to the project, but there is no fsync, backup, or recovery flow if replacement fails after an interruption.
- Safe modification: Preserve the existing project until a fully written ZIP is verified, then use an atomic replace with a recoverable backup where supported.
- Test coverage: No automated save/replace failure tests exist in the repository.

**Platform-specific font selection (medium):**
- Files: `app.py:14`, `app.py:323-327`
- Why fragile: Font names and hard-coded `C:/Windows/Fonts/...` files assume Windows; preview and export can differ when a requested font is unavailable.
- Safe modification: Resolve fonts through a platform-aware registry, persist a fallback policy, and render a preview warning when substitution occurs.
- Test coverage: No cross-platform font-resolution tests exist.

## Scaling Limits

**Embedded-image project format (high):**
- Current capacity: Every original image is base64-encoded into JSON inside a ZIP archive.
- Limit: Project memory use grows with all source image bytes; base64 adds representation overhead, and duplicate frames duplicate content again via `app.py:159-161`.
- Scaling path: Deduplicate image assets by content hash in the ZIP, avoid keeping all decoded images resident, and expose project-size estimates before save/export.

## Dependencies at Risk

**External FFmpeg installation (medium):**
- Risk: FFmpeg is not declared or provisioned by `requirements.txt`; availability and codec support vary by local installation.
- Impact: Export fails at runtime or produces target-specific errors.
- Migration plan: Add a preflight screen that reports the discovered FFmpeg version/codecs, or package/guide a supported distribution.

## Missing Critical Features

**Cancellation and progress reporting for export (high):**
- Problem: Export blocks the UI and gives no progress, cancellation, frame estimate, or disk-space warning.
- Files: `app.py:338-366`
- Blocks: Users cannot safely handle long or unexpectedly expensive exports.

## Test Coverage Gaps

**Core rendering, persistence, import safety, and FFmpeg command construction are untested (high):**
- What's not tested: Frame normalization, transition math, label timing, corrupt/oversized archive handling, save recovery, and all export targets.
- Files: `app.py`; no test files or test configuration are present.
- Risk: Regressions in the only module reach users without automated detection.
- Priority: High.
- Recommended first tests: Extract pure helpers and add `pytest` cases for schema migration, label/render behavior on small fixtures, archive-limit rejection, and the exact FFmpeg argument lists for MP4/WebM/GIF with and without audio.

---

*Concerns audit: 2026-10-29*
