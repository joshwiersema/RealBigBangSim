---
status: awaiting_human_verify
trigger: "imgui-bundle 1.92+ font atlas not marked as built after our custom refresh_font_texture — IM_ASSERT(atlas->TexIsBuilt) fails on imgui.new_frame()"
created: 2026-03-28T00:00:00Z
updated: 2026-03-28T00:00:00Z
---

## Current Focus

hypothesis: CONFIRMED and FIXED
test: Run app and verify new_frame() no longer asserts on TexIsBuilt
expecting: App proceeds past new_frame() into HUD rendering
next_action: Awaiting human verification

## Symptoms

expected: Application launches with imgui HUD rendering correctly
actual: Crashes on first imgui.new_frame() with IM_ASSERT(atlas->TexIsBuilt)
errors: RuntimeError: IM_ASSERT( (atlas->TexIsBuilt) && "Backend does not support ImGuiBackendFlags_RendererHasTextures..." ) --- imgui_draw.cpp:2787
reproduction: Run `py -3.13 -m bigbangsim` — crashes immediately on first render frame
started: After writing _CompatRenderer subclass for moderngl-window 3.1.1 + imgui-bundle 1.92+ incompatibility

## Eliminated

## Evidence

- timestamp: 2026-03-28T00:10:00Z
  checked: ImFontAtlas attributes via Python introspection
  found: tex_is_built (writable bool), renderer_has_textures (writable bool), tex_list with ImTextureData entries having set_status() method
  implication: Multiple paths to solve -- set the flag directly or use backend flags

- timestamp: 2026-03-28T00:12:00Z
  checked: ImTextureStatus enum values
  found: ok=0, destroyed=1, want_create=2, want_updates=3, want_destroy=4. Font atlas tex_list[0] starts with status=want_create(2) after add_font_default()
  implication: Our code leaves status at want_create instead of setting it to ok after GPU upload

- timestamp: 2026-03-28T00:14:00Z
  checked: Whether setting tex_is_built=True or renderer_has_textures backend flag bypasses the assertion
  found: Both work. The imgui assertion is: (renderer_has_textures_flag) OR (tex_is_built). The new API path uses renderer_has_textures flag.
  implication: Setting backend_flags |= renderer_has_textures is the correct new-API approach

- timestamp: 2026-03-28T00:15:00Z
  checked: Full correct flow simulation with renderer_has_textures + set_status(ok)
  found: new_frame() succeeds when both are set correctly
  implication: Fix requires 2 changes: (1) set renderer_has_textures flag, (2) set_status(ok) after GPU upload

- timestamp: 2026-03-28T00:16:00Z
  checked: Base ModernGLRenderer.refresh_font_texture() in moderngl-window 3.1.1
  found: Uses get_tex_data_as_rgba32() which internally calls ImFontAtlasBuild() setting TexIsBuilt=true (old API). This method no longer exists in imgui-bundle 1.92+.
  implication: Root cause confirmed -- old API set TexIsBuilt implicitly; new API requires explicit backend flag

## Resolution

root_cause: imgui-bundle 1.92+ replaced the old ImFontAtlas::GetTexDataAsRGBA32() (which internally called ImFontAtlasBuild, setting TexIsBuilt=true) with a new tex_list API. The _CompatRenderer correctly creates the GPU texture via the new API, but fails to: (1) declare renderer_has_textures backend flag (telling imgui the backend uses the new tex_list protocol), and (2) call set_status(ImTextureStatus.ok) after GPU upload (telling imgui the texture is ready). The imgui new_frame() assertion requires EITHER TexIsBuilt (old API) OR renderer_has_textures (new API).
fix: In _CompatRenderer.__init__() or refresh_font_texture(), set io.backend_flags |= imgui.BackendFlags_.renderer_has_textures. After uploading the GPU texture, call tex.set_status(imgui.ImTextureStatus.ok) to mark it as uploaded.
verification: App launches past new_frame() without TexIsBuilt assertion. Subsequent crash is unrelated (set_window_font_scale API removed in imgui-bundle 1.92+ -- separate issue).
files_changed: [bigbangsim/app.py]
