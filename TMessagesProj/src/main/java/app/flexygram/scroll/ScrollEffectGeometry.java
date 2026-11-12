/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.scroll;

/** A fixed cylinder. Only viewport position and the chosen curvature affect the projection. */
public final class ScrollEffectGeometry {
    public float rotationX, translationY, scaleX = 1f;

    public void calculate(float position, float height, int curvature) {
        rotationX = translationY = 0; scaleX = 1;
        if (height <= 0) return;
        float curve = Math.max(0, Math.min(100, curvature)) / 100f;
        float p = Math.max(-1, Math.min(1, position));
        rotationX = -p * 65f * curve;
        scaleX = 1f - .045f * p * p * curve;
        double angle = p * Math.toRadians(65) * curve;
        double sinc = Math.abs(angle) < .0001 ? 1 - angle * angle / 6 : Math.sin(angle) / angle;
        translationY = (float) ((sinc - 1) * p * height * .5);
    }
}
