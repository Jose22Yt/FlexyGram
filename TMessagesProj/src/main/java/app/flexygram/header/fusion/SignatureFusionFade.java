package app.flexygram.header.fusion;

/**
 * Full-card portrait fade: predominantly opaque on the extreme photo edge,
 * below 4.1% alpha at the FIRST label pixel, and almost invisible across
 * the rest of the card. No per-frame bitmaps or animation callbacks.
 */
public final class SignatureFusionFade {
    static final int[] LTR_COLORS = {
        0xFFFFFFFF, 0xF0FFFFFF, 0xB7FFFFFF, 0x4DFFFFFF,
        0x0AFFFFFF, 0x04FFFFFF, 0x01FFFFFF, 0x00FFFFFF
    };
    static final int[] RTL_COLORS = {
        0x00FFFFFF, 0x01FFFFFF, 0x04FFFFFF, 0x0AFFFFFF,
        0x4DFFFFFF, 0xB7FFFFFF, 0xF0FFFFFF, 0xFFFFFFFF
    };
    // Default stop reference for existing consumers. Real geometry uses fillStops().
    static final float[] LTR_STOPS = {0f,.072f,.176f,.292f,.40f,.61f,.832f,1f};
    static final float[] RTL_STOPS = {0f,.168f,.39f,.60f,.708f,.824f,.928f,1f};
    private SignatureFusionFade() { }
    public static float portraitWidth(float centerWidth, float density) {
        if (centerWidth <= 0 || density <= 0) return 0f;
        return Math.min(Math.max(0f, centerWidth - 8f * density),
                Math.max(80f * density, centerWidth * .92f));
    }
    public static float fadeStartInset(float photoWidth, float density) {
        return Math.min(Math.max(0f, photoWidth * .16f), 12f * density);
    }
    public static float safeStop(float start, float end, float textEdge, boolean rtl) {
        float width = Math.abs(end - start);
        if (!(width > 0)) return .5f;
        float t = rtl ? (start - textEdge) / width : (textEdge - start) / width;
        return Math.max(.12f, Math.min(.86f, t));
    }
    public static void fillStops(float safe, boolean rtl, float[] out) {
        if (out == null || out.length != 8)
            throw new IllegalArgumentException("eight stop slots required");
        safe = Math.max(.12f, Math.min(.86f, safe));
        if (!rtl) {
            out[0]=0f; out[1]=safe*.18f; out[2]=safe*.44f; out[3]=safe*.73f;
            out[4]=safe; out[5]=safe+(1f-safe)*.35f;
            out[6]=safe+(1f-safe)*.72f; out[7]=1f;
        } else {
            out[0]=0f; out[1]=(1f-safe)*.28f; out[2]=(1f-safe)*.65f;
            out[3]=1f-safe; out[4]=1f-safe*.73f; out[5]=1f-safe*.44f;
            out[6]=1f-safe*.18f; out[7]=1f;
        }
    }
    /** Host-side measurement helper; never called by the frame renderer. */
    public static float opacityAt(float fraction, float safeStop) {
        float[] values = new float[8];
        fillStops(safeStop, false, values);
        float t = Math.max(0f, Math.min(1f, fraction));
        if (t <= 0f) return 1f;
        if (t >= 1f) return 0f;
        for (int i=1; i<values.length; i++) if (t <= values[i]) {
            float p = (t-values[i-1]) / (values[i]-values[i-1]);
            int a=LTR_COLORS[i-1] >>> 24, b=LTR_COLORS[i] >>> 24;
            return (a+(b-a)*p)/255f;
        }
        return 0f;
    }
    public static float opacityAt(float fraction) { return opacityAt(fraction, .40f); }
}
