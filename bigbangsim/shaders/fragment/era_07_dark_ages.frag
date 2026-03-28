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
    // Soft glow for diffuse neutral gas
    float glow = soft_glow(gl_PointCoord, 0.5);

    // Subtle noise-driven density perturbations (seeds of structure)
    float noise_val = snoise(gl_PointCoord * 2.0 + vec2(u_era_progress));
    float noise_factor = noise_val * 0.5 + 0.5;

    // Near-black with very faint blue density variations
    vec3 color = mix(u_base_color, u_accent_color, noise_factor * 0.3);

    // Extremely low brightness but NOT invisible
    color *= u_brightness * v_life;

    fragColor = vec4(color, glow * v_life);
}
