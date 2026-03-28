# Phase 2: Core Rendering - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the GPU-accelerated particle rendering pipeline: compute shaders for particle updates (100K-1M particles at 30+ FPS), modular per-era shader architecture with shared utility libraries, and post-processing pipeline (bloom, HDR, tone mapping) for cinematic visual quality. This phase proves the rendering architecture before era-specific content is added in Phase 3.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
User deferred all gray areas to Claude's judgment. Full discretion on:
- Compute shader workgroup sizing and SSBO layout
- Ping-pong double-buffer strategy for particle updates
- Bloom kernel size and HDR tone mapping curve
- Shader utility library organization
- Number and nature of initial shader variants for architecture validation
- Particle billboard vs point sprite rendering approach
- FBO chain for multi-pass post-processing

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 1 Foundation (established patterns)
- `bigbangsim/simulation/constants.py` — Cosmological constants module (read for physics values)
- `bigbangsim/simulation/state.py` — PhysicsState dataclass (rendering reads this)
- `bigbangsim/simulation/engine.py` — SimulationEngine (produces PhysicsState each frame)
- `bigbangsim/app.py` — Main application window (rendering integrates here)
- `bigbangsim/rendering/coordinates.py` — Camera-relative transforms (PHYS-07 pattern)
- `bigbangsim/rendering/camera.py` — DampedOrbitCamera (provides view/projection matrices)

### Research
- `.planning/research/STACK.md` — ModernGL 5.12 compute shader capabilities, SSBO patterns
- `.planning/research/ARCHITECTURE.md` — Ping-pong double-buffered SSBO particle system pattern
- `.planning/research/PITFALLS.md` — GPU compute pitfalls, shader architecture warnings

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `bigbangsim/app.py` — WindowConfig with render loop, test scene, timeline bar
- `bigbangsim/rendering/camera.py` — DampedOrbitCamera with view/projection matrices
- `bigbangsim/rendering/coordinates.py` — Camera-relative coordinate transforms
- `bigbangsim/shaders/test_scene.vert/frag` — GLSL 4.30 shader pattern established

### Established Patterns
- Fixed-timestep simulation → PhysicsState → render loop pattern
- Camera-relative rendering with double-precision subtraction before GPU
- GLSL 4.30 compute compatibility level
- pyproject.toml dependency management

### Integration Points
- `app.py` render loop must integrate particle system rendering
- PhysicsState drives particle behavior uniforms
- Post-processing FBOs wrap the existing render output

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. Research recommends ping-pong double-buffered SSBOs with compute shaders for particle updates, and multi-pass FBO chain for bloom/HDR.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-core-rendering*
*Context gathered: 2026-03-28*
