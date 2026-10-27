/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

/** Allocation-free media palette. Resolve only after theme/mode changes, not each frame. */
public final class SignatureSmartPreviewPalette {
    public static final int NONE=0, FILE=1, VOICE=2, MUSIC=3, LINK=4, EVENT=5, PHOTO=6, VIDEO=7, LOCATION=8, CONTACT=9;
    public static final int ADAPTIVE=0, THEME=1, MATTE=2, OFF=3;
    private static final int[] BASE={
        0xff8892a0,0xff3488df,0xff9960cb,0xffd45a91,
        0xff24a2ae,0xff21a36b,0xffc78d37,0xff7970ce,0xffd58a53,0xff6796c9
    };
    private int oldKind=-1,oldMode=-1,oldAccent,oldSurface;
    private int background=0xffe6edf4,foreground=0xff26313d;
    public int background(){return background;}
    public int foreground(){return foreground;}
    public boolean update(int kind,int mode,int accent,int surface) {
        if(kind<0||kind>=BASE.length||mode<ADAPTIVE||mode>MATTE)kind=NONE;
        if(oldKind==kind&&oldMode==mode&&oldAccent==accent&&oldSurface==surface)return false;
        oldKind=kind;oldMode=mode;oldAccent=accent;oldSurface=surface;
        int opaqueSurface=surface|0xff000000;
        int base=BASE[kind];
        int main=mode==THEME?(accent|0xff000000):
                mode==MATTE?blend(opaqueSurface,base,.16f):blend(base,accent|0xff000000,.14f);
        float tint=mode==MATTE?.09f:.18f;
        background=blend(opaqueSurface,main,tint);
        int ink=blend(main,luminance(background)>.48?0xff172332:0xfff7f9fc,.58f);
        if(contrast(ink,background)<4.5)ink=luminance(background)>.23?0xff172332:0xfff7f9fc;
        if(contrast(ink,background)<4.5)ink=luminance(background)>.18?0xff000000:0xffffffff;
        foreground=ink;
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
