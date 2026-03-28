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
    // Soft circular glow for pure energy field
    float glow = soft_glow(gl_PointCoord, 0.5);

    // High-frequency noise modulation for seething energy
    float noise_val = snoise(gl_PointCoord * 4.0 + vec2(u_era_progress));
    float noise_factor = noise_val * 0.5 + 0.5;  // Remap to [0, 1]

    // Mix base (blinding white) and accent by noise
    vec3 color = mix(u_base_color, u_accent_color, noise_factor);

    // HDR brightness for bloom (values >> 1.0)
    color *= u_brightness * v_life;

    fragColor = vec4(color, glow * v_life);
}
