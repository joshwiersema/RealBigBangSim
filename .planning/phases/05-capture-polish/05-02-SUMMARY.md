---
phase: 05-capture-polish
plan: 02
subsystem: capture
tags: [ffmpeg, video-recording, subprocess, frame-locking, mp4]

# Dependency graph
requires:
  - phase: 05-01
    provides: Screenshot capture module, app.py capture infrastructure, HUD controls hint
provides:
  - VideoRecorder class with FFmpeg subprocess pipe for frame-locked MP4 recording
  - F9 keybind for toggle recording in app.py
  - Frame-locked timing (effective_frame_time) for consistent output quality
  - HUD recording indicator with red [REC] status
affects: []

# Tech tracking
tech-stack:
  added: [ffmpeg-subprocess-pipe]
  patterns: [frame-locked-timing, deferred-toggle-pattern]

key-files:
  created:
    - bigbangsim/capture/recorder.py
    - tests/test_video_recorder.py
  modified:
    - bigbangsim/app.py
    - bigbangsim/presentation/hud.py

key-decisions:
  - "Frame-locked timing uses effective_frame_time override for all subsystems (sim, milestones, camera, camera_controller) during recording"
  - "FFmpeg availability checked once at init; graceful error message on F9 if missing"

patterns-established:
  - "Frame-locked override: recorder.frame_time_override replaces wall-clock frame_time for deterministic output"
  - "Toggle pattern: F9 creates/destroys VideoRecorder instance (not persistent)"

requirements-completed: [CAPT-02, CAPT-03]

# Metrics
duration: 4min
completed: 2026-03-28
---

# Phase 05 Plan 02: Video Recording Summary

**Frame-locked video recording via FFmpeg subprocess pipe with F9 toggle and HUD recording indicator**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-28T22:20:33Z
- **Completed:** 2026-03-28T22:24:57Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- VideoRecorder class with FFmpeg subprocess pipe, vertical frame flipping, and BrokenPipeError handling
- Frame-locked timing: all subsystems (sim, milestones, camera, camera_controller) use effective_frame_time during recording for smooth MP4 output regardless of GPU speed
- F9 toggle with timestamped output filenames, graceful FFmpeg-missing detection, and clean shutdown on app close
- HUD shows red "F9: Record [REC]" indicator when recording active; window title shows " | REC"

## Task Commits

Each task was committed atomically:

1. **Task 1: VideoRecorder class (TDD RED)** - `e8a2c9c` (test)
2. **Task 1: VideoRecorder class (TDD GREEN)** - `dcf15bf` (feat)
3. **Task 2: Wire into app.py and HUD** - `f7f3bc5` (feat)

_TDD task had RED and GREEN commits._

## Files Created/Modified
- `bigbangsim/capture/recorder.py` - VideoRecorder class with FFmpeg subprocess pipe, frame flip, frame_time_override
- `tests/test_video_recorder.py` - 12 tests covering init, FFmpeg detection, start/stop, write_frame, frame-locking
- `bigbangsim/app.py` - F9 keybind, frame-locked effective_frame_time, write_frame in render loop, on_close guard, REC in title
- `bigbangsim/presentation/hud.py` - Recording parameter in render(), red [REC] indicator in controls hint, F9 keybind label

## Decisions Made
- Frame-locked timing uses `effective_frame_time` override for all four subsystems during recording (sim.update, milestones.update, camera.update, camera_controller.update)
- FFmpeg availability checked once at `__init__` time via `VideoRecorder.is_available()`, not on each F9 press
- VideoRecorder instance created/destroyed per recording session (not persistent) to support different window sizes
- CRF 18 for near-lossless quality with libx264 codec, matching research recommendations

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
FFmpeg must be installed for video recording to work. If not installed, pressing F9 prints a message: "FFmpeg not found. Install via: winget install FFmpeg". The application does not crash.

## Next Phase Readiness
- Phase 05 plan 02 (final plan) complete
- All capture functionality (screenshot + video recording) operational
- Full test suite passes (417 tests, 0 failures)

## Self-Check: PASSED

- All created files exist on disk
- All commit hashes found in git history (e8a2c9c, dcf15bf, f7f3bc5)
- Full test suite: 417 passed, 0 failed

---
*Phase: 05-capture-polish*
*Completed: 2026-03-28*
