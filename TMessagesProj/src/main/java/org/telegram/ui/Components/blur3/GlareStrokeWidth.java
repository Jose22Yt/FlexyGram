package org.telegram.ui.Components.blur3;

/** Relative stroke width only; does not alter brightness, blur radius or opacity. */
public final class GlareStrokeWidth {
    public static final int MIN = 5, MAX = 30, DEFAULT = 10;
    private GlareStrokeWidth() {}
    public static float factor() { return app.exteraless.appearance.AppearanceConfig.glassOutlineWidth() / 10f; }
}
