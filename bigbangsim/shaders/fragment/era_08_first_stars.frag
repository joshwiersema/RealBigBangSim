#version 430

#include "colormap.glsl"
#include "era_utils.glsl"

in vec4 v_color;
in float v_life;
out vec4 fragColor;

uniform vec3 u_base_color;
uniform vec3 u_accent_color;
uniform float u_brightness;
uniform float u_reionization_frac;

void main() {
    // Bimodal brightness: stars vs gas
    // As reionization progresses, threshold drops so more particles brighten
    float star_threshold = mix(0.95, 0.6, u_reionization_frac);
    bool is_star = v_life > star_threshold;

    float glow;
    vec3 color;

    if (is_star) {
        // Stars: bright blue-white, large soft glow
        glow = soft_glow(gl_PointCoord, 0.5);
        color = u_accent_color * 3.0;
        color *= u_brightness * v_life;
    } else {
        // Gas: dim base color, sharp edges
        glow = sharp_glow(gl_PointCoord, 0.2, 0.4);
        color = u_base_color * 0.2;
        color *= u_brightness * v_life;
    }

    fragColor = vec4(color, glow * v_life);
}
