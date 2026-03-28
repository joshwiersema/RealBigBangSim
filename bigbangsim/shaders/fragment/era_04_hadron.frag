#version 430

#include "colormap.glsl"
#include "era_utils.glsl"
#include "noise.glsl"

in vec4 v_color;
in float v_life;
out vec4 fragColor;

uniform vec3 u_base_color;
uniform vec3 u_accent_color;
uniform float u_brightness;
uniform float u_era_progress;

void main() {
    // Sharper edges = discrete particles forming from plasma
    float glow = sharp_glow(gl_PointCoord, 0.2, 0.45);

    // Slight noise modulation, less than QGP
    float noise_val = snoise(gl_PointCoord * 2.0 + vec2(u_era_progress * 0.8));
    float noise_factor = noise_val * 0.5 + 0.5;

    // Orange-amber, less saturated than QGP
    vec3 color = mix(u_base_color, u_accent_color, noise_factor * 0.3);

    color *= u_brightness * v_life;

    fragColor = vec4(color, glow * v_life);
}
