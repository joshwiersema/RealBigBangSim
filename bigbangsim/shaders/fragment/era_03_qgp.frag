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
uniform float u_temperature;
uniform float u_era_progress;

void main() {
    // Soft glow for fluid-like plasma
    float glow = soft_glow(gl_PointCoord, 0.5);

    // Temperature factor for color intensity
    float temp_factor = clamp(u_temperature / 1e15, 0.0, 1.0);

    // Noise-driven color variation for fluid turbulence
    float noise_val = snoise(gl_PointCoord * 3.0 + vec2(u_era_progress * 2.0));
    float noise_factor = noise_val * 0.5 + 0.5;

    // Deep orange-red churning fluid
    vec3 color = mix(u_base_color, u_accent_color, temp_factor * 0.5 + noise_factor * 0.3);

    color *= u_brightness * v_life;

    fragColor = vec4(color, glow * v_life);
}
