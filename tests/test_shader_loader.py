"""Unit tests for shader loader with include preprocessing.

Tests cover:
- Loading shader source without includes (passthrough)
- Single #include directive resolution
- Nested includes NOT resolved (single-level only)
- Missing include file raises FileNotFoundError
- Multiple #include directives in one file
- get_shader_dir() returns correct path
"""
from pathlib import Path

import pytest


def _create_shader_dir(tmp_path: Path) -> Path:
    """Create a shader directory structure with include/ subdirectory."""
    shader_dir = tmp_path / "shaders"
    shader_dir.mkdir()
    (shader_dir / "include").mkdir()
    return shader_dir


class TestLoadShaderSourceNoIncludes:
    """Test 1: load_shader_source returns raw content when no #include present."""

    def test_returns_raw_content(self, tmp_path, monkeypatch):
        shader_dir = _create_shader_dir(tmp_path)
        (shader_dir / "simple.vert").write_text(
            "#version 430\nvoid main() { gl_Position = vec4(0.0); }\n"
        )

        from bigbangsim.rendering import shader_loader

        monkeypatch.setattr(shader_loader, "SHADER_DIR", shader_dir)

        result = shader_loader.load_shader_source("simple.vert")
        assert result == "#version 430\nvoid main() { gl_Position = vec4(0.0); }\n"


class TestLoadShaderSourceSingleInclude:
    """Test 2: #include directive replaced with include file content."""

    def test_single_include_resolved(self, tmp_path, monkeypatch):
        shader_dir = _create_shader_dir(tmp_path)
        (shader_dir / "include" / "common.glsl").write_text(
            "uniform float u_dt;\n"
        )
        (shader_dir / "test.frag").write_text(
            '#version 430\n#include "common.glsl"\nvoid main() {}\n'
        )

        from bigbangsim.rendering import shader_loader

        monkeypatch.setattr(shader_loader, "SHADER_DIR", shader_dir)

        result = shader_loader.load_shader_source("test.frag")
        assert "uniform float u_dt;" in result
        assert '#include' not in result


class TestLoadShaderSourceNoNesting:
    """Test 3: Nested includes are NOT resolved (single-level only)."""

    def test_nested_includes_not_resolved(self, tmp_path, monkeypatch):
        shader_dir = _create_shader_dir(tmp_path)
        # inner.glsl includes another file -- should NOT be resolved
        (shader_dir / "include" / "inner.glsl").write_text(
            '#include "deep.glsl"\nfloat inner_val = 1.0;\n'
        )
        (shader_dir / "include" / "deep.glsl").write_text(
            "float deep_val = 2.0;\n"
        )
        (shader_dir / "test.vert").write_text(
            '#version 430\n#include "inner.glsl"\nvoid main() {}\n'
        )

        from bigbangsim.rendering import shader_loader

        monkeypatch.setattr(shader_loader, "SHADER_DIR", shader_dir)

        result = shader_loader.load_shader_source("test.vert")
        # inner.glsl content should be inlined
        assert "float inner_val = 1.0;" in result
        # But the #include "deep.glsl" inside inner.glsl should remain unresolved
        assert '#include "deep.glsl"' in result
        # deep.glsl content should NOT appear
        assert "float deep_val = 2.0;" not in result


class TestLoadShaderSourceMissingInclude:
    """Test 4: Missing include file raises FileNotFoundError."""

    def test_missing_include_raises(self, tmp_path, monkeypatch):
        shader_dir = _create_shader_dir(tmp_path)
        (shader_dir / "test.frag").write_text(
            '#version 430\n#include "nonexistent.glsl"\nvoid main() {}\n'
        )

        from bigbangsim.rendering import shader_loader

        monkeypatch.setattr(shader_loader, "SHADER_DIR", shader_dir)

        with pytest.raises(FileNotFoundError, match="nonexistent.glsl"):
            shader_loader.load_shader_source("test.frag")


class TestLoadShaderSourceMultipleIncludes:
    """Test 5: Multiple #include directives are all resolved."""

    def test_multiple_includes_resolved(self, tmp_path, monkeypatch):
        shader_dir = _create_shader_dir(tmp_path)
        (shader_dir / "include" / "common.glsl").write_text(
            "uniform float u_dt;\n"
        )
        (shader_dir / "include" / "noise.glsl").write_text(
            "float snoise(vec2 v) { return 0.0; }\n"
        )
        (shader_dir / "test.comp").write_text(
            '#version 430\n#include "common.glsl"\n#include "noise.glsl"\nvoid main() {}\n'
        )

        from bigbangsim.rendering import shader_loader

        monkeypatch.setattr(shader_loader, "SHADER_DIR", shader_dir)

        result = shader_loader.load_shader_source("test.comp")
        assert "uniform float u_dt;" in result
        assert "float snoise(vec2 v)" in result
        assert '#include' not in result


class TestGetShaderDir:
    """Test 6: get_shader_dir() returns Path to bigbangsim/shaders/."""

    def test_returns_shaders_path(self):
        from bigbangsim.rendering.shader_loader import get_shader_dir

        result = get_shader_dir()
        assert isinstance(result, Path)
        assert result.name == "shaders"
        assert result.parent.name == "bigbangsim"
