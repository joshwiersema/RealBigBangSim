---
phase: 03-era-content
plan: 03
subsystem: rendering
tags: [moderngl, glsl, fbo, crossfade, transitions, per-era-shaders, physics-uniforms]

# Dependency graph
requires:
  - phase: 03-era-content plan 01
    provides: "EraVisualConfig, physics sub-modules (nucleosynthesis, recombination, structure)"
  - phase: 03-era-content plan 02
    provides: "11 per-era fragment shaders (era_00_planck through era_10_lss), crossfade shader"
provides:
  - "EraTransitionManager for FBO-based era crossfade with smoothstep blend"
  - "ParticleSystem expanded to 11 per-era shader programs with uniform upload API"
  - "Fully integrated app.py render loop with per-era visuals, physics uniforms, and transitions"
affects: [phase-04-audio, phase-05-hud, visual-verification]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "FBO crossfade pattern: render outgoing/incoming to separate FBOs, composite with blend shader"
    - "Per-era uniform upload with 'if name in prog' guards against GLSL optimization"
    - "Physics lookup tables pre-computed at startup, interpolated per-frame"

key-files:
  created:
    - "bigbangsim/rendering/era_transition.py"
    - "tests/test_era_transitions.py"
    - "tests/test_era_sequence.py"
  modified:
    - "bigbangsim/rendering/particles.py"
    - "bigbangsim/app.py"
    - "tests/test_particles.py"

key-decisions:
  - "EraTransitionManager uses smoothstep(t*t*(3-2*t)) blend curve for perceptually smooth crossfades"
  - "Physics lookup tables (ionization, collapsed fraction) pre-computed at startup to avoid per-frame cost"
  - "Render loop split into _render_normal and _render_with_transition for clarity"
  - "Backward-compat aliases (hot->era_03_qgp, cool->era_07_dark_ages) kept in programs dict"

patterns-established:
  - "FBO crossfade: begin_outgoing() -> render outgoing -> composite(incoming_tex, target_fbo)"
  - "Per-era uniform upload: upload_era_uniforms(config, physics_uniforms) with in-prog guards"
  - "Physics sub-module integration: per-era conditional computation of physics uniforms"

requirements-completed: [RNDR-03, RNDR-04, PHYS-01, PHYS-02]

# Metrics
duration: 7min
completed: 2026-03-28
---

# Phase 3 Plan 03: Era Integration Summary

**FBO crossfade transitions, 11 per-era shader programs, and physics-driven uniforms wired into the render loop for full 11-era timeline playthrough**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-28T20:42:05Z
- **Completed:** 2026-03-28T20:49:15Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- EraTransitionManager provides FBO-based crossfade between adjacent eras with smoothstep blend factor (RNDR-04)
- ParticleSystem expanded from 2 shader variants to 11 per-era fragment shaders with upload_era_uniforms() and render_with_shader_key() methods
- App.py render loop fully integrated: per-era visual configs drive shader selection, bloom parameters, compute behavior, and physics-specific uniforms
- Physics sub-modules wired in: BBN helium fraction (era 5), Saha ionization (era 6), reionization ramp (era 8), Press-Schechter collapsed fraction (eras 9-10)
- Full test suite passes: 336 tests including 43 new era transition and sequence coverage tests

## Task Commits

Each task was committed atomically:

1. **Task 1: EraTransitionManager and expanded ParticleSystem** - `536f504` (feat)
2. **Task 2: App integration with per-era visuals and transitions** - `f9539f5` (feat)

## Files Created/Modified
- `bigbangsim/rendering/era_transition.py` - FBO-based crossfade transition manager with smoothstep blend
- `bigbangsim/rendering/particles.py` - Expanded to 11 per-era shader programs with uniform upload API
- `bigbangsim/app.py` - Integrated render loop with per-era visuals, physics uniforms, transitions
- `tests/test_era_transitions.py` - 24 tests for transition lifecycle, smoothstep curve, GPU resource creation
- `tests/test_era_sequence.py` - 19 tests for era data integrity, shader file existence, config validation
- `tests/test_particles.py` - Updated 3 tests for Phase 3 per-era shader selection

## Decisions Made
- Used smoothstep (t*t*(3-2*t)) blend curve for perceptually smooth era crossfades rather than linear interpolation
- Pre-compute ionization and collapsed fraction lookup tables at startup (once) rather than per-frame
- Split render loop into _render_normal() and _render_with_transition() helper methods for clarity
- Kept backward-compat 'hot'/'cool' aliases in programs dict pointing to era_03_qgp/era_07_dark_ages

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated existing test_particles.py tests for Phase 3 behavior**
- **Found during:** Task 2 (full test suite run)
- **Issue:** Three tests in TestParticleSystemShaderSelection expected Phase 2 behavior (default='hot', era ranges use 'hot'/'cool') but Phase 3 changed to per-era shader keys
- **Fix:** Updated test_default_shader_is_hot to test_default_shader_is_era_00, replaced era range tests with test_set_era_shader_selects_correct_key and test_backward_compat_hot_cool_aliases
- **Files modified:** tests/test_particles.py
- **Verification:** Full test suite passes (336 tests)
- **Committed in:** f9539f5 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Test update necessary for correctness. No scope creep.

## Issues Encountered
None

## Known Stubs
None - all data paths are fully wired from physics sub-modules through to shader uniforms.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Full 11-era timeline with distinct visuals and smooth transitions is ready
- Physics uniforms flow from Python to GPU for eras 5, 6, 8, 9, 10
- Audio system (Phase 4) can hook into PhysicsState and EraVisualConfig for era-driven soundscapes
- HUD system (Phase 5) can read EraVisualConfig for educational overlay data

## Self-Check: PASSED

All 7 files verified present on disk. Both task commits (536f504, f9539f5) verified in git log. 336 tests passing.

---
*Phase: 03-era-content*
*Completed: 2026-03-28*
