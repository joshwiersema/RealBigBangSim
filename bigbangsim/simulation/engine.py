"""Fixed-timestep simulation engine with accumulator pattern.

Implements the "Fix Your Timestep!" pattern to decouple physics updates from
render rate. Physics state is computed at fixed intervals (PHYSICS_DT) and
interpolated for smooth rendering between steps.

The engine produces PhysicsState snapshots from wall-clock screen time input
by combining the timeline controller (screen-to-cosmic mapping), the cosmology
model (Friedmann equation parameters), and the era system.
"""
from copy import copy

from bigbangsim.config import PHYSICS_DT, DEFAULT_SPEED, MIN_SPEED, MAX_SPEED
from bigbangsim.simulation.state import PhysicsState
from bigbangsim.simulation.timeline import TimelineController
from bigbangsim.simulation.cosmology import CosmologyModel
from bigbangsim.simulation.eras import ERAS


class SimulationEngine:
    """Fixed-timestep physics simulation engine.

    Uses an accumulator pattern to process frametime in fixed-size physics
    steps. Provides pause/resume and speed control. Returns interpolated
    PhysicsState for smooth rendering.

    Attributes:
        timeline: The piecewise logarithmic timeline controller.
        cosmology: The Friedmann equation cosmology model.
        accumulator: Unprocessed time remaining from frametimes.
        screen_time: Current wall-clock playback position in seconds.
        speed_multiplier: Playback speed factor (1.0 = normal).
        paused: Whether the simulation is paused.
        state: Current physics state at the latest fixed timestep.
        prev_state: Physics state at the previous fixed timestep.
    """

    def __init__(self) -> None:
        """Initialize the simulation engine."""
        self.timeline = TimelineController(ERAS)
        self.cosmology = CosmologyModel()
        self.accumulator: float = 0.0
        self.screen_time: float = 0.0
        self.speed_multiplier: float = DEFAULT_SPEED
        self.paused: bool = False
        self.state: PhysicsState = self._compute_state(0.0)
        self.prev_state: PhysicsState = copy(self.state)

    def _compute_state(self, screen_time: float) -> PhysicsState:
        """Compute full physics state from screen time.

        Maps screen time through the timeline controller to cosmic time,
        then looks up cosmological parameters from the pre-computed model.

        Args:
            screen_time: Wall-clock playback position in seconds.

        Returns:
            Complete PhysicsState snapshot.
        """
        cosmic_time = self.timeline.screen_to_cosmic(screen_time)
        era_idx, era_progress = self.timeline.get_current_era(cosmic_time)
        params = self.cosmology.get_state_at_cosmic_time(cosmic_time)
        return PhysicsState(
            cosmic_time=cosmic_time,
            scale_factor=params["scale_factor"],
            temperature=params["temperature"],
            matter_density=params["matter_density"],
            radiation_density=params["radiation_density"],
            hubble_param=params["hubble_param"],
            current_era=era_idx,
            era_progress=era_progress,
        )

    def update(self, frametime: float) -> tuple[PhysicsState, float]:
        """Advance simulation by the given frametime.

        Uses the fixed-timestep accumulator pattern: frametime is accumulated
        and consumed in fixed PHYSICS_DT steps. Returns an interpolated state
        for smooth rendering between physics steps.

        Args:
            frametime: Real-time elapsed since last update call, in seconds.

        Returns:
            Tuple of (interpolated_state, alpha) where alpha is the
            interpolation factor (0.0 = prev_state, 1.0 = state).
        """
        if self.paused:
            return self.state, 0.0

        self.accumulator += frametime * self.speed_multiplier

        while self.accumulator >= PHYSICS_DT:
            self.prev_state = copy(self.state)
            self.screen_time += PHYSICS_DT
            self.screen_time = min(self.screen_time, self.timeline.total_duration())
            self.state = self._compute_state(self.screen_time)
            self.accumulator -= PHYSICS_DT

        alpha = self.accumulator / PHYSICS_DT
        return self.prev_state.lerp(self.state, alpha), alpha

    def toggle_pause(self) -> None:
        """Toggle the paused state."""
        self.paused = not self.paused

    def set_speed(self, multiplier: float) -> None:
        """Set the playback speed multiplier, clamped to valid range.

        Args:
            multiplier: Speed factor (1.0 = normal, 2.0 = double speed).
        """
        self.speed_multiplier = max(MIN_SPEED, min(MAX_SPEED, multiplier))

    def increase_speed(self) -> None:
        """Double the current playback speed."""
        self.set_speed(self.speed_multiplier * 2.0)

    def decrease_speed(self) -> None:
        """Halve the current playback speed."""
        self.set_speed(self.speed_multiplier / 2.0)
