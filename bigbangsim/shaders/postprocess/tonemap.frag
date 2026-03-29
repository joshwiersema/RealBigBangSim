#version 430

in vec2 v_texcoord;
out vec4 fragColor;

uniform sampler2D u_scene;
uniform sampler2D u_bloom;
uniform float u_exposure;        // Default 1.0
uniform float u_bloom_strength;  // Default 0.3

// ACES filmic tone mapping (Narkowicz 2015 approximation).
// Handles extreme HDR values gracefully with a natural S-curve:
// dark tones stay dark, mid-tones are preserved, highlights
// compress smoothly toward white without hard clipping.
vec3 ACESFilm(vec3 x) {
    float a = 2.51;
    float b = 0.03;
    float c = 2.43;
    float d = 0.59;
    float e = 0.14;
    return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
}

void main() {
    const float gamma = 2.2;
    vec3 hdrColor = texture(u_scene, v_texcoord).rgb;
    vec3 bloomColor = texture(u_bloom, v_texcoord).rgb;

    hdrColor += bloomColor * u_bloom_strength;

    // Apply exposure before tone mapping
    hdrColor *= u_exposure;

    // ACES filmic tone mapping — preserves color detail across
    // the full dynamic range from the Planck epoch's 10^32 K
    // singularity down to the Dark Ages' near-zero luminosity.
    vec3 mapped = ACESFilm(hdrColor);

    // Gamma correction
    mapped = pow(mapped, vec3(1.0 / gamma));

    fragColor = vec4(mapped, 1.0);
}
