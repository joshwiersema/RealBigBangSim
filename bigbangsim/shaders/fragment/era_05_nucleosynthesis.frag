#version 430

#include "colormap.glsl"
#include "era_utils.glsl"

in vec4 v_color;
in float v_life;
out vec4 fragColor;

uniform vec3 u_base_color;
uniform vec3 u_accent_color;
uniform float u_brightness;
uniform float u_helium_fraction;

void main() {
    // Soft glow for nuclear fusion reactions
    float glow = soft_glow(gl_PointCoord, 0.45);

    // Particle color driven by nuclei type via v_life
    // When helium fraction is high (BBN active), accent color represents He-4
    float he_mix = clamp(u_helium_fraction / 0.25, 0.0, 1.0);  // Normalize to ~0.25 peak

    // Use v_life to simulate different nuclei -- high life = newly formed helium
    float nuclei_factor = smoothstep(0.4, 0.8, v_life) * he_mix;

    // Green-gold base with accent for helium-rich particles
    vec3 color = mix(u_base_color, u_accent_color, nuclei_factor);

    // Brief bright flashes for active fusion
    float flash = smoothstep(0.7, 0.9, v_life) * 0.5 + 1.0;
    color *= u_brightness * v_life * flash;

    fragColor = vec4(color, glow * v_life);
}
