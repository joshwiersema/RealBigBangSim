#version 430

in vec2 v_texcoord;
out vec4 fragColor;

uniform sampler2D u_scene;
uniform float u_threshold;  // Default 1.0

void main() {
    vec3 color = texture(u_scene, v_texcoord).rgb;
    float brightness = dot(color, vec3(0.2126, 0.7152, 0.0722));
    fragColor = (brightness > u_threshold) ? vec4(color, 1.0) : vec4(0.0, 0.0, 0.0, 1.0);
}
