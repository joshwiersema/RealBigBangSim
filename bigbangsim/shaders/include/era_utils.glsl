// Shared utility functions for per-era fragment shaders
// Provides common glow/falloff patterns and easing functions

// Soft circular glow falloff for point sprites
float soft_glow(vec2 point_coord, float softness) {
    float dist = length(point_coord - vec2(0.5));
    if (dist > 0.5) discard;
    return 1.0 - smoothstep(0.0, softness, dist);
}

// Sharp circular falloff for distinct particle edges
float sharp_glow(vec2 point_coord, float inner, float outer) {
    float dist = length(point_coord - vec2(0.5));
    if (dist > 0.5) discard;
    return 1.0 - smoothstep(inner, outer, dist);
}

// Smooth easing for transition blend factors
float smoothstep_ease(float t) {
    t = clamp(t, 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);
}
