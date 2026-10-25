package app.flexygram.header;

import android.graphics.RectF;

/** One layout, three equal outer heights. Title always centered in the useful window width. */
public final class HeaderGeometry {
    public final RectF back = new RectF(), title = new RectF(), avatar = new RectF();
    public boolean countVisible;
    public static float height(int width, float titlePx, float subtitlePx, float density, boolean compact) {
        float wanted = Math.max((compact ? 48 : 52) * density, (float) Math.ceil(titlePx + subtitlePx + 12 * density));
        float maximum = Math.max(48 * density, (width - 108 * density) / 2f);
        return Math.min(wanted, maximum);
    }
    public void update(int width, float top, float height, float numberWidth, float density, boolean rtl) {
        float edge = 8 * density, gap = 6 * density;
        float maxSide = Math.max(height, Math.min(width * .28f, (width - 64 * density) / 2 - edge - gap));
        countVisible = numberWidth > 0 && height + numberWidth + 8 * density <= maxSide;
        float side = height + (countVisible ? numberWidth + 8 * density : 0);
        back.set(edge, top, edge + side, top + height);
        avatar.set(width - edge - height, top, width - edge, top + height);
        float inset = edge + Math.max(side, height) + gap;
        title.set(Math.min(width / 2f, inset), top, Math.max(width / 2f, width - inset), top + height);
        if (rtl) { back.offset(width - edge * 2 - side, 0); avatar.offset(-(width - edge * 2 - height), 0); }
    }
}
