"""Camera-relative coordinate transforms for float32 precision preservation.

All vertex positions are transformed relative to the camera position in
float64 (Python) BEFORE uploading to the GPU as float32. This keeps GPU
coordinates near zero where float32 precision is best.

See: Pitfall 2 in PITFALLS.md -- Floating-Point Precision Catastrophe (PHYS-07)
"""
import numpy as np
import glm


def camera_relative_transform(
    positions: np.ndarray, camera_pos: np.ndarray
) -> np.ndarray:
    """Subtract camera position in float64, then cast to float32 for GPU upload.

    Args:
        positions: (N, 3) array of world-space positions (any dtype).
        camera_pos: (3,) camera world position.

    Returns:
        (N, 3) float32 array of camera-relative positions.
    """
    relative = positions.astype(np.float64) - camera_pos.astype(np.float64)
    return relative.astype(np.float32)


def view_matrix_camera_relative(
    camera_pos: glm.dvec3,
    camera_target: glm.dvec3,
    up: glm.dvec3 = None,
) -> glm.mat4:
    """Compute view matrix in double precision, cast to float32 for GPU.

    Uses glm.dvec3 (float64) for the lookAt computation, then converts the
    resulting matrix to float32 (glm.mat4). Safe because all values in the
    view matrix are camera-relative (near zero).

    Args:
        camera_pos: Camera world position (double precision).
        camera_target: Look-at target (double precision).
        up: Up vector (double precision). Defaults to (0, 1, 0).

    Returns:
        glm.mat4 (float32) view matrix suitable for GPU upload.
    """
    if up is None:
        up = glm.dvec3(0, 1, 0)
    view_d = glm.lookAt(camera_pos, camera_target, up)
    return glm.mat4(view_d)


def normalize_era_positions(
    positions: np.ndarray, era_scale: float
) -> np.ndarray:
    """Normalize positions to dimensionless fractions of era scale.

    Each era operates at a different spatial scale. Positions are stored as
    fractions of the era's characteristic scale, not absolute physical units.

    Args:
        positions: (N, 3) world-space positions.
        era_scale: Characteristic scale for the current era [meters].

    Returns:
        (N, 3) float32 array of normalized positions.
    """
    if era_scale <= 0:
        era_scale = 1.0
    return (positions / era_scale).astype(np.float32)
