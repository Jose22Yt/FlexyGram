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
            rotationX = -p * 58f * strength;
            scaleX = 1f - .065f * p * p * strength;
            // Cylinder projection also moves the row's center, closing the gaps caused by tilt.
            double angle = p * Math.toRadians(58);
            translationY = (float) ((Math.sin(angle) / Math.toRadians(58) - p) * height * .5 * strength);
        } else if (style == 2) {
            rotationX = direction * 13f * strength;
            rotationY = -direction * 7f * strength;
            rotationZ = direction * 1.8f * strength;
        } else {
            // A broad, flat center; entering/leaving rows travel from opposite sides.
            float edge = Math.max(0, (Math.abs(p) - .15f) / .85f);
            edge = edge * edge * (3f - 2f * edge);
            translationX = Math.signum(p) * direction * edge * width * .18f * strength;
        }
    }
}
