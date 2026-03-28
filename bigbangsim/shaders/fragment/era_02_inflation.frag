#version 430

#include "colormap.glsl"
#include "era_utils.glsl"

in vec4 v_color;
in float v_life;
out vec4 fragColor;

uniform vec3 u_base_color;
uniform vec3 u_accent_color;
uniform float u_brightness;

void main() {
    // Elongated glow suggesting explosive outward motion
    vec2 coord = gl_PointCoord - vec2(0.5);
    coord.x *= 0.7;  // Slight horizontal elongation
    float dist = length(coord);
    if (dist > 0.5) discard;
    float glow = 1.0 - smoothstep(0.0, 0.4, dist);

    // Bright yellow-white with subtle accent mix
    vec3 color = mix(u_base_color, u_accent_color, 0.2);

    // Strong bloom via high brightness
    color *= u_brightness * v_life;

    fragColor = vec4(color, glow * v_life);
}
