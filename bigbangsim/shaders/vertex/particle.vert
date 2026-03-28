#version 430

uniform mat4 u_projection;
uniform mat4 u_view;
uniform float u_point_scale;  // Default 50.0

struct Particle {
    vec4 position;
    vec4 velocity;
    vec4 color;
};

layout(std430, binding = 0) readonly buffer Particles {
    Particle particles[];
};

out vec4 v_color;
out float v_life;

void main() {
    Particle p = particles[gl_VertexID];
    gl_Position = u_projection * u_view * vec4(p.position.xyz, 1.0);
    gl_PointSize = u_point_scale / max(gl_Position.w, 0.01);
    v_color = p.color;
    v_life = p.position.w;
}
