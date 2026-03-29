"""Data-driven visual configuration for all 11 cosmological eras.

Each era has a unique EraVisualConfig that drives shader selection,
color palettes, particle behavior, and post-processing parameters.
This module lives in the simulation layer (data only) and has zero
rendering imports.

The ERA_VISUAL_CONFIGS list is indexed 0-10 to match the ERAS list
in bigbangsim.simulation.eras. Plan 02's shaders consume these
configs as uniforms, and Plan 03 wires them into the render loop.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class EraVisualConfig:
    """Visual configuration for one cosmological era.

    Drives per-era shader selection and uniform values.
    Lives in simulation layer (data only, no rendering imports).

    Attributes:
        era_index: Sequential era index (0-10), matches eras.ERAS list.
        shader_key: Key into ParticleSystem.programs dict for era-specific shader.
        base_color: Primary color (R, G, B) in [0, 1] range.
        accent_color: Secondary/highlight color (R, G, B) in [0, 1] range.
        particle_size: Point scale multiplier (1.0 = default 50.0).
        bloom_strength: Post-processing bloom intensity (0.0-1.0).
        bloom_threshold: Bright-pass threshold (higher = less bloom).
        expansion_rate: Compute shader expansion modifier.
        noise_strength: Turbulence/noise contribution.
        gravity_strength: Gravitational clustering force.
        damping: Velocity damping factor.
        brightness: Fragment shader brightness multiplier.
        transition_seconds: Duration of crossfade into this era.
    """
    era_index: int
    shader_key: str
    base_color: tuple[float, float, float]
    accent_color: tuple[float, float, float]
    particle_size: float
    bloom_strength: float
    bloom_threshold: float
    expansion_rate: float
    noise_strength: float
    gravity_strength: float
    damping: float
    brightness: float
    transition_seconds: float
    containment_radius: float = 50.0
    exposure: float = 1.0


ERA_VISUAL_CONFIGS: list[EraVisualConfig] = [
    # Era 0: Planck Epoch
    # All forces unified; quantum gravity dominates. Pure white-hot energy.
    # Compact singularity with intense bloom. Center is bright white,
    # edges show subtle warm tones through ACES highlight compression.
    EraVisualConfig(
        era_index=0,
        shader_key="era_00_planck",
        base_color=(1.0, 1.0, 1.0),
        accent_color=(1.0, 0.95, 0.8),
        particle_size=0.8,
        bloom_strength=0.5,
        bloom_threshold=1.2,
        expansion_rate=0.001,
        noise_strength=0.5,
        gravity_strength=0.0,
        damping=0.02,
        brightness=2.5,
        transition_seconds=2.0,
        containment_radius=10.0,
        exposure=0.1,
    ),
    # Era 1: Grand Unification
    # Gravity separates; high-energy golden glow with violet symmetry breaking.
    EraVisualConfig(
        era_index=1,
        shader_key="era_01_gut",
        base_color=(1.0, 0.95, 0.7),
        accent_color=(0.7, 0.5, 0.9),
        particle_size=0.8,
        bloom_strength=0.35,
        bloom_threshold=1.2,
        expansion_rate=0.005,
        noise_strength=0.35,
        gravity_strength=0.0,
        damping=0.02,
        brightness=2.2,
        transition_seconds=2.0,
        containment_radius=12.0,
        exposure=0.12,
    ),
    # Era 2: Inflation
    # Exponential expansion; bright yellow-white stretching outward dramatically.
    # Particles rapidly expand outward — the universe inflates.
    EraVisualConfig(
        era_index=2,
        shader_key="era_02_inflation",
        base_color=(1.0, 0.95, 0.6),
        accent_color=(1.0, 1.0, 0.9),
        particle_size=0.7,
        bloom_strength=0.3,
        bloom_threshold=1.0,
        expansion_rate=0.8,
        noise_strength=0.1,
        gravity_strength=0.0,
        damping=0.003,
        brightness=2.0,
        transition_seconds=1.5,
        containment_radius=30.0,
        exposure=0.18,
    ),
    # Era 3: Quark-Gluon Plasma
    # Superhot plasma; deep orange-red with golden highlights, turbulent.
    EraVisualConfig(
        era_index=3,
        shader_key="era_03_qgp",
        base_color=(1.0, 0.3, 0.05),
        accent_color=(1.0, 0.9, 0.5),
        particle_size=1.0,
        bloom_strength=0.3,
        bloom_threshold=1.0,
        expansion_rate=0.02,
        noise_strength=0.5,
        gravity_strength=0.0,
        damping=0.015,
        brightness=1.8,
        transition_seconds=2.0,
        containment_radius=25.0,
        exposure=0.25,
    ),
    # Era 4: Hadron Epoch
    # Quarks combine into nucleons; warm orange with amber highlights.
    EraVisualConfig(
        era_index=4,
        shader_key="era_04_hadron",
        base_color=(0.95, 0.5, 0.15),
        accent_color=(1.0, 0.8, 0.4),
        particle_size=1.0,
        bloom_strength=0.25,
        bloom_threshold=1.0,
        expansion_rate=0.015,
        noise_strength=0.3,
        gravity_strength=0.0,
        damping=0.02,
        brightness=1.5,
        transition_seconds=2.0,
        containment_radius=30.0,
        exposure=0.35,
    ),
    # Era 5: Nucleosynthesis
    # Light elements form; green-gold nuclear glow.
    EraVisualConfig(
        era_index=5,
        shader_key="era_05_nucleosynthesis",
        base_color=(0.4, 0.8, 0.3),
        accent_color=(1.0, 0.9, 0.4),
        particle_size=1.0,
        bloom_strength=0.25,
        bloom_threshold=1.0,
        expansion_rate=0.01,
        noise_strength=0.25,
        gravity_strength=0.0,
        damping=0.02,
        brightness=1.3,
        transition_seconds=2.0,
        containment_radius=35.0,
        exposure=0.5,
    ),
    # Era 6: Recombination / CMB
    # Electrons bind to nuclei; warm orange fading to deep violet.
    # The "last light" before the cosmic dark ages.
    EraVisualConfig(
        era_index=6,
        shader_key="era_06_recombination",
        base_color=(1.0, 0.7, 0.3),
        accent_color=(0.15, 0.05, 0.2),
        particle_size=1.0,
        bloom_strength=0.2,
        bloom_threshold=1.0,
        expansion_rate=0.008,
        noise_strength=0.1,
        gravity_strength=0.0,
        damping=0.025,
        brightness=1.0,
        transition_seconds=3.0,
        containment_radius=40.0,
        exposure=0.7,
    ),
    # Era 7: Dark Ages
    # No stars; deep dark blue-black void. Dramatic contrast after CMB.
    # Almost invisible — the universe goes dark. Higher exposure to keep
    # the faintest particles barely perceptible.
    EraVisualConfig(
        era_index=7,
        shader_key="era_07_dark_ages",
        base_color=(0.03, 0.03, 0.1),
        accent_color=(0.06, 0.06, 0.15),
        particle_size=0.6,
        bloom_strength=0.05,
        bloom_threshold=2.0,
        expansion_rate=0.005,
        noise_strength=0.03,
        gravity_strength=0.002,
        damping=0.03,
        brightness=0.12,
        transition_seconds=3.0,
        containment_radius=50.0,
        exposure=3.0,
    ),
    # Era 8: First Stars / Reionization
    # First massive stars ignite; dark backdrop with brilliant blue-white points.
    # Maximum drama: the universe lights up again after total darkness.
    EraVisualConfig(
        era_index=8,
        shader_key="era_08_first_stars",
        base_color=(0.03, 0.05, 0.15),
        accent_color=(0.8, 0.9, 1.0),
        particle_size=1.4,
        bloom_strength=0.45,
        bloom_threshold=0.8,
        expansion_rate=0.004,
        noise_strength=0.05,
        gravity_strength=0.008,
        damping=0.02,
        brightness=1.0,
        transition_seconds=2.5,
        containment_radius=55.0,
        exposure=1.5,
    ),
    # Era 9: Galaxy Formation
    # Gravity assembles galaxies; deep violet nebulae with blue-white clusters.
    EraVisualConfig(
        era_index=9,
        shader_key="era_09_galaxy_formation",
        base_color=(0.15, 0.05, 0.3),
        accent_color=(0.5, 0.6, 1.0),
        particle_size=1.2,
        bloom_strength=0.35,
        bloom_threshold=0.8,
        expansion_rate=0.003,
        noise_strength=0.04,
        gravity_strength=0.025,
        damping=0.012,
        brightness=0.9,
        transition_seconds=2.0,
        containment_radius=65.0,
        exposure=1.5,
    ),
    # Era 10: Large-Scale Structure
    # Cosmic web matures; dark indigo with warm golden filaments.
    EraVisualConfig(
        era_index=10,
        shader_key="era_10_lss",
        base_color=(0.08, 0.05, 0.2),
        accent_color=(0.9, 0.75, 0.5),
        particle_size=1.1,
        bloom_strength=0.3,
        bloom_threshold=0.9,
        expansion_rate=0.002,
        noise_strength=0.02,
        gravity_strength=0.02,
        damping=0.012,
        brightness=0.8,
        transition_seconds=2.0,
        containment_radius=80.0,
        exposure=1.5,
    ),
]


def get_era_visual_config(era_index: int) -> EraVisualConfig:
    """Return the visual config for the given era index (0-10).

    Args:
        era_index: Era index matching bigbangsim.simulation.eras.ERAS list.

    Returns:
        EraVisualConfig for the specified era.

    Raises:
        IndexError: If era_index is out of range.
    """
    return ERA_VISUAL_CONFIGS[era_index]
