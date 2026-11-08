package app.exteraless.player;

/** Scroll-owned geometry: the return path is exactly the forward path, with no queued animator. */
public final class OrbitMotion {
    private OrbitMotion() {}
    public static float fraction(float scroll, float distance) {
        float t = Math.max(0f, Math.min(1f, scroll / Math.max(1f, distance)));
        return t * t * (3f - 2f * t);
    }
    public static float mix(float start, float end, float fraction) { return start + (end - start) * fraction; }
}
