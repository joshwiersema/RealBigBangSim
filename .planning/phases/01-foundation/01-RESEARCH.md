# Phase 1: Foundation - Research

**Researched:** 2026-03-27
**Domain:** Real-time cosmological simulation foundation -- window, camera, physics engine, timeline controller, cosmological constants
**Confidence:** HIGH

## Summary

Phase 1 builds the invisible foundation that every subsequent phase depends on: an OpenGL 4.3 window with orbit camera controls, a fixed-timestep simulation loop, a logarithmic timeline controller spanning 60+ orders of magnitude, a centralized cosmological constants module sourced from Planck 2018/PDG values, and the coordinate system architecture needed to avoid floating-point precision breakdown at cosmic scales. None of these systems produce spectacular visuals yet -- the phase renders a test scene (colored grid, axis markers, or placeholder particles) just enough to prove the camera and timing work.

The critical insight is that three of the five most dangerous pitfalls identified in project research (logarithmic time-scale collapse, floating-point precision, and scientific inaccuracy) must be solved architecturally in Phase 1. These cannot be retrofitted later. The timeline controller's piecewise logarithmic mapping, the camera-relative rendering pipeline, and the constants module with citations are all Phase 1 deliverables that downstream phases treat as stable infrastructure.

A significant environment finding: the user's machine has Python 3.14 and 3.13 installed, but NOT Python 3.11 (which the stack research recommended for pyo audio compatibility). Since audio is deferred to Phase 4/v2 and all Phase 1 dependencies (ModernGL 5.12.0, moderngl-window 3.1.1, PyGLM 2.8.3, NumPy 2.4.3, SciPy 1.17.1) install cleanly on Python 3.14, the project should use Python 3.14 now and address the pyo compatibility question when audio becomes relevant.

**Primary recommendation:** Build the foundation in this order: (1) project scaffolding and constants module, (2) window + camera with test scene, (3) fixed-timestep simulation loop, (4) logarithmic timeline controller, (5) coordinate system architecture for camera-relative rendering, (6) play/pause/speed controls with timeline bar placeholder.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
No locked decisions -- user deferred all gray areas to Claude's judgment.

### Claude's Discretion
User deferred all gray areas to Claude's judgment. Full discretion on:
- Timeline pacing strategy (how screen time is distributed across eras)
- Launch experience (window setup, initial scene)
- Speed control feel (stepped vs smooth, shortcuts)
- Test scene visuals (placeholder content for Phase 1)
- Project structure and module organization

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CAMR-01 | User can orbit, zoom, and pan the camera with smooth damping via mouse controls | moderngl-window provides OrbitCamera class with rot_state/zoom_state methods. Needs custom damping (exponential decay on velocity) since built-in has no damping. PyGLM provides glm.lookAt for view matrix. |
| CAMR-04 | Play/pause via spacebar, speed controls via +/- keys (0.5x to 10x range) | moderngl-window on_key_event with self.wnd.keys.SPACE for detection. Speed multiplier applied to timeline controller's wall-clock-to-cosmic-time mapping. |
| PHYS-03 | Logarithmic time mapping spans 60+ orders of magnitude with intuitive visual timeline bar | Piecewise logarithmic function with per-era screen time budgets. Each era gets configurable seconds of real-time display. Timeline bar renders as simple colored bar for Phase 1. |
| PHYS-05 | All physics constants sourced from Planck 2018 results and PDG values -- centralized constants module with citations | Planck 2018 (arXiv:1807.06209) Table 2: H0=67.66, Om0=0.30966, Ob0=0.04897, Tcmb0=2.7255 K, Neff=3.046. PDG for particle masses and BBN yields. Every constant gets a docstring citation. |
| PHYS-06 | Fixed-timestep simulation decoupled from render rate with interpolation for smooth display | Standard accumulator pattern from "Fix Your Timestep!" (Gaffer on Games). Physics steps at fixed dt, render interpolates between prev/current state using alpha = accumulator / dt. |
| PHYS-07 | Camera-relative rendering and era-specific coordinate systems to avoid floating-point precision breakdown at cosmic scales | Compute model-view matrix in double precision on CPU, cast to float32 for GPU upload. Per-era coordinate normalization (positions as fractions of era-scale, not absolute physical units). |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Tech Stack**: Python 3.10+, ModernGL, GLSL shaders -- chosen for balance of GPU performance and Python ecosystem
- **Performance**: Must maintain 30+ FPS on GTX 1060 with 100K+ particles (Phase 2 concern, but architecture must support it)
- **Scientific Accuracy**: All physics parameters must come from published cosmological data (Planck 2018, PDG). No made-up numbers.
- **Platform**: Windows primary, cross-platform compatible code
- **Dependencies**: Minimize exotic dependencies. Prefer well-maintained PyPI packages.
- **GSD Workflow**: Do not make direct repo edits outside a GSD workflow unless explicitly bypassing

## Standard Stack

### Core (Phase 1 Dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.14.x | Runtime | User's installed version. All Phase 1 deps have cp314 wheels. Audio (pyo) pinning to 3.11 only matters in Phase 4. |
| ModernGL | 5.12.0 | OpenGL 4.3 binding | Shader-first design, C++ core, compute shader support. Builds from source on 3.14. |
| moderngl-window | 3.1.1 | Windowing, input, event loop | Official ModernGL companion. Provides WindowConfig base class, OrbitCamera, unified keyboard/mouse events. pyglet 2.1.13 backend. |
| PyGLM | 2.8.3 | 3D math (matrices, vectors, quaternions) | C++ GLM wrapper. 10-100x faster than numpy for individual transforms. Native cp314 wheel. |
| NumPy | 2.4.3 | Array operations, physics calculations | Foundation of scientific Python. cp314 wheel available. |
| SciPy | 1.17.1 | ODE integration for Friedmann equations | scipy.integrate.solve_ivp with Radau/BDF method for stiff cosmological ODEs. cp314 wheel available. |

### Development

| Library | Version | Purpose |
|---------|---------|---------|
| pytest | 9.0.2 | Testing (physics engine is independently testable without GPU) |
| ruff | 0.15.8 | Linting and formatting |

### Not Needed in Phase 1

| Library | Why Deferred |
|---------|-------------|
| pyo / sounddevice | Audio is Phase 4/v2 |
| imgui-bundle | HUD overlay is Phase 4 (Phase 1 timeline bar is simple GLSL quad, not imgui) |
| Pillow | Screenshot capture is Phase 5 |
| FFmpeg | Video recording is Phase 5 |

**Installation (Phase 1):**
```bash
py -3.14 -m venv .venv
.venv\Scripts\activate
pip install moderngl==5.12.0 moderngl-window==3.1.1 PyGLM==2.8.3 numpy scipy
pip install pytest ruff
```

**Version verification:** All versions confirmed installable on Python 3.14 via `pip install --dry-run` on user's machine (2026-03-27). ModernGL builds from source tarball (no cp314 wheel, but C extension compiles); all others have prebuilt wheels.

### Python Version Decision

The stack research recommended Python 3.11 for pyo audio compatibility. However:
- User has Python 3.14 and 3.13 installed; Python 3.11 is NOT installed
- Audio (pyo) is deferred to Phase 4/v2
- All Phase 1 dependencies install on 3.14 (verified)
- When Phase 4 arrives, evaluate: (a) install Python 3.11 alongside for pyo, (b) use sounddevice fallback on 3.14, or (c) pyo may have newer releases by then

**Decision: Use Python 3.14 for Phase 1.** Revisit when audio is in scope.

## Architecture Patterns

### Recommended Project Structure (Phase 1)

```
bigbangsim/
    __main__.py              # Entry point: `python -m bigbangsim`
    app.py                   # WindowConfig subclass, main loop orchestration
    config.py                # Performance settings, default window size

    simulation/
        __init__.py
        constants.py         # Planck 2018 / PDG cosmological constants with citations
        cosmology.py         # Friedmann equations, scale factor, temperature, density
        timeline.py          # Wall-clock to cosmic time mapping (logarithmic)
        state.py             # PhysicsState dataclass (the interface between sim and rendering)

    rendering/
        __init__.py
        camera.py            # Orbit camera with smooth damping (wraps/extends OrbitCamera)

    shaders/
        test_scene.vert      # Simple vertex shader for Phase 1 test scene
        test_scene.frag      # Simple fragment shader for Phase 1 test scene

tests/
    __init__.py
    test_constants.py        # Verify constants match Planck 2018 / PDG published values
    test_cosmology.py        # Verify scale factor, temperature, density at known cosmic times
    test_timeline.py         # Verify logarithmic mapping, era boundaries, round-trip consistency
    test_state.py            # Verify PhysicsState interpolation
```

### Pattern 1: Fixed-Timestep Simulation with Accumulator

**What:** The physics simulation advances in fixed time steps, decoupled from render frame rate. An accumulator collects real elapsed time and drains it in fixed-size physics steps. The render interpolates between previous and current physics states for smooth display.

**When to use:** Always. This is the standard pattern for any real-time simulation. Physics stability requires fixed timesteps; visual smoothness requires rendering at the display's refresh rate.

**Source:** "Fix Your Timestep!" by Glenn Fiedler (gafferongames.com), Game Programming Patterns by Robert Nystrom

**Example:**
```python
# Source: Architecture research + Gaffer on Games pattern
from dataclasses import dataclass

@dataclass
class PhysicsState:
    """The interface between simulation and rendering layers."""
    cosmic_time: float        # Seconds after Big Bang
    scale_factor: float       # a(t), dimensionless
    temperature: float        # Kelvin
    matter_density: float     # kg/m^3
    radiation_density: float  # kg/m^3
    hubble_param: float       # km/s/Mpc
    current_era: int          # Era index
    era_progress: float       # 0.0-1.0 within current era

    def lerp(self, other: 'PhysicsState', alpha: float) -> 'PhysicsState':
        """Linear interpolation for smooth rendering between physics steps."""
        return PhysicsState(
            cosmic_time=self.cosmic_time + (other.cosmic_time - self.cosmic_time) * alpha,
            scale_factor=self.scale_factor + (other.scale_factor - self.scale_factor) * alpha,
            temperature=self.temperature + (other.temperature - self.temperature) * alpha,
            matter_density=self.matter_density + (other.matter_density - self.matter_density) * alpha,
            radiation_density=self.radiation_density + (other.radiation_density - self.radiation_density) * alpha,
            hubble_param=self.hubble_param + (other.hubble_param - self.hubble_param) * alpha,
            current_era=self.current_era,  # Don't interpolate discrete values
            era_progress=self.era_progress + (other.era_progress - self.era_progress) * alpha,
        )


class SimulationEngine:
    PHYSICS_DT = 1.0 / 60.0  # Fixed 60 Hz physics

    def __init__(self):
        self.accumulator = 0.0
        self.state = PhysicsState(...)
        self.prev_state = PhysicsState(...)
        self.speed_multiplier = 1.0
        self.paused = False

    def update(self, frametime: float) -> tuple[PhysicsState, float]:
        """Returns (interpolated_state, alpha) for rendering."""
        if self.paused:
            return self.state, 0.0

        self.accumulator += frametime * self.speed_multiplier

        while self.accumulator >= self.PHYSICS_DT:
            self.prev_state = copy(self.state)
            self._step(self.PHYSICS_DT)
            self.accumulator -= self.PHYSICS_DT

        alpha = self.accumulator / self.PHYSICS_DT
        return self.prev_state.lerp(self.state, alpha), alpha
```

### Pattern 2: Piecewise Logarithmic Timeline Mapping

**What:** Maps wall-clock playback time to cosmic time via a piecewise function. Each cosmological era gets a configurable "screen time budget" (e.g., 15 seconds for Planck epoch, 20 seconds for nucleosynthesis). Within each era, time progresses logarithmically to distribute sub-era detail evenly across orders of magnitude.

**When to use:** This project. The cosmic timeline spans from 10^-43 seconds to ~4.35x10^17 seconds (13.8 billion years) -- 60 orders of magnitude. No single function maps this usefully. The piecewise approach is the only way to give each era appropriate screen time.

**Example:**
```python
# Source: Pitfalls research + project-specific design
import math
from dataclasses import dataclass

@dataclass
class EraTimeBudget:
    """Defines how a cosmological era maps to screen time."""
    name: str
    cosmic_start: float   # Seconds after Big Bang
    cosmic_end: float     # Seconds after Big Bang
    screen_seconds: float # How many seconds of real time this era gets

# Configure per-era screen time budgets (tunable)
ERA_BUDGETS = [
    EraTimeBudget("Planck Epoch",       1e-43,  1e-36,  12.0),
    EraTimeBudget("Grand Unification",  1e-36,  1e-12,  12.0),
    EraTimeBudget("Inflation",          1e-36,  1e-32,  15.0),  # Overlaps GUT
    EraTimeBudget("Quark-Gluon Plasma", 1e-12,  1e-6,   15.0),
    EraTimeBudget("Hadron Epoch",       1e-6,   1.0,    12.0),
    EraTimeBudget("Nucleosynthesis",    1.0,    1200.0, 20.0),
    EraTimeBudget("Recombination/CMB",  1.2e3,  1.2e13, 20.0),
    EraTimeBudget("Dark Ages",          1.2e13, 6.3e15, 12.0),
    EraTimeBudget("First Stars",        6.3e15, 1.3e16, 15.0),
    EraTimeBudget("Galaxy Formation",   1.3e16, 6.3e16, 18.0),
    EraTimeBudget("Large-Scale Struct.", 6.3e16, 4.35e17, 15.0),
]

def screen_to_cosmic(screen_time: float, budgets: list[EraTimeBudget]) -> float:
    """Convert wall-clock playback time to cosmic time (seconds after Big Bang).

    Within each era, uses logarithmic interpolation to distribute detail
    evenly across orders of magnitude.
    """
    elapsed = 0.0
    for era in budgets:
        if screen_time <= elapsed + era.screen_seconds:
            # We are within this era
            frac = (screen_time - elapsed) / era.screen_seconds  # 0.0 to 1.0
            log_start = math.log10(max(era.cosmic_start, 1e-45))
            log_end = math.log10(era.cosmic_end)
            log_time = log_start + frac * (log_end - log_start)
            return 10.0 ** log_time
        elapsed += era.screen_seconds
    # Past all eras -- return end of universe
    return budgets[-1].cosmic_end
```

### Pattern 3: Camera-Relative Rendering for Precision

**What:** All vertex positions are transformed relative to the camera position BEFORE uploading to the GPU. This keeps GPU-side float32 coordinates near zero where precision is highest. The CPU computes the model-view matrix in double precision (Python float64), then casts to float32 only at the GPU upload boundary.

**When to use:** Any simulation spanning more than ~7 orders of magnitude in spatial scale. This project spans 40+ orders of magnitude.

**Source:** Unity HDRP Camera-Relative Rendering documentation, Ogre Forums, game industry standard practice for space simulations

**Example:**
```python
# Source: Camera-relative rendering pattern (industry standard)
import glm
import numpy as np

class CameraRelativeRenderer:
    """Transforms world-space positions relative to camera before GPU upload."""

    def compute_view_matrix(self, camera_pos: glm.dvec3, camera_target: glm.dvec3,
                            up: glm.dvec3 = glm.dvec3(0, 1, 0)) -> glm.mat4:
        """Compute view matrix in double precision, return as float32 for GPU."""
        # Double precision lookAt -- camera position becomes the origin
        view_d = glm.lookAt(camera_pos, camera_target, up)
        # Cast to float32 for GPU -- safe because all values are now camera-relative
        return glm.mat4(view_d)

    def transform_positions_camera_relative(
        self, positions: np.ndarray, camera_pos: np.ndarray
    ) -> np.ndarray:
        """Subtract camera position in float64, then cast to float32."""
        relative = positions.astype(np.float64) - camera_pos.astype(np.float64)
        return relative.astype(np.float32)
```

### Pattern 4: Orbit Camera with Smooth Damping

**What:** Extends moderngl-window's OrbitCamera concept with exponential damping. Mouse drag sets angular velocity; each frame, velocity decays exponentially, producing smooth deceleration after the user releases the mouse button. Zoom (scroll wheel) and pan (middle-click drag) use the same damping approach.

**When to use:** CAMR-01 requires "smooth damping." The built-in OrbitCamera has no damping -- it snaps to the position immediately.

**Example:**
```python
# Source: Standard orbit camera with exponential damping
import glm
import math

class DampedOrbitCamera:
    def __init__(self, target=glm.vec3(0), radius=5.0, fov=60.0,
                 near=0.01, far=1000.0, aspect=16/9):
        self.target = glm.vec3(target)
        self.radius = radius
        self.fov = fov
        self.near = near
        self.far = far
        self.aspect = aspect

        self.azimuth = 0.0      # Horizontal angle (degrees)
        self.elevation = -30.0  # Vertical angle (degrees), clamped to avoid poles

        # Damping state
        self._vel_azimuth = 0.0
        self._vel_elevation = 0.0
        self._vel_zoom = 0.0
        self._vel_pan = glm.vec2(0)
        self.damping = 0.05  # Lower = more damping (0 = instant stop)

    def update(self, dt: float):
        """Apply damped velocities. Call once per frame."""
        decay = self.damping ** dt  # Exponential decay
        self.azimuth += self._vel_azimuth * dt
        self.elevation += self._vel_elevation * dt
        self.elevation = max(-89.0, min(89.0, self.elevation))
        self.radius *= (1.0 + self._vel_zoom * dt)
        self.radius = max(0.01, self.radius)
        # Decay velocities
        self._vel_azimuth *= decay
        self._vel_elevation *= decay
        self._vel_zoom *= decay

    def on_mouse_drag(self, dx: float, dy: float, sensitivity=0.3):
        """Left-click drag: orbit."""
        self._vel_azimuth = dx * sensitivity * 60.0
        self._vel_elevation = dy * sensitivity * 60.0

    def on_scroll(self, y_offset: float, sensitivity=0.1):
        """Scroll wheel: zoom."""
        self._vel_zoom = -y_offset * sensitivity

    @property
    def position(self) -> glm.vec3:
        az = math.radians(self.azimuth)
        el = math.radians(self.elevation)
        return self.target + glm.vec3(
            self.radius * math.cos(el) * math.sin(az),
            self.radius * math.sin(el),
            self.radius * math.cos(el) * math.cos(az),
        )

    @property
    def view_matrix(self) -> glm.mat4:
        return glm.lookAt(self.position, self.target, glm.vec3(0, 1, 0))

    @property
    def projection_matrix(self) -> glm.mat4:
        return glm.perspective(glm.radians(self.fov), self.aspect, self.near, self.far)
```

### Anti-Patterns to Avoid

- **Linear time mapping:** Allocating cosmic time proportionally to wall-clock time. Early eras become invisible. Use piecewise logarithmic mapping.
- **Single global coordinate system:** Using one spatial coordinate system for all eras. Float32 precision breaks at cosmic scales. Use camera-relative rendering and per-era normalized coordinates.
- **Physics in the render loop:** Computing Friedmann equation ODE solutions per frame. Pre-compute the scale factor lookup table at startup. The render loop only interpolates from the table.
- **Hardcoded magic constants:** Embedding cosmological values directly in code without citations. Centralize in constants.py with source comments.
- **Tight coupling between simulation and rendering:** Making physics depend on the OpenGL context. The simulation layer must be independently testable.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Stiff ODE integration | Custom Runge-Kutta for Friedmann equations | `scipy.integrate.solve_ivp(method='Radau')` | Friedmann equations become stiff at radiation-matter transition. Implicit solvers (Radau/BDF) handle this; explicit methods require impractically small steps. |
| 3D matrix math | NumPy matrix operations for camera transforms | PyGLM `glm.lookAt()`, `glm.perspective()`, `glm.rotate()` | PyGLM is 10-100x faster for single-matrix operations and matches GLSL conventions exactly. |
| Windowing / event loop | Custom GLFW/SDL bindings | moderngl-window `WindowConfig` subclass | Handles platform differences, OpenGL context creation, event dispatch, and timer management. |
| Key/mouse input handling | Raw OS input polling | moderngl-window `on_key_event()`, `mouse_drag_event()` | Unified across backends (pyglet, glfw, sdl2). Key constants like `self.wnd.keys.SPACE` are portable. |
| Cosmological parameter lookup | Implementing astropy.cosmology from scratch | Pre-computed lookup table from Friedmann equation integration | Astropy's Planck18 realization provides canonical values for validation. But for runtime, pre-compute a dense table at startup and interpolate at O(1) per frame. |

## Common Pitfalls

### Pitfall 1: Logarithmic Time-Scale Collapse

**What goes wrong:** The timeline spans 60 orders of magnitude. A naive linear mapping makes the first microsecond of the universe (where the most dramatic physics happens) occupy zero screen time, while the Dark Ages (visually boring) dominate.
**Why it happens:** Developers think in wall-clock or linear cosmic time.
**How to avoid:** Implement piecewise logarithmic time mapping with per-era screen time budgets as a first-class configuration system. Each era gets a tunable number of seconds of real-time display.
**Warning signs:** Early eras flash by in under a second. You add `time.sleep()` hacks. Long stretches feel empty.

### Pitfall 2: Floating-Point Precision at Cosmic Scales

**What goes wrong:** Float32 has ~7 decimal digits of precision. Particle positions spanning sub-atomic to cosmic scales cause visible grid-snapping, jitter, and z-fighting.
**Why it happens:** Using a single coordinate system with absolute world-space positions on the GPU.
**How to avoid:** Camera-relative rendering (transform all positions relative to camera in float64, then cast to float32). Per-era coordinate normalization (positions as dimensionless fractions, not absolute units).
**Warning signs:** Particles snap to invisible grid. Jittering at large distances from origin. Z-fighting between overlapping surfaces.

### Pitfall 3: Friedmann Equation Numerical Instability

**What goes wrong:** Using a non-stiff ODE solver (basic Runge-Kutta) for the Friedmann equations. The radiation-to-matter dominance transition creates stiff behavior where the solver requires impractically small timesteps or diverges entirely.
**Why it happens:** Standard RK4/RK45 solvers are not designed for stiff systems.
**How to avoid:** Use `scipy.integrate.solve_ivp` with `method='Radau'` or `'BDF'` (implicit solvers designed for stiff systems). Pre-compute the scale factor table at startup with high resolution, then interpolate at O(1) per frame.
**Warning signs:** Scale factor curve has kinks or oscillations near matter-radiation equality.

### Pitfall 4: Gimbal Lock in Orbit Camera

**What goes wrong:** The orbit camera uses spherical coordinates (azimuth + elevation). When elevation approaches +/-90 degrees (looking straight up/down), the camera flips or jerks unpredictably.
**Why it happens:** At the poles of the sphere, a small change in azimuth produces a large change in the camera's "right" direction, causing instability.
**How to avoid:** Clamp elevation to a safe range (e.g., -89 to +89 degrees). The moderngl-window OrbitCamera already clamps angle_y between -175 and -5 degrees. Our custom damped camera must do the same.
**Warning signs:** Camera flips when looking straight up or down. Camera "spins" at extreme angles.

### Pitfall 5: Physics Engine Coupled to Rendering

**What goes wrong:** The physics engine imports ModernGL or requires an OpenGL context. Tests cannot run on CI or headless environments. Changes to rendering break physics.
**Why it happens:** It feels natural to compute physics parameters and upload them as uniforms in the same function.
**How to avoid:** Strict layered architecture. The simulation/ package has zero imports from rendering/. They communicate through a PhysicsState dataclass containing only Python primitives. Physics is independently testable with `pytest` alone.
**Warning signs:** Physics tests require a window to be open. `import bigbangsim.simulation.cosmology` triggers OpenGL initialization.

## Code Examples

### Cosmological Constants Module

```python
# Source: Planck 2018 (arXiv:1807.06209) Table 2 (TT,TE,EE+lowE+lensing+BAO)
# and PDG Review of Particle Physics

# === Planck 2018 Cosmological Parameters ===
# Reference: Planck Collaboration (2020), A&A 641, A6, Table 2
# Combined TT,TE,EE+lowE+lensing+BAO constraints

H0 = 67.66            # Hubble constant [km/s/Mpc] +/- 0.42
H0_SI = 2.1927e-18    # Hubble constant [1/s] (H0 / Mpc_in_km)
OMEGA_B_H2 = 0.02242  # Baryon density parameter * h^2, +/- 0.00014
OMEGA_C_H2 = 0.11933  # Cold dark matter density * h^2, +/- 0.00091
OMEGA_M = 0.3111       # Total matter density parameter, +/- 0.0056
OMEGA_LAMBDA = 0.6889  # Dark energy density parameter (1 - Omega_m for flat universe)
OMEGA_R = 9.15e-5      # Radiation density parameter (photons + relativistic neutrinos)
SIGMA_8 = 0.8102       # Matter fluctuation amplitude, +/- 0.0060
N_S = 0.9665           # Scalar spectral index, +/- 0.0038
TAU = 0.0561           # Optical depth to reionization, +/- 0.0071
N_EFF = 3.046          # Effective number of neutrino species
T_CMB_0 = 2.7255       # CMB temperature today [K] (Fixsen 2009)
AGE_UNIVERSE = 13.787e9 * 365.25 * 24 * 3600  # Age of universe [seconds], 13.787 +/- 0.020 Gyr

# === Derived Parameters ===
h = H0 / 100.0        # Reduced Hubble parameter, dimensionless
OMEGA_B = OMEGA_B_H2 / h**2  # Baryon density parameter

# === Physical Constants (CODATA 2018 / PDG) ===
G = 6.67430e-11        # Gravitational constant [m^3 kg^-1 s^-2]
C = 2.99792458e8       # Speed of light [m/s]
K_B = 1.380649e-23     # Boltzmann constant [J/K]
HBAR = 1.054571817e-34 # Reduced Planck constant [J s]
M_P = 1.672621924e-27  # Proton mass [kg]
M_E = 9.1093837015e-31 # Electron mass [kg]
SIGMA_T = 6.6524587e-29 # Thomson cross section [m^2]

# === Planck Units ===
T_PLANCK = 5.391e-44   # Planck time [s]
L_PLANCK = 1.616e-35   # Planck length [m]
M_PLANCK = 2.176e-8    # Planck mass [kg]
T_PLANCK_KELVIN = 1.416784e32  # Planck temperature [K]

# === BBN Values (PDG Review 2024) ===
YP_HE4 = 0.2470       # Primordial He-4 mass fraction, +/- 0.0002
DH_RATIO = 2.527e-5   # Primordial D/H ratio, +/- 0.030e-5
# Note: Lithium-7 abundance has the "cosmological lithium problem" --
# theory predicts ~3x more than observed. Display both values with disclaimer.
LI7_H_THEORY = 5.46e-10  # Theoretical Li-7/H (SBBN prediction)
LI7_H_OBSERVED = 1.6e-10 # Observed Li-7/H (Spite plateau)

# === Era Boundaries (approximate, in seconds after Big Bang) ===
ERA_PLANCK_END = 5.39e-44        # End of Planck epoch
ERA_GUT_END = 1e-36              # End of Grand Unification
ERA_INFLATION_END = 1e-32        # End of Inflation
ERA_QGP_END = 1e-6               # End of Quark-Gluon Plasma
ERA_HADRON_END = 1.0             # End of Hadron epoch
ERA_NUCLEOSYNTHESIS_END = 1200.0 # End of Big Bang Nucleosynthesis (~20 min)
ERA_RECOMBINATION_END = 1.2e13   # End of Recombination (~380,000 years)
ERA_DARK_AGES_END = 6.3e15       # End of Dark Ages (~200 Myr)
ERA_FIRST_STARS_END = 1.3e16     # End of Reionization (~400 Myr)
ERA_GALAXY_END = 6.3e16          # End of Galaxy Formation (~2 Gyr)
ERA_LSS_END = 4.35e17            # Present day (13.8 Gyr)
```

### WindowConfig Application Shell

```python
# Source: moderngl-window basic usage + architecture research
import moderngl_window as mglw

class BigBangSimApp(mglw.WindowConfig):
    gl_version = (4, 3)  # Require OpenGL 4.3 for compute shaders (Phase 2+)
    title = "BigBangSim"
    window_size = (1920, 1080)
    resizable = True
    vsync = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.camera = DampedOrbitCamera(
            aspect=self.wnd.aspect_ratio, near=0.01, far=1000.0
        )
        self.simulation = SimulationEngine()
        self.paused = False
        self.speed = 1.0
        # ... load test scene shaders, create test geometry

    def on_render(self, time: float, frametime: float):
        self.ctx.clear(0.02, 0.02, 0.05)  # Near-black background
        self.camera.update(frametime)
        state, alpha = self.simulation.update(frametime)
        # ... render test scene with camera view/projection matrices

    def on_key_event(self, key, action, modifiers):
        keys = self.wnd.keys
        if action == keys.ACTION_PRESS:
            if key == keys.SPACE:
                self.simulation.paused = not self.simulation.paused
            elif key == keys.EQUAL:  # '+' key (unshifted '=')
                self.simulation.speed_multiplier = min(10.0, self.simulation.speed_multiplier * 2.0)
            elif key == keys.MINUS:
                self.simulation.speed_multiplier = max(0.5, self.simulation.speed_multiplier / 2.0)

    def mouse_drag_event(self, x: int, y: int, dx: int, dy: int):
        self.camera.on_mouse_drag(dx, dy)

    def mouse_scroll_event(self, x_offset: float, y_offset: float):
        self.camera.on_scroll(y_offset)

if __name__ == '__main__':
    mglw.run_window_config(BigBangSimApp)
```

### Scale Factor Pre-Computation

```python
# Source: Friedmann equation integration pattern
import numpy as np
from scipy.integrate import solve_ivp

def precompute_scale_factor_table(
    omega_r: float, omega_m: float, omega_lambda: float, h0_si: float,
    a_start: float = 1e-12, a_end: float = 1.0, n_points: int = 10000
) -> tuple[np.ndarray, np.ndarray]:
    """Pre-compute scale factor a(t) vs cosmic time t.

    Uses Friedmann equation: (da/dt)^2 = H0^2 * (Omega_r/a^2 + Omega_m/a + Omega_Lambda * a^2)
    Solved as a first-order ODE system with implicit solver for stiff regions.

    Returns:
        (times, scale_factors) -- sorted arrays for interpolation
    """
    def friedmann_rhs(t, y):
        a = y[0]
        if a <= 0:
            return [0.0]
        # Hubble parameter squared at scale factor a
        H2 = h0_si**2 * (omega_r / a**4 + omega_m / a**3 + omega_lambda)
        dadt = a * np.sqrt(max(H2, 0.0))
        return [dadt]

    # Integrate forward from early universe
    # Use Radau (implicit) for stiff radiation-matter transition
    sol = solve_ivp(
        friedmann_rhs,
        t_span=[0.0, 4.5e17],  # 0 to ~14.2 Gyr in seconds
        y0=[a_start],
        method='Radau',
        max_step=1e14,
        rtol=1e-10,
        atol=1e-15,
        dense_output=True,
    )

    # Generate uniformly-spaced table in log-time for efficient lookup
    log_times = np.linspace(np.log10(1.0), np.log10(4.35e17), n_points)
    times = 10.0 ** log_times
    scale_factors = sol.sol(times)[0]

    return times, scale_factors
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pyrr for 3D math | PyGLM 2.8.3 | 2023+ | pyrr unmaintained, PyGLM is C++ speed with GLM-compatible API |
| pyimgui for HUD | imgui-bundle 1.92.601 | 2024+ | pyimgui wraps ancient ImGui v1.82; imgui-bundle wraps v1.90.9+ |
| pyglet 1.x for windowing | pyglet 2.x (via moderngl-window 3.1.1) | 2024 | moderngl-window 3.1.1 requires pyglet >= 2.0 |
| Python 3.10 as minimum | Python 3.11-3.14 viable | 2025+ | All core deps now have 3.13/3.14 wheels or build from source |
| CPU particle updates | GPU compute shaders (OpenGL 4.3) | Always for 100K+ | The industry standard; CPU is not viable for particle counts in this project |

## Open Questions

1. **OrbitCamera smooth damping tuning**
   - What we know: Exponential damping with a configurable decay constant works well. The built-in OrbitCamera has no damping.
   - What's unclear: Ideal damping constant for "feels good" camera -- needs interactive tuning.
   - Recommendation: Start with damping=0.05 (approximately 3-second decay to 5% velocity). Expose as a config value. Tune during implementation.

2. **Era time budget allocation**
   - What we know: Each era needs a configurable screen time budget. The piecewise logarithmic mapping is the right approach.
   - What's unclear: The exact seconds per era that produce the best viewing experience. Total playback time at 1x speed.
   - Recommendation: Start with the budgets in the code example (~166 seconds total at 1x, about 2.75 minutes). These are tunable configuration, not code. Iterate after Phase 3 when visual content exists.

3. **Friedmann equation initial conditions**
   - What we know: The standard approach is integrating forward from a_start near zero using density parameters.
   - What's unclear: The exact starting scale factor for numeric integration (a=1e-12? 1e-15? earlier?) and whether it matters for the visual timeline.
   - Recommendation: Start integration at a=1e-12 (well within radiation-dominated era). The pre-Planck-epoch physics is not described by standard Friedmann equations anyway. Validate against astropy Planck18 values at known redshifts (z=0, z=1100 for CMB, z~10 for reionization).

4. **Speed control: stepped vs smooth**
   - What we know: CAMR-04 specifies +/- keys with 0.5x to 10x range.
   - What's unclear: Whether speed changes should be stepped (0.5, 1, 2, 4, 8, 10) or smooth (continuous multiplier).
   - Recommendation (Claude's discretion): Use stepped doubling (0.5x, 1x, 2x, 4x, 8x, then cap at 10x). Stepped is more intuitive for keyboard control. Display current speed in corner of window.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | Yes | 3.14.3 | Also have 3.13. Note: 3.11 NOT installed (stack research recommended 3.11 for pyo, but audio is Phase 4) |
| pip | Package install | Yes | 25.3 | -- |
| ModernGL | OpenGL binding | Yes (installable) | 5.12.0 (builds from source) | -- |
| moderngl-window | Windowing | Yes (installable) | 3.1.1 (pure Python wheel) | -- |
| PyGLM | 3D math | Yes (installable) | 2.8.3 (cp314 wheel) | -- |
| NumPy | Arrays | Yes (installable) | 2.4.3 (cp314 wheel) | -- |
| SciPy | ODE solver | Yes (installable) | 1.17.1 (cp314 wheel) | -- |
| OpenGL 4.3+ GPU | Compute shaders | Assumed | User has modern GPU per project constraints | OpenGL 3.3 fallback (reduced features) |
| pytest | Testing | Yes (installable) | 9.0.2 | -- |
| ruff | Linting | Yes (installable) | 0.15.8 | -- |
| Git | Version control | Yes | Present (repo exists) | -- |

**Missing dependencies with no fallback:** None

**Missing dependencies with fallback:** Python 3.11 is not installed but is not needed for Phase 1. If pyo audio is required in Phase 4, install Python 3.11 at that time or use sounddevice fallback.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | None -- Wave 0 creates pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `py -3.14 -m pytest tests/ -x --tb=short` |
| Full suite command | `py -3.14 -m pytest tests/ -v` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PHYS-05 | Constants match Planck 2018/PDG published values | unit | `py -3.14 -m pytest tests/test_constants.py -x` | No -- Wave 0 |
| PHYS-03 | Logarithmic time mapping spans 60+ orders of magnitude | unit | `py -3.14 -m pytest tests/test_timeline.py -x` | No -- Wave 0 |
| PHYS-06 | Fixed-timestep accumulator produces consistent physics | unit | `py -3.14 -m pytest tests/test_simulation.py -x` | No -- Wave 0 |
| PHYS-07 | Camera-relative transform preserves precision | unit | `py -3.14 -m pytest tests/test_camera.py::test_precision -x` | No -- Wave 0 |
| CAMR-01 | Camera orbit/zoom/pan produce expected matrices | unit | `py -3.14 -m pytest tests/test_camera.py -x` | No -- Wave 0 |
| CAMR-04 | Play/pause/speed controls modify simulation state | unit | `py -3.14 -m pytest tests/test_simulation.py::test_speed_controls -x` | No -- Wave 0 |
| PHYS-03 | Timeline bar renders (visual check) | manual-only | Launch app, verify timeline bar visible | N/A |
| CAMR-01 | Camera feels smooth (subjective) | manual-only | Launch app, test mouse orbit/zoom | N/A |

### Sampling Rate

- **Per task commit:** `py -3.14 -m pytest tests/ -x --tb=short`
- **Per wave merge:** `py -3.14 -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `pyproject.toml` -- project metadata, pytest config, ruff config
- [ ] `tests/__init__.py` -- test package init
- [ ] `tests/test_constants.py` -- verify every constant matches published source
- [ ] `tests/test_cosmology.py` -- verify scale factor, temperature, density at known cosmic times
- [ ] `tests/test_timeline.py` -- verify logarithmic mapping, era boundaries, round-trip
- [ ] `tests/test_simulation.py` -- verify fixed-timestep accumulator, speed controls, pause
- [ ] `tests/test_camera.py` -- verify orbit/zoom/pan math, precision preservation
- [ ] Framework install: `pip install pytest ruff` in venv

## Sources

### Primary (HIGH confidence)
- [Planck 2018 Results VI (arXiv:1807.06209)](https://arxiv.org/abs/1807.06209) -- Canonical cosmological parameter values (Table 2)
- [Astropy Planck18 realization](https://docs.astropy.org/en/stable/api/astropy.cosmology.realizations.Planck18.html) -- Cross-reference: H0=67.66, Om0=0.30966, Ob0=0.04897, Tcmb0=2.7255 K
- [moderngl-window camera.py source](https://github.com/moderngl/moderngl-window/blob/master/moderngl_window/scene/camera.py) -- OrbitCamera: rot_state(dx,dy), zoom_state(y_offset), angle clamping
- [moderngl-window WindowConfig basic usage](https://moderngl-window.readthedocs.io/en/latest/guide/basic_usage.html) -- on_render, on_key_event, mouse events API
- [moderngl-window window_events.py example](https://github.com/moderngl/moderngl-window/blob/master/examples/window_events.py) -- Key event handling, mouse events, key state checking
- [Fix Your Timestep! (Gaffer on Games)](https://gafferongames.com/post/fix_your_timestep/) -- Accumulator pattern for fixed-timestep simulation
- [Game Loop (Game Programming Patterns)](https://gameprogrammingpatterns.com/game-loop.html) -- Fixed-timestep with interpolation

### Secondary (MEDIUM confidence)
- [Numerically Modeling Expansion (reedbeta.com)](https://www.reedbeta.com/blog/numerically-modeling-the-expansion-of-the-universe/) -- Friedmann equation numerical integration approach with density parameters
- [Unity HDRP Camera-Relative Rendering](https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@10.3/manual/Camera-Relative-Rendering.html) -- Camera-relative rendering technique: subtract camera position before GPU upload
- [Floating Point Precision in 3D (Medium)](https://medium.com/@thibautandrieu/the-problem-of-floating-point-precision-in-opengl-vulkan-and-3d-in-general-part-3-ce101a80995d) -- Double-precision model-view, cast to float32 at GPU boundary
- [Numerical Solving of Friedmann Equations (dournac.org)](https://dournac.org/info/friedmann) -- Stiff ODE challenges, SciPy solver recommendations
- [PDG Review: Big Bang Nucleosynthesis](https://pdg.lbl.gov/2024/reviews/rpp2024-rev-bbang-nucleosynthesis.pdf) -- BBN yields, lithium problem

### Tertiary (LOW confidence)
- [Visualizing Cosmological Time (ResearchGate)](https://www.researchgate.net/publication/221024616_Visualizing_Cosmological_Time) -- Logarithmic timeline visualization concepts
- [Palaeos: Logarithmic Time](http://palaeos.com/time/logarithmic.html) -- Logarithmic cosmic timeline visualization reference

### Environment Verification (verified 2026-03-27)
- `py -3.14 -m pip install --dry-run` confirmed: moderngl 5.12.0, moderngl-window 3.1.1, PyGLM 2.8.3, numpy 2.4.3, scipy 1.17.1 all installable on Python 3.14.3 (Windows)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries verified installable on user's Python 3.14, versions confirmed via pip
- Architecture: HIGH -- fixed-timestep simulation, orbit camera, layered architecture are industry-standard patterns with multiple verified sources
- Pitfalls: HIGH -- logarithmic time collapse, float precision, ODE stiffness all documented in project research with prevention strategies
- Constants: HIGH -- Planck 2018 Table 2 values cross-referenced with astropy Planck18 realization
- Timeline mapping: MEDIUM -- piecewise logarithmic approach is sound but era time budgets are first-pass estimates requiring iterative tuning

**Research date:** 2026-03-27
**Valid until:** 2026-05-27 (60 days -- stable libraries, fixed scientific constants, well-established patterns)
