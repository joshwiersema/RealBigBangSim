"""Damped orbit camera for smooth 3D navigation (CAMR-01).

Implements an orbit camera with exponential velocity damping. The user applies
impulse velocities via mouse events (drag, scroll), and the camera smoothly
decelerates each frame.

Double-precision position accessors (position_dvec3, target_dvec3) are provided
for the camera-relative rendering pipeline (PHYS-07).
"""
import math

import glm


class DampedOrbitCamera:
    """Orbit camera with exponential velocity damping for smooth feel."""

    def __init__(
        self,
        target: glm.vec3 = None,
        radius: float = 5.0,
        fov: float = 60.0,
        near: float = 0.01,
        far: float = 1000.0,
        aspect: float = 16 / 9,
    ) -> None:
        self.target = glm.vec3(target) if target is not None else glm.vec3(0)
        self.radius = radius
        self.fov = fov
        self.near = near
        self.far = far
        self.aspect = aspect

        self.azimuth: float = 0.0       # Horizontal angle (degrees)
        self.elevation: float = -30.0   # Vertical angle (degrees)

        # Velocity state for damping
        self._vel_azimuth: float = 0.0
        self._vel_elevation: float = 0.0
        self._vel_zoom: float = 0.0
        self._vel_pan_x: float = 0.0
        self._vel_pan_y: float = 0.0
        self.damping: float = 0.05  # Exponential decay factor (lower = more damping)

    def update(self, dt: float) -> None:
        """Apply damped velocities. Call once per frame."""
        decay = self.damping ** dt

        self.azimuth += self._vel_azimuth * dt
        self.elevation += self._vel_elevation * dt
        self.elevation = max(-89.0, min(89.0, self.elevation))  # Clamp to avoid gimbal lock

        self.radius *= (1.0 + self._vel_zoom * dt)
        self.radius = max(0.01, self.radius)

        # Pan: move target in camera-local right/up directions
        right = self._get_right()
        up = glm.vec3(0, 1, 0)
        self.target += right * self._vel_pan_x * dt * self.radius * 0.001
        self.target += up * self._vel_pan_y * dt * self.radius * 0.001

        # Decay all velocities
        self._vel_azimuth *= decay
        self._vel_elevation *= decay
        self._vel_zoom *= decay
        self._vel_pan_x *= decay
        self._vel_pan_y *= decay

    def on_mouse_drag(self, dx: float, dy: float, sensitivity: float = 0.3) -> None:
        """Left-click drag: orbit."""
        self._vel_azimuth = dx * sensitivity * 60.0
        self._vel_elevation = -dy * sensitivity * 60.0

    def on_mouse_pan(self, dx: float, dy: float, sensitivity: float = 1.0) -> None:
        """Middle-click drag: pan."""
        self._vel_pan_x = -dx * sensitivity * 60.0
        self._vel_pan_y = dy * sensitivity * 60.0

    def on_scroll(self, y_offset: float, sensitivity: float = 0.1) -> None:
        """Scroll wheel: zoom."""
        self._vel_zoom = -y_offset * sensitivity

    def _get_right(self) -> glm.vec3:
        az = math.radians(self.azimuth)
        return glm.vec3(math.cos(az), 0, -math.sin(az))

    @property
    def position(self) -> glm.vec3:
        """Camera position in world space (float32)."""
        az = math.radians(self.azimuth)
        el = math.radians(self.elevation)
        return self.target + glm.vec3(
            self.radius * math.cos(el) * math.sin(az),
            self.radius * math.sin(el),
            self.radius * math.cos(el) * math.cos(az),
        )

    @property
    def position_dvec3(self) -> glm.dvec3:
        """Camera position in double precision for camera-relative rendering."""
        p = self.position
        return glm.dvec3(p.x, p.y, p.z)

    @property
    def target_dvec3(self) -> glm.dvec3:
        """Camera target in double precision for camera-relative rendering."""
        t = self.target
        return glm.dvec3(t.x, t.y, t.z)

    @property
    def view_matrix(self) -> glm.mat4:
        """Standard float32 view matrix (for non-critical rendering)."""
        return glm.lookAt(self.position, self.target, glm.vec3(0, 1, 0))

    @property
    def projection_matrix(self) -> glm.mat4:
        """Perspective projection matrix."""
        return glm.perspective(glm.radians(self.fov), self.aspect, self.near, self.far)
