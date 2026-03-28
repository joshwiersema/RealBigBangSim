---
phase: 02-core-rendering
verified: 2026-03-28T20:30:00Z
status: human_needed
score: 11/11 automated must-haves verified
re_verification: false
human_verification:
  - test: "Launch application and verify 30+ FPS with 200K particles"
    expected: "Window title shows '200K particles' and FPS >= 30"
    why_human: "FPS depends on GPU hardware; cannot be tested without running the application"
  - test: "Verify bloom glow is visually present on the particle scene"
    expected: "Particles have a soft halo/glow effect; not hard-edged points"
    why_human: "Bloom visibility is a perceptual judgment requiring visual inspection"
  - test: "Verify shader variant switch at era boundary"
    expected: "Particle colors shift from warm/hot (orange-red) to cool/blue around era 6-7"
    why_human: "Color shift is perceptual and requires running the full timeline"
---

# Phase 2: Core Rendering Verification Report

**Phase Goal:** The simulation renders 100K+ particles in real-time via GPU compute shaders with cinematic post-processing effects, proving the rendering architecture before era content is added
**Verified:** 2026-03-28T20:30:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

All truths are drawn from the three PLAN must_haves sections plus the ROADMAP success criteria.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Shader loader resolves #include directives by concatenating include files | VERIFIED | `load_shader_source` uses `re.compile(r'#include\s+"([^"]+)"')` and substitutes; 6 tests pass |
| 2 | At least 2 distinct fragment shader variants (particle_hot.frag, particle_cool.frag) load and compile | VERIFIED | Both files exist, loaded via shader_loader without errors |
| 3 | No fragment shader contains if/else branching on era index (no mega-shader) | VERIFIED | grep for `if (u_era ==` in both frag files returns nothing |
| 4 | Shared utility functions defined once in include files and reused | VERIFIED | common.glsl, noise.glsl, colormap.glsl exist; hot/cool frags both `#include "colormap.glsl"` |
| 5 | ParticleSystem creates two SSBO buffers for ping-pong double buffering | VERIFIED | `self.buffers = [ctx.buffer(...), ctx.buffer(...)]`; test_two_buffers_created passes |
| 6 | ParticleSystem dispatches compute shader with correct workgroup count and calls memory_barrier | VERIFIED | `(self.count + 255) // 256` ceiling division; `self.ctx.memory_barrier()` present in update() |
| 7 | ParticleSystem swaps buffers after each compute dispatch | VERIFIED | `self.current = 1 - self.current` at end of update(); toggle tests pass |
| 8 | PostProcessingPipeline creates HDR FBO with RGBA16F texture | VERIFIED | `ctx.texture((width, height), 4, dtype="f2")` present; test_hdr_texture_full_resolution passes |
| 9 | PostProcessingPipeline runs 5-pass bloom chain (bright extract, H-blur, V-blur pairs, composite+tonemap) | VERIFIED | begin_scene / end_scene implement all passes; 3 shader programs (bright_prog, blur_prog, tonemap_prog) verified |
| 10 | Bloom runs at half resolution for performance | VERIFIED | `hw, hh = width // 2, height // 2`; test_bloom_textures_half_resolution passes |
| 11 | Application renders particles via GPU compute shaders (not Phase 1 test scene) | VERIFIED | app.py imports ParticleSystem + PostProcessingPipeline; no _create_test_scene, no grid_vao; on_render calls particles.update, postfx.begin_scene, postfx.end_scene |

**Score:** 11/11 automated truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `bigbangsim/rendering/shader_loader.py` | Python-side shader include preprocessor | VERIFIED | 69 lines; exports load_shader_source, get_shader_dir; SHADER_DIR constant; re.compile include pattern; FileNotFoundError on missing include |
| `bigbangsim/shaders/include/common.glsl` | Shared uniform declarations and Particle struct | VERIFIED | Contains `uniform float u_dt`, `struct Particle`, `uniform float u_era_progress` |
| `bigbangsim/shaders/include/noise.glsl` | Simplex noise function | VERIFIED | `float snoise(vec2 v)` present; full Ashima Arts implementation |
| `bigbangsim/shaders/include/colormap.glsl` | Temperature and density color mapping | VERIFIED | `vec3 temperature_to_color` and `vec3 density_to_color` both present |
| `bigbangsim/shaders/compute/particle_update.comp` | Compute shader for GPU particle updates | VERIFIED | `layout(local_size_x = 256)` present; `#include "common.glsl"` resolves correctly |
| `bigbangsim/shaders/vertex/particle.vert` | Particle vertex shader reading from SSBO | VERIFIED | `gl_VertexID` present; reads from SSBO Particles binding |
| `bigbangsim/shaders/fragment/particle_hot.frag` | Hot plasma particle visual style | VERIFIED | `#include "colormap.glsl"` resolves; `temperature_to_color` called; no era branching |
| `bigbangsim/shaders/fragment/particle_cool.frag` | Cool matter particle visual style | VERIFIED | `#include "colormap.glsl"` resolves; `density_to_color` called; no era branching |
| `bigbangsim/shaders/postprocess/fullscreen.vert` | Fullscreen quad passthrough | VERIFIED | `in_position`, `in_texcoord_0` present for quad_fs() |
| `bigbangsim/shaders/postprocess/bright_extract.frag` | Bright-pass extraction | VERIFIED | `u_threshold` uniform present; luminance calculation correct |
| `bigbangsim/shaders/postprocess/gaussian_blur.frag` | Separable Gaussian blur | VERIFIED | `0.227027` 5-tap weights present; `u_horizontal` toggle |
| `bigbangsim/shaders/postprocess/tonemap.frag` | HDR tone mapping + bloom composite | VERIFIED | `u_exposure`, `u_bloom_strength` uniforms present; Reinhard formula |
| `bigbangsim/rendering/particles.py` | ParticleSystem class | VERIFIED | 182 lines; PARTICLE_STRIDE=48; ping-pong SSBOs; compute dispatch; memory_barrier; era shader switching |
| `bigbangsim/rendering/postprocessing.py` | PostProcessingPipeline class | VERIFIED | 210 lines; RGBA16F HDR FBO; half-res bloom; begin_scene/end_scene; resize; release |
| `bigbangsim/app.py` | Integrated render loop | VERIFIED | Imports ParticleSystem + PostProcessingPipeline; render loop: update -> compute -> begin_scene -> particles.render -> end_scene -> timeline overlay |
| `tests/test_shader_loader.py` | Shader loader unit tests | VERIFIED | 6 test behaviors all pass; covers passthrough, single include, no nesting, missing file, multiple includes, get_shader_dir |
| `tests/test_particles.py` | ParticleSystem unit tests | VERIFIED | 19 tests pass; covers data shape/dtype/values, PARTICLE_STRIDE, buffer logic, swap, shader selection |
| `tests/test_postprocessing.py` | PostProcessingPipeline unit tests | VERIFIED | 18 tests pass; covers defaults, dimensions, half-res math, methods, shader loading |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| shader_loader.py | shaders/include/*.glsl | #include directive resolution | VERIFIED | `_INCLUDE_RE.sub(_replace_include, source)` substitutes includes |
| particle_hot.frag | shaders/include/colormap.glsl | `#include "colormap.glsl"` | VERIFIED | Include present; resolved source contains `vec3 temperature_to_color` |
| particle_cool.frag | shaders/include/colormap.glsl | `#include "colormap.glsl"` | VERIFIED | Include present; resolved source contains `vec3 density_to_color` |
| particles.py | shader_loader.py | `load_shader_source(...)` | VERIFIED | Called for compute, vertex, hot frag, cool frag |
| particles.py | simulation/state.py | PhysicsState fields mapped to uniforms | VERIFIED | `physics_state.temperature`, `physics_state.scale_factor`, `physics_state.current_era` all accessed in update() |
| postprocessing.py | shader_loader.py | `load_shader_source(...)` | VERIFIED | Called for fullscreen.vert, bright_extract.frag, gaussian_blur.frag, tonemap.frag |
| postprocessing.py | moderngl_window.geometry.quad_fs | Fullscreen quad for post-processing | VERIFIED | `self.quad = geometry.quad_fs()` present |
| app.py | particles.py | `self.particles.update` in render loop | VERIFIED | `self.particles.update(PHYSICS_DT, state)` in on_render |
| app.py | postprocessing.py | `self.postfx.begin_scene` wrapping particle render | VERIFIED | `self.postfx.begin_scene()` -> particle render -> `self.postfx.end_scene()` |
| app.py | simulation/engine.py | PhysicsState drives particle compute uniforms | VERIFIED | `state, alpha = self.sim.update(frame_time)` then `self.particles.update(PHYSICS_DT, state)` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| app.py (on_render) | state (PhysicsState) | `self.sim.update(frame_time)` -> SimulationEngine | Yes — Friedmann solver produces real cosmological values per-frame | FLOWING |
| particles.py (update) | compute uniforms | `physics_state.temperature`, `.scale_factor`, `.current_era` | Yes — these are real PhysicsState values | FLOWING |
| postprocessing.py (end_scene) | hdr_texture | Particle render writes into hdr_fbo via begin_scene | Yes — HDR FBO receives actual rendered pixels | FLOWING |
| particles.py (_generate_initial_particles) | init_data | numpy RNG with sigma=2.0 Gaussian positions | Yes — real stochastic data, not hardcoded empty | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| App imports cleanly | `py -3.14 -c "from bigbangsim.app import BigBangSimApp; print('OK')"` | App imports OK | PASS |
| ParticleSystem importable, PARTICLE_STRIDE=48 | `py -3.14 -c "from bigbangsim.rendering.particles import ParticleSystem, PARTICLE_STRIDE; assert PARTICLE_STRIDE == 48"` | ParticleSystem OK | PASS |
| Compute shader loads with includes resolved | `load_shader_source('compute/particle_update.comp')` — assert 'Particle' in src, no '#include' | ALL SHADERS VERIFIED | PASS |
| All 8 shader files load | `[load_shader_source(p) for p in [...8 paths...]]` | All 8 shader files load successfully | PASS |
| Full test suite (130 tests) | `py -3.14 -m pytest tests/ -x -q` | 130 passed, 0 failed, 9.76s | PASS |
| 30+ FPS with 200K particles | `py -3.14 -m bigbangsim` — check window title | Cannot test without running app | SKIP (human) |
| Bloom glow visible | Visual inspection of running app | Cannot test programmatically | SKIP (human) |
| Shader variant color shift at era 6-7 | Visual inspection of running timeline | Cannot test programmatically | SKIP (human) |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| RNDR-01 | 02-02, 02-03 | Renders 100K-1M particles at 30+ FPS via GPU compute shaders | PARTIAL — code verified; runtime FPS requires human | 200K particles in ParticleSystem; compute dispatch with ceiling division; app integration verified; FPS needs human check |
| RNDR-02 | 02-02, 02-03 | Post-processing pipeline: bloom, HDR, tone mapping | PARTIAL — code verified; visual quality requires human | PostProcessingPipeline fully implemented; 5-pass bloom chain; RGBA16F HDR FBO; Reinhard tonemap; visual glow needs human check |
| RNDR-06 | 02-01, 02-03 | Per-era shader architecture with shared utilities, separate programs (no mega-shader) | VERIFIED | 3 shared include files; 2 distinct fragment variants; no `if (u_era ==` branching; set_era_shader() switches at runtime |

**Requirements mapping:** All 3 requirement IDs assigned to Phase 2 (RNDR-01, RNDR-02, RNDR-06) are accounted for across plans 02-01, 02-02, and 02-03. No orphaned requirements.

**REQUIREMENTS.md traceability cross-check:** RNDR-01, RNDR-02, RNDR-06 are mapped to Phase 2 in the traceability table. Status matches: all three marked Complete in REQUIREMENTS.md, consistent with the implementation evidence found.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | — | — | — | — |

No TODOs, FIXMEs, placeholder returns, empty handlers, or hardcoded empty data arrays found in any Phase 2 production file. The render() method in particles.py re-creates `self.vao` on every render call (line 172) — this is a minor performance issue (extra object creation per frame) but not a stub and does not affect correctness.

### Human Verification Required

#### 1. 30+ FPS with 200K Particles

**Test:** Launch `py -3.14 -m bigbangsim` and read the window title
**Expected:** Window title shows "200K particles" and FPS >= 30 on GTX 1060-class GPU
**Why human:** FPS depends on GPU hardware and cannot be measured without running the application. The code path is fully wired: 200K particles dispatched via compute shader each frame, confirmed in app.py line 170.

#### 2. Bloom Glow Visible

**Test:** Launch `py -3.14 -m bigbangsim` and inspect the particle scene
**Expected:** Particles show a soft halo/glow effect (not hard-edged points). Brighter particles should bloom outward.
**Why human:** Perceptual visual quality judgment. The post-processing chain is fully implemented (5-pass bloom: bright extract -> H-blur -> V-blur x3 -> tonemap), but actual visual output on this GPU cannot be verified programmatically.

#### 3. Shader Variant Color Shift at Era Boundary

**Test:** Let the simulation run until era 6-7 (or press + to speed up), observe particle colors
**Expected:** During eras 0-5, particles are warm/orange-red (hot shader). After era 6, they shift to cool/blue-purple (cool shader).
**Why human:** The set_era_shader() logic is verified (tests pass for both hot eras 0-5 and cool eras 6-10), but the perceptual color shift during live playback requires visual confirmation.

### Gaps Summary

No automated gaps found. All 11 observable truths verified, all 18 artifacts confirmed substantive and wired, all key links confirmed, data flows to real GPU buffers, 130 tests pass.

The three human verification items above represent the final confirmation that the GPU rendering pipeline produces the intended visual output. These cannot be checked without running the application on the target hardware.

---

_Verified: 2026-03-28T20:30:00Z_
_Verifier: Claude (gsd-verifier)_
