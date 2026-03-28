"""Tests for EraVisualConfig data structure and all 11 era configurations.

Verifies data integrity, index consistency, and value constraints for
the per-era visual configuration that drives shaders and rendering.
"""
import inspect
import pytest


class TestEraVisualConfigList:
    """Tests for the ERA_VISUAL_CONFIGS list as a whole."""

    def test_exactly_11_configs(self):
        """ERA_VISUAL_CONFIGS must have exactly 11 entries (one per era)."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS
        assert len(ERA_VISUAL_CONFIGS) == 11

    def test_era_indexes_match_positions(self):
        """Each config.era_index must match its position in the list."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS
        for i, config in enumerate(ERA_VISUAL_CONFIGS):
            assert config.era_index == i, (
                f"Config at index {i} has era_index={config.era_index}"
            )

    def test_all_shader_keys_unique(self):
        """All shader_key values must be unique."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS
        keys = [c.shader_key for c in ERA_VISUAL_CONFIGS]
        assert len(keys) == len(set(keys)), (
            f"Duplicate shader keys found: {[k for k in keys if keys.count(k) > 1]}"
        )

    def test_base_colors_valid(self):
        """All base_color tuples have 3 float components in [0, 1]."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS
        for config in ERA_VISUAL_CONFIGS:
            assert len(config.base_color) == 3, (
                f"Era {config.era_index}: base_color has {len(config.base_color)} components"
            )
            for j, c in enumerate(config.base_color):
                assert 0.0 <= c <= 1.0, (
                    f"Era {config.era_index}: base_color[{j}]={c} out of [0,1]"
                )

    def test_accent_colors_valid(self):
        """All accent_color tuples have 3 float components in [0, 1]."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS
        for config in ERA_VISUAL_CONFIGS:
            assert len(config.accent_color) == 3, (
                f"Era {config.era_index}: accent_color has {len(config.accent_color)} components"
            )
            for j, c in enumerate(config.accent_color):
                assert 0.0 <= c <= 1.0, (
                    f"Era {config.era_index}: accent_color[{j}]={c} out of [0,1]"
                )

    def test_numeric_params_non_negative(self):
        """All numeric parameters are non-negative."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS
        for config in ERA_VISUAL_CONFIGS:
            assert config.particle_size >= 0, f"Era {config.era_index}: particle_size < 0"
            assert config.bloom_strength >= 0, f"Era {config.era_index}: bloom_strength < 0"
            assert config.bloom_threshold >= 0, f"Era {config.era_index}: bloom_threshold < 0"
            assert config.expansion_rate >= 0, f"Era {config.era_index}: expansion_rate < 0"
            assert config.noise_strength >= 0, f"Era {config.era_index}: noise_strength < 0"
            assert config.gravity_strength >= 0, f"Era {config.era_index}: gravity_strength < 0"
            assert config.damping >= 0, f"Era {config.era_index}: damping < 0"
            assert config.brightness >= 0, f"Era {config.era_index}: brightness < 0"
            assert config.transition_seconds >= 0, f"Era {config.era_index}: transition_seconds < 0"

    def test_bloom_strength_in_range(self):
        """bloom_strength in [0, 1] for all eras."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS
        for config in ERA_VISUAL_CONFIGS:
            assert 0.0 <= config.bloom_strength <= 1.0, (
                f"Era {config.era_index}: bloom_strength={config.bloom_strength}"
            )

    def test_transition_seconds_positive(self):
        """transition_seconds > 0 for all eras."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS
        for config in ERA_VISUAL_CONFIGS:
            assert config.transition_seconds > 0, (
                f"Era {config.era_index}: transition_seconds={config.transition_seconds}"
            )

    def test_particle_size_positive(self):
        """particle_size > 0 for all eras."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS
        for config in ERA_VISUAL_CONFIGS:
            assert config.particle_size > 0, (
                f"Era {config.era_index}: particle_size={config.particle_size}"
            )

    def test_gravity_zero_early_eras(self):
        """gravity_strength is 0.0 for early eras (0-6)."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS
        for i in range(7):
            assert ERA_VISUAL_CONFIGS[i].gravity_strength == 0.0, (
                f"Era {i}: gravity_strength={ERA_VISUAL_CONFIGS[i].gravity_strength}, expected 0.0"
            )

    def test_gravity_positive_late_eras(self):
        """gravity_strength is positive for late eras (7-10)."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS
        for i in range(7, 11):
            assert ERA_VISUAL_CONFIGS[i].gravity_strength > 0.0, (
                f"Era {i}: gravity_strength={ERA_VISUAL_CONFIGS[i].gravity_strength}, expected > 0"
            )

    def test_brightness_highest_planck(self):
        """Brightness is highest for Planck epoch (era 0)."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS
        planck_brightness = ERA_VISUAL_CONFIGS[0].brightness
        for config in ERA_VISUAL_CONFIGS[1:]:
            assert planck_brightness >= config.brightness, (
                f"Era {config.era_index} brightness ({config.brightness}) > "
                f"Planck ({planck_brightness})"
            )

    def test_brightness_lowest_dark_ages(self):
        """Brightness is lowest for Dark Ages (era 7)."""
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS
        dark_brightness = ERA_VISUAL_CONFIGS[7].brightness
        for config in ERA_VISUAL_CONFIGS:
            assert dark_brightness <= config.brightness, (
                f"Era {config.era_index} brightness ({config.brightness}) < "
                f"Dark Ages ({dark_brightness})"
            )


class TestGetEraVisualConfig:
    """Tests for get_era_visual_config helper."""

    def test_returns_correct_config(self):
        """get_era_visual_config(i) returns config with era_index=i."""
        from bigbangsim.simulation.era_visual_config import get_era_visual_config
        for i in range(11):
            config = get_era_visual_config(i)
            assert config.era_index == i

    def test_out_of_range_raises(self):
        """get_era_visual_config with invalid index raises IndexError."""
        from bigbangsim.simulation.era_visual_config import get_era_visual_config
        with pytest.raises(IndexError):
            get_era_visual_config(11)
        with pytest.raises(IndexError):
            get_era_visual_config(-12)

    def test_frozen_dataclass(self):
        """EraVisualConfig instances are immutable (frozen)."""
        from bigbangsim.simulation.era_visual_config import get_era_visual_config
        config = get_era_visual_config(0)
        with pytest.raises(AttributeError):
            config.brightness = 999.0


class TestShaderKeys:
    """Tests for shader key naming convention."""

    def test_planck_key(self):
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS
        assert ERA_VISUAL_CONFIGS[0].shader_key == "era_00_planck"

    def test_lss_key(self):
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS
        assert ERA_VISUAL_CONFIGS[10].shader_key == "era_10_lss"

    def test_all_keys_start_with_era(self):
        from bigbangsim.simulation.era_visual_config import ERA_VISUAL_CONFIGS
        for config in ERA_VISUAL_CONFIGS:
            assert config.shader_key.startswith("era_"), (
                f"Era {config.era_index}: shader_key '{config.shader_key}' doesn't start with 'era_'"
            )


class TestModuleBoundary:
    """Test simulation-rendering boundary."""

    def test_no_rendering_imports(self):
        """era_visual_config module has zero rendering imports."""
        import bigbangsim.simulation.era_visual_config as mod
        source = inspect.getsource(mod)
        assert "from bigbangsim.rendering" not in source
        assert "import moderngl" not in source

    def test_module_importable(self):
        """Module can be imported without any rendering dependencies."""
        from bigbangsim.simulation.era_visual_config import (
            EraVisualConfig,
            ERA_VISUAL_CONFIGS,
            get_era_visual_config,
        )
        assert EraVisualConfig is not None
        assert ERA_VISUAL_CONFIGS is not None
        assert get_era_visual_config is not None
