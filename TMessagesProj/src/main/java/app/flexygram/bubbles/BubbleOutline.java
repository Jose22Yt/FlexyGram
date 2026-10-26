package app.flexygram.bubbles;

/** Pure color policy. Input is always the native bubble palette, never wallpaper or blur output. */
public final class BubbleOutline {
    private BubbleOutline() { }
    private static int mix(int a, int b, int percent) { return a + (b - a) * percent / 100; }
    public static int palette(int base,int first,int second,int third) {
        int r=(base>>>16)&255,g=(base>>>8)&255,b=base&255,count=1;
        if(first!=0){r+=(first>>>16)&255;g+=(first>>>8)&255;b+=first&255;count++;}
        if(second!=0){r+=(second>>>16)&255;g+=(second>>>8)&255;b+=second&255;count++;}
        if(third!=0){r+=(third>>>16)&255;g+=(third>>>8)&255;b+=third&255;count++;}
        return 0xff000000|((r/count)<<16)|((g/count)<<8)|(b/count);
    }
    public static int color(int base, boolean dark, int style, int intensity) {
        int r=(base>>>16)&255,g=(base>>>8)&255,b=base&255;
        int luminance=(r*299+g*587+b*114)/1000;
        if (style == 2) {
            int strength = Math.max(0, Math.min(100, intensity));
            int satin = 14 + strength * 18 / 100;
            return ((150 + strength * 40 / 100) << 24) | (mix(r, 255, satin) << 16)
                    | (mix(g, 255, satin) << 8) | mix(b, 255, satin);
        }
        if (style == 1) {
            int strength=Math.max(0,Math.min(100,intensity));
            int pearl=28+strength*42/100;
            return ((160+strength*80/100)<<24)|(mix(r,255,pearl)<<16)|(mix(g,255,pearl)<<8)|mix(b,255,pearl);
        }
        // Increase native chroma slightly, then contrast; neutral bubbles remain neutral.
        int contrast=dark?24:-24;
        r=Math.max(0,Math.min(255,r+(r-luminance)*12/100+contrast));
        g=Math.max(0,Math.min(255,g+(g-luminance)*12/100+contrast));
        b=Math.max(0,Math.min(255,b+(b-luminance)*12/100+contrast));
        return 0xe8000000|(r<<16)|(g<<8)|b;
    }
}
