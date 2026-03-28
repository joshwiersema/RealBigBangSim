#version 430

#include "colormap.glsl"

in vec4 v_color;
in float v_life;
out vec4 fragColor;

uniform float u_density_normalized;  // 0-1 normalized density

void main() {
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    if (dist > 0.5) discard;

    float alpha = 1.0 - smoothstep(0.3, 0.5, dist);  // Sharper falloff than hot
    vec3 cool_color = density_to_color(u_density_normalized);

    vec3 final_color = mix(v_color.rgb, cool_color, 0.4);
    final_color *= v_life;

    fragColor = vec4(final_color, alpha * v_life * 0.8);
}
