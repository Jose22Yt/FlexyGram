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
        public final Rect backVisual = new Rect(), actionsVisual = new Rect(), unread = new Rect();
        public boolean separateUnread;
        public final Rect callVisual = new Rect(), moreVisual = new Rect();
        public boolean mattePortrait;
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
        return update(g, widthPx, density, rtl, callAvailable, 0);
    }
    public static Layout update(Layout g, float widthPx, float density, boolean rtl, boolean callAvailable, float backExtraPx) {
        if (!(density > 0) || Float.isInfinite(density) || Float.isNaN(widthPx) || Float.isInfinite(widthPx))
            throw new IllegalArgumentException("finite width and density required");
        g.rtl = rtl;
        g.separateUnread = false;
        g.unread.set(0,0,0,0);
        g.mattePortrait = false;
        g.callAvailable = callAvailable;
        float d = density;
        float edge = EDGE_DP * d, gap = GAP_DP * d;
        float back = BACK_DP * d + Math.max(0, backExtraPx);
        float actionH = ACTION_HEIGHT_DP * d;
        float actionW = (callAvailable ? ACTION_WIDTH_DP : ONE_ACTION_WIDTH_DP) * d;
        float centerH = CENTER_HEIGHT_DP * d;
        g.height = Math.max(centerH, Math.max(BACK_DP * d, actionH));
        float bTop = (g.height - BACK_DP * d) * .5f;
        float aTop = (g.height - actionH) * .5f;
        float cTop = (g.height - centerH) * .5f;
        float start = edge + back + gap;
        float end = widthPx - edge - actionW - gap;
        float available = end - start;
        g.fits = available >= MIN_CENTER_WIDTH_DP * d;
        if (!rtl) {
            g.back.set(edge, bTop, edge + back, bTop + BACK_DP * d);
            g.actions.set(widthPx - edge - actionW, aTop, widthPx - edge, aTop + actionH);
        } else {
            g.back.set(widthPx - edge - back, bTop, widthPx - edge, bTop + BACK_DP * d);
            g.actions.set(edge, aTop, edge + actionW, aTop + actionH);
        }
        // Visually compact but with native 48dp touch targets and independent actions.
        float br = BACK_VISUAL_DP * d * .5f;
        float extraHalf = Math.max(0, backExtraPx) * .5f;
        g.backVisual.set(g.back.centerX() - br - extraHalf, g.back.centerY() - br,
                g.back.centerX() + br + extraHalf, g.back.centerY() + br);
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


        // The native portrait extends under nearly the entire card. Its alpha now
        // fades across the left half (right half in RTL) of the card, not abruptly
        // before the first letter. Native title/status views are drawn ON TOP of the
        // avatar; no text layer is faded. The subtitle keeps its previous axis.
        // Title placement is independently centered on the whole pill.
        float photoW = SignatureFusionFade.portraitWidth(cw, d);
        float fadeInset = SignatureFusionFade.fadeStartInset(photoW, d);
        // The two centered lines share one axis, closer to the actual middle
        // of the pill than the previous avatar-width-constrained label region.
        // Full-card alpha is already below four percent at this text boundary.
        float textInset = Math.min(50f * d, Math.max(0f, cw * .35f));
        if (!rtl) {
            g.portrait.set(g.center.left, cTop, g.center.left + photoW, cTop + centerH);
            g.text.set(g.center.left + textInset, cTop,
                    g.center.right - TEXT_RIGHT_PAD_DP * d, cTop + centerH);
            g.fadeStartX = g.portrait.left + fadeInset;
            g.fadeEndX = g.center.left + cw * .56f;
            g.fadeSafeStop = SignatureFusionFade.safeStop(g.fadeStartX, g.fadeEndX, g.text.left, false);
        } else {
            g.portrait.set(g.center.right - photoW, cTop, g.center.right, cTop + centerH);
            g.text.set(g.center.left + TEXT_RIGHT_PAD_DP * d, cTop,
                    g.center.right - textInset, cTop + centerH);
            g.fadeStartX = g.portrait.right - fadeInset;
            g.fadeEndX = g.center.right - cw * .56f;
            g.fadeSafeStop = SignatureFusionFade.safeStop(g.fadeStartX, g.fadeEndX, g.text.right, true);
        }
        // A fallback is preferable to clipping text or creating overlapping buttons.
        g.fits &= g.text.width() >= 48f*d;
        return g;
    }

    /** Split only the painted back island; the reserved native touch rectangle stays unchanged. */
    public static void placeUnread(Layout g, float numberWidth, int mode, float density) {
        g.separateUnread = numberWidth > 0 && mode == 2;
        if (!g.separateUnread) return;
        float size = Math.max(28 * density, numberWidth + 8 * density);
        float arrowWidth = (g.mattePortrait ? CENTER_HEIGHT_DP : BACK_VISUAL_DP) * density;
        if (g.rtl) {
            g.backVisual.left = g.backVisual.right - arrowWidth;
            g.unread.set(g.backVisual.left-3*density-size,g.backVisual.centerY()-size*.5f,
                    g.backVisual.left-3*density,g.backVisual.centerY()+size*.5f);
        } else {
            g.backVisual.right = g.backVisual.left + arrowWidth;
            g.unread.set(g.backVisual.right+3*density,g.backVisual.centerY()-size*.5f,
                    g.backVisual.right+3*density+size,g.backVisual.centerY()+size*.5f);
        }
    }

    /** Matte Portrait reuses the original native 48dp controls and center bounds. */
    public static Layout updatePortrait(Layout g, float width, float density, boolean rtl, boolean callAvailable) {
        return updatePortrait(g, width, density, rtl, callAvailable, 0);
    }
    public static Layout updatePortrait(Layout g, float width, float density, boolean rtl, boolean callAvailable, float backExtraPx) {
        update(g, width, density, rtl, callAvailable, backExtraPx);
        g.mattePortrait = true;
        float radius = CENTER_HEIGHT_DP * density * .5f;
        g.backVisual.set(g.back.centerX()-radius-Math.max(0,backExtraPx)*.5f,g.back.centerY()-radius,g.back.centerX()+radius+Math.max(0,backExtraPx)*.5f,g.back.centerY()+radius);
        g.callVisual.set(g.call.centerX()-radius,g.call.centerY()-radius,g.call.centerX()+radius,g.call.centerY()+radius);
        g.moreVisual.set(g.more.centerX()-radius,g.more.centerY()-radius,g.more.centerX()+radius,g.more.centerY()+radius);
        float photo = 38f*density, inset = 4f*density;
        float left = rtl ? g.center.right-inset-photo : g.center.left+inset;
        g.portrait.set(left,g.center.centerY()-photo*.5f,left+photo,g.center.centerY()+photo*.5f);
        if (rtl) g.text.set(g.center.left+10f*density,g.center.top,g.portrait.left-8f*density,g.center.bottom);
        else g.text.set(g.portrait.right+8f*density,g.center.top,g.center.right-10f*density,g.center.bottom);
        g.fits &= g.text.width() >= 48f*density;
        return g;
    }

    /**
     * Center the contact NAME on the whole pill, independently of the subtitle.
     * Clamp to the text-safe rectangle so names/icons never cover the portrait.
     * A long name is automatically moved into the available text region.
     * The original subtitle axis, sizing and last-seen baseline remain unchanged.
     */
    public static float titleCenterX(Layout g, float measuredTitleWidth) {
        if (g == null || Float.isNaN(measuredTitleWidth) || measuredTitleWidth < 0f)
            throw new IllegalArgumentException("valid title geometry required");
        float half = Math.min(g.text.width(), measuredTitleWidth) * .5f;
        float min = g.text.left + half;
        float max = g.text.right - half;
        if (max < min) return g.text.centerX();
        return Math.max(min, Math.min(g.center.centerX(), max));
    }
}
