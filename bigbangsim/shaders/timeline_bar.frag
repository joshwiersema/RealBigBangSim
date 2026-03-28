#version 430

in vec3 v_color;
out vec4 fragColor;

uniform float u_progress;      // 0.0 to 1.0 overall progress
uniform float u_era_progress;  // 0.0 to 1.0 within current era

void main() {
    fragColor = vec4(v_color, 0.85);
}
