"""Cinematic auto-camera controller with Catmull-Rom spline interpolation (CAMR-02, CAMR-03).

Guides the viewer through all 11 cosmological eras via per-era keyframes.
Users can toggle between auto-camera and free orbit mode; resuming auto mode
smoothly blends back to the scripted path using smoothstep interpolation.

The controller drives the DampedOrbitCamera's azimuth, elevation, radius,
target, and fov properties -- it never bypasses the camera's interface.
Velocity fields are zeroed in auto mode to prevent damping interference.
"""
from __future__ import annotations

from dataclasses import dataclass

import glm

from bigbangsim.rendering.camera import DampedOrbitCamera


# ---------------------------------------------------------------------------
# Catmull-Rom spline (pure scalar)
# ---------------------------------------------------------------------------

def catmull_rom(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
    """Catmull-Rom spline interpolation between p1 and p2.

    Standard Catmull-Rom: C1-continuous interpolation that passes through
    the control points. At t=0 the result is p1, at t=1 the result is p2.

    Args:
        p0: Control point before p1 (influences curvature).
        p1: Start control point.
        p2: End control point.
        p3: Control point after p2 (influences curvature).
        t: Parameter in [0, 1].

    Returns:
        Interpolated scalar value.
    """
    t2 = t * t
    t3 = t2 * t
    return 0.5 * (
        (2.0 * p1)
        + (-p0 + p2) * t
        + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2
        + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3
    )


# ---------------------------------------------------------------------------
# Camera keyframe
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CameraKeyframe:
    """Camera state at a specific point in the cinematic path.

    Uses scalar fields (not glm.vec3) for easy serialization and testing.

    Attributes:
        azimuth: Horizontal angle in degrees.
        elevation: Vertical angle in degrees.
        radius: Distance from the target point.
        target_x: Look-at X coordinate.
        target_y: Look-at Y coordinate.
        target_z: Look-at Z coordinate.
        fov: Field of view in degrees.
    """
    azimuth: float
    elevation: float
    radius: float
    target_x: float
    target_y: float
    target_z: float
    fov: float


# ---------------------------------------------------------------------------
# Per-era keyframes
# ---------------------------------------------------------------------------

ERA_KEYFRAMES: dict[int, list[CameraKeyframe]] = {
    # Era 0 - Planck Epoch: Close-in, wide FOV, looking slightly down
    0: [CameraKeyframe(azimuth=0.0, elevation=-15.0, radius=6.0,
                        target_x=0.0, target_y=0.0, target_z=0.0, fov=70.0)],
    # Era 1 - Grand Unification: Slight orbit
    1: [CameraKeyframe(azimuth=30.0, elevation=-20.0, radius=7.0,
                        target_x=0.0, target_y=0.0, target_z=0.0, fov=65.0)],
    # Era 2 - Inflation: Pull back dramatically
    2: [CameraKeyframe(azimuth=60.0, elevation=-10.0, radius=12.0,
                        target_x=0.0, target_y=0.0, target_z=0.0, fov=75.0)],
    # Era 3 - Quark-Gluon Plasma: Orbit around
    3: [CameraKeyframe(azimuth=100.0, elevation=-15.0, radius=10.0,
                        target_x=0.0, target_y=0.0, target_z=0.0, fov=65.0)],
    # Era 4 - Hadron Epoch: Continue orbit
    4: [CameraKeyframe(azimuth=140.0, elevation=-25.0, radius=9.0,
                        target_x=0.0, target_y=0.0, target_z=0.0, fov=60.0)],
    # Era 5 - Nucleosynthesis: Steady observation
    5: [CameraKeyframe(azimuth=170.0, elevation=-20.0, radius=10.0,
                        target_x=0.0, target_y=0.0, target_z=0.0, fov=60.0)],
    # Era 6 - Recombination/CMB: Pull back for CMB release
    6: [CameraKeyframe(azimuth=200.0, elevation=-10.0, radius=14.0,
                        target_x=0.0, target_y=0.0, target_z=0.0, fov=65.0)],
    # Era 7 - Dark Ages: Far out, narrow FOV
    7: [CameraKeyframe(azimuth=230.0, elevation=-5.0, radius=20.0,
                        target_x=0.0, target_y=0.0, target_z=0.0, fov=55.0)],
    # Era 8 - First Stars / Reionization: Zoom back in
    8: [CameraKeyframe(azimuth=260.0, elevation=-25.0, radius=15.0,
                        target_x=0.0, target_y=0.0, target_z=0.0, fov=60.0)],
    # Era 9 - Galaxy Formation: Wide pan
    9: [CameraKeyframe(azimuth=300.0, elevation=-20.0, radius=18.0,
                        target_x=0.0, target_y=0.0, target_z=0.0, fov=55.0)],
    # Era 10 - Large-Scale Structure: Panoramic finale
    10: [CameraKeyframe(azimuth=350.0, elevation=-30.0, radius=25.0,
                         target_x=0.0, target_y=0.0, target_z=0.0, fov=50.0)],
}


# ---------------------------------------------------------------------------
# Cinematic camera controller
# ---------------------------------------------------------------------------

def _smoothstep(t: float) -> float:
    """Hermite smoothstep: 3t^2 - 2t^3 for t in [0, 1]."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b."""
    return a + (b - a) * t


class CinematicCameraController:
    """Drives a DampedOrbitCamera through per-era cinematic keyframes.

    Uses Catmull-Rom spline interpolation across era keyframes for smooth,
    C1-continuous camera motion. Supports toggling between auto mode
    (scripted path) and free orbit mode, with smooth blend-back on resume.

    Args:
        camera: The DampedOrbitCamera to drive.
        keyframes: Per-era keyframe dict. Defaults to ERA_KEYFRAMES.
        blend_back_duration: Seconds to blend back when resuming auto mode.
    """

    def __init__(
        self,
        camera: DampedOrbitCamera,
        keyframes: dict[int, list[CameraKeyframe]] | None = None,
        blend_back_duration: float = 1.5,
    ) -> None:
        self.camera = camera
        self.keyframes = keyframes if keyframes is not None else ERA_KEYFRAMES
        self.blend_back_duration = blend_back_duration

        self.auto_mode: bool = True
        self.blend_back_timer: float = 0.0

        # Saved free-orbit state for blend-back source
        self._saved_azimuth: float = 0.0
        self._saved_elevation: float = 0.0
        self._saved_radius: float = 5.0
        self._saved_fov: float = 60.0
        self._saved_target_x: float = 0.0
        self._saved_target_y: float = 0.0
        self._saved_target_z: float = 0.0

    @property
    def is_auto(self) -> bool:
        """Whether the controller is in auto (scripted) mode."""
        return self.auto_mode

    def _get_era_keyframe(self, era_index: int) -> CameraKeyframe:
        """Get the primary keyframe for an era, clamping at boundaries."""
        idx = max(0, min(era_index, max(self.keyframes.keys())))
        kfs = self.keyframes.get(idx)
        if kfs and len(kfs) > 0:
            return kfs[0]
        # Fallback: return a sensible default
        return CameraKeyframe(
            azimuth=0.0, elevation=-15.0, radius=10.0,
            target_x=0.0, target_y=0.0, target_z=0.0, fov=60.0,
        )

    def evaluate_path(self, era_index: int, era_progress: float) -> CameraKeyframe:
        """Evaluate the camera position at the given era and progress.

        Uses Catmull-Rom spline interpolation across four adjacent eras'
        keyframes for smooth, C1-continuous motion.

        Args:
            era_index: Current era index (0-10).
            era_progress: Progress within the current era [0, 1].

        Returns:
            Interpolated CameraKeyframe for the current position.
        """
        # Get keyframes for four adjacent eras (clamp at boundaries)
        kf0 = self._get_era_keyframe(era_index - 1)
        kf1 = self._get_era_keyframe(era_index)
        kf2 = self._get_era_keyframe(era_index + 1)
        kf3 = self._get_era_keyframe(era_index + 2)

        t = max(0.0, min(1.0, era_progress))

        return CameraKeyframe(
            azimuth=catmull_rom(kf0.azimuth, kf1.azimuth, kf2.azimuth, kf3.azimuth, t),
            elevation=catmull_rom(kf0.elevation, kf1.elevation, kf2.elevation, kf3.elevation, t),
            radius=catmull_rom(kf0.radius, kf1.radius, kf2.radius, kf3.radius, t),
            target_x=catmull_rom(kf0.target_x, kf1.target_x, kf2.target_x, kf3.target_x, t),
            target_y=catmull_rom(kf0.target_y, kf1.target_y, kf2.target_y, kf3.target_y, t),
            target_z=catmull_rom(kf0.target_z, kf1.target_z, kf2.target_z, kf3.target_z, t),
            fov=catmull_rom(kf0.fov, kf1.fov, kf2.fov, kf3.fov, t),
        )

    def _apply_keyframe(self, kf: CameraKeyframe) -> None:
        """Apply a keyframe to the camera, zeroing velocity fields."""
        self.camera.azimuth = kf.azimuth
        self.camera.elevation = kf.elevation
        self.camera.radius = kf.radius
        self.camera.fov = kf.fov
        self.camera.target = glm.vec3(kf.target_x, kf.target_y, kf.target_z)

        # Zero velocity fields to prevent damping from fighting the scripted position
        self.camera._vel_azimuth = 0.0
        self.camera._vel_elevation = 0.0
        self.camera._vel_zoom = 0.0

    def _apply_blended(self, kf: CameraKeyframe, alpha: float) -> None:
        """Apply a blended state between saved free-orbit and scripted keyframe.

        Args:
            kf: Target scripted keyframe.
            alpha: Blend factor (0 = saved free state, 1 = scripted keyframe).
        """
        self.camera.azimuth = _lerp(self._saved_azimuth, kf.azimuth, alpha)
        self.camera.elevation = _lerp(self._saved_elevation, kf.elevation, alpha)
        self.camera.radius = _lerp(self._saved_radius, kf.radius, alpha)
        self.camera.fov = _lerp(self._saved_fov, kf.fov, alpha)
        self.camera.target = glm.vec3(
            _lerp(self._saved_target_x, kf.target_x, alpha),
            _lerp(self._saved_target_y, kf.target_y, alpha),
            _lerp(self._saved_target_z, kf.target_z, alpha),
        )

        # Zero velocity fields during blend-back too
        self.camera._vel_azimuth = 0.0
        self.camera._vel_elevation = 0.0
        self.camera._vel_zoom = 0.0

    def update(self, dt: float, era_index: int, era_progress: float) -> None:
        """Update the camera based on current mode and era position.

        In auto mode: evaluates the scripted path and applies it to the camera.
        During blend-back: smoothstep-interpolates between saved free state and
        scripted position. In free mode: does nothing (camera under user control).

        Args:
            dt: Frame delta time in seconds.
            era_index: Current era index (0-10).
            era_progress: Progress within the current era [0, 1].
        """
        if not self.auto_mode:
            return

        kf = self.evaluate_path(era_index, era_progress)

        if self.blend_back_timer > 0.0:
            # Smoothstep blend from saved free-orbit state to scripted position
            raw_alpha = 1.0 - (self.blend_back_timer / self.blend_back_duration)
            alpha = _smoothstep(raw_alpha)
            self._apply_blended(kf, alpha)
            self.blend_back_timer = max(0.0, self.blend_back_timer - dt)
        else:
            self._apply_keyframe(kf)

    def toggle_mode(self) -> None:
        """Toggle between auto-camera and free orbit mode.

        When switching TO free mode: saves current camera state.
        When switching TO auto mode: saves current free-orbit state as
        blend-back source and starts the blend-back timer.
        """
        if self.auto_mode:
            # Switching TO free mode -- save current camera state
            self._save_camera_state()
            self.auto_mode = False
        else:
            # Switching TO auto mode -- save free-orbit state for blend-back
            self._save_camera_state()
            self.blend_back_timer = self.blend_back_duration
            self.auto_mode = True

    def _save_camera_state(self) -> None:
        """Snapshot the current camera state for blend-back."""
        self._saved_azimuth = self.camera.azimuth
        self._saved_elevation = self.camera.elevation
        self._saved_radius = self.camera.radius
        self._saved_fov = self.camera.fov
        self._saved_target_x = self.camera.target.x
        self._saved_target_y = self.camera.target.y
        self._saved_target_z = self.camera.target.z
