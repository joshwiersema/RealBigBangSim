"""Tests for CinematicCameraController, Catmull-Rom splines, and mode toggle.

Covers requirements CAMR-02 (auto-camera traverses all 11 eras) and
CAMR-03 (toggle between auto and free orbit with smooth handoff).
"""
import math

import pytest

from bigbangsim.presentation.camera_controller import (
    CameraKeyframe,
    CinematicCameraController,
    ERA_KEYFRAMES,
    catmull_rom,
)
from bigbangsim.rendering.camera import DampedOrbitCamera


# ---------------------------------------------------------------------------
# Catmull-Rom spline tests
# ---------------------------------------------------------------------------

class TestCatmullRom:
    """Pure math tests for the Catmull-Rom interpolation function."""

    def test_t0_returns_p1(self):
        """catmull_rom at t=0.0 must return p1 exactly."""
        result = catmull_rom(0.0, 1.0, 2.0, 3.0, 0.0)
        assert result == pytest.approx(1.0)

    def test_t1_returns_p2(self):
        """catmull_rom at t=1.0 must return p2 exactly."""
        result = catmull_rom(0.0, 1.0, 2.0, 3.0, 1.0)
        assert result == pytest.approx(2.0)

    def test_t05_between_p1_and_p2(self):
        """catmull_rom at t=0.5 returns a point between p1 and p2."""
        result = catmull_rom(0.0, 1.0, 2.0, 3.0, 0.5)
        assert 1.0 < result < 2.0

    def test_uniform_spacing_midpoint(self):
        """For uniformly spaced points, t=0.5 should give the midpoint."""
        result = catmull_rom(0.0, 1.0, 2.0, 3.0, 0.5)
        assert result == pytest.approx(1.5)

    def test_non_uniform_points(self):
        """catmull_rom works with non-uniformly spaced control points."""
        result = catmull_rom(0.0, 5.0, 20.0, 100.0, 0.5)
        # Should be between p1=5 and p2=20
        assert 5.0 < result < 20.0

    def test_identical_points(self):
        """If all points are identical, result is that value for any t."""
        for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
            assert catmull_rom(7.0, 7.0, 7.0, 7.0, t) == pytest.approx(7.0)


# ---------------------------------------------------------------------------
# CameraKeyframe tests
# ---------------------------------------------------------------------------

class TestCameraKeyframe:
    """Tests for the CameraKeyframe data structure."""

    def test_keyframe_has_required_fields(self):
        """CameraKeyframe must have azimuth, elevation, radius, target, fov."""
        kf = CameraKeyframe(
            azimuth=45.0,
            elevation=-15.0,
            radius=10.0,
            target_x=0.0,
            target_y=0.0,
            target_z=0.0,
            fov=60.0,
        )
        assert kf.azimuth == 45.0
        assert kf.elevation == -15.0
        assert kf.radius == 10.0
        assert kf.target_x == 0.0
        assert kf.target_y == 0.0
        assert kf.target_z == 0.0
        assert kf.fov == 60.0

    def test_keyframe_is_frozen(self):
        """CameraKeyframe should be immutable (frozen dataclass)."""
        kf = CameraKeyframe(
            azimuth=0.0, elevation=0.0, radius=1.0,
            target_x=0.0, target_y=0.0, target_z=0.0, fov=60.0,
        )
        with pytest.raises(AttributeError):
            kf.azimuth = 99.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ERA_KEYFRAMES tests
# ---------------------------------------------------------------------------

class TestEraKeyframes:
    """Tests for the per-era keyframe data."""

    def test_all_11_eras_have_keyframes(self):
        """ERA_KEYFRAMES must have entries for all 11 eras (indices 0-10)."""
        for i in range(11):
            assert i in ERA_KEYFRAMES, f"Missing keyframe for era {i}"

    def test_all_keyframe_azimuths_are_finite(self):
        """All keyframe azimuth values must be finite floats."""
        for era_idx, keyframes in ERA_KEYFRAMES.items():
            for kf in keyframes:
                assert math.isfinite(kf.azimuth), (
                    f"Era {era_idx}: azimuth {kf.azimuth} is not finite"
                )

    def test_each_era_has_at_least_one_keyframe(self):
        """Each era must have at least 1 keyframe."""
        for era_idx, keyframes in ERA_KEYFRAMES.items():
            assert len(keyframes) >= 1, f"Era {era_idx} has no keyframes"


# ---------------------------------------------------------------------------
# CinematicCameraController tests
# ---------------------------------------------------------------------------

class TestCinematicCameraController:
    """Tests for the cinematic auto-camera controller."""

    @pytest.fixture()
    def camera(self):
        """Create a DampedOrbitCamera for testing."""
        return DampedOrbitCamera()

    @pytest.fixture()
    def controller(self, camera):
        """Create a CinematicCameraController with default keyframes."""
        return CinematicCameraController(camera)

    def test_starts_in_auto_mode(self, controller):
        """Controller must start with auto_mode=True."""
        assert controller.is_auto is True

    def test_toggle_mode_switches_to_free(self, controller):
        """toggle_mode() switches auto_mode from True to False."""
        controller.toggle_mode()
        assert controller.is_auto is False

    def test_toggle_mode_back_to_auto(self, controller):
        """toggle_mode() twice returns to auto mode."""
        controller.toggle_mode()  # -> free
        controller.toggle_mode()  # -> auto
        assert controller.is_auto is True

    def test_update_auto_mode_sets_camera_state(self, camera, controller):
        """In auto mode, update() sets camera azimuth/elevation/radius."""
        initial_azimuth = camera.azimuth
        controller.update(0.016, era_index=5, era_progress=0.5)
        # Camera state should have changed (unless era 5's keyframe happens
        # to match the default, which is unlikely)
        # We check that the controller did something by verifying specific values
        # from evaluate_path
        kf = controller.evaluate_path(5, 0.5)
        assert camera.azimuth == pytest.approx(kf.azimuth)
        assert camera.elevation == pytest.approx(kf.elevation)
        assert camera.radius == pytest.approx(kf.radius)

    def test_update_free_mode_does_not_modify_camera(self, camera, controller):
        """After toggling to free mode, update() does NOT modify camera state."""
        controller.toggle_mode()  # -> free mode
        # Set camera to known state
        camera.azimuth = 123.0
        camera.elevation = -45.0
        camera.radius = 99.0
        controller.update(0.016, era_index=3, era_progress=0.5)
        assert camera.azimuth == 123.0
        assert camera.elevation == -45.0
        assert camera.radius == 99.0

    def test_toggle_to_auto_sets_blend_back_timer(self, controller):
        """When toggling back to auto mode, blend_back_timer is set."""
        controller.toggle_mode()  # -> free
        controller.toggle_mode()  # -> auto
        assert controller.blend_back_timer == pytest.approx(
            controller.blend_back_duration
        )

    def test_blend_back_interpolates_camera_state(self, camera, controller):
        """During blend-back, camera state is between free position and scripted path."""
        # Update to set camera to some scripted state first
        controller.update(0.016, era_index=5, era_progress=0.5)
        scripted_az = camera.azimuth

        # Toggle to free, move camera far away
        controller.toggle_mode()
        camera.azimuth = scripted_az + 100.0
        free_az = camera.azimuth

        # Toggle back to auto -> blend-back should start
        controller.toggle_mode()

        # First update during blend-back: camera should be between
        # the free position and the scripted position
        controller.update(0.1, era_index=5, era_progress=0.5)
        scripted_kf = controller.evaluate_path(5, 0.5)
        # Camera should not have snapped fully to scripted position
        # (blend timer is still > 0)
        if controller.blend_back_timer > 0:
            # Azimuth should be between the two extremes
            lo = min(free_az, scripted_kf.azimuth)
            hi = max(free_az, scripted_kf.azimuth)
            assert lo <= camera.azimuth <= hi

    def test_evaluate_path_era0_progress0(self, controller):
        """evaluate_path for era_index=0, era_progress=0.0 returns era 0 start values."""
        kf = controller.evaluate_path(0, 0.0)
        era0_kf = ERA_KEYFRAMES[0][0]
        assert kf.azimuth == pytest.approx(era0_kf.azimuth)
        assert kf.elevation == pytest.approx(era0_kf.elevation)
        assert kf.radius == pytest.approx(era0_kf.radius)

    def test_evaluate_path_era10_progress1(self, controller):
        """evaluate_path for era_index=10, era_progress=1.0 returns era 10 end values."""
        kf = controller.evaluate_path(10, 1.0)
        era10_kf = ERA_KEYFRAMES[10][0]
        assert kf.azimuth == pytest.approx(era10_kf.azimuth)
        assert kf.elevation == pytest.approx(era10_kf.elevation)
        assert kf.radius == pytest.approx(era10_kf.radius)

    def test_update_zeros_velocity_fields(self, camera, controller):
        """Auto-mode update zeroes damping velocity fields on the camera."""
        camera._vel_azimuth = 50.0
        camera._vel_elevation = 30.0
        camera._vel_zoom = 0.5
        controller.update(0.016, era_index=3, era_progress=0.5)
        assert camera._vel_azimuth == 0.0
        assert camera._vel_elevation == 0.0
        assert camera._vel_zoom == 0.0

    def test_evaluate_path_all_eras(self, controller):
        """evaluate_path produces valid keyframes for all 11 eras at various progress."""
        for era_idx in range(11):
            for progress in [0.0, 0.25, 0.5, 0.75, 1.0]:
                kf = controller.evaluate_path(era_idx, progress)
                assert math.isfinite(kf.azimuth), f"Era {era_idx} p={progress}"
                assert math.isfinite(kf.elevation), f"Era {era_idx} p={progress}"
                assert math.isfinite(kf.radius), f"Era {era_idx} p={progress}"
                assert kf.radius > 0, f"Era {era_idx} p={progress}"
                assert math.isfinite(kf.fov), f"Era {era_idx} p={progress}"
                assert kf.fov > 0, f"Era {era_idx} p={progress}"
