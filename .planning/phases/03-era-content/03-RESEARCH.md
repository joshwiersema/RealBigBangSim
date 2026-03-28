# Phase 3: Era Content - Research

**Researched:** 2026-03-28
**Domain:** Per-era cosmological physics models, per-era GLSL fragment/compute shaders, crossfade transitions
**Confidence:** HIGH

## Summary

Phase 3 populates all 11 cosmological eras with scientifically accurate physics models and visually distinct GPU shaders. The existing codebase provides a solid foundation: Phase 1 built the simulation layer (Friedmann equations, era definitions, timeline controller, PhysicsState), and Phase 2 built the rendering infrastructure (ping-pong SSBOs, per-era shader switching via `set_era_shader()`, post-processing bloom pipeline, shader include preprocessor). The current system has only two fragment shaders (`particle_hot.frag`, `particle_cool.frag`) and a single generic compute shader -- Phase 3 must expand this to 11 visually distinct eras with physics-driven behavior.

The work divides into three pillars: (1) **per-era physics models** on the Python simulation layer (BBN yields, Saha ionization fraction, Jeans mass, Press-Schechter statistics) that feed new uniforms to shaders; (2) **per-era fragment and compute shader variants** that give each era a unique visual identity driven by those physics uniforms; and (3) **smooth crossfade transitions** between adjacent eras using FBO-based alpha blending during transition windows. The physics models should be analytical/lookup-table approaches (not numerical solvers running per-frame) since all heavy computation must stay within the GPU's existing fixed-timestep compute dispatch.

**Primary recommendation:** Build a data-driven `EraVisualConfig` system that pairs each era with its shader program key, color palette parameters, particle behavior uniforms, and transition duration. Expand `ParticleSystem` to compile 11 fragment shaders and use FBO crossfade blending during era transitions. Add physics sub-modules (`nucleosynthesis.py`, `recombination.py`, `structure.py`) that compute era-specific uniforms from PhysicsState.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
None -- user deferred all gray areas to Claude's judgment.

### Claude's Discretion
Full discretion on:
- Per-era color palettes and visual styles
- Physics model complexity per era (analytical vs numerical)
- Fragment shader count (one per era vs grouping similar eras)
- Crossfade transition implementation (uniform blending vs FBO lerp)
- Particle behavior variation per era (spawn patterns, velocities, lifetimes)
- How to handle early-era visuals (Planck epoch, Grand Unification) where no established conventions exist
- BBN yield calculation detail level
- Saha equation implementation approach
- Jeans instability and Press-Schechter approximation fidelity
- Era-specific compute shader behavior vs uniform-driven variation

### Deferred Ideas (OUT OF SCOPE)
None -- all era content is in scope for this phase.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RNDR-03 | Each of the 11 cosmological eras has visually distinct shader programs with unique color palettes and particle behaviors | Per-era fragment shaders with distinct color palettes; EraVisualConfig system driving shader selection and uniform parameters |
| RNDR-04 | Era transitions crossfade smoothly between visual paradigms (no jarring cuts) | FBO-based dual-render crossfade during configurable transition windows (5-10% of era screen time) |
| PHYS-01 | Simulation covers all 11 cosmological eras: Planck epoch through Large-Scale Structure | Era definitions already exist in `eras.py`; physics sub-modules provide era-specific parameters for all 11 |
| PHYS-02 | Each era uses real cosmological physics models -- Friedmann equations for expansion, BBN yields for nucleosynthesis, Saha equation for recombination, Jeans instability for structure formation, Press-Schechter for halo statistics | Physics sub-modules implementing analytical forms of each model, feeding computed parameters as shader uniforms |
</phase_requirements>

## Standard Stack

No new libraries are required for Phase 3. All physics models use analytical/lookup-table approaches implementable with the existing stack.

### Core (already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| ModernGL | 5.12.0 | Shader programs, FBO rendering | Already in use; FBO crossfade requires creating one additional FBO |
| NumPy | 2.2.x | Array operations for physics sub-modules | Already used for particle init and cosmology model |
| SciPy | 1.14.x | `scipy.special.erfc` for Press-Schechter; `scipy.interpolate` for lookup tables | Already a dependency; needed for complementary error function |

### No New Dependencies
Phase 3 adds no new packages. All work is Python physics modules and GLSL shader files.

## Architecture Patterns

### Recommended Project Structure (Phase 3 additions)
```
bigbangsim/
  simulation/
    physics/                  # NEW: Per-era physics sub-modules
      __init__.py
      nucleosynthesis.py      # BBN yields (PHYS-02)
      recombination.py        # Saha equation (PHYS-02)
      structure.py            # Jeans instability + Press-Schechter (PHYS-02)
    era_visual_config.py      # NEW: Data-driven visual config per era
  rendering/
    particles.py              # MODIFIED: expand to 11 shader variants + crossfade
    era_transition.py         # NEW: FBO crossfade manager
  shaders/
    fragment/                 # EXPANDED: 11 per-era fragment shaders
      era_00_planck.frag
      era_01_gut.frag
      era_02_inflation.frag
      era_03_qgp.frag
      era_04_hadron.frag
      era_05_nucleosynthesis.frag
      era_06_recombination.frag
      era_07_dark_ages.frag
      era_08_first_stars.frag
      era_09_galaxy_formation.frag
      era_10_lss.frag
    compute/
      particle_update.comp    # MODIFIED: era-driven behavior via uniforms
    include/
      era_utils.glsl          # NEW: shared era transition/color utilities
```

### Pattern 1: Data-Driven Era Visual Configuration
**What:** Each era gets a Python dataclass (`EraVisualConfig`) containing its shader program key, base color palette (vec3 uniforms), particle size multiplier, bloom intensity, expansion rate modifier, and transition duration. The `ParticleSystem` reads this config to select the correct shader and upload era-specific uniforms.

**When to use:** Every frame -- the render loop looks up the current era's config and applies it.

**Why this pattern:** Avoids hardcoded if/else chains in Python. Makes tuning visual parameters a data edit, not a code change. Matches Architecture Pattern 3 from ARCHITECTURE.md research.

```python
@dataclass(frozen=True)
class EraVisualConfig:
    """Visual configuration for one cosmological era."""
    era_index: int
    shader_key: str           # Key into ParticleSystem.programs dict
    base_color: tuple[float, float, float]  # Primary palette color
    accent_color: tuple[float, float, float]  # Secondary palette color
    particle_size: float      # Point scale multiplier
    bloom_strength: float     # Post-processing bloom intensity
    expansion_rate: float     # Compute shader expansion modifier
    noise_strength: float     # Noise contribution to particle motion
    transition_seconds: float # Duration of crossfade into this era
```

### Pattern 2: FBO Crossfade Transitions (RNDR-04)
**What:** During era transitions, render the scene twice -- once with the outgoing era's shader, once with the incoming era's shader -- each into separate FBOs. Then composite them with a fullscreen quad using `mix(outgoing, incoming, blend_factor)` where blend_factor ramps from 0.0 to 1.0 over the transition duration.

**When to use:** During the transition window at each era boundary (configurable, default 5-10% of the shorter era's screen time).

**Why FBO crossfade vs. uniform-only blending:** Uniform blending (passing a blend factor to a single shader) cannot blend between two fundamentally different visual styles. The Planck epoch (white energy noise) looks nothing like Grand Unification (purple symmetry-breaking patterns). Only rendering both and compositing can produce a smooth visual transition between radically different shader programs.

**Implementation sketch:**
```python
class EraTransitionManager:
    """Manages FBO-based crossfade between adjacent eras."""

    def __init__(self, ctx, width, height):
        # Second FBO for the outgoing era (incoming uses main HDR FBO)
        self.transition_fbo = ctx.framebuffer(
            color_attachments=[ctx.texture((width, height), 4, dtype="f2")]
        )
        self.blend_factor = 0.0
        self.in_transition = False
        # Fullscreen composite shader: mix(tex_outgoing, tex_incoming, u_blend)
        self.composite_prog = ...

    def render_transition(self, particles, proj, view, outgoing_config, incoming_config):
        # Render outgoing era to transition FBO
        self.transition_fbo.use()
        particles.render_with_config(outgoing_config, proj, view)
        # Render incoming era to main HDR FBO (handled by caller)
        # Composite in end_scene()
```

### Pattern 3: Uniform-Driven Compute Shader Variation (not per-era compute shaders)
**What:** Keep a SINGLE compute shader (`particle_update.comp`) but expand it with additional uniforms (`u_era`, `u_expansion_rate`, `u_noise_strength`, `u_gravity_strength`, `u_clustering_factor`) that change particle physics behavior per era. The compute shader uses these uniforms to modulate its update logic.

**When to use:** Always. Per-era compute shader variants would be wasteful -- the core particle update logic (position += velocity * dt, apply forces) is the same across eras. Only the force magnitudes and directions change.

**Why single compute with uniforms vs. multiple compute shaders:** Unlike fragment shaders (which produce radically different visual output per era), compute shaders perform the same operations with different magnitudes. Branching on `u_era` in compute shaders is acceptable because all particles in a given dispatch are in the same era (no warp divergence). This avoids maintaining 11 nearly-identical compute shader files.

```glsl
// In particle_update.comp -- era-driven behavior via uniforms
uniform float u_expansion_rate;   // Per-era expansion speed
uniform float u_noise_strength;   // Turbulence/random motion
uniform float u_gravity_strength; // Gravitational clustering
uniform float u_damping;          // Velocity damping factor

void main() {
    // ... existing particle read ...

    // Expansion (all eras, different rates)
    vel += pos * u_expansion_rate * u_dt;

    // Turbulence (early eras: strong; late eras: weak)
    // Noise function uses particle position as seed
    vec3 noise_offset = ...;  // from noise.glsl
    vel += noise_offset * u_noise_strength * u_dt;

    // Gravitational clustering (late eras only)
    // Pull toward density centers
    vel += -normalize(pos) * u_gravity_strength * u_dt / max(length(pos), 0.1);

    // Damping
    vel *= (1.0 - u_damping * u_dt);

    // ... existing particle write ...
}
```

### Anti-Patterns to Avoid
- **Per-era compute shaders:** 11 nearly-identical compute files that drift apart during maintenance. Use uniforms instead.
- **Mega-fragment shader with if/else chains:** Violates RNDR-06 (established in Phase 2). Keep separate fragment programs per era.
- **CPU-side per-frame physics computation for shader uniforms:** BBN yields, Saha ionization fraction, and Press-Schechter statistics should be pre-computed as lookup tables at startup, then interpolated per-frame. Never call `scipy.special.erfc` in the render loop.
- **Sudden shader switches without crossfade:** Violates RNDR-04. Even a 0.5-second crossfade prevents visual "jump cuts."
- **Hardcoded color values in shader source:** Colors should come from uniforms (driven by EraVisualConfig), not as literals in GLSL. This enables tuning without recompilation.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Saha equation numerical solver | Per-frame ODE solver for ionization fraction | Pre-computed lookup table indexed by temperature | Saha equation has a closed-form solution for hydrogen: x^2/(1-x) = f(T, n_b). Solve once at init, interpolate. |
| BBN network reaction solver | Nuclear reaction network integrator | Lookup table of known yields from PDG values | BBN yields depend only on baryon-to-photon ratio (fixed by Planck). Results are constants, not computed. |
| Press-Schechter halo mass function | Full mass function integration per frame | Pre-computed table of collapsed fraction F(>M) vs redshift | scipy.special.erfc computes the analytic PS formula. Tabulate at init. |
| Noise function in Python for particle motion | CPU-side Perlin/simplex noise per particle | GLSL simplex noise in compute shader (noise.glsl already exists) | Must run on GPU for 200K particles at 60 FPS. |
| Custom FBO management for crossfade | Raw framebuffer creation and binding | Extend existing PostProcessingPipeline with transition FBO | Reuse the half-float texture pattern already established. |

**Key insight:** The physics models for Phase 3 are all pre-computable. BBN yields are constants from observations. The Saha equation has a quadratic closed-form solution. Jeans mass is an analytical formula. Press-Schechter is an analytical formula with erfc. None of these need per-frame numerical integration -- they all become lookup tables sampled by cosmic time or temperature.

## Per-Era Visual Design

### Era 0: Planck Epoch (index 0, 10^-43 to 10^-36 s)
**Physics:** Quantum gravity regime. All forces unified. Temperature ~10^32 K.
**Visual language:** Abstract -- no physical particles exist. Pure energy field visualization.
**Color palette:** Blinding white core fading to pale gold edges. Maximum bloom.
**Particle behavior:** Tight Gaussian cluster, high noise/turbulence, minimal expansion. Particles represent energy density fluctuations, not physical objects.
**Shader character:** Intense white glow with high-frequency noise modulation. Point sizes small but extremely bright (HDR values >> 1.0 for bloom to catch).
**Educational note:** "Artistic interpretation -- physics beyond current theory."

### Era 1: Grand Unification (index 1, 10^-36 to 10^-12 s)
**Physics:** Gravity separates. Strong/weak/EM remain unified. Temperature ~10^28 K.
**Visual language:** Symmetry-breaking motif -- uniform field develops structure.
**Color palette:** Pale gold transitioning to lavender/purple (representing force separation).
**Particle behavior:** Slight expansion begins. Noise decreases as "order" emerges from symmetry breaking.
**Shader character:** Gradient from warm gold to cool lavender, animated with slow noise.

### Era 2: Inflation (index 2, 10^-36 to 10^-32 s)
**Physics:** Exponential expansion by factor ~10^26. Temperature drops then reheats.
**Visual language:** Dramatic outward explosion. Particles rush outward rapidly.
**Color palette:** Bright yellow-white (reheating energy) with space-stretching visual distortion.
**Particle behavior:** Extreme expansion rate (highest of any era). Particles accelerate outward from center. Low noise -- expansion dominates.
**Shader character:** Bright yellow-white particles with motion-blur-like elongated point sprites (or increased point size to suggest speed). Strong bloom.

### Era 3: Quark-Gluon Plasma (index 3, 10^-12 to 10^-6 s)
**Physics:** Free quarks and gluons in a superhot soup. Temperature ~10^15 to 10^12 K.
**Visual language:** Hot flowing fluid (CERN convention: orange-red churning fluid).
**Color palette:** Deep orange-red core, yellow-white highlights. Based on CERN/RHIC visualization conventions.
**Particle behavior:** High turbulence (noise_strength high), moderate expansion. Particles churn and swirl.
**Shader character:** Orange-red gradient with temperature-driven brightness variation. High noise in fragment shader for fluid-like texture.

### Era 4: Hadron Epoch (index 4, 10^-6 to 1 s)
**Physics:** Quarks combine into protons and neutrons. Temperature ~10^12 to 10^10 K.
**Visual language:** Transition from fluid to discrete particles. "Crystallization" motif.
**Color palette:** Orange fading to warm amber. Less saturated than QGP.
**Particle behavior:** Turbulence decreasing. Particles begin to separate into distinct entities. Expansion moderate.
**Shader character:** Warmer, more distinct particle edges (sharper alpha falloff than QGP's soft glow).

### Era 5: Nucleosynthesis (index 5, 1 to 1200 s)
**Physics:** BBN -- protons and neutrons fuse into H, He, Li. Temperature ~10^9 K.
**Visual language:** Nuclear fusion events. Particles cluster briefly then separate.
**Color palette:** Warm green-gold. Green tint represents nuclear energy.
**Particle behavior:** Moderate turbulence. Some clustering (pairs/triples forming then dispersing).
**Shader uniforms (PHYS-02):** `u_helium_fraction` (Y_P=0.247), `u_deuterium_fraction`, `u_lithium_fraction` from pre-computed BBN lookup. These drive particle type coloring: ~75% hydrogen (green-white), ~25% helium (gold), trace deuterium/lithium (blue specks).
**Shader character:** Particles colored by type. Brief bright flashes at fusion events (simulated by particle life cycling).

### Era 6: Recombination/CMB (index 6, 1.2x10^3 to 1.2x10^13 s)
**Physics:** Electrons bind to nuclei. Universe transitions from opaque plasma to transparent gas. CMB released at T~3000 K.
**Visual language:** THE signature transition of the universe. Opaque orange-white fog clearing to reveal dark space with faint glow.
**Color palette:** Starts warm orange-white (plasma), transitions through CMB gold, ends with faint red-orange glow on near-black.
**Shader uniforms (PHYS-02):** `u_ionization_fraction` from Saha equation lookup. Drives opacity: x=1.0 (fully ionized) = opaque bright; x=0.0 (neutral) = transparent dark. This is the most physically meaningful uniform in the entire simulation.
**Shader character:** Particle alpha modulated by ionization fraction. As recombination proceeds, particles fade from bright opaque to dim transparent. Background "clears." This should be the most visually dramatic moment in the entire simulation.

**Saha equation for ionization fraction:**
```
x^2 / (1 - x) = (1/n_b) * (2*pi*m_e*k_B*T / h^2)^(3/2) * exp(-13.6 eV / (k_B*T))
```
Where n_b = baryon number density (from cosmology model), T = temperature (from PhysicsState).
Solve this quadratic for x at each temperature in a lookup table at init.

### Era 7: Dark Ages (index 7, 1.2x10^13 to 6.3x10^15 s)
**Physics:** No stars. Neutral gas in expanding darkness. Temperature ~60 K down to ~20 K.
**Visual language:** Almost complete darkness. Minimal particle activity. Lonely, vast emptiness.
**Color palette:** Near-black with very faint deep blue. Extremely low bloom.
**Particle behavior:** Very slow expansion. Minimal noise. Particles dim and sparse.
**Shader character:** Particles nearly invisible (low alpha, low brightness). Faint density perturbations (seeds of future structure) visible as slightly brighter regions -- use noise to create subtle density fluctuations.

### Era 8: First Stars / Reionization (index 8, 6.3x10^15 to 1.3x10^16 s)
**Physics:** First massive Pop III stars ignite. UV radiation reionizes surrounding hydrogen.
**Visual language:** "Let there be light" moment. Bright point sources appear in the darkness.
**Color palette:** Deep blue-black background with brilliant blue-white star points. Stars are very hot (T > 30,000 K = blue-white).
**Particle behavior:** Most particles dim (gas). A few particles become extremely bright (stars). Stars appear gradually, then their light "spreads" as reionization bubbles.
**Shader uniforms (PHYS-02):** `u_jeans_mass` from Jeans instability calculation determines which particles are "massive enough" to be stars. `u_reionization_fraction` ramps from 0 to 1 as UV bubbles expand.
**Shader character:** Bimodal brightness: most particles dim, a few blazing bright. Star particles get large point sizes and maximum bloom. As era progresses, more particles brighten (reionization spreading).

**Jeans mass formula:**
```
M_J = (pi/6) * (c_s^3) / (G^(3/2) * rho^(1/2))
```
Where c_s = sound speed = sqrt(5*k_B*T / (3*mu*m_p)), rho = matter density.

### Era 9: Galaxy Formation (index 9, 1.3x10^16 to 6.3x10^16 s)
**Physics:** Gravity assembles matter into protogalaxies, galaxy clusters.
**Visual language:** Gravitational clustering visible. Particles form filaments and knots.
**Color palette:** Purple-blue filaments with bright blue-white nodes (galaxy centers).
**Particle behavior:** Strong gravitational clustering (gravity_strength high). Particles pulled toward density peaks. Filamentary structure emerges.
**Shader uniforms (PHYS-02):** `u_collapsed_fraction` from Press-Schechter gives the fraction of matter in collapsed halos. Drives clustering intensity.
**Shader character:** Density-mapped coloring. Low-density regions dark blue (voids), medium density purple (filaments), high density bright blue-white (galaxy clusters). Based on existing `density_to_color()` in colormap.glsl.

**Press-Schechter collapsed fraction:**
```
F(>M) = erfc(delta_c / (sqrt(2) * sigma(M,z)))
```
Where delta_c = 1.686 (critical overdensity), sigma(M,z) uses sigma_8 = 0.8102 from Planck 2018.

### Era 10: Large-Scale Structure (index 10, 6.3x10^16 to 4.35x10^17 s)
**Physics:** Cosmic web matures. Voids, filaments, walls, clusters.
**Visual language:** Grand cosmic web structure. Zoomed-out view of interconnected filaments.
**Color palette:** Deep space blue-black with bright blue-purple filaments and golden-white cluster nodes.
**Particle behavior:** Continued clustering. Well-defined filamentary network. Some particles in voids barely moving.
**Shader character:** Similar to Galaxy Formation but more structured and mature. Higher contrast between voids (dark) and filaments (bright). Warmer highlights at cluster nodes.

## Physics Model Implementation Details

### BBN Yields (nucleosynthesis.py) -- PHYS-02
**Approach:** Lookup table, NOT a reaction network solver.

The BBN yields are effectively constants determined by the baryon-to-photon ratio eta, which is fixed by Planck 2018 measurements (Omega_b * h^2 = 0.02242). The project's `constants.py` already contains the PDG 2024 values:
- Y_P = 0.2470 (He-4 mass fraction)
- D/H = 2.527e-5
- He-3/H = 1.04e-5
- Li-7/H = 1.6e-10 (theoretical; observed ~3x lower -- the "cosmological lithium problem")

**Implementation:** A simple module that returns these fractions as a function of temperature (nucleosynthesis proceeds from ~10^9 K to ~10^8 K). Before BBN onset, return 100% free protons/neutrons. After BBN completion, return the final yields. During BBN, interpolate linearly in log-temperature.

```python
def get_bbn_fractions(temperature: float) -> dict:
    """Return element mass fractions at given temperature.

    Pre-BBN (T > 10^9 K): all free nucleons
    During BBN (10^9 K > T > 3x10^8 K): interpolated yields
    Post-BBN (T < 3x10^8 K): final PDG yields
    """
```

**Confidence:** HIGH -- yields are published constants, not computed values.

### Saha Equation (recombination.py) -- PHYS-02
**Approach:** Pre-computed lookup table of ionization fraction x(T) at init.

The Saha equation for hydrogen ionization:
```
x^2 / (1 - x) = (2*pi*m_e*k_B*T)^(3/2) / (n_b * h^3) * exp(-E_ion / (k_B*T))
```
Where:
- x = ionization fraction (0 = fully neutral, 1 = fully ionized)
- m_e = electron mass = 9.109e-31 kg
- k_B = Boltzmann constant (from constants.py)
- T = temperature in Kelvin
- n_b = baryon number density (from cosmology model at each temperature)
- h = Planck constant = 6.626e-34 J*s
- E_ion = 13.6 eV = 2.179e-18 J (hydrogen ionization energy)

This is a quadratic in x: x^2 + A*x - A = 0, where A = (RHS of Saha).
Solution: x = (-A + sqrt(A^2 + 4A)) / 2, clamped to [0, 1].

**Pre-compute** a table of x(T) for T from 10,000 K down to 1,000 K (the recombination range) at init. During rendering, interpolate this table using temperature from PhysicsState.

**Important caveat:** The Saha equation assumes equilibrium and overpredicts recombination speed. For a visualization, this is acceptable -- the key visual effect is the transition from opaque (x~1) to transparent (x~0) around T~3000 K, and Saha captures this correctly. The Peebles equation would be more accurate but adds unnecessary complexity for visual purposes.

**Confidence:** HIGH -- Saha equation is textbook physics with a closed-form solution.

### Jeans Instability (structure.py) -- PHYS-02
**Approach:** Analytical formula evaluated at each temperature/density.

The Jeans mass determines the minimum mass for gravitational collapse:
```
M_J = (pi/6) * c_s^3 / (G^(3/2) * rho^(1/2))
```
Where:
- c_s = sound speed = sqrt(gamma * k_B * T / (mu * m_p))
- gamma = 5/3 (monatomic ideal gas)
- mu = mean molecular weight (~0.6 for ionized, ~1.22 for neutral)
- m_p = proton mass
- G = gravitational constant
- rho = matter density (from PhysicsState)

For the visualization: compute M_J at each frame. When M_J drops below the characteristic mass scale of the simulation's particle representation, particles should begin clustering. This transition drives the First Stars and Galaxy Formation eras.

**Pre-compute** M_J(z) as a function of redshift/temperature. Use as a uniform to modulate gravity_strength in the compute shader.

**Confidence:** HIGH -- analytical formula, well-established physics.

### Press-Schechter Formalism (structure.py) -- PHYS-02
**Approach:** Analytical formula with scipy.special.erfc, pre-computed at init.

The collapsed fraction (fraction of matter in halos above mass M):
```
F(>M) = erfc(delta_c / (sqrt(2) * sigma(M, z)))
```
Where:
- delta_c = 1.686 (critical overdensity for spherical collapse)
- sigma(M, z) = sigma_8 * D(z) * (M/M_8)^(-(n_s+3)/6)
- sigma_8 = 0.8102 (from Planck 2018, already in constants.py)
- D(z) = growth factor (proportional to scale factor in matter-dominated era)
- n_s = 0.9665 (scalar spectral index, already in constants.py)
- M_8 = mass within a sphere of radius 8 Mpc/h

For the visualization: compute F_collapsed(z) at several representative mass scales. The total collapsed fraction drives `u_clustering_factor` in the compute shader, which modulates gravitational attraction strength.

**Pre-compute** collapsed fraction vs cosmic time table at init. Interpolate per-frame.

**Confidence:** HIGH -- analytical formula, all parameters from Planck 2018.

## Transition Implementation Details

### Transition Window Configuration
Each era transition gets a configurable duration (default: 2 seconds of screen time, adjustable per boundary). The transition window is split evenly across the boundary: the last 1 second of the outgoing era and the first 1 second of the incoming era.

### Blend Factor Computation
```python
def compute_blend_factor(screen_time: float, boundary_screen_time: float,
                         transition_duration: float) -> float:
    """Returns 0.0 (fully outgoing) to 1.0 (fully incoming)."""
    half_dur = transition_duration / 2.0
    t = (screen_time - boundary_screen_time + half_dur) / transition_duration
    return smoothstep(clamp(t, 0.0, 1.0))  # Smooth easing, not linear
```

### Render Pipeline During Transitions
1. Render particles with **outgoing** era's fragment shader into `transition_fbo`
2. Render particles with **incoming** era's fragment shader into `hdr_fbo` (normal path)
3. Composite: `final = mix(transition_fbo, hdr_fbo, blend_factor)` via fullscreen quad
4. Continue with normal post-processing (bloom, tonemap)

This requires rendering particles twice during transitions (performance cost ~2x for particle rendering, but only during the ~2s transition window). At 200K particles this should remain well above 30 FPS.

### Special Transition: Recombination/CMB (Era 6)
This is the most visually dramatic transition. Rather than a simple crossfade, the ionization fraction uniform itself drives the visual change organically:
- As `u_ionization_fraction` drops from 1.0 to 0.0, the fragment shader smoothly transitions particle appearance from bright opaque plasma to dim transparent gas
- This means the recombination transition is PHYSICS-DRIVEN, not just a visual crossfade
- The FBO crossfade handles the shader program switch at the era boundary; the ionization fraction handles the visual evolution within the era

## Shader Uniform Expansion

### Current uniforms (common.glsl)
```glsl
uniform float u_dt;
uniform float u_temperature;
uniform float u_scale_factor;
uniform uint u_particle_count;
uniform int u_era;
uniform float u_era_progress;
```

### Phase 3 additions
```glsl
// Compute shader uniforms (particle behavior)
uniform float u_expansion_rate;    // Era-specific expansion speed
uniform float u_noise_strength;    // Turbulence magnitude
uniform float u_gravity_strength;  // Gravitational clustering force
uniform float u_damping;           // Velocity damping factor

// Fragment shader uniforms (visual appearance)
uniform vec3 u_base_color;         // Primary era color
uniform vec3 u_accent_color;       // Secondary era color
uniform float u_color_mix;         // Base-to-accent blend based on physics
uniform float u_brightness;        // Overall brightness multiplier
uniform float u_point_scale_era;   // Era-specific point size modifier

// Physics-specific uniforms (per-era)
uniform float u_ionization_fraction;  // Saha (era 6)
uniform float u_helium_fraction;      // BBN (era 5)
uniform float u_collapsed_fraction;   // Press-Schechter (eras 9-10)
uniform float u_reionization_frac;    // Reionization progress (era 8)
```

## Common Pitfalls

### Pitfall 1: Fragment Shader Uniform Optimization
**What goes wrong:** GLSL compilers aggressively optimize away uniforms that are not used in a particular shader. If you upload a uniform that the active fragment shader does not reference, ModernGL raises an error (KeyError on the uniform name). This already happened in Phase 2 (commit c94d2c1 fixed this for timeline bar uniforms).
**Why it happens:** Different fragment shaders use different subsets of uniforms. Uploading `u_ionization_fraction` to era_00_planck.frag (which does not use it) crashes.
**How to avoid:** Use `if 'uniform_name' in program:` guard before every uniform upload, as established in `app.py` on line 193-198. Alternatively, use a shared UBO for common uniforms (the shader compiler will silently ignore unused UBO members).
**Warning signs:** KeyError on program dictionary access during era transitions.

### Pitfall 2: Transition FBO Not Cleared Between Frames
**What goes wrong:** The transition FBO retains ghost images from previous frames, causing visual artifacts during crossfade -- outgoing era's particles appear doubled or smeared.
**Why it happens:** Forgetting to clear the transition FBO before rendering the outgoing era into it.
**How to avoid:** Always call `transition_fbo.clear(0.0, 0.0, 0.0, 0.0)` before rendering.

### Pitfall 3: Compute Shader Branching on u_era
**What goes wrong:** If the compute shader has `if (u_era == 0) ... else if (u_era == 1) ...` with divergent code paths, it looks like a problem but actually is NOT a problem here. All particles in a dispatch are in the same era, so all threads in every warp take the same branch. No divergence penalty.
**Why it matters:** Developers might over-engineer per-era compute shaders to avoid branching. This is unnecessary. Uniform-driven behavior is the correct approach for compute shaders where all invocations share the same uniform value.

### Pitfall 4: Bloom Blow-Out in High-Energy Eras
**What goes wrong:** Early eras (Planck, QGP) with extremely bright particles cause bloom to blow out the entire screen into white.
**Why it happens:** Fragment shaders output HDR values (e.g., 5.0, 10.0) for bright particles. The bloom bright-pass extracts everything above threshold, and the Gaussian blur spreads it everywhere.
**How to avoid:** Scale the bloom threshold and strength per era via EraVisualConfig. High-energy eras need higher bloom threshold (only the brightest particles glow) and lower bloom strength.

### Pitfall 5: Dark Ages Era Appearing Completely Black
**What goes wrong:** The Dark Ages era is supposed to be dim, but if particle alpha is set too low, the user sees nothing but a black screen for 12 seconds. This feels like a bug, not a feature.
**Why it happens:** Overcommitting to physical accuracy (the universe really is dark during this era) at the expense of user experience.
**How to avoid:** Keep faint density perturbations visible. Use very low but non-zero particle brightness. Add subtle noise-driven density fluctuations that hint at future structure. The educational overlay carries narrative weight during this era. Bloom should be disabled or minimal to avoid washing out the faint details.

### Pitfall 6: Saha Equation Numerical Instability at Extreme Temperatures
**What goes wrong:** At T >> 10,000 K, the Saha equation gives x very close to 1.0 (fully ionized). At T << 2,000 K, x is very close to 0.0. The exponential in the Saha equation overflows or underflows float64.
**Why it happens:** exp(-13.6 eV / (k_B * T)) spans from ~0 (low T) to ~1 (high T), with the exponential argument ranging from -158,000 (at T=1000 K) to near 0 (at T=100,000 K).
**How to avoid:** Clamp the ionization fraction to [0.0, 1.0] after computation. For T > 10,000 K, hardcode x = 1.0. For T < 1,500 K, hardcode x = 0.0. Only compute the Saha equation in the 1,500 K - 10,000 K range where it is physically meaningful.

## Code Examples

### Saha Equation Lookup Table Construction
```python
# Source: Wikipedia Saha ionization equation + cosmological application
import math
import numpy as np
from bigbangsim.simulation.constants import K_B, HBAR, M_ELECTRON

# Hydrogen ionization energy: 13.6 eV in Joules
E_ION = 13.6 * 1.602176634e-19  # J
H_PLANCK = 2 * math.pi * HBAR   # Planck constant
M_E_KG = M_ELECTRON * 1e6 * 1.602176634e-19 / (2.998e8)**2  # MeV/c^2 to kg

def build_ionization_table(cosmology_model, n_points=500):
    """Pre-compute ionization fraction x(T) for the recombination era.

    Returns arrays of (temperature, ionization_fraction) for interpolation.
    """
    # Temperature range: recombination window
    temps = np.logspace(np.log10(1500), np.log10(10000), n_points)
    x_values = np.zeros(n_points)

    for i, T in enumerate(temps):
        # Get baryon density at this temperature
        state = cosmology_model.get_state_at_cosmic_time(
            # Temperature -> cosmic time via T = T_CMB0 / a, a -> t
            ...  # Use cosmology model's inverse lookup
        )
        n_b = state['matter_density'] / 1.67e-27  # Convert to number density

        # Saha equation: x^2/(1-x) = A
        A = (1.0 / n_b) * (2 * math.pi * M_E_KG * K_B * T / H_PLANCK**2)**1.5 \
            * math.exp(-E_ION / (K_B * T))

        # Solve quadratic: x^2 + Ax - A = 0
        x = (-A + math.sqrt(A**2 + 4*A)) / 2.0
        x_values[i] = max(0.0, min(1.0, x))

    return temps, x_values
```

### Per-Era Fragment Shader Template (Example: Era 3 QGP)
```glsl
#version 430

#include "colormap.glsl"
#include "noise.glsl"

in vec4 v_color;
in float v_life;
out vec4 fragColor;

uniform float u_temperature;
uniform float u_era_progress;
uniform vec3 u_base_color;      // Deep orange-red
uniform vec3 u_accent_color;    // Yellow-white highlights
uniform float u_brightness;

void main() {
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    if (dist > 0.5) discard;

    // Soft glow falloff (soft for fluid-like appearance)
    float alpha = 1.0 - smoothstep(0.0, 0.5, dist);

    // Temperature-driven color: hotter = more accent (yellow-white)
    float temp_factor = clamp(u_temperature / 1e15, 0.0, 1.0);
    vec3 color = mix(u_base_color, u_accent_color, temp_factor * 0.5);

    // Noise-driven turbulence in color (fluid churning effect)
    float n = snoise(gl_PointCoord * 3.0 + u_era_progress * 2.0) * 0.5 + 0.5;
    color = mix(color, u_accent_color, n * 0.3);

    // HDR brightness for bloom
    color *= u_brightness * v_life;

    fragColor = vec4(color, alpha * v_life);
}
```

### EraVisualConfig Data Structure
```python
ERA_VISUAL_CONFIGS = [
    EraVisualConfig(
        era_index=0,  # Planck Epoch
        shader_key="era_00_planck",
        base_color=(1.0, 1.0, 1.0),      # White
        accent_color=(1.0, 0.95, 0.8),    # Pale gold
        particle_size=0.6,
        bloom_strength=0.6,
        expansion_rate=0.001,
        noise_strength=0.5,
        transition_seconds=2.0,
    ),
    # ... 10 more configs
]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single hot/cool shader binary | Per-era fragment shader programs | Phase 3 | Each era gets unique visual identity |
| Generic compute shader | Uniform-driven compute with per-era parameters | Phase 3 | Particle behavior varies by era |
| Instant era switching | FBO-based crossfade transitions | Phase 3 | Smooth visual continuity (RNDR-04) |
| Physics-agnostic rendering | Physics uniforms (Saha, BBN, PS) driving visuals | Phase 3 | Science drives aesthetics (core value) |

**Deprecated/outdated after Phase 3:**
- `particle_hot.frag` and `particle_cool.frag` replaced by 11 per-era fragment shaders
- Binary `set_era_shader()` (hot/cool) replaced by `set_era_shader(era_index)` mapping to specific program
- Hardcoded expansion_rate in compute shader replaced by uniform `u_expansion_rate`

## Project Constraints (from CLAUDE.md)

- **Tech Stack**: Python 3.10+, ModernGL, GLSL shaders -- all Phase 3 work uses these exclusively
- **Performance**: Must maintain 30+ FPS on GTX 1060 with 100K+ particles. Transition rendering (2x particle passes) must stay above 30 FPS for 200K particles during the ~2s crossfade window.
- **Scientific Accuracy**: All physics parameters from Planck 2018 / PDG. BBN yields, Saha equation, Jeans mass, Press-Schechter all use constants already in `constants.py`.
- **No new dependencies**: Phase 3 adds only Python modules and GLSL files.
- **Per-era shader architecture**: RNDR-06 (completed Phase 2) mandates separate programs per era, not a mega-shader. Phase 3 expands from 2 to 11 fragment programs.
- **Simulation-rendering boundary**: Simulation layer has zero imports from rendering (established Phase 1). New physics sub-modules (`nucleosynthesis.py`, `recombination.py`, `structure.py`) live in `simulation/physics/` and produce data consumed by rendering.
- **Mock-based testing**: All rendering tests use MagicMock for moderngl.Context (established Phase 2). Physics sub-module tests do not require GPU.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (latest) |
| Config file | None -- uses default pytest discovery |
| Quick run command | `python -m pytest tests/ -x -q` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RNDR-03 | 11 distinct era shader programs compile and render without error | unit (mock ctx) | `python -m pytest tests/test_era_shaders.py -x` | Wave 0 |
| RNDR-04 | Era transitions produce smooth blend factors (no discontinuities) | unit | `python -m pytest tests/test_era_transitions.py -x` | Wave 0 |
| PHYS-01 | All 11 eras present and play in correct sequence | unit | `python -m pytest tests/test_era_sequence.py -x` | Wave 0 |
| PHYS-02 (BBN) | Nucleosynthesis yields match PDG values | unit | `python -m pytest tests/test_nucleosynthesis.py -x` | Wave 0 |
| PHYS-02 (Saha) | Ionization fraction transitions from ~1 to ~0 around 3000 K | unit | `python -m pytest tests/test_recombination.py -x` | Wave 0 |
| PHYS-02 (Jeans) | Jeans mass decreases with cosmic time in matter-dominated era | unit | `python -m pytest tests/test_structure.py -x` | Wave 0 |
| PHYS-02 (PS) | Collapsed fraction increases with cosmic time | unit | `python -m pytest tests/test_structure.py -x` | Wave 0 |
| Full run | Full timeline playthrough without crashes or visual artifacts | manual | Run app, observe all 11 eras | Manual verification |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green + manual full-timeline playthrough before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_nucleosynthesis.py` -- covers PHYS-02 BBN yields
- [ ] `tests/test_recombination.py` -- covers PHYS-02 Saha equation
- [ ] `tests/test_structure.py` -- covers PHYS-02 Jeans + Press-Schechter
- [ ] `tests/test_era_shaders.py` -- covers RNDR-03 shader compilation (mock-based)
- [ ] `tests/test_era_transitions.py` -- covers RNDR-04 blend factor computation
- [ ] `tests/test_era_sequence.py` -- covers PHYS-01 all 11 eras in order
- [ ] `tests/test_era_visual_config.py` -- covers EraVisualConfig data integrity

## Open Questions

1. **Noise function in compute shader for 3D particle turbulence**
   - What we know: `noise.glsl` has 2D simplex noise. Compute shader needs 3D noise for particle velocity perturbation.
   - What's unclear: Whether to extend noise.glsl with 3D simplex or use a cheaper hash-based noise for compute.
   - Recommendation: Add 3D simplex noise to `noise.glsl` (well-known algorithm, same Ashima Arts source has a 3D variant). The cost per particle is trivial compared to the memory bandwidth of SSBO reads/writes.

2. **Point size variation per era**
   - What we know: Current vertex shader uses `u_point_scale / gl_Position.w` for perspective-correct sizing.
   - What's unclear: Whether per-era point scale should be a vertex shader uniform or a particle attribute (per-particle size variation).
   - Recommendation: Use per-era uniform for base size, with per-particle variation via the existing `life` attribute (particle.position.w). Larger points for bright stars in era 8, smaller for dim gas in era 7.

3. **Transition FBO performance during crossfade**
   - What we know: Rendering particles twice costs ~2x particle rendering time. At 200K particles, single render is well under budget.
   - What's unclear: Exact performance on GTX 1060 during transition with full bloom pipeline.
   - Recommendation: Profile during implementation. If needed, reduce particle count during transitions or skip one bloom pass on the transition FBO.

## Sources

### Primary (HIGH confidence)
- `bigbangsim/simulation/constants.py` -- Planck 2018 / PDG values already in codebase
- `bigbangsim/rendering/particles.py` -- Current ParticleSystem implementation
- `bigbangsim/shaders/` -- All existing shader files reviewed
- [Saha Ionization Equation (Wikipedia)](https://en.wikipedia.org/wiki/Saha_ionization_equation) -- mathematical formulation
- [Press-Schechter Formalism (Wikipedia)](https://en.wikipedia.org/wiki/Press%E2%80%93Schechter_formalism) -- analytical mass function
- [Jeans Instability (Wikipedia)](https://en.wikipedia.org/wiki/Jeans_instability) -- Jeans mass/length formulae
- [PDG 2024 BBN Review](https://pdg.lbl.gov/2024/reviews/rpp2024-rev-bbang-nucleosynthesis.pdf) -- nucleosynthesis yields
- [Planck 2018 Results (arXiv:1807.06209)](https://arxiv.org/abs/1807.06209) -- cosmological parameters

### Secondary (MEDIUM confidence)
- [LearnOpenGL - Blending](https://learnopengl.com/Advanced-OpenGL/Blending) -- FBO compositing techniques
- [GL Transitions](https://gl-transitions.com/) -- GLSL transition shader patterns
- [ModernGL Compute Shader Docs](https://moderngl.readthedocs.io/en/latest/reference/compute_shader.html) -- uniform API
- [CERN QGP Visualizations](https://home.cern/news/series/feature/ten-year-journey-through-quark-gluon-plasma-and-beyond) -- visual conventions for QGP
- [Caltech Recombination Lecture Notes](http://www.tapir.caltech.edu/~chirata/ph217/lec06.pdf) -- Saha in cosmological context
- [UMD Press-Schechter Lecture](https://pages.astro.umd.edu/~mcmiller/teaching/astr422/lecture24.pdf) -- analytical PS implementation

### Tertiary (LOW confidence)
- [Saha ionization for non-equilibrium states (arXiv:2505.08972)](https://arxiv.org/html/2505.08972v1) -- Peebles equation refinements (not needed for visualization fidelity)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new libraries needed; all work extends existing infrastructure
- Architecture: HIGH -- EraVisualConfig + FBO crossfade are well-established patterns; codebase already supports per-era shader switching
- Physics models: HIGH -- all models have analytical closed-form solutions using constants already in the codebase
- Per-era visual design: MEDIUM -- color palette and visual style choices are aesthetic judgments informed by scientific conventions but not empirically verified until visual testing
- Pitfalls: HIGH -- based on Phase 2 experience (uniform optimization bug c94d2c1) and established GPU rendering knowledge

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable -- no library updates expected to affect this phase)
