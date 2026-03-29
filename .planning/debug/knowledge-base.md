# GSD Debug Knowledge Base

Resolved debug sessions. Used by `gsd-debugger` to surface known-pattern hypotheses at the start of new investigations.

---

## particle-visibility-compat-profile — GL_POINT_SPRITE required in Compatibility Profile for gl_PointCoord to work
- **Date:** 2026-03-29
- **Error patterns:** particles invisible, black screen, gl_PointCoord, discard, Compatibility Profile, AMD, moderngl_window, point sprite
- **Root cause:** moderngl_window creates a Compatibility Profile OpenGL context (4.6.0) on AMD RX 5600 XT. In Compatibility Profile, gl_PointCoord requires GL_POINT_SPRITE (0x8861) to be enabled via glEnable. Without it, gl_PointCoord returns undefined values, and any discard-on-radius check kills ALL fragments. Additionally, post-processing bloom pipeline was disabled (end_scene was a no-op), and u_era_progress was never uploaded to the compute shader.
- **Fix:** (1) Enable GL_POINT_SPRITE (0x8861) via ctx.enable_direct() at startup and re-enable before each particle render pass since imgui's enable_only(BLEND) can disable it. (2) Restore bloom/tonemap pipeline: begin_scene binds hdr_fbo, end_scene runs bright-extract -> gaussian blur -> Reinhard tonemap; add scratch FBO (f4) for transition compositing. (3) Upload u_era_progress uniform in particles.update() compute shader call.
- **Files changed:** bigbangsim/app.py, bigbangsim/rendering/postprocessing.py, bigbangsim/rendering/particles.py
---
