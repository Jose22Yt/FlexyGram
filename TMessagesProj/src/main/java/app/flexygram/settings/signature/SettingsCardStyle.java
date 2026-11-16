package app.flexygram.settings.signature;

/** Shared settings-only geometry and opaque surface; no preference writes. */
public final class SettingsCardStyle {
    public static final int OUTER_RADIUS = 20, INNER_RADIUS = 6, GAP = 4, INSET = 10, ICON = 22;
    public static final int ROW = 48, TEXT = 15, TEXT_START = 50, TEXT_END = 14;
    private SettingsCardStyle() {}
    public static int surface(int requested, int page) {
        return surface(requested, page, 0xff808080, luminance(page) < 128000);
    }
    public static int surface(int requested, int page, int accent, boolean dark) {
        if (dark) {
            // Charcoal with an 8% Monet accent, always distinct from the black page.
            return accentTint(0xff1d1f21,accent,8);
        }
        int r=(requested>>>16)&255,g=(requested>>>8)&255,b=requested&255;
        int pr=(page>>>16)&255,pg=(page>>>8)&255,pb=page&255;
        if (Math.max(Math.abs(r-pr),Math.max(Math.abs(g-pg),Math.abs(b-pb))) < 12) {
            int shift=luminance(page)<128000 ? 16 : -12;
            r=Math.max(0,Math.min(255,r+shift));g=Math.max(0,Math.min(255,g+shift));b=Math.max(0,Math.min(255,b+shift));
        }
        return 0xFF000000|(r<<16)|(g<<8)|b;
    }
    /** Mix only RGB, retaining native material opacity. Shared with optional chat surfaces. */
    public static int accentTint(int color,int accent,int percent) {
        int amount=Math.max(0,Math.min(100,percent)),base=100-amount;
        int r=(((color>>>16)&255)*base+((accent>>>16)&255)*amount+50)/100;
        int g=(((color>>>8)&255)*base+((accent>>>8)&255)*amount+50)/100;
        int b=((color&255)*base+(accent&255)*amount+50)/100;
        return (color&0xff000000)|(r<<16)|(g<<8)|b;
    }
    private static int luminance(int color) {
        return ((color>>>16)&255)*299+((color>>>8)&255)*587+(color&255)*114;
    }
}
