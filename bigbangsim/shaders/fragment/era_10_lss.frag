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
    // Sharp glow for mature cosmic web nodes
    float glow = sharp_glow(gl_PointCoord, 0.1, 0.4);

    // Density-mapped coloring with higher contrast than galaxy formation
    float density = v_color.r;
    float density_mix = density * v_life * u_collapsed_fraction;

    // Purple-blue filament coloring via density map
    vec3 density_tint = density_to_color(clamp(density_mix, 0.0, 1.0));

    // Warm golden-white highlights at cluster nodes (highest density particles)
    vec3 cluster_highlight = vec3(0.8, 0.7, 0.5);
    float cluster_factor = smoothstep(0.7, 0.95, v_life) * smoothstep(0.5, 1.0, density);

    vec3 color = mix(u_base_color, u_accent_color, clamp(density_mix, 0.0, 1.0));
    color = mix(color, density_tint, 0.4);
    color = mix(color, cluster_highlight, cluster_factor);

    color *= u_brightness * v_life;

    fragColor = vec4(color, glow * v_life);
}
