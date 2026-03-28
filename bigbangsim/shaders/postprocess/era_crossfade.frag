#version 430

in vec2 v_texcoord;
out vec4 fragColor;

uniform sampler2D u_outgoing;    // Outgoing era's rendered scene
uniform sampler2D u_incoming;    // Incoming era's rendered scene
uniform float u_blend_factor;    // 0.0 = fully outgoing, 1.0 = fully incoming

void main() {
    vec4 out_color = texture(u_outgoing, v_texcoord);
    vec4 in_color = texture(u_incoming, v_texcoord);
    fragColor = mix(out_color, in_color, u_blend_factor);
}
