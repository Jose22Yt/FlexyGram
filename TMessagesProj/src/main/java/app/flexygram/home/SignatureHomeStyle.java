/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

/** Presentation only. No preferences, account state or navigation ownership. */
public final class SignatureHomeStyle {
    private SignatureHomeStyle() { }

    public static float controlDiameter(float width, float height, float density) {
        return Math.max(0, Math.min(36 * density, Math.min(width, height) - 8 * density));
    }

    public static float categoryHeight(float height, float density) {
        return Math.max(0, Math.min(30 * density, height - 4 * density));
    }

    public static float selection(int id, int selected, int previous, boolean moving, float progress) {
        if (!moving || selected == previous) return id == selected ? 1 : 0;
        float p = Math.max(0, Math.min(1, progress));
        return id == selected ? p : id == previous ? 1 - p : 0;
    }

    public static int surface(boolean dark, boolean glass) {
        return dark ? (glass ? 0xE632353B : 0xFF32353B)
                : (glass ? 0xE6F1F2F5 : 0xFFF1F2F5);
    }

    public static int selectedSurface(boolean dark, boolean glass) {
        return dark ? (glass ? 0xF0444D5A : 0xFF444D5A)
                : (glass ? 0xF0DFE8F2 : 0xFFDFE8F2);
    }

    public static int text(boolean dark, boolean selected) {
        return dark ? (selected ? 0xFFFFFFFF : 0xFFE7E9ED)
                : (selected ? 0xFF244E75 : 0xFF454C56);
    }

    public static int edge(boolean dark) {
        return dark ? 0x24FFFFFF : 0x10000000;
    }
}
