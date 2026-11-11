package app.exteraless.player;

public final class Spring {

    private final float stiffness;
    private final float damping;
    private final float epsilon;
    public float value;
    public float target;
    private float velocity;

    public Spring(float value, float stiffness, float dampingRatio, float epsilon) {
        this.value = value;
        this.target = value;
        this.stiffness = stiffness;
        this.damping = 2f * dampingRatio * (float) Math.sqrt(stiffness);
        this.epsilon = epsilon;
    }

    public void snap(float v) {
        value = v;
        target = v;
        velocity = 0;
    }

    /** Transfers a live interaction without dropping its momentum. */
    public float velocity() { return velocity; }

    public void setState(float position, float speed) {
        value = position;
        velocity = speed;
    }

    public boolean settled() {
        return Math.abs(value - target) < epsilon && Math.abs(velocity) < epsilon * 10f;
    }

    /** Exact damped motion for message interactions. Other callers retain the existing step().
     * Equal elapsed time produces the same trajectory at 60/90/120/144 Hz and on missed frames. */
    public boolean stepExact(float dt) {
        if (settled()) { value = target; velocity = 0f; return false; }
        if (!(dt > 0f) || !Float.isFinite(dt)) return true;
        double t = dt, offset = value - target, speed = velocity;
        double decay = damping * .5d;
        double discriminant = stiffness - decay * decay;
        double position, nextSpeed;
        if (Math.abs(discriminant) <= stiffness * .00001d) {
            double coefficient = speed + decay * offset;
            double attenuation = Math.exp(-decay * t);
            position = attenuation * (offset + coefficient * t);
            nextSpeed = attenuation * (speed - decay * coefficient * t);
        } else if (discriminant > 0d) {
            double frequency = Math.sqrt(discriminant);
            double angle = frequency * t;
            double sine = Math.sin(angle), cosine = Math.cos(angle);
            double attenuation = Math.exp(-decay * t);
            position = attenuation * (offset * cosine + (speed + decay * offset) / frequency * sine);
            nextSpeed = attenuation * (speed * cosine - (decay * speed + stiffness * offset) / frequency * sine);
        } else {
            double frequency = Math.sqrt(-discriminant);
            double slow = -decay + frequency, fast = -decay - frequency;
            double a = (speed - fast * offset) / (slow - fast), b = offset - a;
            double first = a * Math.exp(slow * t), second = b * Math.exp(fast * t);
            position = first + second;
            nextSpeed = slow * first + fast * second;
        }
        value = target + (float) position;
        velocity = (float) nextSpeed;
        if (settled()) { value = target; velocity = 0f; return false; }
        return true;
    }

    public boolean step(float dt) {
        if (settled()) {
            value = target;
            velocity = 0;
            return false;
        }
        float remaining = Math.min(dt, 0.064f);
        while (remaining > 0f) {
            float h = Math.min(remaining, 0.008f);
            float a = -stiffness * (value - target) - damping * velocity;
            velocity += a * h;
            value += velocity * h;
            remaining -= h;
        }
        if (settled()) {
            value = target;
            velocity = 0;
            return false;
        }
        return true;
    }
}
