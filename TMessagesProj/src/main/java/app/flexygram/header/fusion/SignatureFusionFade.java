package app.flexygram.header.fusion;

/** Cached native alpha curve. The tail reaches the original name area without moving text. */
public final class SignatureFusionFade {
    static final float[] LTR_STOPS = {0f,.15f,.30f,.50f,.70f,.85f,.90f,1f};
    static final float[] RTL_STOPS = {0f,.10f,.15f,.30f,.50f,.70f,.85f,1f};
    static final int[] LTR_COLORS = {0xFFFFFFFF,0xEFFFFFFF,0xC8FFFFFF,0x80FFFFFF,0x37FFFFFF,0x10FFFFFF,0x07FFFFFF,0x00FFFFFF};
    static final int[] RTL_COLORS = {0x00FFFFFF,0x07FFFFFF,0x10FFFFFF,0x37FFFFFF,0x80FFFFFF,0xC8FFFFFF,0xEFFFFFFF,0xFFFFFFFF};
    private SignatureFusionFade() { }
    public static float portraitWidth(float centerWidth,float density) {
        return Math.min(80f*density,Math.max(0f,centerWidth-53f*density));
    }
    public static float fadeTail(float photoWidth,float density) {
        return photoWidth-Math.min(32f*density,photoWidth*.4f);
    }
    /** Same piecewise smoothstep samples supplied to LinearGradient; useful for geometry verification. */
    public static float opacityAt(float fraction) {
        if (Float.isNaN(fraction)) throw new IllegalArgumentException("finite fraction required");
        if (fraction<=0) return 1f;
        if (fraction>=1) return 0f;
        for(int i=1;i<LTR_STOPS.length;i++) if(fraction<=LTR_STOPS[i]) {
            float t=(fraction-LTR_STOPS[i-1])/(LTR_STOPS[i]-LTR_STOPS[i-1]);
            float a=LTR_COLORS[i-1]>>>24,b=LTR_COLORS[i]>>>24;
            return (a+(b-a)*t)/255f;
        }
        return 0f;
    }
}
