# Phase 5: Capture & Polish - Research

**Researched:** 2026-03-28
**Domain:** Screenshot capture, video recording, fullscreen toggle, window state persistence
**Confidence:** HIGH

## Summary

Phase 5 adds the final user-facing features to BigBangSim: screenshot capture (PNG via Pillow), video recording (MP4 via FFmpeg subprocess pipe), fullscreen toggle, and window state persistence between sessions. This is the final phase -- all rendering, simulation, HUD, and camera systems are already complete from Phases 1-4.

The technical approach is well-established and low-risk. Pillow is already installed (12.1.1). The moderngl-window library has built-in screenshot utilities (`moderngl_window.screenshot.create`) and native fullscreen support via the pyglet backend (`wnd.fullscreen` property, F11 key toggle). FFmpeg is NOT installed on the target machine but this is documented as a known risk with graceful degradation -- video recording should be disabled with clear install instructions when FFmpeg is absent.

**Primary recommendation:** Use moderngl-window's built-in screenshot utility for PNG capture, subprocess.Popen with rawvideo pipe for FFmpeg frame-locked recording, and the pyglet backend's native fullscreen toggle with JSON-file state persistence in the user's APPDATA directory.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RNDR-05 | Application supports fullscreen toggle and remembers window state | moderngl-window pyglet backend supports `wnd.fullscreen` property setter, F11 key built-in, `wnd.position`/`wnd.size` readable; JSON file in APPDATA for persistence; `on_close()` callback available for saving state |
| CAPT-01 | User can capture high-resolution screenshots at any moment via keypress (PNG format) | moderngl-window ships `screenshot.create()` utility; reads from `ctx.fbo` (default framebuffer) or `hdr_fbo`; Pillow 12.1.1 already installed; `Image.frombytes()` + vertical flip pattern well-documented |
| CAPT-02 | Full cinematic run can be recorded to MP4 via ffmpeg subprocess with frame-locked capture | subprocess.Popen with `-f rawvideo -pix_fmt rgb24 -r FPS -i pipe:0 -vcodec libx264 -pix_fmt yuv420p` pattern; pipe raw bytes from `fbo.read()` to FFmpeg stdin; no Python wrapper library needed |
| CAPT-03 | Video recording decoupled from real-time playback (frame-locked) | Frame-locked mode: override `on_render` timing to advance simulation by exactly 1/FPS per frame regardless of wall clock; read framebuffer after each render; pipe to FFmpeg at declared FPS |
</phase_requirements>

## Standard Stack

### Core (Already Installed)
| Library | Version | Purpose | Already Installed |
|---------|---------|---------|-------------------|
| Pillow | 12.1.1 | PNG screenshot capture via `Image.frombytes()` | YES |
| moderngl | 5.12.0 | Framebuffer read via `fbo.read()` | YES |
| moderngl-window | 3.1.1 | Screenshot utility, fullscreen toggle, window events | YES |
| imgui-bundle | (installed) | HUD controls hint update for new keybindings | YES |

### External Tool
| Tool | Version | Purpose | Installed |
|------|---------|---------|-----------|
| FFmpeg | system | MP4 video encoding via subprocess pipe | NO - must detect and degrade gracefully |

### No New Dependencies
No new Python packages need to be added to `pyproject.toml`. Pillow is already installed (not in pyproject.toml but available). It SHOULD be added to pyproject.toml dependencies for completeness.

## Architecture Patterns

### Recommended Module Structure
```
bigbangsim/
  capture/
    __init__.py
    screenshot.py      # Screenshot capture (CAPT-01)
    recorder.py        # Video recorder with FFmpeg pipe (CAPT-02, CAPT-03)
  config.py            # Add window state persistence path
  app.py               # Add key handlers, fullscreen toggle, on_close, recording hooks
```

### Pattern 1: Screenshot Capture (CAPT-01)
**What:** Read the default framebuffer after post-processing renders to screen, save as PNG.
**When to use:** On keypress (e.g., F12 or P).
**Implementation:**

```python
# Use moderngl-window's built-in screenshot utility
from moderngl_window.screenshot import create as screenshot_create

def take_screenshot(self):
    """Capture current frame as PNG screenshot."""
    # ctx.fbo is the default framebuffer (screen) after end_scene() renders to it
    screenshot_create(
        source=self.ctx.fbo,
        file_format="png",
        name=f"bigbangsim_{timestamp}.png",
        mode="RGB",
        alignment=1,
    )
```

**Key detail:** The screenshot must be taken AFTER `end_scene()` (which tone-maps and composites to the default FBO) but BEFORE the next frame clears it. The current render order in `on_render` is: render scene -> `end_scene()` -> render HUD -> swap buffers. Screenshots should capture AFTER HUD rendering to include the overlay, or provide an option to capture without HUD.

### Pattern 2: Frame-Locked Video Recording (CAPT-02, CAPT-03)
**What:** Override timing to produce exactly one frame per 1/FPS interval, pipe raw pixels to FFmpeg.
**When to use:** User presses record key; simulation runs in frame-locked mode.

```python
import subprocess
import shutil

class VideoRecorder:
    """Frame-locked video recorder using FFmpeg subprocess pipe."""

    def __init__(self, width, height, fps=60, output_path="output.mp4"):
        self.width = width
        self.height = height
        self.fps = fps
        self.output_path = output_path
        self.process = None
        self.recording = False

    def start(self):
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path is None:
            raise RuntimeError("FFmpeg not found in PATH")

        cmd = [
            ffmpeg_path,
            '-y',                       # Overwrite output
            '-f', 'rawvideo',           # Input format
            '-vcodec', 'rawvideo',      # Input codec
            '-s', f'{self.width}x{self.height}',  # Frame size
            '-pix_fmt', 'rgb24',        # Pixel format (3 bytes per pixel)
            '-r', str(self.fps),        # Input frame rate
            '-i', 'pipe:0',            # Read from stdin
            '-vcodec', 'libx264',       # H.264 output codec
            '-pix_fmt', 'yuv420p',      # Output pixel format (compatibility)
            '-preset', 'medium',        # Encoding speed/quality tradeoff
            '-crf', '18',              # Quality (lower = better, 18 = visually lossless)
            self.output_path,
        ]
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.recording = True

    def write_frame(self, fbo):
        """Read framebuffer and pipe raw RGB data to FFmpeg."""
        if not self.recording or self.process is None:
            return
        # Read RGB data from framebuffer (bottom-to-top in OpenGL)
        data = fbo.read(components=3, alignment=1)
        # Flip vertically (OpenGL origin is bottom-left, video is top-left)
        frame_size = self.width * 3
        rows = [data[i:i + frame_size] for i in range(0, len(data), frame_size)]
        flipped = b''.join(reversed(rows))
        try:
            self.process.stdin.write(flipped)
        except BrokenPipeError:
            self.stop()

    def stop(self):
        if self.process and self.process.stdin:
            self.process.stdin.close()
            self.process.wait()
        self.recording = False
        self.process = None
```

**Frame-locking strategy (CAPT-03):** During recording, the simulation should NOT use wall-clock time. Instead, each call to `on_render` should advance the simulation by exactly `1/recording_fps` seconds. This ensures output quality is independent of GPU speed. The key change is in `on_render`:

```python
if self.recorder and self.recorder.recording:
    # Frame-locked: advance by exactly 1 frame duration
    frame_time = 1.0 / self.recorder.fps
    # ... rest of render with this fixed frame_time ...
    # After rendering, capture frame
    self.recorder.write_frame(self.ctx.fbo)
```

### Pattern 3: Fullscreen Toggle (RNDR-05)
**What:** Toggle fullscreen via F11 (or custom key), remember state.
**Implementation:**

moderngl-window's pyglet backend already supports fullscreen:
- `self.wnd.fullscreen = True/False` toggles fullscreen via pyglet
- `self.wnd.fullscreen_key` defaults to F11 (already wired in BaseWindow)
- The built-in F11 handling in BaseWindow toggles fullscreen automatically

**Important:** The F11 fullscreen key is handled internally by the window backend. We do NOT need to add it to `on_key_event`. However, if we want to use a different key (e.g., F) or add additional behavior (like saving state), we should add custom handling.

The `on_resize` callback already exists and handles camera aspect, postfx resize, transition resize, and imgui resize. Fullscreen toggle triggers `on_resize` automatically.

### Pattern 4: Window State Persistence (RNDR-05)
**What:** Save/restore window position, size, and fullscreen state between sessions.
**When to use:** On close (save) and on startup (restore).

```python
import json
from pathlib import Path
import os

def _get_settings_path() -> Path:
    """Get cross-platform settings file path."""
    # Windows: use LOCALAPPDATA; fallback to home directory
    base = os.environ.get('LOCALAPPDATA', str(Path.home()))
    settings_dir = Path(base) / "BigBangSim"
    settings_dir.mkdir(parents=True, exist_ok=True)
    return settings_dir / "window_state.json"

def save_window_state(wnd):
    """Save window position, size, fullscreen to JSON."""
    state = {
        "position": list(wnd.position),
        "size": list(wnd.size),
        "fullscreen": wnd.fullscreen,
    }
    path = _get_settings_path()
    path.write_text(json.dumps(state, indent=2))

def load_window_state() -> dict | None:
    """Load saved window state, or None if not found."""
    path = _get_settings_path()
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, KeyError):
            return None
    return None
```

**Applying restored state:** Window position and fullscreen state must be applied AFTER the window is created (in `__init__`), since `WindowConfig.__init__` is called after the window is created by `run_window_config`. The window object is accessible as `self.wnd`.

### Anti-Patterns to Avoid
- **Reading HDR FBO for screenshots:** The HDR FBO contains linear HDR data before tone mapping. Always read from `ctx.fbo` (default framebuffer) which has the final tone-mapped, gamma-corrected image.
- **Using wall-clock time during recording:** This makes video quality depend on GPU speed. Frame-locked recording MUST use fixed time steps.
- **Writing frame data without vertical flip:** OpenGL framebuffers have origin at bottom-left; video files expect top-left. Always flip vertically.
- **Blocking the render thread with FFmpeg:** FFmpeg subprocess runs asynchronously. Write to `stdin.pipe` which buffers. Large frames (4K) may need a larger pipe buffer.
- **Saving window state on every frame:** Only save on close (`on_close`). JSON write on every frame would tank performance.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Screenshot to PNG | Manual pixel reading + PNG encoding | `moderngl_window.screenshot.create()` | Handles framebuffer read, vertical flip, Pillow conversion, timestamped filename, and file saving in 1 call |
| FFmpeg detection | Manual PATH scanning | `shutil.which("ffmpeg")` | Standard library, cross-platform, handles PATH correctly |
| Fullscreen toggle | Manual pyglet window mode switching | `self.wnd.fullscreen = not self.wnd.fullscreen` | moderngl-window handles the pyglet backend call internally |
| Settings directory | Hardcoded paths | `os.environ.get('LOCALAPPDATA')` + fallback | Cross-platform pattern; Windows-primary but works everywhere |

## Common Pitfalls

### Pitfall 1: Framebuffer Read After HUD vs Before HUD
**What goes wrong:** Screenshot captures frame without HUD overlay, or only captures the HUD without the scene.
**Why it happens:** The render pipeline renders scene to HDR FBO, then tone-maps to default FBO, then renders imgui HUD to default FBO. Reading `ctx.fbo` at different points gives different results.
**How to avoid:** Take the screenshot AFTER `imgui.render()` and `self.imgui_renderer.render()` but BEFORE swap_buffers. This captures the complete composited frame. In the `on_render` method, the screenshot call should be the LAST thing before the method returns (moderngl-window handles swap_buffers after on_render).
**Warning signs:** Screenshots show black screen or missing HUD.

### Pitfall 2: Vertical Flip for Video Frames
**What goes wrong:** Recorded video is upside down.
**Why it happens:** OpenGL framebuffer origin is bottom-left, but video formats expect top-left origin.
**How to avoid:** Flip frame data vertically before piping to FFmpeg. Can be done with row-reversal on the raw bytes, or use FFmpeg's `-vf vflip` filter.
**Warning signs:** Video plays upside down.

### Pitfall 3: FFmpeg Pipe Blocking
**What goes wrong:** Application freezes or stutters during recording.
**Why it happens:** FFmpeg's stdin pipe buffer fills up if encoding can't keep pace with frame generation. Default pipe buffer is often too small for high-res frames.
**How to avoid:** Use `subprocess.PIPE` for stdin (Python handles buffering), write frames in the render thread (not a separate thread to avoid OpenGL context issues), and consider reducing resolution for recording. If stuttering occurs, `-preset ultrafast` in FFmpeg trades quality for speed.
**Warning signs:** Application hangs on `stdin.write()`, broken pipe errors.

### Pitfall 4: Frame-Locked Timing Drift
**What goes wrong:** Recorded video runs too fast/slow or has timing inconsistencies.
**Why it happens:** Using wall-clock `frame_time` during recording instead of a fixed time step.
**How to avoid:** When recording, pass `1.0 / recording_fps` as the frame_time to `sim.update()` instead of the real elapsed time. This makes every frame exactly 1/FPS apart, regardless of how long rendering actually takes.
**Warning signs:** Video playback speed doesn't match expected duration.

### Pitfall 5: Window State Restore with Invalid Coordinates
**What goes wrong:** Window opens off-screen after monitor configuration change.
**Why it happens:** Saved position was on an external monitor that's no longer connected.
**How to avoid:** After restoring position, validate that the window is at least partially visible on a current monitor. Simple approach: clamp position to (0, 0) minimum. More robust: skip position restore if coordinates seem unreasonable (negative or beyond typical screen bounds like 4000).
**Warning signs:** Application appears to not start (window is actually off-screen).

### Pitfall 6: FFmpeg Not Installed -- Silent Failure
**What goes wrong:** User presses record key, nothing happens, no error shown.
**Why it happens:** FFmpeg is not in PATH, and the error is swallowed silently.
**How to avoid:** Check for FFmpeg at startup with `shutil.which("ffmpeg")`. Show a clear message in the HUD if recording is attempted but FFmpeg is unavailable. Disable the recording keybind or show an error notification.
**Warning signs:** No video file produced, no error messages visible.

### Pitfall 7: Pillow Not in pyproject.toml
**What goes wrong:** Fresh install from pyproject.toml fails to capture screenshots because Pillow is not declared as a dependency.
**Why it happens:** Pillow was installed as a transitive dependency of imgui-bundle or manually, but not listed in pyproject.toml.
**How to avoid:** Add `Pillow>=12` to the `dependencies` list in pyproject.toml.
**Warning signs:** `ImportError: No module named 'PIL'` on clean install.

## Code Examples

### Screenshot Capture with moderngl-window Utility
```python
# Source: moderngl_window.screenshot module (verified from installed source)
from moderngl_window.screenshot import create as screenshot_create
from datetime import datetime

def take_screenshot(ctx_fbo, output_dir="screenshots"):
    """Capture current default framebuffer to PNG."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_create(
        source=ctx_fbo,
        file_format="png",
        name=os.path.join(output_dir, f"bigbangsim_{timestamp}.png"),
        mode="RGB",
        alignment=1,
    )
```

### FFmpeg Subprocess Launch
```python
# Source: FFmpeg documentation + verified patterns
import subprocess
import shutil

def create_ffmpeg_process(width, height, fps, output_path):
    """Create an FFmpeg subprocess for raw frame piping."""
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        return None

    return subprocess.Popen(
        [
            ffmpeg_path,
            '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', f'{width}x{height}',
            '-pix_fmt', 'rgb24',
            '-r', str(fps),
            '-i', 'pipe:0',
            '-an',                    # No audio
            '-vcodec', 'libx264',
            '-pix_fmt', 'yuv420p',    # Widely compatible output format
            '-preset', 'medium',
            '-crf', '18',             # Near-lossless quality
            output_path,
        ],
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
```

### Fullscreen Toggle
```python
# Source: moderngl-window BaseWindow API (verified from installed source)
# In BigBangSimApp.on_key_event:
elif key == keys.F11:
    self.wnd.fullscreen = not self.wnd.fullscreen
```

Note: moderngl-window already handles F11 via `fullscreen_key` property in the window backend. However, explicitly adding it to on_key_event allows us to also save the fullscreen state for persistence.

### Framebuffer Vertical Flip for Video
```python
# Source: OpenGL convention + Pillow pattern from moderngl-window screenshot.py
def flip_frame_bytes(data: bytes, width: int, height: int, components: int = 3) -> bytes:
    """Flip raw framebuffer bytes vertically for video output."""
    row_size = width * components
    rows = [data[i:i + row_size] for i in range(0, len(data), row_size)]
    return b''.join(reversed(rows))
```

Alternative: Use FFmpeg's `-vf vflip` filter in the command line to avoid flipping in Python. This moves the work to FFmpeg's optimized C code:
```python
# Add to FFmpeg command before output file:
'-vf', 'vflip',
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| opencv-python for video capture | FFmpeg subprocess pipe | N/A - always preferred for this use case | Avoids 50MB+ dependency, full FFmpeg codec access |
| Manual OpenGL pixel reading | `moderngl_window.screenshot.create()` | moderngl-window 2.x+ | One-call screenshot with auto flip and Pillow conversion |
| pyimgui for HUD updates | imgui-bundle | 2024-2025 | Already using imgui-bundle since Phase 4 |

## Open Questions

1. **FFmpeg Installation on Target Machine**
   - What we know: FFmpeg is NOT in PATH on the current Windows machine.
   - What's unclear: Whether the user wants to install FFmpeg or just have the feature degrade gracefully.
   - Recommendation: Implement graceful degradation -- detect at startup, show "FFmpeg not found" in HUD if user tries to record, provide install instructions. The code should still be fully testable without FFmpeg via mocking.

2. **Screenshot Output Directory**
   - What we know: `moderngl_window.screenshot` defaults to cwd if `SCREENSHOT_PATH` is not set.
   - What's unclear: Whether screenshots should go to a `screenshots/` subfolder, the cwd, or a user-configurable path.
   - Recommendation: Use a `screenshots/` subfolder in the project directory. Add `screenshots/` to `.gitignore`.

3. **Recording Resolution**
   - What we know: Recording at window resolution (1280x720 default) is straightforward. 4K would require rendering to an offscreen FBO.
   - What's unclear: Whether high-res recording beyond window size is needed.
   - Recommendation: Record at current window resolution. This satisfies the requirement. Higher-res recording is a v2 feature.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Pillow | Screenshot capture (CAPT-01) | YES | 12.1.1 | -- |
| FFmpeg | Video recording (CAPT-02, CAPT-03) | NO | -- | Disable recording feature, show install instructions |
| moderngl-window | Fullscreen toggle, screenshot util | YES | 3.1.1 | -- |
| imgui-bundle | HUD keybinding hints update | YES | installed | -- |
| Python | Runtime | YES | 3.14.3 | -- |

**Missing dependencies with no fallback:**
- None that block the core phase. All Python deps are available.

**Missing dependencies with fallback:**
- FFmpeg: Not installed. Video recording (CAPT-02, CAPT-03) will degrade gracefully. Code should detect absence via `shutil.which("ffmpeg")` at startup and disable recording UI. User can install via `winget install FFmpeg`.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.x |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `py -m pytest tests/ -x -q` |
| Full suite command | `py -m pytest tests/ -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CAPT-01 | Screenshot capture produces valid PNG bytes | unit | `py -m pytest tests/test_screenshot.py -x` | Wave 0 |
| CAPT-02 | VideoRecorder starts/stops FFmpeg process, writes frames | unit (mocked) | `py -m pytest tests/test_recorder.py -x` | Wave 0 |
| CAPT-03 | Frame-locked mode uses fixed timestep, not wall-clock | unit | `py -m pytest tests/test_recorder.py::test_frame_locked_timing -x` | Wave 0 |
| RNDR-05 | Window state save/load roundtrips correctly (JSON) | unit | `py -m pytest tests/test_window_state.py -x` | Wave 0 |
| RNDR-05 | Fullscreen toggle sets wnd.fullscreen property | unit (mocked) | `py -m pytest tests/test_window_state.py::test_fullscreen_toggle -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `py -m pytest tests/ -x -q`
- **Per wave merge:** `py -m pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_screenshot.py` -- covers CAPT-01 (screenshot capture logic, file creation, flip)
- [ ] `tests/test_recorder.py` -- covers CAPT-02, CAPT-03 (FFmpeg subprocess mock, frame-locked timing)
- [ ] `tests/test_window_state.py` -- covers RNDR-05 (save/load JSON, fullscreen toggle, position validation)

Note: All GPU operations (framebuffer reads, FFmpeg piping) require mocked moderngl contexts, following the established Phase 2 pattern of `MagicMock`-based testing.

## Sources

### Primary (HIGH confidence)
- moderngl-window 3.1.1 installed source -- `moderngl_window.screenshot` module, `BaseWindow.fullscreen` property, `WindowConfig.on_close` callback (verified by `inspect.getsource()`)
- moderngl-window 3.1.1 installed source -- `create_window_config_instance` window creation flow, argparse flags (`--fullscreen`, `--size`)
- ModernGL 5.12.0 installed -- `Framebuffer.read()`, `Context.fbo` default framebuffer
- Pillow 12.1.1 installed -- `Image.frombytes()` API

### Secondary (MEDIUM confidence)
- [moderngl-window screenshot.py on GitHub](https://github.com/moderngl/moderngl-window/blob/master/moderngl_window/screenshot.py) -- full source verified against installed version
- [ModernGL Framebuffer docs](https://moderngl.readthedocs.io/en/latest/reference/framebuffer.html) -- Framebuffer.read() parameters
- [FFmpeg with Python (Gumlet)](https://www.gumlet.com/learn/ffmpeg-python/) -- subprocess pipe pattern
- [Read and write video frames in Python using FFMPEG (Zulko)](http://zulko.github.io/blog/2013/09/27/read-and-write-video-frames-in-python-using-ffmpeg/) -- rawvideo pipe pattern

### Tertiary (LOW confidence)
- None -- all findings verified against installed libraries or official documentation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already installed and verified; APIs inspected via source
- Architecture: HIGH -- screenshot utility exists in moderngl-window; FFmpeg pipe pattern is well-established; fullscreen API verified
- Pitfalls: HIGH -- derived from code inspection of actual render pipeline and OpenGL conventions

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable libraries, no breaking changes expected)
