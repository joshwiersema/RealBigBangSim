#version 430

#include "colormap.glsl"

in vec4 v_color;
in float v_life;
out vec4 fragColor;

uniform float u_temperature;

void main() {
    // Soft circular particle (distance from point center)
    vec2 coord = gl_PointCoord - vec2(0.5);
    float dist = length(coord);
    if (dist > 0.5) discard;

    float alpha = 1.0 - smoothstep(0.0, 0.5, dist);
    vec3 temp_color = temperature_to_color(u_temperature);

    // Blend vertex color with temperature-derived color
    vec3 final_color = mix(v_color.rgb, temp_color, 0.6);

    // Boost brightness for additive blending glow effect
    final_color *= 1.5 * v_life;

    fragColor = vec4(final_color, alpha * v_life);
}
