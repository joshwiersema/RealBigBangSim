"""Physics state interface between simulation and rendering layers.

This dataclass carries all physics parameters computed by the simulation engine.
The rendering layer reads from PhysicsState but never writes to it.
The simulation layer has ZERO imports from rendering.
"""
from dataclasses import dataclass


@dataclass
class PhysicsState:
    """Snapshot of cosmological state at a point in cosmic time.

    Used as the interface between the simulation layer (pure physics) and
    the rendering layer (GPU). Communication is one-way: simulation produces
    PhysicsState, rendering consumes it.

    All continuous fields support linear interpolation via lerp() for smooth
    rendering between fixed-timestep physics updates (PHYS-06).
    """
    cosmic_time: float        # Seconds after Big Bang
    scale_factor: float       # a(t), dimensionless (1.0 = today)
    temperature: float        # Kelvin
    matter_density: float     # kg/m^3
    radiation_density: float  # kg/m^3
    hubble_param: float       # km/s/Mpc
    current_era: int          # Era index (0-10)
    era_progress: float       # 0.0-1.0 within current era

    def lerp(self, other: 'PhysicsState', alpha: float) -> 'PhysicsState':
        """Linear interpolation for smooth rendering between physics steps.

        Args:
            other: The next physics state.
            alpha: Interpolation factor (0.0 = self, 1.0 = other).

        Returns:
            Interpolated PhysicsState. Discrete fields (current_era) use self's value.
        """
        def _mix(a: float, b: float) -> float:
            return a + (b - a) * alpha

        return PhysicsState(
            cosmic_time=_mix(self.cosmic_time, other.cosmic_time),
            scale_factor=_mix(self.scale_factor, other.scale_factor),
            temperature=_mix(self.temperature, other.temperature),
            matter_density=_mix(self.matter_density, other.matter_density),
            radiation_density=_mix(self.radiation_density, other.radiation_density),
            hubble_param=_mix(self.hubble_param, other.hubble_param),
            current_era=self.current_era,  # Discrete: don't interpolate
            era_progress=_mix(self.era_progress, other.era_progress),
        )
