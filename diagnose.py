"""Diagnostic script — run on the target machine to identify rendering issues.

Usage: py -3.13 diagnose.py
"""
import sys
import struct
import numpy as np

print(f"Python {sys.version}")

# --- 1. Create headless OpenGL context ---
import moderngl
try:
    ctx = moderngl.create_standalone_context()
    print(f"[OK] OpenGL context: {ctx.info['GL_RENDERER']}")
    print(f"     Version: {ctx.info['GL_VERSION']}")
except Exception as e:
    print(f"[FAIL] Cannot create context: {e}")
    sys.exit(1)

# --- 2. Test compute shader ---
print("\n--- Compute Shader Test ---")
try:
    comp_src = """
    #version 430
    layout(local_size_x = 1) in;
    layout(std430, binding = 0) buffer Data { float vals[]; };
    void main() { vals[gl_GlobalInvocationID.x] = float(gl_GlobalInvocationID.x) * 2.0; }
    """
    comp = ctx.compute_shader(comp_src)
    buf = ctx.buffer(reserve=4 * 4)
    buf.bind_to_storage_buffer(0)
    comp.run(group_x=4)
    ctx.memory_barrier()
    result = struct.unpack("4f", buf.read())
    expected = (0.0, 2.0, 4.0, 6.0)
    ok = all(abs(a - b) < 0.01 for a, b in zip(result, expected))
    print(f"[{'OK' if ok else 'FAIL'}] Compute shader: {result} (expected {expected})")
except Exception as e:
    print(f"[FAIL] Compute shader: {e}")

# --- 3. Test SSBO read from vertex shader (the particle rendering technique) ---
print("\n--- SSBO + Empty VAO Rendering Test ---")
try:
    WIDTH, HEIGHT = 64, 64
    fbo_tex = ctx.texture((WIDTH, HEIGHT), 4, dtype="f2")
    fbo = ctx.framebuffer(color_attachments=[fbo_tex])

    vert = """
    #version 430
    struct P { vec4 pos; vec4 vel; vec4 col; };
    layout(std430, binding = 0) readonly buffer Particles { P particles[]; };
    out vec4 v_color;
    void main() {
        P p = particles[gl_VertexID];
        gl_Position = vec4(p.pos.xy, 0.0, 1.0);  // Direct NDC, no matrix
        gl_PointSize = 20.0;
        v_color = p.col;
    }
    """
    frag = """
    #version 430
    in vec4 v_color;
    out vec4 fragColor;
    void main() { fragColor = v_color; }
    """
    prog = ctx.program(vertex_shader=vert, fragment_shader=frag)

    # 4 particles at known NDC positions with bright colors
    data = np.array([
        # pos(x,y,z,w), vel(x,y,z,w), col(r,g,b,a)
        0.0, 0.0, 0.0, 1.0,  0,0,0,0,  1.0, 0.0, 0.0, 1.0,  # center, red
        0.5, 0.5, 0.0, 1.0,  0,0,0,0,  0.0, 1.0, 0.0, 1.0,  # top-right, green
       -0.5,-0.5, 0.0, 1.0,  0,0,0,0,  0.0, 0.0, 1.0, 1.0,  # bottom-left, blue
        0.5,-0.5, 0.0, 1.0,  0,0,0,0,  1.0, 1.0, 0.0, 1.0,  # bottom-right, yellow
    ], dtype="f4")
    ssbo = ctx.buffer(data.tobytes())
    ssbo.bind_to_storage_buffer(0)

    ctx.enable(moderngl.PROGRAM_POINT_SIZE)

    # Test A: Empty VAO
    fbo.use()
    fbo.clear(0, 0, 0, 0)
    vao_empty = ctx.vertex_array(prog, [])
    vao_empty.render(moderngl.POINTS, vertices=4)
    pixels_a = np.frombuffer(fbo.read(components=4, dtype="f2"), dtype="float16")
    nonzero_a = np.count_nonzero(pixels_a)
    print(f"[{'OK' if nonzero_a > 0 else 'FAIL'}] Empty VAO: {nonzero_a} non-zero values (of {len(pixels_a)})")

    # Test B: Dummy buffer VAO
    fbo.use()
    fbo.clear(0, 0, 0, 0)
    dummy = ctx.buffer(b"\x00" * 4)
    try:
        vao_dummy = ctx.vertex_array(prog, [(dummy, "1x /i")])
    except Exception:
        vao_dummy = ctx.vertex_array(prog, [])
    vao_dummy.render(moderngl.POINTS, vertices=4)
    pixels_b = np.frombuffer(fbo.read(components=4, dtype="f2"), dtype="float16")
    nonzero_b = np.count_nonzero(pixels_b)
    print(f"[{'OK' if nonzero_b > 0 else 'FAIL'}] Dummy VAO: {nonzero_b} non-zero values (of {len(pixels_b)})")

except Exception as e:
    print(f"[FAIL] SSBO rendering: {e}")
    import traceback; traceback.print_exc()

# --- 4. Test fullscreen quad post-processing ---
print("\n--- Post-Processing Pipeline Test ---")
try:
    fbo.use()
    fbo.clear(0.5, 0.3, 0.1, 1.0)  # Write known color to "HDR" FBO

    out_tex = ctx.texture((WIDTH, HEIGHT), 4, dtype="f2")
    out_fbo = ctx.framebuffer(color_attachments=[out_tex])

    pp_vert = """
    #version 430
    in vec3 in_position;
    in vec2 in_texcoord_0;
    out vec2 v_uv;
    void main() { gl_Position = vec4(in_position, 1.0); v_uv = in_texcoord_0; }
    """
    pp_frag = """
    #version 430
    in vec2 v_uv;
    uniform sampler2D u_scene;
    out vec4 fragColor;
    void main() { fragColor = texture(u_scene, v_uv); }
    """
    pp_prog = ctx.program(vertex_shader=pp_vert, fragment_shader=pp_frag)
    pp_prog["u_scene"].value = 0

    from moderngl_window import geometry
    quad = geometry.quad_fs()

    out_fbo.use()
    out_fbo.clear(0, 0, 0, 0)
    fbo_tex.use(location=0)
    quad.render(pp_prog)

    pixels_pp = np.frombuffer(out_fbo.read(components=4, dtype="f2"), dtype="float16")
    nonzero_pp = np.count_nonzero(pixels_pp)
    print(f"[{'OK' if nonzero_pp > 0 else 'FAIL'}] Fullscreen quad blit: {nonzero_pp} non-zero values")

except Exception as e:
    print(f"[FAIL] Post-processing: {e}")
    import traceback; traceback.print_exc()

# --- 5. Test matrix upload ---
print("\n--- Matrix Upload Test ---")
try:
    mat_vert = """
    #version 430
    uniform mat4 u_proj;
    uniform mat4 u_view;
    struct P { vec4 pos; vec4 vel; vec4 col; };
    layout(std430, binding = 0) readonly buffer Particles { P particles[]; };
    out vec4 v_color;
    void main() {
        P p = particles[gl_VertexID];
        gl_Position = u_proj * u_view * vec4(p.pos.xyz, 1.0);
        gl_PointSize = 50.0 / max(gl_Position.w, 0.01);
        v_color = p.col;
    }
    """
    mat_prog = ctx.program(vertex_shader=mat_vert, fragment_shader=frag)

    import glm
    proj = glm.perspective(glm.radians(60.0), 1.0, 0.01, 100.0)
    view = glm.lookAt(glm.vec3(0, 0, 5), glm.vec3(0, 0, 0), glm.vec3(0, 1, 0))

    # Particles at world origin
    world_data = np.array([
        0.0, 0.0, 0.0, 1.0,  0,0,0,0,  1.0, 1.0, 1.0, 1.0,
        0.5, 0.5, 0.0, 1.0,  0,0,0,0,  1.0, 1.0, 1.0, 1.0,
       -0.5,-0.5, 0.0, 1.0,  0,0,0,0,  1.0, 1.0, 1.0, 1.0,
        1.0,-1.0, 0.0, 1.0,  0,0,0,0,  1.0, 1.0, 1.0, 1.0,
    ], dtype="f4")
    world_ssbo = ctx.buffer(world_data.tobytes())
    world_ssbo.bind_to_storage_buffer(0)

    fbo.use()

    # Method A: bytes(glm.mat4) — original code
    fbo.clear(0, 0, 0, 0)
    mat_prog["u_proj"].write(bytes(proj))
    mat_prog["u_view"].write(bytes(view))
    vao_m = ctx.vertex_array(mat_prog, [])
    vao_m.render(moderngl.POINTS, vertices=4)
    px_a = np.frombuffer(fbo.read(components=4, dtype="f2"), dtype="float16")
    nz_a = np.count_nonzero(px_a)
    print(f"[{'OK' if nz_a > 0 else 'FAIL'}] bytes(glm.mat4): {nz_a} non-zero values")

    # Method B: numpy F-order — current fix
    fbo.clear(0, 0, 0, 0)
    mat_prog["u_proj"].write(np.array(proj, dtype='f4').tobytes(order='F'))
    mat_prog["u_view"].write(np.array(view, dtype='f4').tobytes(order='F'))
    vao_m2 = ctx.vertex_array(mat_prog, [])
    vao_m2.render(moderngl.POINTS, vertices=4)
    px_b = np.frombuffer(fbo.read(components=4, dtype="f2"), dtype="float16")
    nz_b = np.count_nonzero(px_b)
    print(f"[{'OK' if nz_b > 0 else 'FAIL'}] np F-order: {nz_b} non-zero values")

    # Method C: glm.value_ptr
    fbo.clear(0, 0, 0, 0)
    mat_prog["u_proj"].write(bytes(np.array(glm.value_ptr(proj), dtype='f4')))
    mat_prog["u_view"].write(bytes(np.array(glm.value_ptr(view), dtype='f4')))
    vao_m3 = ctx.vertex_array(mat_prog, [])
    vao_m3.render(moderngl.POINTS, vertices=4)
    px_c = np.frombuffer(fbo.read(components=4, dtype="f2"), dtype="float16")
    nz_c = np.count_nonzero(px_c)
    print(f"[{'OK' if nz_c > 0 else 'FAIL'}] glm.value_ptr: {nz_c} non-zero values")

except Exception as e:
    print(f"[FAIL] Matrix upload: {e}")
    import traceback; traceback.print_exc()

print("\n--- Summary ---")
print("If Empty VAO is FAIL but Dummy VAO is OK -> need dummy vertex buffer")
print("If both VAO tests FAIL -> SSBO-from-vertex-shader is broken on this GPU")
print("If post-processing FAIL -> fullscreen quad rendering is broken")
print("If all matrix methods FAIL -> point rendering itself is broken")
print("If bytes() FAIL but F-order OK -> matrix byte order fix is correct")
print("\nPaste this entire output back to me.")
