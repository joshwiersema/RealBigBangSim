#version 430

#include "colormap.glsl"
#include "era_utils.glsl"

in vec4 v_color;
in float v_life;
out vec4 fragColor;

uniform vec3 u_base_color;
uniform vec3 u_accent_color;
uniform float u_brightness;
uniform float u_ionization_fraction;

void main() {
    // Soft glow for plasma/gas transition
    float glow = soft_glow(gl_PointCoord, 0.5);

    // THE most dramatic shader: opaque plasma -> transparent dark space
    // ionization_fraction: 1.0 = fully ionized plasma, 0.0 = neutral gas (transparent)

    // Alpha modulated by ionization fraction
    float alpha = glow * mix(0.05, 1.0, u_ionization_fraction);

    // Color transitions: warm orange plasma (x=1) -> dark (x=0)
    vec3 color = mix(u_accent_color, u_base_color, u_ionization_fraction);

    // Brightness modulated by ionization state
    color *= u_brightness * mix(0.1, 1.0, u_ionization_fraction) * v_life;

    fragColor = vec4(color, alpha * v_life);
}
