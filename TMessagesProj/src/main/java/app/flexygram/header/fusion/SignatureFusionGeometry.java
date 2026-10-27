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
    public static final float GAP_DP = 10f;
    public static final float BACK_DP = 46f;
    public static final float ACTION_HEIGHT_DP = 46f;
    public static final float ACTION_WIDTH_DP = 96f; // two independently tappable 48dp slots
    public static final float ONE_ACTION_WIDTH_DP = 48f;
    public static final float CENTER_HEIGHT_DP = 50f; // ONLY 4dp taller than sides
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
        /** The avatar image is cropped to this panel inside the central pill. */
        public final Rect portrait = new Rect();
        /** Logical hit targets, ordered phone then overflow for LTR; mirrored for RTL. */
        public final Rect call = new Rect(), more = new Rect();
        public final Rect text = new Rect();
        public float fadeStartX, fadeEndX;
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
        g.height = centerH;
        float bTop = (centerH - back) * .5f;
        float aTop = (centerH - actionH) * .5f;
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
        // Center is capped on tablets but must not move either side control.
        float cw = Math.min(MAX_CENTER_WIDTH_DP * d, Math.max(0f, available));
        float cx = widthPx * .5f;
        if (!rtl) {
            float left = Math.max(start, Math.min(cx - cw*.5f, end - cw));
            g.center.set(left, 0, left + cw, centerH);
        } else {
            float lEdge = edge + actionW + gap;
            float rEdge = widthPx - edge - back - gap;
            float left = Math.max(lEdge, Math.min(cx - cw*.5f, rEdge - cw));
            g.center.set(left, 0, left + cw, centerH);
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

        // Preserve the approved text/control geometry. Only the photo/mask extends.
        // The sampled smooth fade continues into the name area at under 5% alpha.
        float originalPhotoW = Math.min(73f*d, Math.max(0f, cw - 60f*d));
        float photoW = SignatureFusionFade.portraitWidth(cw,d);
        float fadeTail = SignatureFusionFade.fadeTail(photoW,d);
        float labelPad = 7f*d;
        if (!rtl) {
            g.portrait.set(g.center.left, 0, g.center.left+photoW, centerH);
            g.fadeStartX = g.portrait.right - fadeTail;
            g.fadeEndX = g.portrait.right;
            g.text.set(g.center.left + Math.max(0f, originalPhotoW - 5f*d) + labelPad, 0,
                    g.center.right - TEXT_RIGHT_PAD_DP*d, centerH);
        } else {
            g.portrait.set(g.center.right-photoW, 0, g.center.right, centerH);
            g.fadeStartX = g.portrait.left + fadeTail;
            g.fadeEndX = g.portrait.left;
            g.text.set(g.center.left + TEXT_RIGHT_PAD_DP*d, 0,
                    g.center.right - Math.max(0f,originalPhotoW-5f*d) - labelPad, centerH);
        }
        // A fallback is preferable to clipping text or creating overlapping buttons.
        g.fits &= g.text.width() >= 48f*d;
        return g;
    }
}
