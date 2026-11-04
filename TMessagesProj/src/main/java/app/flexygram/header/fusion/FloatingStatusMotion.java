package app.flexygram.header.fusion;

/** One bounded reveal per attachment/style activation. No animator, timer or retained View. */
public final class FloatingStatusMotion {
    public static final long DURATION_MS = 220;
    private long start = -1;
    private boolean finished;
    public void reset() { start = -1; finished = false; }
    public float progress(long now, boolean animationsEnabled) {
        return progress(now, animationsEnabled, DURATION_MS);
    }
    public float progress(long now, boolean animationsEnabled, long duration) {
        if (!animationsEnabled || finished || duration <= 0) { finished = true; return 1f; }
        if (start < 0) start = now;
        float t = Math.max(0f, Math.min(1f, (now - start) / (float) duration));
        if (t >= 1f) finished = true;
        float remaining = 1f - t;
        return 1f - remaining * remaining * remaining;
    }
}
