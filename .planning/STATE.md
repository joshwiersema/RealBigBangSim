---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Ready to plan
stopped_at: Completed 04-03-PLAN.md
last_updated: "2026-03-28T21:33:38Z"
progress:
  total_phases: 5
  completed_phases: 3
  total_plans: 12
  completed_plans: 12
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-27)

**Core value:** The simulation must be both scientifically accurate AND visually stunning -- real cosmological physics driving beautiful real-time 3D rendering that teaches as it mesmerizes.
**Current focus:** Phase 04 — presentation

## Current Position

Phase: 04 (presentation) — EXECUTING
Plan: 3 of 3

## Performance Metrics

**Velocity:**

- Total plans completed: 0
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
| Phase 01-foundation P01 | 6min | 2 tasks | 14 files |
| Phase 01 P02 | 10min | 2 tasks | 7 files |
| Phase 01-foundation P03 | 6min | 3 tasks | 11 files |
| Phase 02 P01 | 5min | 2 tasks | 13 files |
| Phase 02 P02 | 5min | 2 tasks | 4 files |
| Phase 02 P03 | 3min | 2 tasks | 1 files |
| Phase 03 P02 | 4min | 2 tasks | 18 files |
| Phase 03 P01 | 8min | 2 tasks | 9 files |
| Phase 03 P03 | 7min | 2 tasks | 6 files |
| Phase 04-presentation P03 | 5min | 2 tasks | 3 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

-

- [Phase 01-foundation]: Used Python 3.14 instead of 3.11 -- all Phase 1 deps install cleanly, audio deferred to Phase 4
- [Phase 01-foundation]: Established simulation-rendering boundary: simulation modules have zero imports from rendering layer
- [Phase 01]: Analytical Jacobian for Radau solver: dt/da ODE has zero dependence on t, so jac=[[0.0]]
- [Phase 01]: Era overlap (Grand Unification/Inflation) handled by returning highest-index era containing cosmic time
- [Phase 01]: Friedmann integration time normalized to AGE_UNIVERSE at a=1.0
- [Phase 01-foundation]: Used bytes(matrix) for glm.mat4 to moderngl uniform upload
- [Phase 01-foundation]: Corrected moderngl-window 3.1.1 callbacks: on_mouse_drag_event, on_mouse_scroll_event
- [Phase 01-foundation]: keys.EQUAL for speed increase (keys.PLUS not in BaseKeys)
- [Phase 02]: Single-level shader include resolution only (no recursion) for simplicity
- [Phase 02]: Particle SSBO struct: 3x vec4 (position+life, velocity+type, color) for std430 alignment
- [Phase 02]: Per-era fragment shader variants (hot/cool) instead of mega-shader branching (RNDR-06)
- [Phase 02]: Mock-based testing strategy: all rendering tests use MagicMock for moderngl.Context, enabling CI without GPU
- [Phase 02]: Empty VAO for gl_VertexID-based particle rendering (no vertex attributes, data from SSBO)
- [Phase 02]: 6 blur iterations (3H + 3V) default for bloom, balancing quality vs performance
- [Phase 02]: Additive blending (GL_ONE, GL_ONE) for particles -- emissive light sources, not opaque objects
- [Phase 02]: Post-processing scene pass wraps particle render; timeline overlay after post-processing to avoid bloom bleed into UI
- [Phase 03]: Physics-specific uniforms scoped per-shader to avoid GLSL optimization KeyError (Phase 2 pitfall c94d2c1)
- [Phase 03]: Compute shader uses uniform-driven behavior for per-era physics (expansion, noise, gravity, damping)
- [Phase 03]: Numerically stable Saha solver: use 2A/(A+sqrt(A^2+4A)) for large A to avoid catastrophic cancellation
- [Phase 03]: Physics sub-module pattern: build_*_table() + get_*() precomputed lookup with interpolation for GPU uniform data
- [Phase 03]: EraVisualConfig frozen dataclass: per-era config data (shader_key, colors, params) in simulation layer, zero rendering imports
- [Phase 03]: EraTransitionManager uses smoothstep blend curve for perceptually smooth crossfades
- [Phase 03]: Physics lookup tables pre-computed at startup, not per-frame
- [Phase 03]: Render loop split into _render_normal and _render_with_transition paths
- [Phase 04]: imgui HUD rendered after postfx.end_scene() to prevent bloom bleed into text
- [Phase 04]: Timeline bar uses imgui foreground draw list for pixel-precise custom rendering
- [Phase 04]: All 7 moderngl-window event types forwarded to imgui with want_capture guards

### Pending Todos

None yet.

### Blockers/Concerns

- Research flag: pyo audio library has not published to PyPI since March 2023. Phase 4 decision point: evaluate pyo vs sounddevice+numpy as primary audio path.
- Research flag: Early-era visual language (Planck epoch, Grand Unification) has no established conventions. Phase 3 will require creative experimentation with educational disclaimers.

## Session Continuity

Last session: 2026-03-28T21:33:38Z
Stopped at: Completed 04-03-PLAN.md
Resume file: None
