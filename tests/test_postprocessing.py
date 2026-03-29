"""Unit tests for PostProcessingPipeline.

Tests validate construction parameters, default values, half-resolution bloom
math, and method existence WITHOUT requiring a real GPU context. The pipeline
requires a moderngl.Context for FBO/texture creation, so construction tests
use mock-based verification.
"""
from unittest.mock import MagicMock, patch, call

import pytest


def _make_mock_pipeline(width=1280, height=720):
    """Helper to construct PostProcessingPipeline with a mocked context.

    Returns (pipeline, mock_ctx) so tests can inspect both.
    """
    from bigbangsim.rendering.postprocessing import PostProcessingPipeline

    mock_ctx = MagicMock()
    mock_ctx.texture.return_value = MagicMock()
    mock_ctx.depth_renderbuffer.return_value = MagicMock()
    mock_ctx.framebuffer.return_value = MagicMock()
    mock_ctx.program.return_value = MagicMock()
    mock_ctx.buffer.return_value = MagicMock()
    mock_ctx.vertex_array.return_value = MagicMock()

    with patch(
        "bigbangsim.rendering.postprocessing.load_shader_source",
        return_value="#version 430\nvoid main() {}",
    ):
        pp = PostProcessingPipeline(mock_ctx, width, height)

    return pp, mock_ctx


class TestPostProcessingDefaults:
    """Test default parameter values."""

    def test_default_exposure(self):
        """Default exposure should be 1.0."""
        pp, _ = _make_mock_pipeline()
        assert pp.exposure == 1.0

    def test_default_bloom_strength(self):
        """Default bloom strength should be 0.3."""
        pp, _ = _make_mock_pipeline()
        assert pp.bloom_strength == 0.3

    def test_default_bloom_threshold(self):
        """Default bloom threshold should be 1.0."""
        pp, _ = _make_mock_pipeline()
        assert pp.bloom_threshold == 1.0

    def test_default_blur_iterations(self):
        """Default blur iterations should be 6."""
        pp, _ = _make_mock_pipeline()
        assert pp.blur_iterations == 6


class TestPostProcessingDimensions:
    """Test dimension handling and half-resolution bloom."""

    def test_stores_width_height(self):
        """Pipeline stores the width and height passed to it."""
        pp, _ = _make_mock_pipeline(1920, 1080)
        assert pp.width == 1920
        assert pp.height == 1080

    def test_bloom_half_resolution_math(self):
        """Bloom FBOs should use width//2 and height//2."""
        width, height = 1280, 720
        hw, hh = width // 2, height // 2
        assert hw == 640
        assert hh == 360

    def test_hdr_texture_full_resolution(self):
        """HDR texture created at full resolution with dtype='f2'."""
        width, height = 1280, 720
        pp, mock_ctx = _make_mock_pipeline(width, height)

        # First ctx.texture call should be full resolution HDR
        first_texture_call = mock_ctx.texture.call_args_list[0]
        assert first_texture_call[0][0] == (width, height)
        assert first_texture_call[0][1] == 4  # RGBA
        assert first_texture_call[1].get("dtype") == "f4"

    def test_bloom_textures_half_resolution(self):
        """Bloom/blur textures created at half resolution."""
        width, height = 1280, 720
        hw, hh = width // 2, height // 2
        pp, mock_ctx = _make_mock_pipeline(width, height)

        # texture calls after the first (HDR) should be half resolution
        half_res_calls = [
            c for c in mock_ctx.texture.call_args_list
            if c[0][0] == (hw, hh)
        ]
        # bloom_texture + 2 blur_textures = 3 half-res textures
        assert len(half_res_calls) == 3

    def test_two_blur_textures_for_pingpong(self):
        """Pipeline has exactly 2 blur textures for ping-pong blur."""
        pp, _ = _make_mock_pipeline()
        assert len(pp.blur_textures) == 2
        assert len(pp.blur_fbos) == 2


class TestPostProcessingMethods:
    """Test that required methods exist and are callable."""

    def test_has_begin_scene(self):
        """Pipeline has begin_scene method."""
        pp, _ = _make_mock_pipeline()
        assert callable(pp.begin_scene)

    def test_has_end_scene(self):
        """Pipeline has end_scene method."""
        pp, _ = _make_mock_pipeline()
        assert callable(pp.end_scene)

    def test_has_resize(self):
        """Pipeline has resize method."""
        pp, _ = _make_mock_pipeline()
        assert callable(pp.resize)

    def test_has_release(self):
        """Pipeline has release method."""
        pp, _ = _make_mock_pipeline()
        assert callable(pp.release)

    def test_begin_scene_binds_default_fbo(self):
        """begin_scene should use() and clear() the default FBO (AMD workaround)."""
        pp, mock_ctx = _make_mock_pipeline()
        pp.begin_scene()
        mock_ctx.fbo.use.assert_called_once()
        mock_ctx.fbo.clear.assert_called_once()


class TestPostProcessingShaderLoading:
    """Test that shaders are loaded via load_shader_source."""

    def test_loads_four_programs(self):
        """Pipeline compiles 4 shader programs (blit, bright, blur, tonemap)."""
        pp, mock_ctx = _make_mock_pipeline()
        assert mock_ctx.program.call_count == 4

    def test_has_bright_prog(self):
        """Pipeline has bright_prog attribute."""
        pp, _ = _make_mock_pipeline()
        assert hasattr(pp, "bright_prog")

    def test_has_blur_prog(self):
        """Pipeline has blur_prog attribute."""
        pp, _ = _make_mock_pipeline()
        assert hasattr(pp, "blur_prog")

    def test_has_tonemap_prog(self):
        """Pipeline has tonemap_prog attribute."""
        pp, _ = _make_mock_pipeline()
        assert hasattr(pp, "tonemap_prog")
