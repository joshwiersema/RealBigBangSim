---
status: awaiting_human_verify
trigger: "Black screen on AMD Radeon integrated GPU — HUD renders fine but no particles visible despite 268 FPS and working simulation. PROGRAM_POINT_SIZE already enabled."
created: 2026-03-28T12:00:00Z
updated: 2026-03-28T12:00:00Z
---

## Current Focus

hypothesis: CONFIRMED — bytes(glm.mat4) gives ROW-MAJOR data, but OpenGL .write() expects COLUMN-MAJOR. Matrices are transposed on GPU, causing incorrect clip-space transforms that clip all particles.
test: Replaced bytes(proj) with glm.value_ptr()-based column-major bytes; rendered to HDR FBO with depth+blend
expecting: Particles visible with correct matrix upload
next_action: Implement fix in app.py and particles.py, then verify

## Symptoms

expected: Glowing particles visible in the 3D viewport, with the HUD overlaid on top
actual: Completely black viewport — only imgui HUD panels are visible. Simulation runs (eras progress, physics readouts update) but nothing renders in the 3D scene. 268 FPS is suspiciously fast for 200K particles.
errors: No errors in console — clean exit with "Duration: 83.90s @ 268.34 FPS"
reproduction: Run `py -3.13 -m bigbangsim` on AMD Radeon (TM) Graphics integrated GPU (OpenGL 4.6, driver 23.19.23.14.250826)
started: Never worked on this AMD GPU. App was developed/tested on a different machine. First run on AMD integrated graphics.

## Eliminated

## Evidence

- timestamp: 2026-03-28T12:05:00Z
  checked: particles.py render() method (lines 254-256) and render_with_shader_key() (line 290)
  found: Both methods create ctx.vertex_array(prog, []) with an EMPTY buffer list every frame, then call vao.render(POINTS, vertices=count). The __init__ has a try/except fallback to a dummy buffer, but render() never uses self.vao from __init__ — it overwrites self.vao every frame with a freshly created empty VAO.
  implication: AMD drivers may silently skip draw calls on VAOs with zero vertex attribute bindings. NVIDIA tolerates this because the vertex shader only uses gl_VertexID + SSBO, but AMD requires at least one buffer binding.

- timestamp: 2026-03-28T12:06:00Z
  checked: 268 FPS performance on AMD integrated GPU with 200K particles
  found: 268 FPS is suspiciously high for an integrated GPU processing 200K point sprites through vertex+fragment shaders plus a full bloom post-processing pipeline. This suggests the draw calls are being completely skipped (no-op).
  implication: Strong circumstantial evidence that particles are NOT being drawn at all — the GPU is only doing compute dispatch + empty draw + post-processing on a black FBO.

- timestamp: 2026-03-28T12:07:00Z
  checked: particle.vert shader — no vertex attributes declared, only SSBO read
  found: The vertex shader reads `particles[gl_VertexID]` from SSBO binding 0. It declares NO `in` attributes. This is valid GLSL but relies on the driver executing the vertex shader invocations even with no vertex attribute arrays bound.
  implication: AMD Mesa/AMDGPU drivers are known to require at least one active vertex attribute for draw calls to execute. An empty VAO means the driver sees 0 active vertex attributes and may optimize away the entire draw call.

- timestamp: 2026-03-28T12:08:00Z
  checked: __init__ VAO creation (lines 99-103) vs render() VAO creation (line 255)
  found: __init__ tries empty VAO, falls back to dummy buffer. But render() IGNORES self.vao from __init__ and creates a NEW empty VAO every frame with the current program. The fallback is never used at render time.
  implication: Even if __init__ successfully created a dummy-buffer VAO, it is thrown away every frame by render()

- timestamp: 2026-03-28T12:15:00Z
  checked: Whether empty VAO is actually the problem (isolated test on AMD RX 5600 XT)
  found: Empty VAO with hardcoded positions in shader WORKS (255 red pixels). Empty VAO with SSBO + projection*view matrices produces BLACK (0 pixels). SSBO data read itself works (fixed position + SSBO color = visible).
  implication: Empty VAO is NOT the root cause. The matrix upload is the problem.

- timestamp: 2026-03-28T12:20:00Z
  checked: bytes(glm.mat4) byte ordering vs OpenGL expectation
  found: bytes(glm.mat4) gives ROW-MAJOR data. OpenGL glUniformMatrix4fv expects COLUMN-MAJOR by default. ModernGL .write() sends bytes as-is without transposing. So the matrix is effectively TRANSPOSED in the shader. For perspective projection, this moves the w=-z term from [3][2] to [2][3], breaking the perspective divide and causing all particles to be clipped.
  implication: ROOT CAUSE FOUND. All matrix uploads via .write(bytes(glm.mat4)) are wrong.

- timestamp: 2026-03-28T12:22:00Z
  checked: Fix via glm.value_ptr() for column-major bytes
  found: prog['u_projection'].write(glm_value_ptr_bytes(proj)) renders particles correctly on AMD with full HDR pipeline (f2 FBO, depth+blend). 2917 non-zero red pixels in 256x256 FBO. Also confirmed prog['u_projection'].value = tuple(col-major) works identically.
  implication: Fix verified in isolation. Need to apply to app.py where bytes(proj) and bytes(view) are computed.

- timestamp: 2026-03-28T12:24:00Z
  checked: Why this might have appeared to work on NVIDIA
  found: For many test scenarios, a transposed perspective matrix can still produce SOME visible output (just incorrectly transformed). NVIDIA drivers may also handle certain edge cases differently. The key: the app was developed/tested on a different machine — it may have had subtly wrong rendering that wasn't noticed, or PyGLM version differences.
  implication: This is a genuine bug in the matrix upload path, not an AMD-specific quirk. Fixing it produces correct behavior on all GPUs.

## Resolution

root_cause: bytes(glm.mat4) serializes in ROW-MAJOR order, but OpenGL uniform mat4 expects COLUMN-MAJOR data. ModernGL's .write() sends bytes as-is without transposing. The projection and view matrices are effectively transposed on the GPU, which moves the perspective divide term (w=-z) to the wrong position. This causes all particles to have incorrect clip coordinates and be clipped out entirely. The result is a black screen with no visible particles despite the simulation running correctly.
fix: In app.py lines 403-404, replaced `bytes(proj)` and `bytes(view)` with `np.array(m, dtype='f4').tobytes(order='F')` which serializes in column-major (Fortran) order matching OpenGL's expectation. Updated docstrings in particles.py to reflect column-major bytes requirement.
verification: (1) Standalone test: 200K particles on AMD RX 5600 XT — fixed method shows 83.1% pixel coverage with max HDR brightness 33.3; old method shows 0 pixels (BLACK). (2) App launch: BigBangSim runs without errors on AMD for 15+ seconds. (3) Awaiting human verification on target AMD integrated GPU.
files_changed: [bigbangsim/app.py, bigbangsim/rendering/particles.py]
