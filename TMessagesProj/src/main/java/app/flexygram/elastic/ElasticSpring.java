package app.flexygram.elastic;

/** Critically bounded spring, independent of Android and frame rate. Units are fractions/dp. */
public final class ElasticSpring {
    public float value, velocity, target;
    public ElasticSpring(float value) { this.value = target = value; }
    public void step(float seconds) {
        // Small integration steps keep rapid interruptions/slow frames stable.
        float remaining = Math.min(Math.max(seconds, 0), .064f);
        while (remaining > 0) {
            float dt = Math.min(remaining, .008f);
            velocity += (420f * (target - value) - 31f * velocity) * dt;
            value += velocity * dt;
            remaining -= dt;
        }
        if (settled()) { value = target; velocity = 0; }
    }
    public boolean settled() { return Math.abs(value - target) < .0007f && Math.abs(velocity) < .006f; }
}
