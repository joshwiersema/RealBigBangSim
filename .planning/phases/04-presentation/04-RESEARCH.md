# Phase 4: Presentation - Research

**Researched:** 2026-03-28
**Domain:** imgui-bundle HUD overlay, cinematic auto-camera, milestone system
**Confidence:** HIGH

## Summary

Phase 4 adds the educational presentation layer to BigBangSim: an imgui-bundle HUD with era labels, live physics readouts, contextual explanations, milestone notifications, and a cinematic auto-camera system. The existing codebase provides a solid foundation -- PhysicsState already exposes all needed readout fields (temperature, matter_density, radiation_density, scale_factor, current_era, era_progress), the 11 eras are well-defined with descriptions, and the timeline system provides screen-to-cosmic mapping for milestone triggering.

The critical integration point is that imgui-bundle 1.92.601 has Python 3.14 wheels and integrates natively with moderngl-window 3.1.1 via `moderngl_window.integrations.imgui_bundle.ModernglWindowRenderer`. The imgui rendering must happen AFTER post-processing (bloom/tonemap) to avoid bloom bleeding into HUD text -- this matches the existing pattern where the GLSL timeline bar already renders after `postfx.end_scene()`. The existing GLSL timeline bar will be REPLACED by an imgui-based timeline bar for visual consistency and richer interactivity.

The auto-camera system extends the existing `DampedOrbitCamera` with a `CinematicCameraController` that drives azimuth, elevation, radius, and target through per-era keyframes interpolated with Catmull-Rom splines. The user can toggle between auto and free-orbit modes, with smooth handoff in both directions.

**Primary recommendation:** Install imgui-bundle, create a `presentation/` sub-package under `bigbangsim/` containing hud.py, milestones.py, camera_controller.py, and educational_content.py. Wire into app.py render loop after postfx.end_scene().

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CAMR-02 | Cinematic auto-camera follows scripted path through all 11 eras with smooth transitions | CinematicCameraController with per-era keyframes + Catmull-Rom interpolation |
| CAMR-03 | User can pause auto-camera and freely orbit/zoom, then resume cinematic mode | Camera mode toggle with smooth handoff; io.want_capture_mouse for input routing |
| PHYS-04 | ~20 milestone markers trigger at correct cosmic timestamps | MilestoneManager with cosmic_time triggers derived from published cosmological data |
| HUD-01 | Current era name displayed prominently with visual timeline bar | imgui window with era name text + custom-drawn timeline progress bar |
| HUD-02 | Live physics readouts (temperature, density, radiation density, scale factor) | imgui window reading PhysicsState fields, formatted in scientific notation with SI units |
| HUD-03 | Contextual educational explanations at key moments | Triggered by milestone system and era transitions; imgui overlay with fade-in/out |
| HUD-04 | HUD uses imgui-bundle with clean, non-intrusive PhET-style design | imgui-bundle 1.92.601 + ModernglWindowRenderer; transparent windows, minimal chrome |
| HUD-05 | HUD elements can be toggled on/off by user | H key binding toggles HUD visibility; individual panel toggles via imgui checkboxes |
</phase_requirements>

## Standard Stack

### Core (Phase 4 additions)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| imgui-bundle | 1.92.601 | HUD overlay, educational text, physics readouts | CLAUDE.md specifies. Wraps Dear ImGui v1.90.9+ with ImPlot. Native moderngl-window integration via ModernglWindowRenderer. Python 3.14 wheel confirmed available. |

### Already Installed (from prior phases)
| Library | Version | Purpose | Phase 4 Usage |
|---------|---------|---------|---------------|
| moderngl | 5.12.0 | OpenGL binding | Existing render pipeline |
| moderngl-window | 3.1.1 | Windowing, events | imgui integration module, event routing |
| PyGLM | 2.8.3 | 3D math | Camera spline math, matrix interpolation |
| NumPy | 2.4.3 | Arrays | Milestone data, camera keyframe arrays |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| imgui-bundle | pyimgui | CLAUDE.md decision: pyimgui wraps ancient ImGui v1.82; imgui-bundle wraps v1.90.9+ with ImPlot and native moderngl-window support. Not an option. |
| imgui-bundle | Custom GLSL text rendering | Weeks of work vs. built-in widget library. Violates "Don't Hand-Roll" principle. |
| Catmull-Rom splines | Linear keyframes | Visually jarring camera motion. Catmull-Rom passes through control points with C1 continuity. |

**Installation:**
```bash
py -3.14 -m pip install imgui-bundle==1.92.601
```

**Version verification:** imgui-bundle 1.92.601 confirmed on PyPI with cp314-cp314-win_amd64 wheel. Dry-run install succeeded on this machine.

## Architecture Patterns

### Recommended Project Structure
```
bigbangsim/
  presentation/           # NEW: Phase 4 presentation layer
    __init__.py
    hud.py                # HUDManager: imgui window layout, rendering
    milestones.py         # MilestoneManager: event triggers, notification queue
    camera_controller.py  # CinematicCameraController: auto-camera paths
    educational_content.py # Static educational text + milestone definitions
  app.py                  # MODIFIED: wire in imgui + presentation layer
  rendering/
    camera.py             # EXTENDED: add set_from_state() for camera handoff
```

### Pattern 1: imgui-bundle Integration with moderngl-window
**What:** Initialize imgui context and renderer in __init__, delegate all input events to imgui first, render HUD after post-processing.
**When to use:** Always -- this is the standard pattern from moderngl-window's official example.
**Example:**
```python
# Source: https://github.com/moderngl/moderngl-window/blob/master/examples/integration_imgui.py
from imgui_bundle import imgui
from moderngl_window.integrations.imgui_bundle import ModernglWindowRenderer

class BigBangSimApp(moderngl_window.WindowConfig):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        imgui.create_context()
        self.imgui_renderer = ModernglWindowRenderer(self.wnd)
        self.hud = HUDManager()
        # ... existing init code ...

    def on_render(self, time, frame_time):
        # ... existing render pipeline (simulation, particles, postfx) ...
        # AFTER postfx.end_scene() -- HUD renders to default framebuffer
        self._render_hud(state)

    def _render_hud(self, state):
        imgui.new_frame()
        self.hud.render(state, self.sim, self.milestones)
        imgui.render()
        self.imgui_renderer.render(imgui.get_draw_data())

    # ALL input events must be forwarded to imgui
    def on_key_event(self, key, action, modifiers):
        self.imgui_renderer.key_event(key, action, modifiers)
        io = imgui.get_io()
        if not io.want_capture_keyboard:
            # Existing key handling (SPACE, EQUAL, MINUS, ESCAPE)
            # Plus new: H for HUD toggle, C for camera mode toggle

    def on_mouse_drag_event(self, x, y, dx, dy):
        self.imgui_renderer.mouse_drag_event(x, y, dx, dy)
        io = imgui.get_io()
        if not io.want_capture_mouse:
            self.camera.on_mouse_drag(dx, dy)

    def on_mouse_scroll_event(self, x_offset, y_offset):
        self.imgui_renderer.mouse_scroll_event(x_offset, y_offset)
        io = imgui.get_io()
        if not io.want_capture_mouse:
            self.camera.on_scroll(y_offset)

    def on_mouse_position_event(self, x, y, dx, dy):
        self.imgui_renderer.mouse_position_event(x, y, dx, dy)

    def on_mouse_press_event(self, x, y, button):
        self.imgui_renderer.mouse_press_event(x, y, button)

    def on_mouse_release_event(self, x, y, button):
        self.imgui_renderer.mouse_release_event(x, y, button)

    def on_unicode_char_entered(self, char):
        self.imgui_renderer.unicode_char_entered(char)

    def on_resize(self, width, height):
        # ... existing resize logic ...
        self.imgui_renderer.resize(width, height)
```

### Pattern 2: Transparent HUD Windows (PhET Minimal Style)
**What:** Use imgui window flags to create non-intrusive, semi-transparent overlay panels.
**When to use:** All HUD panels -- era info, physics readouts, milestones, educational text.
**Example:**
```python
# Source: imgui-bundle Python API stubs (github.com/pthom/imgui_bundle)
HUD_FLAGS = (
    imgui.WindowFlags_.no_title_bar
    | imgui.WindowFlags_.no_resize
    | imgui.WindowFlags_.no_move
    | imgui.WindowFlags_.no_scrollbar
    | imgui.WindowFlags_.always_auto_resize
    | imgui.WindowFlags_.no_saved_settings
)

def render_era_panel(state, window_width):
    """Top-left: era name + description."""
    imgui.set_next_window_pos(imgui.ImVec2(20, 20))
    imgui.set_next_window_bg_alpha(0.6)
    imgui.begin("Era Info", None, HUD_FLAGS)
    era = ERAS[state.current_era]
    imgui.push_style_color(imgui.Col_.text, imgui.ImVec4(1.0, 0.9, 0.7, 1.0))
    # Large era name -- use push_font or scale
    imgui.text(era.name)
    imgui.pop_style_color()
    imgui.text(era.description)
    imgui.end()
```

### Pattern 3: Cinematic Camera with Catmull-Rom Splines
**What:** Per-era camera keyframes interpolated with Catmull-Rom for smooth cinematic paths.
**When to use:** Auto-camera mode traversing the 11 eras.
**Example:**
```python
# Catmull-Rom spline: passes through all control points with C1 continuity
# Pure Python implementation using PyGLM
import glm

def catmull_rom(p0, p1, p2, p3, t):
    """Catmull-Rom spline interpolation between p1 and p2.

    Args:
        p0, p1, p2, p3: Four control points (glm.vec3).
        t: Parameter in [0, 1] (0=p1, 1=p2).

    Returns:
        Interpolated glm.vec3 position.
    """
    t2 = t * t
    t3 = t2 * t
    return 0.5 * (
        (2.0 * p1) +
        (-p0 + p2) * t +
        (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2 +
        (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3
    )
```

### Pattern 4: Camera Mode Toggle with Smooth Handoff
**What:** User presses C (or clicks button) to switch between auto-camera and free orbit. When entering free mode, the camera state is captured. When resuming auto, the camera smoothly interpolates back to the scripted position.
**When to use:** CAMR-03 requirement.
**Example:**
```python
class CinematicCameraController:
    def __init__(self, camera: DampedOrbitCamera, eras):
        self.camera = camera
        self.auto_mode = True
        self.blend_back_timer = 0.0
        self.blend_back_duration = 1.5  # seconds to blend back to auto
        self.keyframes = self._build_keyframes(eras)

    def update(self, dt, era_index, era_progress):
        if self.auto_mode:
            target_state = self._evaluate_path(era_index, era_progress)
            if self.blend_back_timer > 0:
                # Smooth blend from free position back to scripted path
                alpha = 1.0 - (self.blend_back_timer / self.blend_back_duration)
                alpha = alpha * alpha * (3 - 2 * alpha)  # smoothstep
                self._apply_blended(target_state, alpha)
                self.blend_back_timer -= dt
            else:
                self._apply_camera_state(target_state)

    def toggle_mode(self):
        self.auto_mode = not self.auto_mode
        if self.auto_mode:
            self.blend_back_timer = self.blend_back_duration
```

### Anti-Patterns to Avoid
- **Rendering imgui BEFORE post-processing:** Bloom would bleed into HUD text, making it unreadable. Always render imgui AFTER postfx.end_scene().
- **Not forwarding ALL input events to imgui:** Missing any event handler (mouse_position_event, unicode_char_entered, etc.) causes imgui to malfunction -- hover detection fails, text input breaks.
- **Hardcoding pixel positions:** Use window-relative positioning that scales with resolution. imgui.get_io().display_size gives current window dimensions.
- **Blocking the render loop with milestone checks:** Use pre-sorted milestone list with a single index pointer, not linear scan every frame.
- **Modifying DampedOrbitCamera directly from auto-camera:** Use camera's existing setter/property interface (azimuth, elevation, radius, target). Don't bypass the damping system.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Text rendering on OpenGL | Custom font atlas + glyph rendering | imgui-bundle's built-in text rendering | Font loading, kerning, Unicode, DPI scaling are all solved |
| UI layout system | Manual NDC coordinate math | imgui window positioning + auto-sizing | imgui handles resize, DPI, overlap detection |
| Progress bar widget | Custom GLSL quad | imgui.progress_bar() | Built-in, styled, with overlay text support |
| Input event routing | Custom focus/capture system | imgui.get_io().want_capture_mouse/keyboard | Dear ImGui's built-in input capture tracking |
| Scientific notation formatting | Manual string formatting | Python f-strings with :.2e format | Python's built-in formatting is sufficient here |

**Key insight:** The existing GLSL timeline bar (timeline_bar.vert/frag + indicator geometry in app.py) should be REPLACED with an imgui-drawn equivalent. This eliminates the custom NDC coordinate math, VBO management, and hardcoded 1280px width in the fragment shader, while gaining resolution independence and visual consistency with the rest of the HUD.

## Common Pitfalls

### Pitfall 1: imgui Rendering Before Post-Processing
**What goes wrong:** Bloom/HDR tone mapping applies to HUD text, creating unreadable glowing UI.
**Why it happens:** Natural instinct is to add UI rendering inline with scene rendering.
**How to avoid:** Render imgui AFTER `postfx.end_scene()` returns to the default framebuffer. The existing code already renders the timeline bar after post-processing -- follow the same pattern.
**Warning signs:** HUD text appears blurry/glowing, colors are washed out.

### Pitfall 2: Missing imgui Event Handlers
**What goes wrong:** Mouse hover detection fails, text input doesn't work, scroll events are lost.
**Why it happens:** Only forwarding key_event and mouse_drag_event, forgetting mouse_position_event, mouse_press_event, mouse_release_event, and unicode_char_entered.
**How to avoid:** Forward ALL seven event types from WindowConfig to the imgui renderer: key_event, mouse_position_event, mouse_drag_event, mouse_scroll_event, mouse_press_event, mouse_release_event, unicode_char_entered.
**Warning signs:** imgui windows don't respond to clicks, hover highlights don't appear.

### Pitfall 3: Camera Auto-to-Free Handoff Jerk
**What goes wrong:** When switching from auto-camera back to free orbit, the camera snaps to the scripted position instead of smoothly blending.
**Why it happens:** Directly setting camera angles without transition period.
**How to avoid:** When resuming auto mode, capture current free-orbit state and smoothstep-blend to the scripted position over ~1.5 seconds.
**Warning signs:** Visible camera jump when pressing the camera toggle key.

### Pitfall 4: Milestone Triggers Fire Multiple Times
**What goes wrong:** A milestone notification shows repeatedly because the trigger condition remains true across multiple frames.
**Why it happens:** Checking `cosmic_time >= milestone_time` without tracking whether the milestone has already fired.
**How to avoid:** Maintain a `triggered: bool` flag per milestone, or use a sorted list with a monotonically advancing index.
**Warning signs:** Same notification pops up every frame for the duration of a cosmic era.

### Pitfall 5: OpenGL State Corruption from imgui
**What goes wrong:** After imgui renders, the next frame's particle rendering has wrong blend mode, scissor test enabled, etc.
**Why it happens:** imgui's OpenGL renderer changes blend mode, scissor rect, and other state.
**How to avoid:** The ModernglWindowRenderer handles state save/restore internally. But verify that DEPTH_TEST and BLEND states are correct at the start of each frame. The existing code already re-enables DEPTH_TEST after the timeline bar.
**Warning signs:** Particles render with wrong blending, clipped to a sub-rectangle of the screen.

### Pitfall 6: Timeline Bar Fragment Shader Hardcoded Width
**What goes wrong:** The existing `timeline_bar.frag` has `gl_FragCoord.x / 1280.0` hardcoded.
**Why it happens:** Phase 1 implementation used a fixed window width.
**How to avoid:** Replace the GLSL timeline bar entirely with an imgui-drawn version, which automatically handles any window size.
**Warning signs:** Timeline glow effect misaligned after window resize.

### Pitfall 7: PhysicsState Fields Missing for HUD
**What goes wrong:** HUD tries to display a field that PhysicsState doesn't have.
**Why it happens:** Assuming additional physics fields exist.
**How to avoid:** PhysicsState already has ALL needed fields: cosmic_time, scale_factor, temperature, matter_density, radiation_density, hubble_param, current_era, era_progress. No modifications needed to the simulation layer.
**Warning signs:** AttributeError at runtime.

## Code Examples

### imgui Window Flags for HUD Overlay
```python
# Source: imgui-bundle Python API stubs
# Combine flags for non-intrusive transparent HUD panels
HUD_FLAGS = (
    imgui.WindowFlags_.no_title_bar
    | imgui.WindowFlags_.no_resize
    | imgui.WindowFlags_.no_move
    | imgui.WindowFlags_.no_scrollbar
    | imgui.WindowFlags_.always_auto_resize
    | imgui.WindowFlags_.no_saved_settings
)
```

### Scientific Notation Formatting for Physics Readouts
```python
def format_physics_value(value: float, unit: str) -> str:
    """Format a physics value in scientific notation with SI unit."""
    if abs(value) < 1e-3 or abs(value) > 1e6:
        return f"{value:.2e} {unit}"
    else:
        return f"{value:.4f} {unit}"

# Examples:
# temperature: "2.73e+00 K" or "2725.0000 K"
# density: "9.47e-27 kg/m^3"
# scale_factor: "0.0010" (dimensionless)
```

### Milestone Data Structure
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Milestone:
    """A significant cosmic event with trigger and display data."""
    cosmic_time: float      # Seconds after Big Bang (trigger threshold)
    era_index: int           # Which era this belongs to
    name: str                # Short event name for notification
    description: str         # Educational explanation (2-3 sentences)
    temperature: float | None  # Temperature at this event (K), if applicable

# Example entries (scientifically sourced):
MILESTONES = [
    Milestone(1e-43, 0, "Planck Time",
        "The universe is one Planck time old. Quantum gravity effects dominate. "
        "All four fundamental forces are believed to be unified.", 1.4e32),
    Milestone(1e-36, 1, "Gravity Separates",
        "Gravity becomes a distinct force. The strong, weak, and electromagnetic "
        "forces remain unified as a single grand unified force.", 1e28),
    # ... ~18 more milestones ...
]
```

### imgui-Drawn Timeline Bar (Replacing GLSL Version)
```python
def render_timeline_bar(state, eras, window_width, window_height):
    """Draw timeline bar at bottom of screen using imgui draw list."""
    draw_list = imgui.get_foreground_draw_list()
    bar_height = 30.0
    bar_y = window_height - bar_height - 10.0
    bar_x = 20.0
    bar_width = window_width - 40.0

    total_screen = sum(e.screen_seconds for e in eras)
    cumulative = 0.0

    era_colors = [...]  # Same 11 colors as existing

    for i, era in enumerate(eras):
        x0 = bar_x + (cumulative / total_screen) * bar_width
        x1 = bar_x + ((cumulative + era.screen_seconds) / total_screen) * bar_width
        col = imgui.get_color_u32(imgui.ImVec4(*era_colors[i], 0.8))
        draw_list.add_rect_filled(imgui.ImVec2(x0, bar_y),
                                   imgui.ImVec2(x1, bar_y + bar_height), col)
        cumulative += era.screen_seconds

    # Progress indicator
    progress = state.era_progress  # Need overall progress, computed from sim
    indicator_x = bar_x + progress * bar_width
    draw_list.add_rect_filled(
        imgui.ImVec2(indicator_x - 2, bar_y - 3),
        imgui.ImVec2(indicator_x + 2, bar_y + bar_height + 3),
        imgui.get_color_u32(imgui.ImVec4(1, 1, 1, 1.0)),
    )
```

### Camera Keyframe Structure
```python
@dataclass
class CameraKeyframe:
    """Camera state at a specific point in the cinematic path."""
    azimuth: float       # Horizontal angle (degrees)
    elevation: float     # Vertical angle (degrees)
    radius: float        # Distance from target
    target: glm.vec3     # Look-at point
    fov: float           # Field of view (degrees)

# Per-era keyframes (11 eras, 1-2 keyframes each)
ERA_KEYFRAMES = {
    0: [CameraKeyframe(0, -15, 6.0, glm.vec3(0), 70)],      # Planck: close, wide
    1: [CameraKeyframe(30, -20, 7.0, glm.vec3(0), 65)],      # GUT: slight orbit
    2: [CameraKeyframe(60, -10, 12.0, glm.vec3(0), 75)],     # Inflation: pull back
    # ...
    7: [CameraKeyframe(180, -5, 20.0, glm.vec3(0), 55)],     # Dark Ages: far, narrow
    8: [CameraKeyframe(210, -25, 15.0, glm.vec3(0), 60)],    # First Stars: zoom in
    10: [CameraKeyframe(350, -30, 25.0, glm.vec3(0), 50)],   # LSS: panoramic
}
```

## Milestone Event List (Scientifically Sourced)

The following ~20 milestones are derived from the Chronology of the Universe (Wikipedia, sourced from Planck 2018, PDG, and standard cosmology textbooks). Cosmic times match published values.

| # | Cosmic Time (s) | Era | Event Name | Source |
|---|-----------------|-----|------------|--------|
| 1 | 1e-43 | 0 | Planck Time | Planck units (CODATA) |
| 2 | 1e-36 | 1 | Gravity Separates | GUT scale ~1e16 GeV |
| 3 | 1e-36 | 2 | Inflation Begins | Guth 1981, Planck 2018 |
| 4 | 1e-32 | 2 | Inflation Ends / Reheating | ~e-folds complete |
| 5 | 2e-11 | 3 | Electroweak Symmetry Breaking | T ~1e15 K |
| 6 | 2e-5 | 3 | QCD Phase Transition | T ~1.5e12 K (QGP to hadrons) |
| 7 | 1e-4 | 4 | First Protons & Neutrons | Quarks confine into baryons |
| 8 | 1.0 | 4 | Neutrino Decoupling | T ~1e10 K |
| 9 | 6.0 | 4 | Electron-Positron Annihilation | T ~5e9 K |
| 10 | 10.0 | 5 | Nucleosynthesis Begins | T ~1e9 K (1 MeV) |
| 11 | 180.0 | 5 | Deuterium Bottleneck Breaks | T ~8e8 K |
| 12 | 1200.0 | 5 | Nucleosynthesis Ends | T ~3e7 K; He-4 mass frac ~0.247 |
| 13 | 1.5e12 | 6 | Matter-Radiation Equality | ~47,000 years |
| 14 | 1.2e13 | 6 | Recombination / CMB Release | ~380,000 years; T ~3000 K |
| 15 | 1.2e13 | 7 | Dark Ages Begin | No luminous sources |
| 16 | 6.3e15 | 8 | First Stars Ignite | ~200 Myr; Population III |
| 17 | 7.9e15 | 8 | Reionization Begins | UV photons ionize IGM |
| 18 | 1.3e16 | 9 | First Galaxies Form | ~400 Myr; proto-galaxies |
| 19 | 3.2e16 | 9 | Reionization Complete | ~1 Gyr; IGM fully ionized |
| 20 | 3.1e17 | 10 | Dark Energy Dominance | ~9.8 Gyr; expansion accelerates |

Note: Cosmic times for milestones 16-20 are approximate. The existing `constants.py` and era boundaries in `eras.py` provide the exact boundaries; milestones are placed within those boundaries at physically motivated positions.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pyimgui (ImGui v1.82) | imgui-bundle (ImGui v1.90.9+) | 2024+ | ImPlot, docking, better Python typing, active maintenance |
| Custom GLSL HUD rendering | imgui overlay after post-processing | Standard pattern | Resolution-independent, rich widgets, minimal code |
| Linear camera keyframes | Catmull-Rom spline interpolation | Long-established | C1 continuous, passes through control points, cinematic feel |
| GLSL timeline bar (current) | imgui-drawn timeline bar | Phase 4 | Fixes hardcoded 1280px width, gains resolution independence |

**Deprecated/outdated:**
- pyimgui: Wraps ImGui v1.82; imgui-bundle wraps v1.90.9+. CLAUDE.md specifies imgui-bundle.
- The existing GLSL timeline_bar.vert/.frag: Will be replaced by imgui draw list equivalent. Remove the GLSL files and all timeline bar VBO/VAO code from app.py.

## Open Questions

1. **Font size for era names vs body text**
   - What we know: imgui-bundle supports loading custom fonts at different sizes. The default font is readable but small.
   - What's unclear: Whether to load a second font at 2x size for era names, or use push_font_size (if available in 1.92.601).
   - Recommendation: Start with default font, scale text using imgui.set_window_font_scale() for headers. If insufficient, load a second font instance at larger size in Wave 0.

2. **Milestone notification animation**
   - What we know: imgui doesn't have built-in toast/notification animations.
   - What's unclear: Exact visual treatment for milestone popups (fade in/out, slide, duration).
   - Recommendation: Use alpha animation (set_next_window_bg_alpha with time-based ramp). Show for 4-5 seconds, fade out over 1 second. Simple and effective.

3. **ImPlot for physics readout graphs**
   - What we know: imgui-bundle includes ImPlot which can render real-time line graphs.
   - What's unclear: Whether mini-graphs alongside numeric readouts add educational value or clutter.
   - Recommendation: Start with numeric readouts only (HUD-02). ImPlot graphs are a natural enhancement if space allows, but not required by the spec.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| imgui-bundle | HUD-01 through HUD-05 | Installable (not yet installed) | 1.92.601 | None -- core requirement |
| moderngl-window | imgui integration | Installed | 3.1.1 | -- |
| PyGLM | Camera spline math | Installed | 2.8.3 | -- |
| Python 3.14 | Runtime | Available | 3.14 | -- |
| pytest | Testing | Installed | 9.0.2 | -- |

**Missing dependencies with no fallback:**
- imgui-bundle must be installed before implementation begins: `py -3.14 -m pip install imgui-bundle==1.92.601`

**Missing dependencies with fallback:**
- None. All other dependencies are already installed.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | None (default pytest discovery) |
| Quick run command | `py -3.14 -m pytest tests/ -x -q` |
| Full suite command | `py -3.14 -m pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| HUD-01 | Era name + timeline bar rendered | unit (mock imgui) | `py -3.14 -m pytest tests/test_hud.py::test_era_panel_renders -x` | Wave 0 |
| HUD-02 | Physics readouts display correct values | unit | `py -3.14 -m pytest tests/test_hud.py::test_physics_readouts -x` | Wave 0 |
| HUD-03 | Educational explanations triggered correctly | unit | `py -3.14 -m pytest tests/test_milestones.py::test_educational_triggers -x` | Wave 0 |
| HUD-04 | imgui-bundle integration initializes | integration | `py -3.14 -m pytest tests/test_hud.py::test_imgui_init -x` | Wave 0 |
| HUD-05 | HUD toggle hides/shows elements | unit | `py -3.14 -m pytest tests/test_hud.py::test_hud_toggle -x` | Wave 0 |
| PHYS-04 | Milestones trigger at correct cosmic times | unit | `py -3.14 -m pytest tests/test_milestones.py::test_milestone_triggers -x` | Wave 0 |
| CAMR-02 | Auto-camera traverses all 11 eras | unit | `py -3.14 -m pytest tests/test_camera_controller.py::test_auto_camera_all_eras -x` | Wave 0 |
| CAMR-03 | Camera mode toggle + smooth handoff | unit | `py -3.14 -m pytest tests/test_camera_controller.py::test_mode_toggle -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `py -3.14 -m pytest tests/ -x -q`
- **Per wave merge:** `py -3.14 -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_hud.py` -- covers HUD-01, HUD-02, HUD-04, HUD-05
- [ ] `tests/test_milestones.py` -- covers PHYS-04, HUD-03
- [ ] `tests/test_camera_controller.py` -- covers CAMR-02, CAMR-03
- [ ] imgui-bundle install: `py -3.14 -m pip install imgui-bundle==1.92.601`

**Testing strategy:** Follow the established Phase 2 pattern of mock-based testing (MagicMock for moderngl.Context and imgui module). HUDManager, MilestoneManager, and CinematicCameraController should be testable without a GPU or window -- they produce render commands / state changes that can be verified through assertions on their public API. The Catmull-Rom spline function is pure math and directly unit-testable.

## Sources

### Primary (HIGH confidence)
- [moderngl-window imgui integration example](https://github.com/moderngl/moderngl-window/blob/master/examples/integration_imgui.py) -- official integration pattern, all 7 event handlers
- [imgui-bundle Python API stubs](https://github.com/pthom/imgui_bundle/blob/main/bindings/imgui_bundle/imgui/__init__.pyi) -- complete function signatures for all imgui functions
- [imgui-bundle PyPI](https://pypi.org/project/imgui-bundle/) -- version 1.92.601, Python 3.14 wheel confirmed
- [moderngl-window docs](https://moderngl-window.readthedocs.io/en/latest/) -- version 3.1.1, integration documentation
- [Chronology of the Universe (Wikipedia)](https://en.wikipedia.org/wiki/Chronology_of_the_universe) -- milestone timestamps sourced from Planck 2018 and standard cosmology
- [Catmull-Rom spline (Wikipedia)](https://en.wikipedia.org/wiki/Catmull%E2%80%93Rom_spline) -- spline mathematics for camera interpolation
- Existing codebase: `bigbangsim/simulation/state.py`, `eras.py`, `constants.py` -- PhysicsState fields, era definitions, cosmological constants

### Secondary (MEDIUM confidence)
- [Dear ImGui WantCaptureMouse docs](https://github.com/ocornut/imgui/issues/3916) -- input routing pattern (io.want_capture_mouse, io.want_capture_keyboard)
- [moderngl-window CHANGELOG](https://github.com/moderngl/moderngl-window/blob/master/CHANGELOG.md) -- 3.0.0 API overhaul confirmed imgui-bundle support
- [PhET minimal-text principles](https://phet.colorado.edu/) -- educational simulation design philosophy (referenced in CONTEXT.md)

### Tertiary (LOW confidence)
- None. All critical findings verified against official sources.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- imgui-bundle confirmed available with Python 3.14 wheel, native moderngl-window integration verified via official example
- Architecture: HIGH -- integration pattern is directly from moderngl-window's official example; render-after-postfx pattern established in existing codebase
- Pitfalls: HIGH -- all pitfalls derived from actual code inspection (hardcoded 1280px, timeline bar render order) and documented Dear ImGui patterns (event forwarding, input capture)
- Milestones: MEDIUM -- cosmic timestamps sourced from Wikipedia's Chronology of the Universe; verified against constants.py and eras.py boundaries

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable domain; imgui-bundle and moderngl-window both recently released)
