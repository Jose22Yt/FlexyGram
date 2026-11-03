package app.exteraless.appearance;

/** Stable contrast over every possible backdrop; no screen capture or frame-dependent color flip. */
public final class GlassContrastPolicy {
    public static final int MIN_LIGHT_ALPHA = 184;
    private GlassContrastPolicy() {}

    public static int lightSurface(int color, int requestedAlpha) {
        int alpha = Math.max(MIN_LIGHT_ALPHA, Math.min(255, requestedAlpha));
        int base = color | 0xFF000000;
        int surface = (base & 0xFFFFFF) | (alpha << 24);
        if (luminance(composite(surface, 0xFF000000)) >= .30) return surface;
        // A custom light theme may supply a dark tint. Lift only as far as needed.
        double lo = 0, hi = 1;
        for (int i = 0; i < 12; i++) {
            double amount = (lo + hi) / 2;
            int candidate = (mix(base, 0xFFFFFFFF, amount) & 0xFFFFFF) | (alpha << 24);
            if (luminance(composite(candidate, 0xFF000000)) >= .30) hi = amount;
            else lo = amount;
        }
        return (mix(base, 0xFFFFFFFF, hi) & 0xFFFFFF) | (alpha << 24);
    }

    public static int readableInk(int original, int surface) {
        int color = original | 0xFF000000;
        if (minimumContrast(color, surface) >= 4.5) return color;
        int target = minimumContrast(0xFF000000, surface) >= minimumContrast(0xFFFFFFFF, surface)
                ? 0xFF000000 : 0xFFFFFFFF;
        double lo = 0, hi = 1;
        for (int i = 0; i < 12; i++) {
            double amount = (lo + hi) / 2;
            if (minimumContrast(mix(color, target, amount), surface) >= 4.5) hi = amount;
            else lo = amount;
        }
        return mix(color, target, hi);
    }

    public static double minimumContrast(int ink, int surface) {
        return Math.min(contrast(ink, composite(surface, 0xFF000000)),
                contrast(ink, composite(surface, 0xFFFFFFFF)));
    }

    public static int composite(int front, int back) {
        int alpha = front >>> 24;
        int r = (((front >>> 16) & 255) * alpha + ((back >>> 16) & 255) * (255 - alpha) + 127) / 255;
        int g = (((front >>> 8) & 255) * alpha + ((back >>> 8) & 255) * (255 - alpha) + 127) / 255;
        int b = ((front & 255) * alpha + (back & 255) * (255 - alpha) + 127) / 255;
        return 0xFF000000 | (r << 16) | (g << 8) | b;
    }

    public static double contrast(int first, int second) {
        double a = luminance(first), b = luminance(second);
        return (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
    }

    private static double luminance(int color) {
        return .2126 * linear((color >>> 16) & 255) + .7152 * linear((color >>> 8) & 255) + .0722 * linear(color & 255);
    }
    private static double linear(int channel) {
        double value = channel / 255.0;
        return value <= .04045 ? value / 12.92 : Math.pow((value + .055) / 1.055, 2.4);
    }
    private static int mix(int from, int to, double amount) {
        int r = (int)Math.round(((from >>> 16) & 255) * (1 - amount) + ((to >>> 16) & 255) * amount);
        int g = (int)Math.round(((from >>> 8) & 255) * (1 - amount) + ((to >>> 8) & 255) * amount);
        int b = (int)Math.round((from & 255) * (1 - amount) + (to & 255) * amount);
        return 0xFF000000 | (r << 16) | (g << 8) | b;
    }
}
