---
phase: 04-presentation
plan: 03
subsystem: ui
tags: [imgui-bundle, hud, overlay, milestones, camera-controller, timeline-bar]

requires:
  - phase: 04-01
    provides: milestone system and educational content data
  - phase: 04-02
    provides: cinematic camera controller with Catmull-Rom splines
provides:
  - HUDManager with 6 imgui panels (era, physics, education, milestones, timeline, controls)
  - Full presentation layer integration into app.py render loop
  - imgui event forwarding for all 7 moderngl-window input types
  - Replacement of GLSL timeline bar with imgui draw list version
affects: [05-audio, future-ui-enhancements]

tech-stack:
  added: [imgui-bundle 1.92.601, moderngl_window.integrations.imgui_bundle]
  patterns: [imgui HUD after postfx, event forwarding with want_capture guards, foreground draw list for custom rendering]

key-files:
  created: [bigbangsim/presentation/hud.py, tests/test_hud.py]
  modified: [bigbangsim/app.py]

key-decisions:
  - "imgui HUD rendered after postfx.end_scene() to prevent bloom bleed into text"
  - "Timeline bar uses imgui foreground draw list instead of imgui windows for pixel-precise layout"
  - "All 7 moderngl-window event types forwarded to imgui (key, drag, scroll, position, press, release, unicode)"
  - "GLSL timeline bar fully removed: _load_shader, _create_timeline_bar, _update_indicator all deleted"

patterns-established:
  - "imgui panels use HUD_FLAGS (no title, no resize, no move, auto-resize, no saved settings) for non-intrusive overlay"
  - "format_physics_value: scientific notation for |v| < 1e-3 or > 1e6, fixed-point otherwise"
  - "format_cosmic_time: auto-selects units (s/min/hr/yr/Myr/Gyr) by magnitude"

requirements-completed: [HUD-01, HUD-02, HUD-03, HUD-04, HUD-05]

duration: 5min
completed: 2026-03-28
---

# Phase 4 Plan 03: HUD Integration Summary

**imgui-bundle HUD with 6 overlay panels, full event forwarding, and GLSL timeline bar replacement wired into app.py render loop**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-28T21:28:09Z
- **Completed:** 2026-03-28T21:33:38Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created HUDManager with 6 panels: era info, physics readouts, educational text, milestone notifications, timeline bar, and controls hint
- Integrated full presentation layer (HUD, milestones, cinematic camera) into app.py render loop with imgui after post-processing
- Forwarded all 7 moderngl-window input events to imgui with want_capture_mouse/keyboard guards
- Completely removed GLSL timeline bar (shader, VBO, VAO, update methods) and replaced with imgui draw list version

## Task Commits

Each task was committed atomically:

1. **Task 1: Install imgui-bundle and create HUDManager** - `ab2a244` (feat)
2. **Task 2: Wire presentation layer into app.py** - `df779a9` (feat)

## Files Created/Modified
- `bigbangsim/presentation/hud.py` - HUDManager class with 6 panel methods, format helpers, ERA_COLORS, HUD_FLAGS
- `tests/test_hud.py` - 17 tests covering visibility, formatters, constants, mocked render
- `bigbangsim/app.py` - imgui init, event forwarding, HUD render after postfx, milestone/camera updates, GLSL timeline removed

## Decisions Made
- imgui HUD rendered after postfx.end_scene() to prevent bloom bleed into text -- matches existing pattern where GLSL timeline bar already rendered after post-processing
- Timeline bar uses imgui.get_foreground_draw_list() for pixel-precise custom rendering rather than imgui windows -- provides better control over bar segmentation and progress indicator
- All 7 event types forwarded to imgui first, then guarded with io.want_capture_mouse/keyboard before passing to camera/simulation -- prevents input conflicts
- _load_shader method removed entirely since it was only used for timeline_bar shader loading

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - imgui-bundle was installed as part of Task 1 execution.

## Next Phase Readiness
- Full presentation layer is wired and functional
- Phase 4 complete: all 3 plans (milestones/educational content, cinematic camera, HUD integration) are done
- Ready for Phase 5 (audio) -- the HUD and milestone systems provide hooks for audio events

## Self-Check: PASSED

- All 3 created/modified files exist on disk
- Both task commits (ab2a244, df779a9) found in git log
- 397 tests pass (17 new + 380 existing)
- All acceptance criteria verified via grep

---
*Phase: 04-presentation*
*Completed: 2026-03-28*
