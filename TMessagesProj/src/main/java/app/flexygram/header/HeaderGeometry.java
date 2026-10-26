package app.flexygram.header;

import android.graphics.RectF;

/** One layout, three equal outer heights. Title always centered in the useful window width. */
public final class HeaderGeometry {
    public final RectF back = new RectF(), title = new RectF(), avatar = new RectF(), badge = new RectF();
    public boolean separateCount;
    public boolean countVisible;
    public static float height(int width, float titlePx, float subtitlePx, float density, boolean compact) {
        float wanted = Math.max((compact ? 40 : 44) * density, (float) Math.ceil(titlePx + subtitlePx + 8 * density));
        float maximum = Math.max(48 * density, (width - 108 * density) / 2f);
        return Math.min(wanted, maximum);
    }
    public void update(int width, float top, float height, float numberWidth, float density, boolean rtl) {
        update(width, top, height, numberWidth, density, rtl, 1);
    }
    public void update(int width, float top, float height, float numberWidth, float density, boolean rtl, int counterMode) {
        update(width, top, height, numberWidth, density, rtl, counterMode, Float.MAX_VALUE);
    }
    public void update(int width, float top, float height, float numberWidth, float density, boolean rtl, int counterMode, float desiredTitleWidth) {
        float edge = 8 * density, gap = 6 * density;
        float maxSide = Math.max(height, Math.min(width * .28f, (width - 64 * density) / 2 - edge - gap));
        float extra = counterMode == 2 ? Math.max(height * .65f, numberWidth + 8 * density) + 3 * density : numberWidth + 8 * density;
        countVisible = counterMode != 0 && numberWidth > 0 && height + extra <= maxSide;
        separateCount = countVisible && counterMode == 2;
        float side = height + (countVisible ? extra : 0);
        back.set(edge, top, edge + side, top + height);
        avatar.set(width - edge - height, top, width - edge, top + height);
        float inset = edge + Math.max(side, height) + gap;
        title.set(Math.min(width / 2f, inset), top, Math.max(width / 2f, width - inset), top + height);
        float preferred = Math.min(title.width(), Math.max(80 * density, desiredTitleWidth));
        title.set(width / 2f - preferred / 2f, top, width / 2f + preferred / 2f, top + height);
        float badgeSize = separateCount ? extra - 3 * density : extra;
        float badgeLeft = rtl ? width - edge - side : back.left + height + (separateCount ? 3 * density : 0);
        badge.set(badgeLeft, top + (height - badgeSize) / 2f, badgeLeft + badgeSize, top + (height + badgeSize) / 2f);
        if (rtl) { back.offset(width - edge * 2 - side, 0); avatar.offset(-(width - edge * 2 - height), 0); }
    }
}
