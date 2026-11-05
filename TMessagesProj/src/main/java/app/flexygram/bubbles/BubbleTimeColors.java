package app.flexygram.bubbles;

import app.exteraless.appearance.GlassContrastPolicy;

/** Secondary timestamp ink for automatically generated outgoing gradient themes. */
public final class BubbleTimeColors {
    private BubbleTimeColors() {}

    // Resolve only when the theme changes, never from message drawing or scrolling.
    public static int gradientSecondary(int primary, int surface) {
        primary |= 0xFF000000;
        surface |= 0xFF000000;
        int secondary = mix(primary, surface, .28);
        if (GlassContrastPolicy.contrast(secondary, surface) >= 3.0) return secondary;
        // Keep the existing text polarity on unusual low-contrast gradients.
        double low = 0, high = .28;
        for (int i = 0; i < 12; i++) {
            double amount = (low + high) / 2;
            if (GlassContrastPolicy.contrast(mix(primary, surface, amount), surface) >= 3.0)
                low = amount;
            else high = amount;
        }
        return mix(primary, surface, low);
    }

    private static int mix(int primary, int surface, double amount) {
        int result = 0xFF000000;
        for (int shift = 0; shift <= 16; shift += 8) {
            int from = (primary >>> shift) & 255, to = (surface >>> shift) & 255;
            result |= (int) Math.round(from + (to - from) * amount) << shift;
        }
        return result;
    }
}
