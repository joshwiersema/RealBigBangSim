#version 430

in vec2 v_texcoord;
out vec4 fragColor;

uniform sampler2D u_scene;
uniform sampler2D u_bloom;
uniform float u_exposure;        // Default 1.0
uniform float u_bloom_strength;  // Default 0.3

void main() {
    const float gamma = 2.2;
    vec3 hdrColor = texture(u_scene, v_texcoord).rgb;
    vec3 bloomColor = texture(u_bloom, v_texcoord).rgb;

    hdrColor += bloomColor * u_bloom_strength;

    // Reinhard-style exposure tone mapping
    vec3 mapped = vec3(1.0) - exp(-hdrColor * u_exposure);

    // Gamma correction
    mapped = pow(mapped, vec3(1.0 / gamma));

    fragColor = vec4(mapped, 1.0);
}
