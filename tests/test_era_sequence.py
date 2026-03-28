"""Unit tests for era sequence coverage and data integrity.

Verifies that all 11 eras are properly defined, have visual configs,
and map to existing shader files. These are pure data integrity tests
that do not require a GPU.
"""
from pathlib import Path

import pytest


class TestEraSequenceCoverage:
    """Test that all 11 eras are defined and indexed correctly."""

    def test_eleven_eras_defined(self):
        """ERAS list has exactly 11 entries."""
        from bigbangsim.simulation.eras import ERAS

        assert len(ERAS) == 11

    def test_era_indexes_zero_to_ten(self):
        """Era indexes span 0-10 with no gaps."""
        from bigbangsim.simulation.eras import ERAS

        indexes = [era.index for era in ERAS]
        assert indexes == list(range(11))

    def test_each_era_has_unique_name(self):
        """Each era has a unique display name."""
        from bigbangsim.simulation.eras import ERAS

        names = [era.name for era in ERAS]
        assert len(set(names)) == 11


class TestEraVisualConfigCoverage:
    """Test that ERA_VISUAL_CONFIGS covers all 11 eras."""

    def test_eleven_configs_defined(self):
        """ERA_VISUAL_CONFIGS has exactly 11 entries."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS

        assert len(ERA_VISUAL_CONFIGS) == 11

    def test_config_indexes_match_eras(self):
        """Each config's era_index matches its position in the list."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS

        for i, config in enumerate(ERA_VISUAL_CONFIGS):
            assert config.era_index == i, f"Config at index {i} has era_index={config.era_index}"

    def test_each_config_has_shader_key(self):
        """Each config specifies a non-empty shader_key."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS

        for config in ERA_VISUAL_CONFIGS:
            assert config.shader_key, f"Era {config.era_index} has empty shader_key"

    def test_shader_keys_unique(self):
        """Each era has a unique shader_key."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS

        keys = [config.shader_key for config in ERA_VISUAL_CONFIGS]
        assert len(set(keys)) == 11

    def test_get_era_visual_config_for_all(self):
        """get_era_visual_config returns valid config for each era 0-10."""
        from bigbangsim.simulation.era_visual_config import (
            get_era_visual_config,
            ERA_VISUAL_CONFIGS,
        )

        for i in range(11):
            config = get_era_visual_config(i)
            assert config is ERA_VISUAL_CONFIGS[i]


class TestShaderFileExistence:
    """Test that all era shader files exist on disk."""

    def test_all_era_fragment_shaders_exist(self):
        """Each ERA_VISUAL_CONFIGS shader_key maps to an existing .frag file."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS

        shader_dir = Path(__file__).parent.parent / "bigbangsim" / "shaders" / "fragment"
        for config in ERA_VISUAL_CONFIGS:
            frag_path = shader_dir / (config.shader_key + ".frag")
            assert frag_path.exists(), (
                f"Missing shader file: {frag_path} for era {config.era_index}"
            )

    def test_crossfade_shader_exists(self):
        """The era crossfade fragment shader exists."""
        shader_dir = Path(__file__).parent.parent / "bigbangsim" / "shaders" / "postprocess"
        assert (shader_dir / "era_crossfade.frag").exists()

    def test_fullscreen_vert_exists(self):
        """The fullscreen vertex shader exists."""
        shader_dir = Path(__file__).parent.parent / "bigbangsim" / "shaders" / "postprocess"
        assert (shader_dir / "fullscreen.vert").exists()


class TestParticleSystemEraShaderNames:
    """Test the _ERA_SHADER_NAMES list in particles.py."""

    def test_eleven_shader_entries(self):
        """_ERA_SHADER_NAMES has exactly 11 entries."""
        from bigbangsim.rendering.particles import _ERA_SHADER_NAMES

        assert len(_ERA_SHADER_NAMES) == 11

    def test_shader_keys_match_configs(self):
        """_ERA_SHADER_NAMES keys match ERA_VISUAL_CONFIGS shader_keys."""
        from bigbangsim.rendering.particles import _ERA_SHADER_NAMES
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS

        particle_keys = [name for name, _path in _ERA_SHADER_NAMES]
        config_keys = [config.shader_key for config in ERA_VISUAL_CONFIGS]
        assert particle_keys == config_keys

    def test_shader_paths_reference_fragment_dir(self):
        """All shader paths start with 'fragment/'."""
        from bigbangsim.rendering.particles import _ERA_SHADER_NAMES

        for _key, path in _ERA_SHADER_NAMES:
            assert path.startswith("fragment/"), f"Unexpected shader path: {path}"


class TestEraVisualConfigValues:
    """Test that config values are within valid ranges."""

    def test_base_color_in_range(self):
        """base_color RGB values are in [0, 1]."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS

        for config in ERA_VISUAL_CONFIGS:
            for c in config.base_color:
                assert 0.0 <= c <= 1.0, f"Era {config.era_index} base_color out of range"

    def test_accent_color_in_range(self):
        """accent_color RGB values are in [0, 1]."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS

        for config in ERA_VISUAL_CONFIGS:
            for c in config.accent_color:
                assert 0.0 <= c <= 1.0, f"Era {config.era_index} accent_color out of range"

    def test_particle_size_positive(self):
        """particle_size is positive."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS

        for config in ERA_VISUAL_CONFIGS:
            assert config.particle_size > 0, f"Era {config.era_index} particle_size <= 0"

    def test_bloom_strength_in_range(self):
        """bloom_strength is in [0, 1]."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS

        for config in ERA_VISUAL_CONFIGS:
            assert 0.0 <= config.bloom_strength <= 1.0, (
                f"Era {config.era_index} bloom_strength out of range"
            )

    def test_transition_seconds_positive(self):
        """transition_seconds is positive for all eras."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS

        for config in ERA_VISUAL_CONFIGS:
            assert config.transition_seconds > 0, (
                f"Era {config.era_index} transition_seconds <= 0"
            )
