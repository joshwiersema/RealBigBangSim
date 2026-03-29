---
status: resolved
trigger: "Particles invisible in windowed BigBangSim app. Root cause already identified and verified through diagnostic tests."
created: 2026-03-29T00:00:00Z
updated: 2026-03-29T00:00:00Z
---

## Current Focus

hypothesis: CONFIRMED - GL_POINT_SPRITE not enabled in Compatibility Profile context
test: All three fixes applied, syntax verified, awaiting user runtime test
expecting: Particles visible with bloom/glow in the windowed app
next_action: User runs `python -m bigbangsim` and confirms particles are visible

## Symptoms

expected: 200K particles visible as a glowing cloud in the BigBangSim window
actual: Black screen with only the imgui HUD overlay visible - zero particles rendered
errors: No error messages - app runs fine, shaders compile, but all fragments are discarded
reproduction: Run the app normally (python -m bigbangsim). Particles are never visible.
started: Particles have never been visible in the windowed app. They work in standalone headless tests.

## Eliminated

- hypothesis: Shader compilation failure
  evidence: No errors reported, shaders compile successfully
  timestamp: pre-session (diagnostic tests)

- hypothesis: Particle data not reaching GPU
  evidence: Standalone tests with flat shader (no gl_PointCoord) showed 138,992 non-black pixels
  timestamp: pre-session (diagnostic tests)

- hypothesis: Float FBO incompatibility on AMD discrete GPU
  evidence: f4 and f2 FBOs both produced 16,213 pixels in tests on RX 5600 XT
  timestamp: pre-session (diagnostic tests)

## Evidence

- timestamp: pre-session
  checked: Flat shader (no gl_PointCoord) in windowed context
  found: 138,992 non-black pixels rendered successfully
  implication: Particle data and vertex pipeline work; issue is fragment-shader-specific

- timestamp: pre-session
  checked: Era shader WITHOUT GL_POINT_SPRITE enabled
  found: 0 non-black pixels
  implication: gl_PointCoord returns undefined in Compatibility Profile without GL_POINT_SPRITE, causing discard

- timestamp: pre-session
  checked: Era shader WITH GL_POINT_SPRITE (0x8861) enabled
  found: 134,270 non-black pixels
  implication: Enabling GL_POINT_SPRITE fixes the visibility issue completely

- timestamp: pre-session
  checked: OpenGL context profile in windowed app
  found: 4.6.0 Compatibility Profile Context (not Core Profile)
  implication: moderngl_window creates Compatibility Profile on this AMD GPU; GL_POINT_SPRITE must be explicitly enabled

- timestamp: pre-session
  checked: Float FBO support on RX 5600 XT discrete GPU
  found: Both f4 and f2 FBOs work correctly (16,213 pixels each)
  implication: Full bloom/tonemap pipeline can be restored (was disabled for AMD integrated GPUs)

- timestamp: 2026-03-29
  checked: All three fixes applied and syntax-verified
  found: py_compile passes on all three files, imports work
  implication: Code is syntactically correct, ready for runtime testing

## Resolution

root_cause: moderngl_window creates a Compatibility Profile OpenGL context (4.6.0 Compatibility Profile) on AMD RX 5600 XT. In Compatibility Profile, gl_PointCoord requires GL_POINT_SPRITE (0x8861) to be enabled via glEnable. Without it, gl_PointCoord returns undefined values, and the discard in soft_glow() kills ALL fragments. Additionally, post-processing bloom pipeline was disabled (end_scene was a no-op), and u_era_progress was never uploaded to the compute shader.
fix: |
  Three fixes applied:
  1. GL_POINT_SPRITE (0x8861): Enabled via ctx.enable_direct() at startup in __init__ and re-enabled before each particle render pass (_render_normal, _render_with_transition outgoing, _render_with_transition incoming) since imgui's enable_only(BLEND) can disable it.
  2. Bloom/tonemap pipeline restored: begin_scene() now binds hdr_fbo (not default FBO), end_scene() runs full bright-extract -> gaussian blur ping-pong -> Reinhard tonemap pipeline. Added scratch FBO (f4) for transition compositing to avoid read-write hazard with hdr_fbo. _default_copy_tex replaced with _scratch_tex/_scratch_fbo (f4 format, with depth).
  3. u_era_progress upload: Added to particles.update() compute shader uniform block. The compute shader uses it for noise seeding and respawn hashing.
verification: CONFIRMED by user 2026-03-29. 262,144/262,144 pixels visible (100%), max pixel 252, center pixel [243,243,240] (bright white with bloom). Full bloom+tonemap pipeline working. All three fixes verified: GL_POINT_SPRITE, bloom/tonemap, u_era_progress.
files_changed:
  - bigbangsim/app.py
  - bigbangsim/rendering/postprocessing.py
  - bigbangsim/rendering/particles.py
