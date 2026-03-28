"""Tests for DampedOrbitCamera (CAMR-01).

Validates orbit camera behavior: initial state, velocity-based damping,
clamping, and matrix output types.
"""
import math

import glm
import pytest

from bigbangsim.rendering.camera import DampedOrbitCamera


class TestDampedOrbitCameraInit:
    """Initial state after construction."""

    def test_default_radius(self):
        cam = DampedOrbitCamera()
        assert cam.radius == 5.0

    def test_default_azimuth(self):
        cam = DampedOrbitCamera()
        assert cam.azimuth == 0.0

    def test_default_elevation(self):
        cam = DampedOrbitCamera()
        assert cam.elevation == -30.0

    def test_initial_position_correct(self):
        """Position derived from radius=5, azimuth=0, elevation=-30."""
        cam = DampedOrbitCamera()
        pos = cam.position
        # azimuth=0, elevation=-30 degrees:
        # x = 5 * cos(-30deg) * sin(0) = 0
        # y = 5 * sin(-30deg) = -2.5
        # z = 5 * cos(-30deg) * cos(0) = 5 * cos(30deg)
        assert abs(pos.x - 0.0) < 1e-5
        assert abs(pos.y - 5.0 * math.sin(math.radians(-30.0))) < 1e-5
        expected_z = 5.0 * math.cos(math.radians(-30.0)) * math.cos(0.0)
        assert abs(pos.z - expected_z) < 1e-5


class TestDampedOrbitCameraDrag:
    """Mouse drag sets velocity."""

    def test_on_mouse_drag_sets_nonzero_velocity(self):
        cam = DampedOrbitCamera()
        cam.on_mouse_drag(10.0, 5.0)
        assert cam._vel_azimuth != 0.0
        assert cam._vel_elevation != 0.0


class TestDampedOrbitCameraUpdate:
    """Update applies velocity and decays it."""

    def test_update_applies_velocity_and_decays(self):
        cam = DampedOrbitCamera()
        cam.on_mouse_drag(10.0, 0.0)
        initial_az = cam.azimuth
        vel_before = cam._vel_azimuth
        cam.update(1.0)
        # Azimuth should have changed
        assert cam.azimuth != initial_az
        # Velocity should have decayed toward zero
        assert abs(cam._vel_azimuth) < abs(vel_before)


class TestDampedOrbitCameraClamp:
    """Elevation and radius clamping."""

    def test_elevation_clamped_below_89(self):
        cam = DampedOrbitCamera()
        cam._vel_elevation = 1e6  # Extreme positive
        cam.update(1.0)
        assert cam.elevation <= 89.0

    def test_elevation_clamped_above_minus_89(self):
        cam = DampedOrbitCamera()
        cam._vel_elevation = -1e6  # Extreme negative
        cam.update(1.0)
        assert cam.elevation >= -89.0

    def test_radius_never_below_minimum(self):
        cam = DampedOrbitCamera()
        cam._vel_zoom = 1e6  # Extreme zoom out... or in
        cam.update(1.0)
        assert cam.radius >= 0.01


class TestDampedOrbitCameraMatrices:
    """Matrix property return types."""

    def test_view_matrix_returns_mat4(self):
        cam = DampedOrbitCamera()
        assert isinstance(cam.view_matrix, glm.mat4)

    def test_projection_matrix_returns_mat4(self):
        cam = DampedOrbitCamera()
        assert isinstance(cam.projection_matrix, glm.mat4)
