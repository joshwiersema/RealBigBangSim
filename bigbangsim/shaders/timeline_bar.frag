#version 430

in vec3 v_color;
out vec4 fragColor;

uniform float u_progress;      // 0.0 to 1.0 overall progress
uniform float u_era_progress;  // 0.0 to 1.0 within current era

void main() {
    // Slight brightness boost near the playback position
    float glow = smoothstep(0.0, 0.05, abs(gl_FragCoord.x / 1280.0 - u_progress));
    float alpha = mix(1.0, 0.75, glow);
    fragColor = vec4(v_color * (1.0 + 0.2 * u_era_progress), alpha);
}
