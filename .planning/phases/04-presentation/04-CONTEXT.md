# Phase 4: Presentation - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the educational presentation layer: imgui-bundle HUD with era labels, live physics readouts (temperature, density, radiation density, scale factor), contextual educational explanations at key moments, ~20 milestone markers at correct cosmic timestamps with notifications, and a cinematic auto-camera that follows scripted paths through all 11 eras with pause/resume to free orbit mode.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
User deferred all gray areas to Claude's judgment. Full discretion on:
- imgui-bundle layout, styling, and window arrangement
- HUD element positioning (minimalist, non-intrusive per PhET principles)
- Educational text content and length
- Milestone marker list (which ~20 cosmic events to highlight)
- Milestone notification visual style and duration
- Auto-camera keyframe positions, speeds, and easing
- Camera path interpolation method (Catmull-Rom, bezier, etc.)
- How to toggle between auto-camera and free orbit mode
- HUD toggle key binding
- Physics readout formatting (scientific notation, SI units, etc.)
- Whether to use imgui docking or fixed-position windows

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 3 Era System (build upon)
- `bigbangsim/app.py` — Main render loop with era visuals, transitions, and physics uniforms
- `bigbangsim/simulation/eras.py` — 11 era definitions with time boundaries and descriptions
- `bigbangsim/simulation/state.py` — PhysicsState dataclass (all fields for HUD readouts)
- `bigbangsim/simulation/engine.py` — SimulationEngine with timeline, pause, speed controls
- `bigbangsim/simulation/era_visual_config.py` — Per-era visual config (bloom, colors, etc.)
- `bigbangsim/simulation/constants.py` — Cosmological constants for milestone timestamps

### Phase 1 Camera System (extend)
- `bigbangsim/rendering/camera.py` — DampedOrbitCamera (manual controls to preserve)
- `bigbangsim/config.py` — Window dimensions, physics timing, speed settings

### Phase 2 Rendering (integrate)
- `bigbangsim/rendering/particles.py` — ParticleSystem (scene rendering for camera framing)
- `bigbangsim/rendering/postprocessing.py` — PostProcessingPipeline (HUD renders after post-fx)

### Dependencies
- CLAUDE.md technology stack — imgui-bundle 1.92.601 for HUD overlay

</canonical_refs>

<specifics>
## Specific Ideas

- HUD should follow PhET minimal-text principles — clean, non-intrusive design
- Educational explanations should be accessible to non-physicists but not dumbed down
- Milestone markers should include events like: first protons form, nucleosynthesis begins, universe becomes transparent (CMB), first stars ignite, first galaxies form
- Auto-camera should create a cinematic "tour guide" experience through cosmic history
- User must be able to pause auto-camera at any time to freely orbit, then resume

</specifics>

<deferred>
## Deferred Ideas

None — all presentation features are in scope for this phase.

</deferred>

---

*Phase: 04-presentation*
*Context gathered: 2026-03-28*
