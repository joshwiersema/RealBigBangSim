---
status: awaiting_human_verify
trigger: "particles-and-hud-visibility"
created: 2026-03-28T00:00:00Z
updated: 2026-03-28T00:00:00Z
---

## Current Focus

hypothesis: CONFIRMED - Two independent root causes found
test: Both confirmed via code analysis and headless imgui testing
expecting: Fix both and verify
next_action: Implement fixes for compute shader containment and renderer texture lifecycle

## Symptoms

expected: Glowing particles visible throughout all 11 eras with the camera tracking them. HUD panels show readable text (era name, physics values, educational content, controls).
actual: (1) Yellow particles appeared in era 0 during a diagnostic test but vanished after the first era transition. (2) HUD boxes appear (background visible) but text content is invisible/empty.
errors: No errors in console — both are silent visual failures.
reproduction: Run `py -3.13 -m bigbangsim` on AMD Radeon integrated GPU. Particles show briefly in era 0 then vanish. HUD boxes visible but empty.
started: Never worked visually — app was built with mock GPU tests. First visual run on AMD hardware.

## Eliminated

## Evidence

- timestamp: 2026-03-28T00:10:00Z
  checked: Compute shader expansion math (particle_update.comp line 24)
  found: vel += pos * u_expansion_rate * u_dt — this is exponential (Hubble-like) expansion with no position containment. For era 2 (Inflation) expansion_rate=0.5 and damping=0.005, particles fly to infinity within seconds. No position wrapping or respawn logic exists.
  implication: Particles become invisible after era 0 because they drift beyond camera far plane (1000.0)

- timestamp: 2026-03-28T00:15:00Z
  checked: _CompatRenderer.render() texture lifecycle handling
  found: imgui-bundle 1.92+ with renderer_has_textures requires the backend to process draw_data.textures each frame — handling want_create (upload pixels, set tex_id, mark ok) and want_updates (re-upload pixels, mark ok). The _CompatRenderer.render() method NEVER processes draw_data.textures.
  implication: After init, first new_frame() sets font texture to want_updates. Since renderer never handles it, imgui suppresses ALL draw commands — draw_data has 0 cmd_lists, 0 vertices. ALL text is invisible.

- timestamp: 2026-03-28T00:18:00Z
  checked: Headless imgui test simulating exact init + render sequence
  found: Confirmed via test — after refresh_font_texture sets status ok, new_frame() changes it to want_updates (status=3). Without processing want_updates in render loop, draw_data.cmd_lists_count=0. After adding texture status processing, text renders from frame 1 onward (vtx=78+).
  implication: The fix must add texture lifecycle processing to _CompatRenderer.render()

- timestamp: 2026-03-28T00:20:00Z
  checked: _push_scaled_font compatibility with imgui-bundle 1.92+
  found: push_font(font, size) API works correctly in 1.92+. The call itself is fine. However, scaling triggers dynamic re-rasterization which produces more want_updates. Since the base issue is that want_updates is never handled, scaling is a secondary concern — fixing the texture lifecycle will fix both scaled and unscaled text.
  implication: Font scaling code is correct but depends on texture lifecycle fix working

## Resolution

root_cause: |
  Issue 1 (Particles): Compute shader applies Hubble-like expansion (vel += pos * expansion_rate * dt) with no position containment. Particles expand exponentially and fly beyond camera far plane. Damping values are too small to counteract expansion rates.

  Issue 2 (HUD text): _CompatRenderer.render() does not process draw_data.textures lifecycle. imgui-bundle 1.92+ with renderer_has_textures flag requires backend to handle texture want_create/want_updates status each frame. Without this, imgui suppresses ALL draw commands after first new_frame() — producing empty draw data (0 vertices, 0 cmd_lists).
fix: |
  Issue 1 (Particles): Added containment system to compute shader. Particles beyond the containment
  radius are respawned at a hash-based pseudo-random position near origin (inner 40% of radius).
  Particles approaching the boundary (80-100%) get a soft inward pull. Each era has a per-era
  containment_radius field (15-100 units, scaling with cosmic expansion). Added u_containment_radius
  uniform to common.glsl, hash3() function and containment logic to particle_update.comp, and
  containment_radius field to EraVisualConfig.

  Issue 2 (HUD text): Added _process_texture_updates() method to _CompatRenderer that processes
  draw_data.textures lifecycle each frame. Handles want_create (upload pixels, register texture,
  set tex_id, mark ok), want_updates (re-upload or recreate if size changed, mark ok), and
  want_destroy (release, mark destroyed). Called at the start of render() BEFORE processing
  draw commands. This satisfies imgui-bundle 1.92+ requirement for renderer_has_textures backends.
verification: All 417 unit tests pass. Headless imgui testing confirms texture lifecycle fix produces draw data (vtx > 0) from frame 1 onward.
files_changed:
  - bigbangsim/app.py
  - bigbangsim/shaders/compute/particle_update.comp
  - bigbangsim/shaders/include/common.glsl
  - bigbangsim/simulation/era_visual_config.py
  - bigbangsim/rendering/particles.py
