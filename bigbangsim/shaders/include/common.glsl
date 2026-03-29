// Common uniforms for particle system
// Shared across compute, vertex, and fragment shaders via include directive

uniform float u_dt;
uniform float u_temperature;
uniform float u_scale_factor;
uniform uint u_particle_count;
uniform int u_era;
uniform float u_era_progress;

// Per-era behavior uniforms (set from EraVisualConfig)
uniform float u_expansion_rate;
uniform float u_noise_strength;
uniform float u_gravity_strength;
uniform float u_damping;

// Containment radius -- particles beyond this distance from origin
// are respawned nearby to keep the cloud visible across all eras.
uniform float u_containment_radius;

// Particle struct matching SSBO layout (all vec4 for std430 alignment safety)
struct Particle {
    vec4 position;  // xyz = position, w = life (0.0-1.0)
    vec4 velocity;  // xyz = velocity, w = type (float-encoded int)
    vec4 color;     // rgba
};
