#version 430

#include "colormap.glsl"
#include "era_utils.glsl"

in vec4 v_color;
in float v_life;
out vec4 fragColor;

uniform vec3 u_base_color;
uniform vec3 u_accent_color;
uniform float u_brightness;
uniform float u_collapsed_fraction;

void main() {
    // Sharp glow for discrete gravitationally-bound structures
    float glow = sharp_glow(gl_PointCoord, 0.15, 0.4);

    // Density-mapped coloring via v_color.r as proxy for local density
    float density = v_color.r;

    // Low density: dark purple (base), High density: bright blue-white (accent)
    float density_mix = density * v_life * u_collapsed_fraction;
    vec3 color = mix(u_base_color, u_accent_color, clamp(density_mix, 0.0, 1.0));

    // Use density_to_color for additional color variation
    vec3 density_tint = density_to_color(density);
    color = mix(color, density_tint, 0.3);

    color *= u_brightness * v_life;

    fragColor = vec4(color, glow * v_life);
}
