---
phase: 01-foundation
plan: 03
subsystem: rendering
tags: [moderngl, glsl, opengl, camera, orbit-camera, coordinate-transforms, timeline-bar]

# Dependency graph
requires:
  - phase: 01-foundation/01
    provides: "Cosmological constants, PhysicsState dataclass"
  - phase: 01-foundation/02
    provides: "SimulationEngine, TimelineController, CosmologyModel, ERAS"
provides:
  - "DampedOrbitCamera with exponential velocity damping and dvec3 accessors"
  - "Camera-relative coordinate transforms (PHYS-07) for float32 precision preservation"
  - "GLSL 4.30 shaders for test scene and timeline bar"
  - "BigBangSimApp WindowConfig with render loop, controls, and timeline overlay"
  - "Launchable application: python -m bigbangsim"
affects: [02-particles, 03-visuals, 04-audio, 05-polish]

# Tech tracking
tech-stack:
  added: [moderngl, moderngl-window, PyGLM, GLSL 4.30]
  patterns: [camera-relative rendering, exponential velocity damping, fixed-timestep render loop, NDC overlay rendering]

key-files:
  created:
    - bigbangsim/app.py
    - bigbangsim/rendering/camera.py
    - bigbangsim/rendering/coordinates.py
    - bigbangsim/shaders/test_scene.vert
    - bigbangsim/shaders/test_scene.frag
    - bigbangsim/shaders/timeline_bar.vert
    - bigbangsim/shaders/timeline_bar.frag
    - tests/test_camera.py
    - tests/test_coordinates.py
    - tests/test_controls.py
  modified:
    - bigbangsim/__main__.py

key-decisions:
  - "Used bytes(matrix) for glm.mat4 to moderngl uniform upload -- confirmed working with PyGLM 2.8.3"
  - "Corrected moderngl-window 3.1.1 callback names: on_mouse_drag_event, on_mouse_scroll_event (plan had mouse_drag_event)"
  - "Used keys.EQUAL instead of keys.PLUS for speed increase (PLUS not in BaseKeys)"

patterns-established:
  - "PHYS-07 camera-relative rendering: double-precision lookAt in Python, cast to float32 for GPU"
  - "Exponential velocity damping: impulse on input, decay = damping^dt each frame"
  - "NDC overlay rendering: disable depth test, render 2D quads in clip space for HUD elements"
  - "Shader loading pattern: _load_shader(name) reads .vert/.frag from resource_dir"

requirements-completed: [CAMR-01, CAMR-04, PHYS-07]

# Metrics
duration: 6min
completed: 2026-03-28
---

# Phase 1 Plan 3: Application Shell Summary

**OpenGL 4.3 window with damped orbit camera, play/pause/speed controls, camera-relative rendering (PHYS-07), and era-colored timeline bar overlay**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-28T04:31:15Z
- **Completed:** 2026-03-28T04:37:53Z
- **Tasks:** 3 (2 auto + 1 checkpoint auto-approved)
- **Files modified:** 11

## Accomplishments
- DampedOrbitCamera with exponential velocity damping, orbit/pan/zoom, and double-precision position accessors for PHYS-07
- Camera-relative coordinate transform pipeline: float64 subtraction in Python, float32 upload to GPU -- prevents precision breakdown at large cosmic scales
- BigBangSimApp with test scene (grid, RGB axes, 500 particle cloud), timeline bar with 11 era-colored segments and progress indicator
- Full input handling: spacebar pause, +/- speed control, mouse orbit/zoom, escape to quit
- 87 total tests passing (28 new: 11 camera, 7 coordinates, 1 PHYS-07 wiring, 9 controls)

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing tests for camera + coordinates** - `322dd97` (test)
1. **Task 1 (GREEN): Camera, coordinates, GLSL shaders** - `7b5aab9` (feat)
2. **Task 2: Application window + controls + timeline bar** - `451ee74` (feat)
3. **Task 3: Visual verification** - Auto-approved (checkpoint, no commit)

## Files Created/Modified
- `bigbangsim/app.py` - Main WindowConfig app with render loop, input handling, test scene, and timeline bar
- `bigbangsim/rendering/camera.py` - DampedOrbitCamera with exponential velocity damping and dvec3 accessors
- `bigbangsim/rendering/coordinates.py` - Camera-relative transforms (PHYS-07) and era position normalization
- `bigbangsim/shaders/test_scene.vert` - Vertex shader with projection/view/model uniforms
- `bigbangsim/shaders/test_scene.frag` - Fragment shader with vertex color passthrough
- `bigbangsim/shaders/timeline_bar.vert` - NDC 2D vertex shader for timeline overlay
- `bigbangsim/shaders/timeline_bar.frag` - Fragment shader with progress/era_progress uniforms
- `bigbangsim/__main__.py` - Updated entry point to launch BigBangSimApp.run()
- `tests/test_camera.py` - 11 tests for camera init, damping, clamping, matrices
- `tests/test_coordinates.py` - 7 tests for transforms, normalization, and PHYS-07 wiring
- `tests/test_controls.py` - 9 tests for pause, speed control, paused update behavior

## Decisions Made
- Used `bytes(matrix)` for glm.mat4 to moderngl uniform upload (confirmed working with PyGLM 2.8.3)
- Corrected moderngl-window 3.1.1 callback names to `on_mouse_drag_event` and `on_mouse_scroll_event` (plan had incorrect names)
- Used `keys.EQUAL` for speed increase since `keys.PLUS` is not in moderngl-window BaseKeys

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Corrected moderngl-window callback method signatures**
- **Found during:** Task 2 (Application window implementation)
- **Issue:** Plan specified `mouse_drag_event` and `mouse_scroll_event` but moderngl-window 3.1.1 uses `on_mouse_drag_event` and `on_mouse_scroll_event`
- **Fix:** Used correct API method names verified via inspect of WindowConfig class
- **Files modified:** bigbangsim/app.py
- **Verification:** Method signatures match WindowConfig base class
- **Committed in:** 451ee74 (Task 2 commit)

**2. [Rule 3 - Blocking] Corrected on_render parameter name**
- **Found during:** Task 2 (Application window implementation)
- **Issue:** Plan used `frametime` parameter but moderngl-window signature is `frame_time`
- **Fix:** Used `frame_time` matching the actual WindowConfig.on_render signature
- **Files modified:** bigbangsim/app.py
- **Verification:** Matches `inspect.signature(WindowConfig.on_render)`
- **Committed in:** 451ee74 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 blocking -- API name mismatches)
**Impact on plan:** Both fixes required for runtime correctness. No scope creep.

## Issues Encountered
None beyond the API name corrections documented above.

## Known Stubs
None -- all code paths are fully wired to real data sources.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 1 foundation complete: constants, cosmology, simulation engine, camera, coordinates, app shell, and timeline bar all working
- Ready for Phase 2 particle system: the render loop, camera-relative transforms, and GLSL shader loading pattern are established
- The test scene (grid + particle cloud) serves as a visual reference during Phase 2 development

---
*Phase: 01-foundation*
*Completed: 2026-03-28*

## Self-Check: PASSED

All 11 files verified present. All 3 commit hashes verified in git log. 87 tests passing.
