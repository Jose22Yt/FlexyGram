package app.flexygram.header.fusion;

/**
 * Pure-Java, Android-independent geometry for the OPTIONAL Signature Fusion chat header.
 * All coordinates are pixels. Density/available width are supplied by the host.
 * Used by the live optional header and its synthetic preview.
 *
 * Back/control placement is stable: changes to contact text and photo do not
 * move either side control. A fallback is exposed for very narrow windows.
 */
public final class SignatureFusionGeometry {
    public static final float EDGE_DP = 8f;
    public static final float GAP_DP = 8f;
    public static final float BACK_DP = 48f; // native 48dp hit target
    public static final float ACTION_HEIGHT_DP = 48f; // native 48dp hit target
    public static final float ACTION_WIDTH_DP = 96f; // two independently tappable 48dp slots
    public static final float ONE_ACTION_WIDTH_DP = 48f;
    // Only the painted surfaces shrink: actions remain 48dp tappable.
    public static final float BACK_VISUAL_DP = 42f;
    public static final float ACTION_VISUAL_HEIGHT_DP = 40f;
    public static final float ACTION_VISUAL_WIDTH_DP = 84f;
    public static final float ONE_ACTION_VISUAL_WIDTH_DP = 40f;
    public static final float CENTER_HEIGHT_DP = 46f;
    public static final float MAX_CENTER_WIDTH_DP = 320f;
    public static final float MIN_CENTER_WIDTH_DP = 124f;
    public static final float TEXT_RIGHT_PAD_DP = 10f;

    private SignatureFusionGeometry() { }

    public static final class Rect {
        public float left, top, right, bottom;
        public float width() { return right - left; }
        public float height() { return bottom - top; }
        public float centerX() { return (left + right) * .5f; }
        public float centerY() { return (top + bottom) * .5f; }
        void set(float l, float t, float r, float b) { left = l; top = t; right = r; bottom = b; }
        @Override public String toString() { return "["+left+","+top+","+right+","+bottom+"]"; }
    }
    public static final class Layout {
        public final Rect back = new Rect(), center = new Rect(), actions = new Rect();
        public final Rect backVisual = new Rect(), actionsVisual = new Rect();
        /** The avatar image is cropped to this panel inside the central pill. */
        public final Rect portrait = new Rect();
        /** Logical hit targets, ordered phone then overflow for LTR; mirrored for RTL. */
        public final Rect call = new Rect(), more = new Rect();
        public final Rect text = new Rect();
        public float fadeStartX, fadeEndX, fadeSafeStop;
        public float height;
        public boolean fits;
        public boolean rtl;
        public boolean callAvailable;
    }

    /**
     * @param widthPx measured header width
     * @param density Android display density (>0)
     * @param rtl right-to-left visual order
     * @param callAvailable whether Telegram's native call action exists in this chat
     */
    public static Layout calculate(float widthPx, float density, boolean rtl, boolean callAvailable) {
        if (!(density > 0) || Float.isNaN(widthPx) || Float.isInfinite(widthPx)) {
            throw new IllegalArgumentException("finite width and positive density required");
        }
        return update(new Layout(), widthPx, density, rtl, callAvailable);
    }

    /** The live header retains this layout; no Rect/Layout allocation on repeated measurement. */
    public static Layout update(Layout g, float widthPx, float density, boolean rtl, boolean callAvailable) {
        if (!(density > 0) || Float.isInfinite(density) || Float.isNaN(widthPx) || Float.isInfinite(widthPx))
            throw new IllegalArgumentException("finite width and density required");
        g.rtl = rtl;
        g.callAvailable = callAvailable;
        float d = density;
        float edge = EDGE_DP * d, gap = GAP_DP * d;
        float back = BACK_DP * d;
        float actionH = ACTION_HEIGHT_DP * d;
        float actionW = (callAvailable ? ACTION_WIDTH_DP : ONE_ACTION_WIDTH_DP) * d;
        float centerH = CENTER_HEIGHT_DP * d;
        g.height = Math.max(centerH, Math.max(back, actionH));
        float bTop = (g.height - back) * .5f;
        float aTop = (g.height - actionH) * .5f;
        float cTop = (g.height - centerH) * .5f;
        float start = edge + back + gap;
        float end = widthPx - edge - actionW - gap;
        float available = end - start;
        g.fits = available >= MIN_CENTER_WIDTH_DP * d;
        if (!rtl) {
            g.back.set(edge, bTop, edge + back, bTop + back);
            g.actions.set(widthPx - edge - actionW, aTop, widthPx - edge, aTop + actionH);
        } else {
            g.back.set(widthPx - edge - back, bTop, widthPx - edge, bTop + back);
            g.actions.set(edge, aTop, edge + actionW, aTop + actionH);
        }
        // Visually compact but with native 48dp touch targets and independent actions.
        float br = BACK_VISUAL_DP * d * .5f;
        g.backVisual.set(g.back.centerX() - br, g.back.centerY() - br,
                g.back.centerX() + br, g.back.centerY() + br);
        float arx = (callAvailable ? ACTION_VISUAL_WIDTH_DP : ONE_ACTION_VISUAL_WIDTH_DP) * d * .5f;
        float ary = ACTION_VISUAL_HEIGHT_DP * d * .5f;
        g.actionsVisual.set(g.actions.centerX() - arx, g.actions.centerY() - ary,
                g.actions.centerX() + arx, g.actions.centerY() + ary);
        // Center is capped on tablets but must not move either side control.
        float cw = Math.min(MAX_CENTER_WIDTH_DP * d, Math.max(0f, available));
        float cx = widthPx * .5f;
        if (!rtl) {
            float left = Math.max(start, Math.min(cx - cw*.5f, end - cw));
            g.center.set(left, cTop, left + cw, cTop + centerH);
        } else {
            float lEdge = edge + actionW + gap;
            float rEdge = widthPx - edge - back - gap;
            float left = Math.max(lEdge, Math.min(cx - cw*.5f, rEdge - cw));
            g.center.set(left, cTop, left + cw, cTop + centerH);
        }

        float actionSlot = 48f * d;
        if (callAvailable) {
            if (rtl) {
                g.more.set(g.actions.left, aTop, g.actions.left + actionSlot, aTop + actionH);
                g.call.set(g.actions.left + actionSlot, aTop, g.actions.right, aTop + actionH);
            } else {
                g.call.set(g.actions.left, aTop, g.actions.left + actionSlot, aTop + actionH);
                g.more.set(g.actions.left + actionSlot, aTop, g.actions.right, aTop + actionH);
            }
        } else {
            g.more.set(g.actions.left, aTop, g.actions.right, aTop + actionH);
            g.call.set(0,0,0,0);
        }


        // The native portrait extends under nearly the entire card. The mask reaches
        // <=4% alpha at the FIRST text pixel; the remaining tail fades to zero.
        // Both lines use one common horizontal center without shifting side actions.
        float photoW = SignatureFusionFade.portraitWidth(cw, d);
        float fadeInset = SignatureFusionFade.fadeStartInset(photoW, d);
        // Shift both lines closer to the visual card center, not just the
        // clear portion after the original avatar crop. The adaptive alpha
        // mask is already <=4% at the FIRST text pixel.
        float textInset = Math.min(50f * d, Math.max(0f, cw * .35f));
        if (!rtl) {
            g.portrait.set(g.center.left, cTop, g.center.left + photoW, cTop + centerH);
            g.text.set(g.center.left + textInset, cTop,
                    g.center.right - TEXT_RIGHT_PAD_DP * d, cTop + centerH);
            g.fadeStartX = g.portrait.left + fadeInset;
            g.fadeEndX = g.portrait.right;
            g.fadeSafeStop = SignatureFusionFade.safeStop(g.fadeStartX, g.fadeEndX, g.text.left, false);
        } else {
            g.portrait.set(g.center.right - photoW, cTop, g.center.right, cTop + centerH);
            g.text.set(g.center.left + TEXT_RIGHT_PAD_DP * d, cTop,
                    g.center.right - textInset, cTop + centerH);
            g.fadeStartX = g.portrait.right - fadeInset;
            g.fadeEndX = g.portrait.left;
            g.fadeSafeStop = SignatureFusionFade.safeStop(g.fadeStartX, g.fadeEndX, g.text.right, true);
        }
        // A fallback is preferable to clipping text or creating overlapping buttons.
        g.fits &= g.text.width() >= 48f*d;
        return g;
    }
}
