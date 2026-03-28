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
    // Soft glow for unified force field
    float glow = soft_glow(gl_PointCoord, 0.5);

    // Slow noise animation for force field undulations
    float noise_val = snoise(gl_PointCoord * 3.0 + vec2(u_era_progress * 0.5));
    float noise_factor = noise_val * 0.5 + 0.5;

    // Warm gold to cool lavender gradient
    vec3 color = mix(u_base_color, u_accent_color, noise_factor);

    // Moderate HDR
    color *= u_brightness * v_life * 0.3;

    fragColor = vec4(color, glow * v_life);
}
