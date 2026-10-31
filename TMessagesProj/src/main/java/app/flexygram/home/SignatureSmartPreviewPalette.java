/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

/** Allocation-free media palette. Resolve only after theme/mode changes, not each frame. */
public final class SignatureSmartPreviewPalette {
    public static final int NONE=0, FILE=1, VOICE=2, MUSIC=3, LINK=4, EVENT=5, PHOTO=6, VIDEO=7, LOCATION=8, CONTACT=9;
    public static final int PDF=10, TXT=11, ZIP=12, RAR=13, ARCHIVE=14, APK=15,
            PNG=16, JPG=17, IMAGE_FILE=18, GIF=19, STICKER=20, POLL=21,
            JOINED=22, LEFT=23, PINNED=24, EDITED=25, DOCUMENT=26,
            SPREADSHEET=27, PRESENTATION=28, CHANNEL=29, ADMIN=30, OWNER=31, DELETED=32;
    public static final int ADAPTIVE=0, THEME=1, MATTE=2, OFF=3;
    private static final int[] BASE={
        0xff8892a0,0xff1e88e5,0xff8e24aa,0xffe91e63,
        0xff00acc1,0xff00897b,0xff2e7d32,0xff5e35b1,0xffff8f00,0xff0288d1,
        0xff1e88e5,0xff1976d2,0xffff9800,0xffff8f00,0xffffa000,0xff00897b,
        0xff2e7d32,0xff388e3c,0xff43a047,0xff5e35b1,0xff7b1fa2,0xff00838f,
        0xff00897b,0xffc2185b,0xff0097a7,0xff546e7a,0xff1e88e5,0xff2e7d32,
        0xffe65100,0xff546e7a,0xffffb300,0xffff8f00,0xffe53935
    };
    private int oldKind=-1,oldMode=-1,oldAccent,oldSurface;
    private int background=0xffe6edf4,foreground=0xff26313d,iconColor=0xff26313d;
    public int background(){return background;}
    public int foreground(){return foreground;}
    public int iconColor(){return iconColor;}

    private static int cachedMode = -1, cachedAccent = 0, cachedSurface = 0;
    private static final int[][] CACHED_PALETTE = new int[BASE.length][3];

    public static void resolveColors(int kind, int mode, int accent, int surface, int[] outColors) {
        if (kind < 0 || kind >= BASE.length) kind = NONE;
        if (cachedMode != mode || cachedAccent != accent || cachedSurface != surface) {
            cachedMode = mode; cachedAccent = accent; cachedSurface = surface;
            int opaqueSurface = surface | 0xff000000;
            boolean isDark = luminance(opaqueSurface) < 0.45;
            for (int k = 0; k < BASE.length; k++) {
                int base = BASE[k];
                int main = (mode == THEME) ? (accent | 0xff000000) : base;
                int bg, fg, ic;
                if (mode == MATTE) {
                    if (isDark) {
                        bg = blend(opaqueSurface, 0xffffffff, 0.16f);
                        fg = 0xffffffff;
                        ic = blend(base, 0xffffffff, 0.35f);
                    } else {
                        bg = blend(opaqueSurface, 0xff000000, 0.08f);
                        fg = 0xff1c2024;
                        ic = blend(base, 0xff000000, 0.20f);
                    }
                } else {
                    if (isDark) {
                        bg = blend(opaqueSurface, main, 0.28f);
                        fg = 0xffffffff;
                        ic = fg;
                    } else {
                        bg = blend(0xffffffff, main, 0.16f);
                        int darkInk = blend(main, 0xff000000, 0.40f);
                        if (contrast(darkInk, bg) < 4.5) {
                            darkInk = blend(main, 0xff000000, 0.60f);
                        }
                        fg = darkInk;
                        ic = fg;
                    }
                }
                if (contrast(fg, bg) < 4.5) {
                    fg = luminance(bg) > 0.23 ? 0xff172332 : 0xfff7f9fc;
                }
                if (contrast(fg, bg) < 4.5) {
                    fg = luminance(bg) > 0.18 ? 0xff000000 : 0xffffffff;
                }
                if (mode != MATTE) {
                    ic = fg;
                }
                CACHED_PALETTE[k][0] = bg;
                CACHED_PALETTE[k][1] = fg;
                CACHED_PALETTE[k][2] = ic;
            }
        }
        outColors[0] = CACHED_PALETTE[kind][0];
        outColors[1] = CACHED_PALETTE[kind][1];
        outColors[2] = CACHED_PALETTE[kind][2];
    }

    public boolean update(int kind,int mode,int accent,int surface) {
        if(kind<0||kind>=BASE.length||mode<ADAPTIVE||mode>OFF)kind=NONE;
        if(oldKind==kind&&oldMode==mode&&oldAccent==accent&&oldSurface==surface)return false;
        oldKind=kind;oldMode=mode;oldAccent=accent;oldSurface=surface;
        int[] c = new int[3];
        resolveColors(kind, mode, accent, surface, c);
        background = c[0];
        foreground = c[1];
        iconColor = c[2];
        return true;
    }
    private static int blend(int a,int b,float f){
        int v=0;for(int s=0;s<24;s+=8){
            int left=(a>>>s)&255,right=(b>>>s)&255;
            v|=Math.round(left+(right-left)*f)<<s;
        }return v|0xff000000;
    }
    private static double channel(int c){double v=c/255.;return v<=.04045?v/12.92:Math.pow((v+.055)/1.055,2.4);}
    public static double luminance(int c){return .2126*channel((c>>>16)&255)+.7152*channel((c>>>8)&255)+.0722*channel(c&255);}
    public static double contrast(int a,int b){double x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);}
}
