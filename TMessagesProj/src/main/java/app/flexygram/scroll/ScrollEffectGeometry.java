/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.scroll;

/** Reusable transform output. Coordinates are normalized to the visible viewport, for parity. */
public final class ScrollEffectGeometry {
    public float rotationX, rotationY, rotationZ, translationX, translationY, scaleX = 1f;

    public void calculate(int style, float position, float width, float height,
                          float amount, float direction, float intensity) {
        rotationX = rotationY = rotationZ = translationX = translationY = 0;
        scaleX = 1f;
        if (width <= 0 || height <= 0 || style < 1 || style > 3) return;
        float p = Math.max(-1f, Math.min(1f, position));
        float strength = Math.max(0, Math.min(1f, amount)) * Math.max(0, Math.min(1.3f, intensity));
        if (style == 1) {
            rotationX = -p * 40f * strength;
            scaleX = 1f - .030f * p * p * strength;
            // Use the displayed angle for both tilt and projection. The old linear blend of
            // full-angle projection and partial-angle tilt could compress centers too far.
            double angle = p * Math.toRadians(40) * strength;
            double sinc = Math.abs(angle) < .0001 ? 1 - angle * angle / 6 : Math.sin(angle) / angle;
            translationY = (float) ((sinc - 1) * p * height * .5);
        } else if (style == 2) {
            rotationX = direction * 9f * strength;
            rotationY = -direction * 4.5f * strength;
            rotationZ = direction * .7f * strength;
        } else {
            // A broad, flat center; entering/leaving rows travel from opposite sides.
            float edge = Math.max(0, (Math.abs(p) - .15f) / .85f);
            edge = edge * edge * (3f - 2f * edge);
            translationX = Math.signum(p) * direction * edge * width * .12f * strength;
        }
    }
}
