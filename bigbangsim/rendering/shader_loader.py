"""Shader loading with #include directive preprocessing.

Provides a Python-side shader preprocessor that resolves #include directives
by concatenating include files from bigbangsim/shaders/include/ into the
shader source before passing it to ModernGL for compilation.

Include resolution is single-level only: includes within included files are
NOT recursively resolved. This keeps the preprocessor simple and predictable.

Usage:
    from bigbangsim.rendering.shader_loader import load_shader_source
    source = load_shader_source("compute/particle_update.comp")
    program = ctx.compute_shader(source)
"""
import re
from pathlib import Path

# Root directory for all shader files
SHADER_DIR: Path = Path(__file__).parent.parent / "shaders"

# Regex matching #include "filename.glsl" directives
_INCLUDE_RE = re.compile(r'#include\s+"([^"]+)"')


def get_shader_dir() -> Path:
    """Return the path to the shader directory (bigbangsim/shaders/).

    Returns:
        Path to the shader directory.
    """
    return SHADER_DIR


def load_shader_source(shader_path: str) -> str:
    """Load a shader source file, resolving #include directives.

    Reads the shader file at SHADER_DIR / shader_path and replaces any
    ``#include "filename"`` directives with the content of the corresponding
    file from SHADER_DIR / "include" / filename.

    Include resolution is single-level: if an included file itself contains
    #include directives, those are left as-is (not recursively resolved).

    Args:
        shader_path: Relative path from SHADER_DIR (e.g. "compute/particle_update.comp").

    Returns:
        The fully assembled shader source string with includes inlined.

    Raises:
        FileNotFoundError: If the shader file or any referenced include file
            does not exist.
    """
    full_path = SHADER_DIR / shader_path
    source = full_path.read_text()

    include_dir = SHADER_DIR / "include"

    def _replace_include(match: re.Match) -> str:
        include_name = match.group(1)
        include_path = include_dir / include_name
        if not include_path.exists():
            raise FileNotFoundError(
                f"Shader include file not found: {include_path} "
                f"(referenced from {shader_path})"
            )
        return include_path.read_text()

    return _INCLUDE_RE.sub(_replace_include, source)
