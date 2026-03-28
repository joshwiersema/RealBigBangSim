---
phase: 05-capture-polish
verified: 2026-03-28T22:30:00Z
status: passed
score: 8/8 must-haves verified
re_verification: false
---

# Phase 5: Capture & Polish Verification Report

**Phase Goal:** Users can capture and share the experience through high-resolution screenshots and full cinematic video recording, with final polish for a complete desktop application
**Verified:** 2026-03-28T22:30:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #  | Truth                                                                                                   | Status     | Evidence                                                                                     |
|----|---------------------------------------------------------------------------------------------------------|------------|----------------------------------------------------------------------------------------------|
| 1  | User presses F12 and a PNG file appears in the screenshots/ directory                                   | VERIFIED   | `on_key_event` sets `_screenshot_requested=True` on `keys.F12`; `on_render` end calls `take_screenshot(self.ctx.fbo, ...)` which creates `bigbangsim_*.png` via Pillow |
| 2  | User presses F11 and the window toggles between fullscreen and windowed mode                            | VERIFIED   | `on_key_event` `keys.F11` branch: `self.wnd.fullscreen = not self.wnd.fullscreen` — app.py line 456 |
| 3  | User closes the app, relaunches, and the window appears at the same position and size                   | VERIFIED   | `on_close` calls `save_window_state(self.wnd)`; `__init__` calls `load_window_state()` and restores position/size/fullscreen |
| 4  | Window state is saved as JSON in LOCALAPPDATA/BigBangSim/window_state.json                              | VERIFIED   | `config.py` `_get_settings_path()` uses `os.environ.get("LOCALAPPDATA")` on Windows; `save_window_state` writes JSON with `"position"`, `"size"`, `"fullscreen"` keys |
| 5  | User presses F9 to start recording and a status indicator appears in the HUD                            | VERIFIED   | `on_key_event` `keys.F9` creates and starts `VideoRecorder`; `_render_hud` passes `recording=True` to `hud.render`; HUD shows red `"F9: Record [REC]"` and window title shows `" | REC"` |
| 6  | User presses F9 again to stop recording and an MP4 file is produced                                     | VERIFIED   | F9 second press calls `self.recorder.stop()` which closes FFmpeg stdin and waits; output is timestamped `bigbangsim_*.mp4` |
| 7  | Recording uses fixed timestep (1/60s) regardless of actual GPU frame rate                               | VERIFIED   | `on_render` computes `effective_frame_time` from `recorder.frame_time_override` (returns `1.0 / fps` when recording); all 4 subsystems — `sim.update`, `milestones.update`, `camera.update`, `camera_controller.update` — use `effective_frame_time` |
| 8  | If FFmpeg is not installed, pressing F9 shows an error message instead of crashing                      | VERIFIED   | `__init__` caches `self._ffmpeg_available = VideoRecorder.is_available()` (calls `shutil.which("ffmpeg")`); F9 branch prints `"FFmpeg not found. Install via: winget install FFmpeg"` when False |

**Score:** 8/8 truths verified

### Required Artifacts

| Artifact                               | Expected                                      | Status     | Details                                              |
|----------------------------------------|-----------------------------------------------|------------|------------------------------------------------------|
| `bigbangsim/capture/__init__.py`       | Capture package init                          | VERIFIED   | Exists, 1 line docstring — correct for package init  |
| `bigbangsim/capture/screenshot.py`     | `take_screenshot` function                    | VERIFIED   | 45 lines, real implementation with Pillow, vertical flip, `fbo.read(components=3, alignment=1)`, `os.makedirs` |
| `bigbangsim/capture/recorder.py`       | `VideoRecorder` class with FFmpeg subprocess  | VERIFIED   | 127 lines, full class with `start`, `write_frame`, `stop`, `is_available`, `frame_time_override`, `subprocess.Popen` |
| `bigbangsim/config.py`                 | `save_window_state`, `load_window_state`      | VERIFIED   | Exports both functions; JSON persistence with position clamping `max(0, min(x, 4000))` |
| `tests/test_screenshot.py`             | Unit tests for screenshot capture             | VERIFIED   | 47 lines, 3 tests covering file creation, directory creation, FBO params |
| `tests/test_fullscreen.py`             | Unit tests for fullscreen/window persistence  | VERIFIED   | 86 lines (>40 required), 5 tests covering round-trip, missing file, malformed JSON, position clamping |
| `tests/test_video_recorder.py`         | Unit tests for video recording                | VERIFIED   | 115 lines (>50 required), 12 tests in 5 classes covering init, FFmpeg detection, start/stop, write_frame, frame-locking |

### Key Link Verification

| From                          | To                                | Via                                                       | Status   | Details                                                                                         |
|-------------------------------|-----------------------------------|-----------------------------------------------------------|----------|-------------------------------------------------------------------------------------------------|
| `bigbangsim/app.py`           | `bigbangsim/capture/screenshot.py`| `on_key_event` F12 sets flag; `on_render` calls `take_screenshot(self.ctx.fbo, ...)` | WIRED    | app.py line 35: `from bigbangsim.capture.screenshot import take_screenshot`; called at line 315 |
| `bigbangsim/app.py`           | `bigbangsim/config.py`            | `on_close` saves; `__init__` restores via `save_window_state`/`load_window_state` | WIRED    | app.py lines 28-34 import both; `load_window_state()` at line 121; `save_window_state(self.wnd)` at line 518 |
| `bigbangsim/app.py`           | `bigbangsim/capture/recorder.py`  | `on_key_event` F9 toggles recording; `on_render` calls `self.recorder.write_frame(self.ctx.fbo)` | WIRED    | app.py line 36: `from bigbangsim.capture.recorder import VideoRecorder`; `self.recorder` used at lines 117-118, 238-241, 319-320, 457-473, 516-517 |
| `bigbangsim/capture/recorder.py` | FFmpeg subprocess              | `subprocess.Popen` with rawvideo pipe                     | WIRED    | recorder.py line 88: `self._process = subprocess.Popen(cmd, stdin=subprocess.PIPE, ...)`; stdin piped at line 113 |
| `bigbangsim/app.py`           | simulation update timing          | `effective_frame_time` from `recorder.frame_time_override` | WIRED    | app.py lines 237-251: all 4 subsystems use `effective_frame_time` during recording             |

### Data-Flow Trace (Level 4)

No dynamic data rendering artifacts in this phase. All artifacts are capture utilities (write to disk/subprocess), config persistence (read/write JSON), and key handlers. Level 4 data-flow trace is not applicable — the "data" is framebuffer pixels read from GPU and written to files/pipes, which is fully verified by the test suite with mocked FBO objects.

### Behavioral Spot-Checks

| Behavior                                | Command                                                                                                        | Result                                         | Status  |
|-----------------------------------------|----------------------------------------------------------------------------------------------------------------|------------------------------------------------|---------|
| `take_screenshot` importable            | `from bigbangsim.capture.screenshot import take_screenshot; print(type(take_screenshot))`                      | `<class 'function'>`                           | PASS    |
| `VideoRecorder` importable and functional | `from bigbangsim.capture.recorder import VideoRecorder; r=VideoRecorder(100,100); print(r.recording, r.frame_time_override)` | `False None`                    | PASS    |
| `save_window_state`/`load_window_state` importable | `from bigbangsim.config import save_window_state, load_window_state; print(type(save_window_state))` | `<class 'function'>`               | PASS    |
| Phase-specific tests (20 tests)         | `python -m pytest tests/test_screenshot.py tests/test_fullscreen.py tests/test_video_recorder.py -v`           | 20 passed                                      | PASS    |
| Full test suite (no regressions)        | `python -m pytest tests/ -q`                                                                                   | 417 passed, 1 warning (PyGLM deprecation only) | PASS    |

### Requirements Coverage

| Requirement | Source Plan | Description                                                                                        | Status    | Evidence                                                                                                     |
|-------------|-------------|----------------------------------------------------------------------------------------------------|-----------|--------------------------------------------------------------------------------------------------------------|
| CAPT-01     | 05-01       | User can capture high-resolution screenshots at any moment via keypress (PNG format)               | SATISFIED | `take_screenshot` reads `ctx.fbo`, flips vertically, saves `bigbangsim_*.png`; F12 wired in `on_key_event`  |
| RNDR-05     | 05-01       | Application supports fullscreen toggle and remembers window state                                  | SATISFIED | F11 toggles `wnd.fullscreen`; `save_window_state`/`load_window_state` persist JSON to LOCALAPPDATA          |
| CAPT-02     | 05-02       | Full cinematic run can be recorded to MP4 via FFmpeg subprocess with frame-locked capture          | SATISFIED | `VideoRecorder` launches FFmpeg with `-f rawvideo -pix_fmt rgb24 -vcodec libx264`; `write_frame` pipes flipped frames |
| CAPT-03     | 05-02       | Video recording decoupled from real-time playback (frame-locked) so output quality is GPU-independent | SATISFIED | `frame_time_override` returns `1.0/fps` when recording; all 4 subsystems use `effective_frame_time` in `on_render` |

No orphaned requirements found. REQUIREMENTS.md confirms all 4 IDs map to Phase 5 with status "Complete".

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | — | — | — | — |

No TODO/FIXME/placeholder comments, empty returns, or stub indicators found in any phase 05 modified file.

Note: `pass` in app.py line 130 (`except Exception: pass`) is intentional defensive coding for a backend that may not support `wnd.position`/`wnd.size` set — not a stub.

### Human Verification Required

The following behaviors require running the application and cannot be verified programmatically:

**1. F12 Screenshot End-to-End**

**Test:** Run the application, wait for any era to render, press F12.
**Expected:** A `bigbangsim_*.png` file appears in the `screenshots/` subdirectory of the working directory. The image shows the full composited frame including HUD overlay, with correct top-to-bottom orientation (not flipped).
**Why human:** Requires GPU context — the test suite mocks `fbo.read()`. Actual vertical flip correctness and HUD inclusion can only be verified visually.

**2. F11 Fullscreen Toggle**

**Test:** Run the application, press F11.
**Expected:** Window switches to fullscreen mode. Press F11 again — window returns to previous windowed size/position.
**Why human:** Fullscreen toggle behavior depends on OS window manager and moderngl-window backend. Cannot test without a live window.

**3. Window State Persistence Across Runs**

**Test:** Run the application, resize/move the window, close it. Relaunch.
**Expected:** Window reopens at the same position and size as when closed.
**Why human:** Requires two separate app invocations and visual inspection of window placement.

**4. F9 Video Recording (FFmpeg must be installed)**

**Test:** Install FFmpeg, run the application, press F9. Let it record for a few seconds. Press F9 again.
**Expected:** A `bigbangsim_*.mp4` file appears in the working directory. The video plays back at smooth 60fps, with correct colors, top-to-bottom orientation, and simulation advancing at consistent speed.
**Why human:** Requires FFmpeg installed and a live GPU context. Frame quality and timing correctness require human review of the output file.

**5. HUD Recording Indicator Visibility**

**Test:** With FFmpeg installed, press F9 to start recording.
**Expected:** The bottom-right controls hint panel shows red "F9: Record [REC]" text. The window title bar shows " | REC" appended.
**Why human:** Color rendering and imgui text display require visual inspection.

### Gaps Summary

No gaps found. All 8 observable truths are verified against the codebase. All 7 required artifacts exist with substantive implementations. All 5 key links are fully wired. The full test suite passes with 417 tests and 0 failures.

---

_Verified: 2026-03-28T22:30:00Z_
_Verifier: Claude (gsd-verifier)_
