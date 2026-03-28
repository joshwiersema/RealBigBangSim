"""Tests for screenshot capture module (CAPT-01)."""
import os
from unittest.mock import MagicMock

import pytest


def test_take_screenshot_creates_file(tmp_path):
    """take_screenshot creates a PNG file with bigbangsim_ prefix."""
    from bigbangsim.capture.screenshot import take_screenshot

    fbo = MagicMock()
    fbo.read.return_value = b'\x00' * (64 * 64 * 3)

    output_dir = str(tmp_path / "screenshots")
    result = take_screenshot(fbo, 64, 64, output_dir=output_dir)

    assert os.path.isfile(result)
    assert result.endswith(".png")
    basename = os.path.basename(result)
    assert basename.startswith("bigbangsim_")


def test_take_screenshot_creates_directory(tmp_path):
    """take_screenshot creates output directory if it does not exist."""
    from bigbangsim.capture.screenshot import take_screenshot

    fbo = MagicMock()
    fbo.read.return_value = b'\x00' * (64 * 64 * 3)

    nested = str(tmp_path / "deeply" / "nested" / "dir")
    assert not os.path.exists(nested)

    take_screenshot(fbo, 64, 64, output_dir=nested)
    assert os.path.isdir(nested)


def test_take_screenshot_reads_correct_fbo_params(tmp_path):
    """take_screenshot reads framebuffer with components=3, alignment=1."""
    from bigbangsim.capture.screenshot import take_screenshot

    fbo = MagicMock()
    fbo.read.return_value = b'\x00' * (64 * 64 * 3)

    take_screenshot(fbo, 64, 64, output_dir=str(tmp_path))

    fbo.read.assert_called_once_with(components=3, alignment=1)
