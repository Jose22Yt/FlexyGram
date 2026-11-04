package app.flexygram.settings.signature;

/** Shared settings-only geometry and theme surface, without preference writes or draw allocations. */
public final class SettingsCardStyle {
    public static final int OUTER_RADIUS = 28, INNER_RADIUS = 6, GAP = 4, INSET = 12, ICON = 24;
    private SettingsCardStyle() {}
    public static int surface(int requested, int page) {
        int r=(requested>>>16)&255,g=(requested>>>8)&255,b=requested&255;
        int pr=(page>>>16)&255,pg=(page>>>8)&255,pb=page&255;
        if (Math.max(Math.abs(r-pr),Math.max(Math.abs(g-pg),Math.abs(b-pb))) < 12) {
            int shift=(pr*299+pg*587+pb*114)<128000 ? 16 : -12;
            r=Math.max(0,Math.min(255,r+shift));g=Math.max(0,Math.min(255,g+shift));b=Math.max(0,Math.min(255,b+shift));
        }
        return 0xFF000000|(r<<16)|(g<<8)|b;
    }
}
