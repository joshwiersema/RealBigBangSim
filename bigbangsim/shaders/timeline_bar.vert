#version 430

in vec2 in_position;
in vec3 in_color;

out vec3 v_color;

void main() {
    gl_Position = vec4(in_position, 0.0, 1.0);
    v_color = in_color;
}
