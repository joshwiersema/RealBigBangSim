// Temperature and density to RGB color mapping utilities
// Used by fragment shaders to visualize physical state as color

// Map Kelvin temperature to approximate blackbody RGB color
// Simplified Planckian locus approximation for real-time rendering
vec3 temperature_to_color(float temp_kelvin) {
    // Clamp to reasonable range
    float T = clamp(temp_kelvin, 1000.0, 40000.0);

    if (T < 3500.0) {
        // Red-orange: hot embers to warm flame
        float t = T / 3500.0;
        return vec3(1.0, 0.4 + 0.3 * t, 0.1);
    } else if (T < 6500.0) {
        // Warm white: orange-white to pure white
        float t = (T - 3500.0) / 3000.0;
        return mix(vec3(1.0, 0.7, 0.3), vec3(1.0, 1.0, 1.0), t);
    } else if (T < 10000.0) {
        // Cool white: white to blue-white
        float t = (T - 6500.0) / 3500.0;
        return mix(vec3(1.0, 1.0, 1.0), vec3(0.7, 0.8, 1.0), t);
    } else {
        // Blue-white: very hot stars / early universe
        float t = clamp((T - 10000.0) / 30000.0, 0.0, 1.0);
        return mix(vec3(0.7, 0.8, 1.0), vec3(0.6, 0.7, 1.0), t);
    }
}

// Map normalized density (0-1) to blue-purple palette for cool/late eras
// Used for matter-dominated epochs (dark ages, structure formation)
vec3 density_to_color(float density_normalized) {
    float d = clamp(density_normalized, 0.0, 1.0);

    // Low density: deep blue (voids)
    // Medium density: purple (filaments)
    // High density: bright blue-white (galaxy clusters)
    vec3 low = vec3(0.05, 0.05, 0.2);    // Deep space blue
    vec3 mid = vec3(0.3, 0.1, 0.5);      // Purple filaments
    vec3 high = vec3(0.5, 0.6, 1.0);     // Bright clusters

    if (d < 0.5) {
        return mix(low, mid, d * 2.0);
    } else {
        return mix(mid, high, (d - 0.5) * 2.0);
    }
}
