# Phase 3: Era Content - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Populate all 11 cosmological eras with scientifically accurate physics models and visually distinct rendering. Each era gets its own fragment shader with unique color palettes and particle behaviors driven by real physics (Friedmann equations, BBN yields, Saha equation, Jeans instability, Press-Schechter). Era transitions crossfade smoothly between visual paradigms. A full timeline playthrough from singularity to large-scale structure completes without crashes.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
User deferred all gray areas to Claude's judgment. Full discretion on:
- Per-era color palettes and visual styles
- Physics model complexity per era (analytical vs numerical)
- Fragment shader count (one per era vs grouping similar eras)
- Crossfade transition implementation (uniform blending vs FBO lerp)
- Particle behavior variation per era (spawn patterns, velocities, lifetimes)
- How to handle early-era visuals (Planck epoch, Grand Unification) where no established conventions exist
- BBN yield calculation detail level
- Saha equation implementation approach
- Jeans instability and Press-Schechter approximation fidelity
- Era-specific compute shader behavior vs uniform-driven variation

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 2 Rendering Infrastructure (build upon)
- `bigbangsim/rendering/shader_loader.py` — Shader include preprocessor
- `bigbangsim/rendering/particles.py` — ParticleSystem with ping-pong SSBOs and era shader switching
- `bigbangsim/rendering/postprocessing.py` — PostProcessingPipeline (HDR/bloom)
- `bigbangsim/shaders/include/common.glsl` — Shared uniforms and Particle struct
- `bigbangsim/shaders/include/colormap.glsl` — Temperature/density color mapping utilities
- `bigbangsim/shaders/include/noise.glsl` — Simplex noise for procedural effects
- `bigbangsim/shaders/fragment/particle_hot.frag` — Hot era fragment shader (template pattern)
- `bigbangsim/shaders/fragment/particle_cool.frag` — Cool era fragment shader (template pattern)
- `bigbangsim/shaders/compute/particle_update.comp` — Compute shader for particle physics

### Phase 1 Simulation Layer (read physics from)
- `bigbangsim/simulation/constants.py` — Planck 2018/PDG cosmological constants
- `bigbangsim/simulation/state.py` — PhysicsState dataclass (rendering reads this)
- `bigbangsim/simulation/cosmology.py` — Friedmann equation solver
- `bigbangsim/simulation/eras.py` — Era definitions with cosmic time boundaries
- `bigbangsim/simulation/engine.py` — SimulationEngine producing PhysicsState
- `bigbangsim/app.py` — Main application with render loop

### Research
- `.planning/research/ARCHITECTURE.md` — Overall architecture patterns
- `.planning/research/PITFALLS.md` — Known pitfalls for GPU rendering

</canonical_refs>

<specifics>
## Specific Ideas

- Each era should have a visually distinctive "personality" — the user should be able to tell which era they're in at a glance
- Early eras (Planck, GUT, Inflation) are speculative — use abstract/artistic representations with educational disclaimers
- BBN era should show nuclei forming (hydrogen, helium, lithium proportions matching Planck 2018 values)
- CMB/Recombination should be the most visually dramatic transition — from opaque plasma to transparent space
- Dark Ages should feel empty and dark — minimal particle activity
- First Stars should be a dramatic "lights on" moment
- Galaxy Formation should show gravitational clustering

</specifics>

<deferred>
## Deferred Ideas

None — all era content is in scope for this phase.

</deferred>

---

*Phase: 03-era-content*
*Context gathered: 2026-03-28*
