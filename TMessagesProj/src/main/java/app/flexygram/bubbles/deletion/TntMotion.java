/* Adapted from Bubble Fracture v1.0 by @larrat23, supplied with this change.
 * Original attribution retained; see CREDITS.md. */

package app.flexygram.bubbles.deletion;

/** Two smooth fuse flashes, followed by a fast impulse with a soft landing. */
public final class TntMotion {
    private TntMotion() {}

    public static float flash(float fuseProgress) {
        float t = FractureMotionMath.unit(fuseProgress);
        if (t == 0f || t == 1f) return 0f;
        float wave = (float) Math.sin(2f * Math.PI * t);
        return wave * wave;
    }

    public static float travel(float progress) {
        float t = FractureMotionMath.unit(progress);
        return 1f - (1f-t)*(1f-t)*(1f-t);
    }

    public static float fade(float progress) {
        return 1f - FractureMotionMath.smooth((progress - .30f) / .70f);
    }

    public static int fuseDuration(int requested, int duration) {
        return Math.max(180, Math.min(requested, Math.round(duration * .40f)));
    }
}
