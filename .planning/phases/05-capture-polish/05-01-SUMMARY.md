---
phase: 05-capture-polish
plan: 01
subsystem: capture
tags: [pillow, screenshot, png, fullscreen, window-state, json, persistence]

# Dependency graph
requires:
  - phase: 04-presentation
    provides: imgui HUD with controls hint panel, moderngl-window event handling
provides:
  - bigbangsim/capture/ package with screenshot.py (take_screenshot function)
  - Window state persistence (save_window_state, load_window_state) in config.py
  - F12 screenshot capture wired into app.py render loop
  - F11 fullscreen toggle wired into app.py key handler
  - on_close callback saving window state to LOCALAPPDATA
affects: [05-02-video-recording]

# Tech tracking
tech-stack:
  added: [Pillow>=12]
  patterns: [flag-based deferred capture, JSON window state persistence, position clamping]

key-files:
  created:
    - bigbangsim/capture/__init__.py
    - bigbangsim/capture/screenshot.py
    - tests/test_screenshot.py
    - tests/test_fullscreen.py
  modified:
    - bigbangsim/config.py
    - bigbangsim/app.py
    - bigbangsim/presentation/hud.py
    - pyproject.toml
    - .gitignore

key-decisions:
  - "Screenshot captured at end of on_render (after HUD) via deferred flag pattern, not in on_key_event"
  - "Window position clamped to (0-4000, 0-3000) bounds to prevent off-screen windows after monitor config change"
  - "Pillow>=12 added as explicit dependency in pyproject.toml (was transitive via imgui-bundle)"

patterns-established:
  - "Deferred capture: on_key_event sets flag, on_render end captures (ensures complete frame with HUD)"
  - "Window state persistence: JSON file in LOCALAPPDATA/BigBangSim/ on Windows, XDG_CONFIG_HOME on Linux"

requirements-completed: [CAPT-01, RNDR-05]

# Metrics
duration: 4min
completed: 2026-03-28
---

# Phase 05 Plan 01: Screenshot Capture and Window State Summary

**PNG screenshot capture via Pillow with F12 hotkey, F11 fullscreen toggle, and JSON-based window state persistence across sessions**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-28T22:13:15Z
- **Completed:** 2026-03-28T22:17:02Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Screenshot capture module reads framebuffer, flips vertically, saves timestamped PNG to screenshots/ directory
- Window state persistence saves/loads position, size, and fullscreen state as JSON in LOCALAPPDATA
- F12 captures screenshot at end of render frame (after HUD overlay), F11 toggles fullscreen
- Window state restored on application launch with position clamping for safety
- HUD controls hint updated to show all keybindings including F12 and F11
- 8 new tests covering screenshot creation, directory creation, FBO params, state round-trip, missing file, malformed JSON, and position clamping

## Task Commits

Each task was committed atomically:

1. **Task 1: Screenshot capture module and fullscreen/window state persistence** - `dff9c24` (test: failing tests), `4f0c12f` (feat: implementation)
2. **Task 2: Wire screenshot and fullscreen into app.py and update HUD** - `71189a7` (feat: app integration)

## Files Created/Modified
- `bigbangsim/capture/__init__.py` - Capture sub-package init
- `bigbangsim/capture/screenshot.py` - take_screenshot function with FBO read, vertical flip, PNG save
- `bigbangsim/config.py` - Added save_window_state/load_window_state with JSON persistence and position validation
- `bigbangsim/app.py` - F12/F11 key handlers, screenshot at end of render, on_close saves window state, load on init
- `bigbangsim/presentation/hud.py` - Controls hint updated with F12: Screenshot and F11: Fullscreen, wider panel
- `pyproject.toml` - Added Pillow>=12 dependency
- `.gitignore` - Added screenshots/ and *.mp4 exclusions
- `tests/test_screenshot.py` - 3 tests for screenshot capture
- `tests/test_fullscreen.py` - 5 tests for window state persistence

## Decisions Made
- Screenshot captured via deferred flag pattern: on_key_event sets `_screenshot_requested`, on_render end captures. This ensures the screenshot includes the complete composited frame with HUD overlay.
- Window position clamped to (0-4000, 0-3000) bounds to prevent windows appearing off-screen after monitor configuration changes (Pitfall 5 from research).
- Pillow>=12 added as explicit pyproject.toml dependency. It was already installed as a transitive dependency of imgui-bundle, but declaring it explicitly prevents ImportError on clean installs.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None - all features are fully wired with no placeholder data.

## Next Phase Readiness
- capture/ package established and ready for Plan 02 (video recording via FFmpeg subprocess)
- take_screenshot pattern (FBO read + vertical flip) directly reusable for video frame capture
- F12/F11 key handler pattern in on_key_event ready for additional capture keybindings

## Self-Check: PASSED

- All 9 created/modified files verified present on disk
- Commits dff9c24, 4f0c12f, 71189a7 verified in git log
- 405 tests pass (8 new + 397 existing, 0 regressions)

---
*Phase: 05-capture-polish*
*Completed: 2026-03-28*
