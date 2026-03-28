"""Unit tests for ParticleSystem.

Tests validate buffer creation, data layout, ping-pong swapping, and initial
particle generation WITHOUT requiring a real GPU context. The static method
_generate_initial_particles is tested directly (pure numpy). Buffer creation
and compute dispatch are tested via mocking moderngl.Context.
"""
import numpy as np
import pytest


class TestGenerateInitialParticles:
    """Test the static _generate_initial_particles method (no GPU needed)."""

    def test_output_shape(self):
        """Particle data has shape (count, 12) -- 3 vec4s = 12 floats."""
        from bigbangsim.rendering.particles import ParticleSystem

        count = 1000
        data = ParticleSystem._generate_initial_particles(count)
        assert data.shape == (count, 12)

    def test_output_dtype_float32(self):
        """Particle data must be float32 for GPU upload."""
        from bigbangsim.rendering.particles import ParticleSystem

        data = ParticleSystem._generate_initial_particles(500)
        assert data.dtype == np.float32

    def test_positions_in_range(self):
        """Positions (cols 0-2) should be Gaussian with sigma=2.0.

        99.7% of values within [-6, 6] for sigma=2.0.
        All values within [-10, 10] practically guaranteed for 10K particles.
        """
        from bigbangsim.rendering.particles import ParticleSystem

        data = ParticleSystem._generate_initial_particles(10_000)
        positions = data[:, 0:3]
        assert np.all(positions > -10.0), "Positions too negative"
        assert np.all(positions < 10.0), "Positions too positive"
        # Check approximate standard deviation
        std = np.std(positions)
        assert 1.5 < std < 2.5, f"Position std={std}, expected ~2.0"

    def test_life_initialized_to_one(self):
        """Life (col 3 = position.w) should be 1.0 for all particles."""
        from bigbangsim.rendering.particles import ParticleSystem

        data = ParticleSystem._generate_initial_particles(500)
        life = data[:, 3]
        np.testing.assert_array_equal(life, 1.0)

    def test_velocities_small(self):
        """Velocities (cols 4-6) should be small (sigma=0.1)."""
        from bigbangsim.rendering.particles import ParticleSystem

        data = ParticleSystem._generate_initial_particles(5000)
        velocities = data[:, 4:7]
        assert np.all(np.abs(velocities) < 1.0), "Velocities too large"

    def test_particle_type_zero(self):
        """Particle type (col 7 = velocity.w) should be 0.0."""
        from bigbangsim.rendering.particles import ParticleSystem

        data = ParticleSystem._generate_initial_particles(500)
        ptype = data[:, 7]
        np.testing.assert_array_equal(ptype, 0.0)

    def test_colors_in_unit_range(self):
        """RGB colors (cols 8-10) should be in [0, 1] range."""
        from bigbangsim.rendering.particles import ParticleSystem

        data = ParticleSystem._generate_initial_particles(1000)
        colors = data[:, 8:11]
        assert np.all(colors >= 0.0), "Colors below 0"
        assert np.all(colors <= 1.0), "Colors above 1"

    def test_alpha_initialized_to_one(self):
        """Alpha (col 11 = color.a) should be 1.0 for all particles."""
        from bigbangsim.rendering.particles import ParticleSystem

        data = ParticleSystem._generate_initial_particles(500)
        alpha = data[:, 11]
        np.testing.assert_array_equal(alpha, 1.0)


class TestParticleStride:
    """Test the PARTICLE_STRIDE constant."""

    def test_stride_is_48(self):
        """3 vec4 * 4 bytes = 48 bytes per particle."""
        from bigbangsim.rendering.particles import PARTICLE_STRIDE

        assert PARTICLE_STRIDE == 48

    def test_buffer_size_calculation(self):
        """Buffer size should be count * 48 bytes."""
        from bigbangsim.rendering.particles import ParticleSystem, PARTICLE_STRIDE

        count = 1000
        data = ParticleSystem._generate_initial_particles(count)
        expected_size = count * PARTICLE_STRIDE
        assert data.nbytes == expected_size


class TestParticleSystemBufferLogic:
    """Test ping-pong buffer swap logic and render buffer selection."""

    def test_initial_current_is_zero(self):
        """current buffer index starts at 0."""
        from bigbangsim.rendering.particles import ParticleSystem

        # We can't construct ParticleSystem without a context,
        # but we can verify the class attribute default via a mock
        from unittest.mock import MagicMock, patch

        mock_ctx = MagicMock()
        mock_ctx.buffer.return_value = MagicMock()
        mock_ctx.compute_shader.return_value = MagicMock()
        mock_ctx.program.return_value = MagicMock()
        mock_ctx.vertex_array.return_value = MagicMock()

        with patch(
            "bigbangsim.rendering.particles.load_shader_source",
            return_value="#version 430\nvoid main() {}",
        ):
            ps = ParticleSystem(mock_ctx, count=100)
            assert ps.current == 0

    def test_two_buffers_created(self):
        """Ping-pong requires exactly 2 SSBO buffers."""
        from bigbangsim.rendering.particles import ParticleSystem
        from unittest.mock import MagicMock, patch

        mock_ctx = MagicMock()
        mock_buf = MagicMock()
        mock_ctx.buffer.return_value = mock_buf
        mock_ctx.compute_shader.return_value = MagicMock()
        mock_ctx.program.return_value = MagicMock()
        mock_ctx.vertex_array.return_value = MagicMock()

        with patch(
            "bigbangsim.rendering.particles.load_shader_source",
            return_value="#version 430\nvoid main() {}",
        ):
            ps = ParticleSystem(mock_ctx, count=100)
            assert len(ps.buffers) == 2

    def test_buffer_size_matches_particle_count(self):
        """Each buffer should be allocated with count * 48 bytes."""
        from bigbangsim.rendering.particles import ParticleSystem, PARTICLE_STRIDE
        from unittest.mock import MagicMock, patch, call

        mock_ctx = MagicMock()
        mock_ctx.buffer.return_value = MagicMock()
        mock_ctx.compute_shader.return_value = MagicMock()
        mock_ctx.program.return_value = MagicMock()
        mock_ctx.vertex_array.return_value = MagicMock()

        count = 256
        expected_bytes = count * PARTICLE_STRIDE

        with patch(
            "bigbangsim.rendering.particles.load_shader_source",
            return_value="#version 430\nvoid main() {}",
        ):
            ps = ParticleSystem(mock_ctx, count=count)

            # buffer() called twice, each with bytes of expected length
            assert mock_ctx.buffer.call_count == 2
            for c in mock_ctx.buffer.call_args_list:
                buf_data = c[0][0]  # First positional argument
                assert len(buf_data) == expected_bytes

    def test_get_render_buffer_returns_current(self):
        """get_render_buffer returns buffers[current]."""
        from bigbangsim.rendering.particles import ParticleSystem
        from unittest.mock import MagicMock, patch

        mock_ctx = MagicMock()
        buf0 = MagicMock(name="buf0")
        buf1 = MagicMock(name="buf1")
        mock_ctx.buffer.side_effect = [buf0, buf1]
        mock_ctx.compute_shader.return_value = MagicMock()
        mock_ctx.program.return_value = MagicMock()
        mock_ctx.vertex_array.return_value = MagicMock()

        with patch(
            "bigbangsim.rendering.particles.load_shader_source",
            return_value="#version 430\nvoid main() {}",
        ):
            ps = ParticleSystem(mock_ctx, count=100)
            assert ps.get_render_buffer() is buf0

    def test_swap_toggles_current(self):
        """After swap, current toggles between 0 and 1."""
        from bigbangsim.rendering.particles import ParticleSystem
        from unittest.mock import MagicMock, patch

        mock_ctx = MagicMock()
        mock_ctx.buffer.return_value = MagicMock()
        mock_ctx.compute_shader.return_value = MagicMock()
        mock_ctx.program.return_value = MagicMock()
        mock_ctx.vertex_array.return_value = MagicMock()

        with patch(
            "bigbangsim.rendering.particles.load_shader_source",
            return_value="#version 430\nvoid main() {}",
        ):
            ps = ParticleSystem(mock_ctx, count=100)
            assert ps.current == 0
            # Simulate what update() does: swap
            ps.current = 1 - ps.current
            assert ps.current == 1
            ps.current = 1 - ps.current
            assert ps.current == 0

    def test_get_render_buffer_after_swap(self):
        """After swap, get_render_buffer returns the other buffer."""
        from bigbangsim.rendering.particles import ParticleSystem
        from unittest.mock import MagicMock, patch

        mock_ctx = MagicMock()
        buf0 = MagicMock(name="buf0")
        buf1 = MagicMock(name="buf1")
        mock_ctx.buffer.side_effect = [buf0, buf1]
        mock_ctx.compute_shader.return_value = MagicMock()
        mock_ctx.program.return_value = MagicMock()
        mock_ctx.vertex_array.return_value = MagicMock()

        with patch(
            "bigbangsim.rendering.particles.load_shader_source",
            return_value="#version 430\nvoid main() {}",
        ):
            ps = ParticleSystem(mock_ctx, count=100)
            assert ps.get_render_buffer() is buf0
            ps.current = 1 - ps.current
            assert ps.get_render_buffer() is buf1


class TestParticleSystemShaderSelection:
    """Test era-based shader variant switching (Phase 3: 11 per-era shaders)."""

    def test_default_shader_is_era_00(self):
        """Default active program key is 'era_00_planck' (Phase 3)."""
        from bigbangsim.rendering.particles import ParticleSystem
        from unittest.mock import MagicMock, patch

        mock_ctx = MagicMock()
        mock_ctx.buffer.return_value = MagicMock()
        mock_ctx.compute_shader.return_value = MagicMock()
        mock_ctx.program.return_value = MagicMock()
        mock_ctx.vertex_array.return_value = MagicMock()

        with patch(
            "bigbangsim.rendering.particles.load_shader_source",
            return_value="#version 430\nvoid main() {}",
        ):
            ps = ParticleSystem(mock_ctx, count=100)
            assert ps.active_program_key == "era_00_planck"

    def test_set_era_shader_selects_correct_key(self):
        """set_era_shader selects the correct per-era shader key from EraVisualConfig."""
        from bigbangsim.rendering.particles import ParticleSystem
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS
        from unittest.mock import MagicMock, patch

        mock_ctx = MagicMock()
        mock_ctx.buffer.return_value = MagicMock()
        mock_ctx.compute_shader.return_value = MagicMock()
        mock_ctx.program.return_value = MagicMock()
        mock_ctx.vertex_array.return_value = MagicMock()

        with patch(
            "bigbangsim.rendering.particles.load_shader_source",
            return_value="#version 430\nvoid main() {}",
        ):
            ps = ParticleSystem(mock_ctx, count=100)
            for era_idx in range(11):
                ps.set_era_shader(era_idx)
                expected_key = ERA_VISUAL_CONFIGS[era_idx].shader_key
                assert ps.active_program_key == expected_key, (
                    f"Era {era_idx} should use '{expected_key}'"
                )

    def test_backward_compat_hot_cool_aliases(self):
        """'hot' and 'cool' program keys exist as backward-compat aliases."""
        from bigbangsim.rendering.particles import ParticleSystem
        from unittest.mock import MagicMock, patch

        mock_ctx = MagicMock()
        mock_ctx.buffer.return_value = MagicMock()
        mock_ctx.compute_shader.return_value = MagicMock()
        mock_ctx.program.return_value = MagicMock()
        mock_ctx.vertex_array.return_value = MagicMock()

        with patch(
            "bigbangsim.rendering.particles.load_shader_source",
            return_value="#version 430\nvoid main() {}",
        ):
            ps = ParticleSystem(mock_ctx, count=100)
            assert "hot" in ps.programs
            assert "cool" in ps.programs
