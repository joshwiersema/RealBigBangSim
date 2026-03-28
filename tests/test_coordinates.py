"""Tests for camera-relative coordinate transforms (PHYS-07).

Validates float64 subtraction -> float32 casting pattern,
era position normalization, and view matrix computation.
"""
import numpy as np
import glm
import pytest

from bigbangsim.rendering.coordinates import (
    camera_relative_transform,
    normalize_era_positions,
    view_matrix_camera_relative,
)


class TestCameraRelativeTransform:
    """camera_relative_transform subtracts camera pos in float64, returns float32."""

    def test_subtracts_camera_position(self):
        positions = np.array([[100.0, 200.0, 300.0]], dtype=np.float64)
        camera_pos = np.array([100.0, 200.0, 300.0], dtype=np.float64)
        result = camera_relative_transform(positions, camera_pos)
        np.testing.assert_allclose(result[0], [0.0, 0.0, 0.0], atol=1e-6)

    def test_output_dtype_is_float32(self):
        positions = np.array([[1.0, 2.0, 3.0]], dtype=np.float64)
        camera_pos = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        result = camera_relative_transform(positions, camera_pos)
        assert result.dtype == np.float32

    def test_preserves_relative_distances(self):
        """Two points 1.0 apart remain 1.0 apart after transform."""
        positions = np.array([
            [1000.0, 2000.0, 3000.0],
            [1000.0, 2000.0, 3001.0],
        ], dtype=np.float64)
        camera_pos = np.array([1000.0, 2000.0, 3000.0], dtype=np.float64)
        result = camera_relative_transform(positions, camera_pos)
        dist = np.linalg.norm(result[1] - result[0])
        assert abs(dist - 1.0) < 1e-5


class TestNormalizeEraPositions:
    """normalize_era_positions divides by era scale."""

    def test_divides_by_era_scale(self):
        positions = np.array([[1e10, 2e10, 3e10]], dtype=np.float64)
        result = normalize_era_positions(positions, era_scale=1e10)
        np.testing.assert_allclose(result[0], [1.0, 2.0, 3.0], atol=1e-5)

    def test_output_dtype_is_float32(self):
        positions = np.array([[1.0, 2.0, 3.0]], dtype=np.float64)
        result = normalize_era_positions(positions, era_scale=1.0)
        assert result.dtype == np.float32


class TestViewMatrixCameraRelative:
    """view_matrix_camera_relative returns glm.mat4 from double-precision lookAt."""

    def test_returns_mat4(self):
        cam_pos = glm.dvec3(0, 0, 5)
        cam_target = glm.dvec3(0, 0, 0)
        result = view_matrix_camera_relative(cam_pos, cam_target)
        assert isinstance(result, glm.mat4)


def test_app_uses_camera_relative_rendering():
    """Verify PHYS-07: the render loop uses camera-relative coordinates, not raw float32 lookAt."""
    from pathlib import Path
    app_source = (Path(__file__).parent.parent / "bigbangsim" / "app.py").read_text()
    assert "view_matrix_camera_relative" in app_source, (
        "app.py on_render must call view_matrix_camera_relative from coordinates.py "
        "to satisfy PHYS-07 camera-relative rendering. Found raw view_matrix instead."
    )
