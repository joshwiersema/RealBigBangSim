# Technology Stack

**Project:** BigBangSim -- Cinematic Cosmological Big Bang Simulation
**Researched:** 2026-03-27

## Recommended Stack

### Runtime

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | 3.11.x | Runtime | Sweet spot: newest NumPy/SciPy support, all target libraries ship wheels for 3.11. Python 3.12+ would break pyo (no wheels above 3.11 on PyPI). Python 3.11 also has significant performance improvements over 3.10. | HIGH |

**Why not 3.12+:** The pyo audio library (1.0.5 on PyPI, March 2023) only ships wheels for Python 3.7-3.11. Version 1.0.6 is tagged on GitHub (March 2025) but never published to PyPI. If pyo is dropped in favor of sounddevice+numpy for audio, Python 3.12 or 3.13 become viable -- but pyo provides significantly richer DSP primitives for generative audio. Pin to 3.11 and revisit if pyo publishes 3.12+ wheels.

### Core Rendering

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| ModernGL | 5.12.0 | OpenGL 3.3+/4.3 binding | The best Python OpenGL wrapper. Shader-first design, C++ core for performance, clean Pythonic API. Supports compute shaders (OpenGL 4.3) essential for GPU particle updates. Actively maintained, wheels for Python 3.8-3.13. | HIGH |
| moderngl-window | 3.1.1 | Windowing, input, event loop | Official companion to ModernGL. Provides cross-platform window management (pyglet backend by default), unified keyboard/mouse events, timer, and imgui integration. Released January 2025. | HIGH |
| GLSL | 4.30+ | Shader language | Required for compute shaders (particle physics on GPU) and vertex/fragment shaders (rendering). OpenGL 4.3 is the minimum for compute; target 4.30 GLSL version. GTX 1060 supports OpenGL 4.6, so no compatibility concern. | HIGH |

**Architecture note:** ModernGL wraps OpenGL but does NOT abstract it away -- you still write raw GLSL shaders and manage buffers/VAOs explicitly. This is a feature, not a bug, for a project that needs fine-grained GPU control over particle systems.

### 3D Mathematics

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| PyGLM | 2.8.3 | Matrices, vectors, quaternions, transforms | C++ core (wraps GLM), significantly faster than numpy for 3D math operations. GLM-compatible API means GLSL shader math and Python math use identical conventions. Buffer protocol support for direct ModernGL interop. Released November 2025, supports Python 3.9-3.14. | HIGH |

**Why not pyrr:** Pyrr (0.10.3) is unmaintained -- no releases in years, low community activity. PyGLM is actively maintained, faster (C++ vs pure Python+numpy), and has a larger API surface matching GLM exactly.

**Why not raw numpy for transforms:** Numpy excels at bulk array operations (particle data) but is overkill and slower for individual matrix/vector operations (camera transforms, projection matrices). PyGLM handles the latter; numpy handles the former.

### Scientific Computing

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| NumPy | 2.2.x | Array operations, particle data, physics calculations | Foundation of scientific Python. Used for CPU-side particle initialization, physics parameter arrays, and data marshaling to GPU buffers. Pin to 2.2.x for Python 3.11 compatibility (NumPy 2.4+ requires Python 3.11+ but latest may have edge cases). | HIGH |
| SciPy | 1.14.x | Signal processing, special functions, interpolation | Needed for: scipy.signal (audio filter design), scipy.special (Saha equation, nucleosynthesis calculations), scipy.interpolate (smooth era transitions). Pin to 1.14.x for 3.11 compat. | MEDIUM |

**Why not CuPy:** CuPy (GPU-accelerated numpy) is overkill here. The heavy parallel computation (particle updates) runs in GLSL compute shaders directly on GPU. CPU-side numpy handles initialization and parameter computation that doesn't need GPU acceleration. Adding CuPy would introduce an NVIDIA CUDA dependency that breaks AMD/Intel GPU compatibility.

### Audio

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| pyo | 1.0.5 | Generative audio synthesis, real-time DSP | Purpose-built for exactly this use case: real-time procedural audio with oscillators, filters, envelopes, granular synthesis, and noise generators. Server-based architecture manages audio thread automatically. Far richer DSP primitives than raw sounddevice+numpy. | MEDIUM |
| sounddevice | 0.5.5 | Fallback audio I/O (if pyo unavailable) | PortAudio bindings with numpy array I/O. If pyo cannot be installed (Python version mismatch), use sounddevice with hand-rolled DSP using numpy/scipy. More work, but guaranteed to install. | HIGH |

**Audio strategy:** Primary path is pyo with Python 3.11. Implement an audio abstraction layer so the DSP engine can swap between pyo (rich) and sounddevice+numpy+scipy (lean) backends. This protects against pyo's uncertain PyPI release cadence.

**Why not PyOpenAL:** Project constraints mention PyOpenAL. OpenAL is a 3D positional audio API designed for games -- it plays pre-loaded sounds in 3D space. It is NOT a synthesis engine. For generative ambient soundscapes tied to physics parameters, we need oscillators/filters/envelopes, not a 3D audio playback engine. PyOpenAL is the wrong tool.

### UI / HUD Overlay

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| imgui-bundle | 1.92.601 | Educational overlay, HUD, debug controls | Full Dear ImGui (v1.90.9+) with ImPlot for real-time graphs, docking support, and native moderngl-window integration via `pip install moderngl-window[imgui]`. Production/stable, MIT licensed, released March 2026. Much more current than pyimgui (stuck on ImGui v1.82). | HIGH |

**Why not pyimgui:** pyimgui wraps Dear ImGui v1.82 (ancient). imgui-bundle wraps v1.90.9+ with ImPlot, ImGuizmo, node editor, and more. moderngl-window explicitly supports imgui-bundle integration. No reason to use the older binding.

**Why not custom overlay rendering:** Building HUD text rendering from scratch (font atlas, glyph layout, quad rendering) is weeks of work that imgui solves in hours. The educational overlay (era labels, physics readouts, temperature/density) is a core feature, not a nice-to-have. Use imgui.

### Screenshot and Video Capture

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Pillow | 12.1.1 | Screenshot capture (PNG) | Industry-standard Python imaging. `Image.frombytes('RGB', size, fbo.read())` converts ModernGL framebuffer data to saveable images. Supports PNG, JPEG, TIFF. Released February 2026. | HIGH |
| FFmpeg | system | Video recording (MP4 via subprocess pipe) | Pipe raw frames from ModernGL framebuffer reads to FFmpeg via subprocess stdin for H.264/MP4 encoding. No Python wrapper library needed -- direct subprocess.Popen with `-f rawvideo -pix_fmt rgb24` input. This avoids pulling in opencv-python (huge) or moviepy (abstraction overhead). | MEDIUM |

**Why subprocess FFmpeg over opencv-python:** OpenCV pulls in ~50MB of dependencies for what amounts to a thin wrapper around FFmpeg. We only need "pipe frames to encoder." A 20-line subprocess wrapper does this with zero extra dependencies beyond FFmpeg itself being installed on the system.

**Why not moviepy:** MoviePy is designed for video editing (trim, merge, effects), not real-time frame piping from a 3D renderer. It would add unnecessary abstraction.

### Supporting Libraries

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| numpy | 2.2.x | Array math, data marshaling | Always -- particle data, physics arrays, audio buffers | HIGH |
| scipy | 1.14.x | Filters, special functions, interpolation | Era transitions, cosmological equations, audio filter design | MEDIUM |
| Pillow | 12.1.1 | Image I/O | Screenshot capture | HIGH |
| PyGLM | 2.8.3 | 3D math (matrices, vectors, quaternions) | Camera system, projection, transforms | HIGH |

### Development Dependencies

| Library | Version | Purpose | Confidence |
|---------|---------|---------|------------|
| pytest | latest | Testing | HIGH |
| ruff | latest | Linting and formatting | HIGH |
| mypy | latest | Type checking (optional but recommended) | MEDIUM |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| OpenGL binding | ModernGL 5.12.0 | PyOpenGL | PyOpenGL is a thin, verbose wrapper. ModernGL is Pythonic, faster (C++ core), and shader-first. PyOpenGL requires boilerplate that ModernGL eliminates. |
| OpenGL binding | ModernGL 5.12.0 | Pygfx / wgpu-py | WebGPU-based. Newer but less mature, smaller community, fewer examples for compute shader particle systems. ModernGL is battle-tested for this use case. |
| OpenGL binding | ModernGL 5.12.0 | Vulkan (via vulkan-python) | Massive complexity for no benefit at this scale. Vulkan's explicit memory management and pipeline state objects are overkill for 1M particles. OpenGL 4.3 compute shaders are sufficient. |
| 3D math | PyGLM 2.8.3 | pyrr 0.10.3 | Unmaintained, slower (pure Python), smaller API. PyGLM wraps C++ GLM library directly. |
| 3D math | PyGLM 2.8.3 | numpy (raw) | Good for bulk arrays, slow for individual transforms. PyGLM is 10-100x faster for single matrix operations. |
| Audio | pyo 1.0.5 | PyOpenAL | OpenAL is 3D positional audio playback, not synthesis. Cannot generate oscillators/filters/envelopes needed for generative soundscapes. |
| Audio | pyo 1.0.5 | pygame.mixer | Playback only, no synthesis. Cannot generate audio from physics parameters. |
| Audio | pyo 1.0.5 | torchaudio | ML-focused, massive PyTorch dependency. Nuclear option for what is fundamentally classical DSP (oscillators + filters). |
| HUD | imgui-bundle | pyimgui | Wraps ancient ImGui v1.82. imgui-bundle wraps v1.90.9+ with ImPlot and has native moderngl-window support. |
| HUD | imgui-bundle | Custom GLSL text rendering | Weeks of work to build what imgui provides out of the box. |
| Video capture | FFmpeg subprocess | opencv-python | 50MB+ dependency for 20 lines of subprocess code. We only need frame piping, not OpenCV's computer vision stack. |
| Video capture | FFmpeg subprocess | moviepy | Designed for video editing, not real-time frame piping. Adds abstraction overhead. |
| GPU arrays | GLSL compute shaders | CuPy | Locks to NVIDIA CUDA. Our compute runs in OpenGL shaders which work on any GPU supporting OpenGL 4.3. |
| Windowing | moderngl-window | pygame | pygame works but moderngl-window provides tighter ModernGL integration, unified event system, and imgui support out of the box. |
| Windowing | moderngl-window | glfw (direct) | Possible but you lose moderngl-window's resource loading, timer management, and imgui integration. Reinventing wheels. |

## Minimum Hardware Requirements

| Component | Minimum | Recommended | Rationale |
|-----------|---------|-------------|-----------|
| GPU | GTX 1060 / RX 580 | GTX 1070+ / RX 5700+ | OpenGL 4.3 compute shaders required. GTX 1060 supports OpenGL 4.6. More VRAM = more particles. |
| VRAM | 3 GB | 6 GB+ | 1M particles x (3 floats position + 3 floats velocity + 4 floats color + 2 floats misc) = ~48 MB. Headroom needed for framebuffers, textures, shader storage. |
| RAM | 8 GB | 16 GB | Python + numpy arrays + audio buffers. Modest requirements. |
| CPU | 4 cores | 6+ cores | Physics parameter computation, audio synthesis (pyo runs its own thread), frame encoding for video capture. |

## OpenGL Version Strategy

The project requires two OpenGL capability levels:

1. **OpenGL 3.3 (minimum for ModernGL):** Basic vertex/fragment shader rendering. Used as fallback if compute shaders unavailable.
2. **OpenGL 4.3 (required for compute shaders):** GPU-side particle physics updates via SSBO (Shader Storage Buffer Objects) and compute shaders. This is the primary path.

**Fallback strategy:** Detect OpenGL version at startup. If < 4.3, fall back to CPU-side particle updates with numpy (slower, cap at ~100K particles). If >= 4.3, use compute shaders for full 1M particle simulation. This ensures the application runs on older hardware, just with reduced particle counts.

```python
# Version detection pattern
ctx = moderngl.create_context()
gl_version = ctx.version_code  # e.g., 430 for OpenGL 4.3
use_compute = gl_version >= 430
```

## Installation

```bash
# Create virtual environment with Python 3.11
python3.11 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Core rendering
pip install moderngl==5.12.0
pip install moderngl-window[imgui]==3.1.1

# 3D math
pip install PyGLM==2.8.3

# Scientific computing
pip install numpy==2.2.4
pip install scipy==1.14.1

# Audio synthesis
pip install pyo==1.0.5

# Audio fallback (if pyo fails to install)
pip install sounddevice==0.5.5

# Screenshot capture
pip install Pillow==12.1.1

# Development
pip install pytest ruff mypy
```

**System dependency:** FFmpeg must be installed separately for video recording.
- Windows: `winget install FFmpeg` or download from https://ffmpeg.org
- Linux: `sudo apt install ffmpeg`
- macOS: `brew install ffmpeg`

## Key Version Pins and Rationale

| Package | Pinned | Rationale |
|---------|--------|-----------|
| Python | 3.11.x | pyo compatibility ceiling. All other deps support 3.11. |
| moderngl | 5.12.0 | Latest stable. No reason to pin lower. |
| moderngl-window | 3.1.1 | Latest stable (Jan 2025). Major version bump (3.x) from late 2024. |
| PyGLM | 2.8.3 | Latest stable (Nov 2025). |
| numpy | 2.2.x | Latest 2.2 series. Avoid 2.4+ which requires Python 3.11+ minimum and may have breaking API changes. |
| pyo | 1.0.5 | Only version on PyPI. 1.0.6 exists in git but unpublished. |

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| pyo not releasing Python 3.12+ wheels | Medium | Abstract audio layer; sounddevice+numpy+scipy fallback ready |
| pyo 1.0.5 has bugs fixed in unreleased 1.0.6 | Low | Can install from git: `pip install git+https://github.com/belangeo/pyo.git` |
| ModernGL compute shader API limited documentation | Medium | Community examples exist (ModernGL_ParticleSim). Compute shader API is thin (create, bind buffers, run). Core GLSL knowledge transfers directly. |
| imgui-bundle large dependency | Low | ~30MB installed. Acceptable for a desktop application. |
| FFmpeg not installed on user system | Medium | Detect at startup, disable video recording feature gracefully, show install instructions |
| OpenGL 4.3 not available on user GPU | Low | GTX 1060 (2016) supports 4.6. Only very old or integrated GPUs lack 4.3. Fallback to CPU particle updates. |

## Sources

- [ModernGL 5.12.0 Documentation](https://moderngl.readthedocs.io/en/latest/) -- HIGH confidence
- [ModernGL PyPI](https://pypi.org/project/moderngl/) -- version 5.12.0, released Oct 2024
- [moderngl-window PyPI](https://pypi.org/project/moderngl-window/) -- version 3.1.1, released Jan 2025
- [ModernGL Compute Shader Docs](https://moderngl.readthedocs.io/en/latest/reference/compute_shader.html) -- HIGH confidence
- [ModernGL_ParticleSim (compute shader example)](https://github.com/casparmaria/ModernGL_ParticleSim) -- community example, 2^27 particles at 60fps
- [PyGLM PyPI](https://pypi.org/project/PyGLM/) -- version 2.8.3, released Nov 2025
- [PyGLM GitHub](https://github.com/Zuzu-Typ/PyGLM) -- actively maintained
- [pyo PyPI](https://pypi.org/project/pyo/) -- version 1.0.5, released Mar 2023, wheels to Python 3.11
- [pyo GitHub](https://github.com/belangeo/pyo) -- version 1.0.6 tagged Mar 2025, NOT on PyPI
- [pyo Documentation](https://belangeo.github.io/pyo/) -- version 1.0.6 docs
- [sounddevice PyPI](https://pypi.org/project/sounddevice/) -- version 0.5.5, released Jan 2026
- [Pillow PyPI](https://pypi.org/project/Pillow/) -- version 12.1.1, released Feb 2026
- [imgui-bundle PyPI](https://pypi.org/project/imgui-bundle/) -- version 1.92.601, released Mar 2026
- [NumPy PyPI](https://pypi.org/project/numpy/) -- version 2.4.3, released Mar 2026 (requires 3.11+)
- [SciPy PyPI](https://pypi.org/project/scipy/) -- version 1.17.1, released Feb 2026 (requires 3.11+)
- [pyrr PyPI](https://pypi.org/project/pyrr/) -- version 0.10.3, unmaintained
- [Procedural Audio Techniques](https://peerdh.com/blogs/programming-insights/procedural-audio-generation-techniques-for-adaptive-soundscapes-in-games) -- MEDIUM confidence
- [FFmpeg with Python](https://www.gumlet.com/learn/ffmpeg-python/) -- MEDIUM confidence
