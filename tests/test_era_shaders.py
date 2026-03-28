"""Unit tests for per-era fragment shaders.

Tests cover:
- All 11 era shader files exist and load via shader_loader
- Each shader contains required common uniforms (u_base_color, u_brightness)
- Physics-specific uniforms appear ONLY in correct shaders
- All shaders have #version 430
- All shaders have matching in/out declarations
- Include resolution works for all shaders
"""
import pytest
from bigbangsim.rendering.shader_loader import load_shader_source


# All 11 era shader paths (relative to SHADER_DIR)
ERA_SHADERS = [
    "fragment/era_00_planck.frag",
    "fragment/era_01_gut.frag",
    "fragment/era_02_inflation.frag",
    "fragment/era_03_qgp.frag",
    "fragment/era_04_hadron.frag",
    "fragment/era_05_nucleosynthesis.frag",
    "fragment/era_06_recombination.frag",
    "fragment/era_07_dark_ages.frag",
    "fragment/era_08_first_stars.frag",
    "fragment/era_09_galaxy_formation.frag",
    "fragment/era_10_lss.frag",
]


class TestEraShaderFilesExist:
    """All 11 era shader files exist and can be loaded."""

    @pytest.mark.parametrize("shader_path", ERA_SHADERS)
    def test_shader_loads_without_error(self, shader_path):
        """Each shader file loads via shader_loader without FileNotFoundError."""
        src = load_shader_source(shader_path)
        assert len(src) > 0, f"Shader {shader_path} loaded but was empty"


class TestEraShaderVersion:
    """All shaders must declare #version 430."""

    @pytest.mark.parametrize("shader_path", ERA_SHADERS)
    def test_has_version_430(self, shader_path):
        src = load_shader_source(shader_path)
        assert "#version 430" in src, f"{shader_path} missing #version 430"


class TestEraShaderCommonUniforms:
    """All shaders must have u_base_color and u_brightness uniforms."""

    @pytest.mark.parametrize("shader_path", ERA_SHADERS)
    def test_has_base_color(self, shader_path):
        src = load_shader_source(shader_path)
        assert "u_base_color" in src, f"{shader_path} missing u_base_color"

    @pytest.mark.parametrize("shader_path", ERA_SHADERS)
    def test_has_brightness(self, shader_path):
        src = load_shader_source(shader_path)
        assert "u_brightness" in src, f"{shader_path} missing u_brightness"


class TestEraShaderIODeclarations:
    """All shaders must have matching in/out declarations."""

    @pytest.mark.parametrize("shader_path", ERA_SHADERS)
    def test_has_v_color_input(self, shader_path):
        src = load_shader_source(shader_path)
        assert "in vec4 v_color" in src, f"{shader_path} missing 'in vec4 v_color'"

    @pytest.mark.parametrize("shader_path", ERA_SHADERS)
    def test_has_v_life_input(self, shader_path):
        src = load_shader_source(shader_path)
        assert "in float v_life" in src, f"{shader_path} missing 'in float v_life'"

    @pytest.mark.parametrize("shader_path", ERA_SHADERS)
    def test_has_frag_color_output(self, shader_path):
        src = load_shader_source(shader_path)
        assert "out vec4 fragColor" in src, f"{shader_path} missing 'out vec4 fragColor'"


class TestPhysicsUniformScoping:
    """Physics-specific uniforms must appear ONLY in their respective shaders."""

    def test_ionization_fraction_only_in_era_06(self):
        """u_ionization_fraction appears only in era_06_recombination.frag."""
        for shader_path in ERA_SHADERS:
            src = load_shader_source(shader_path)
            if "era_06_recombination" in shader_path:
                assert "u_ionization_fraction" in src, (
                    "era_06 must have u_ionization_fraction"
                )
            else:
                assert "u_ionization_fraction" not in src, (
                    f"u_ionization_fraction should not be in {shader_path}"
                )

    def test_helium_fraction_only_in_era_05(self):
        """u_helium_fraction appears only in era_05_nucleosynthesis.frag."""
        for shader_path in ERA_SHADERS:
            src = load_shader_source(shader_path)
            if "era_05_nucleosynthesis" in shader_path:
                assert "u_helium_fraction" in src, (
                    "era_05 must have u_helium_fraction"
                )
            else:
                assert "u_helium_fraction" not in src, (
                    f"u_helium_fraction should not be in {shader_path}"
                )

    def test_reionization_frac_only_in_era_08(self):
        """u_reionization_frac appears only in era_08_first_stars.frag."""
        for shader_path in ERA_SHADERS:
            src = load_shader_source(shader_path)
            if "era_08_first_stars" in shader_path:
                assert "u_reionization_frac" in src, (
                    "era_08 must have u_reionization_frac"
                )
            else:
                assert "u_reionization_frac" not in src, (
                    f"u_reionization_frac should not be in {shader_path}"
                )

    def test_collapsed_fraction_only_in_era_09_and_10(self):
        """u_collapsed_fraction appears only in era_09 and era_10."""
        for shader_path in ERA_SHADERS:
            src = load_shader_source(shader_path)
            if "era_09_galaxy_formation" in shader_path or "era_10_lss" in shader_path:
                assert "u_collapsed_fraction" in src, (
                    f"{shader_path} must have u_collapsed_fraction"
                )
            else:
                assert "u_collapsed_fraction" not in src, (
                    f"u_collapsed_fraction should not be in {shader_path}"
                )


class TestIncludeResolution:
    """Shader includes are properly resolved by shader_loader."""

    @pytest.mark.parametrize("shader_path", ERA_SHADERS)
    def test_no_unresolved_includes(self, shader_path):
        """After loading, no #include directives should remain."""
        src = load_shader_source(shader_path)
        assert '#include' not in src, (
            f"{shader_path} has unresolved #include directives"
        )

    def test_noise_shaders_contain_snoise(self):
        """Shaders that include noise.glsl should have snoise function available."""
        noise_shaders = [
            "fragment/era_00_planck.frag",
            "fragment/era_01_gut.frag",
            "fragment/era_03_qgp.frag",
            "fragment/era_04_hadron.frag",
            "fragment/era_07_dark_ages.frag",
        ]
        for shader_path in noise_shaders:
            src = load_shader_source(shader_path)
            assert "snoise" in src, (
                f"{shader_path} includes noise.glsl but snoise not found"
            )

    def test_era_utils_functions_available(self):
        """All shaders that include era_utils.glsl have soft_glow/sharp_glow."""
        for shader_path in ERA_SHADERS:
            src = load_shader_source(shader_path)
            assert "soft_glow" in src or "sharp_glow" in src, (
                f"{shader_path} missing era_utils glow functions"
            )
