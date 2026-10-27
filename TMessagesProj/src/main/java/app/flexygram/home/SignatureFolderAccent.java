/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

/** Cached theme-event color resolution. Drawing only uses the resolved integer pair. */
public final class SignatureFolderAccent {
    private int previousAccent,previousInk,previousSurface,previousNeutral;
    private final int[] selectionInk=new int[129];
    private boolean initialized;
    public int color,ink;
    public boolean update(int accent,int preferredInk,int surface){
        return update(accent,preferredInk,surface,((surface>>>16)&255)<128?0xffe7e9ed:0xff454c56);
    }
    public boolean update(int accent,int preferredInk,int surface,int neutralInk){
        if(initialized&&accent==previousAccent&&preferredInk==previousInk&&surface==previousSurface&&neutralInk==previousNeutral)return false;
        initialized=true;previousAccent=accent;previousInk=preferredInk;previousSurface=surface;previousNeutral=neutralInk;
        int alpha=accent>>>24;color=0xff000000;
        for(int shift=0;shift<=16;shift+=8){
            int c=(accent>>>shift)&255,b=(surface>>>shift)&255;
            color|=((c*alpha+b*(255-alpha)+127)/255)<<shift;
        }
        int preferred=preferredInk|0xff000000;
        ink=contrast(preferred,color)>=4.5?preferred:
            (contrast(0xff000000,color)>=contrast(0xffffffff,color)?0xff000000:0xffffffff);
        // Text crossfades can lose contrast when the active accent is much darker
        // than the neutral surface. Resolve that transition palette once per theme.
        for(int i=0;i<selectionInk.length;i++){
            float f=i/(float)(selectionInk.length-1);
            int background=blend(surface,color,f),candidate=blend(neutralInk,ink,f);
            selectionInk[i]=contrast(candidate,background)>=4.5?candidate:
                (contrast(0xff000000,background)>=contrast(0xffffffff,background)?0xff000000:0xffffffff);
        }
        return true;
    }
    public int inkAt(float selection){return selectionInk[Math.max(0,Math.min(selectionInk.length-1,Math.round(selection*(selectionInk.length-1))))];}
    private static int blend(int a,int b,float f){int c=0;for(int shift=0;shift<=24;shift+=8)c|=Math.round(((a>>>shift)&255)+(((b>>>shift)&255)-((a>>>shift)&255))*f)<<shift;return c;}
    private static double channel(int c){double v=c/255.0;return v<=.04045?v/12.92:Math.pow((v+.055)/1.055,2.4);}
    public static double luminance(int c){return .2126*channel((c>>>16)&255)+.7152*channel((c>>>8)&255)+.0722*channel(c&255);}
    public static double contrast(int a,int b){double x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);}
}
