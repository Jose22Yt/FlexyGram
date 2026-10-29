/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles;

import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;

/** Three narrow in-silhouette color bands, not a new bubble surface/blur/shader.
 * The native path, theme palette, transparency and contour-position shader remain authoritative. */
public final class BubbleFusion {
    private int previousFill,previousEdge,previousStrength=-1;
    private boolean previousAdapt;
    private int outerColor,middleColor;
    public void draw(Canvas canvas,Path path,Paint paint,float stroke,int edge,int fill,int strength,boolean adapt){
        strength=Math.max(0,Math.min(100,strength));
        if(strength==0)return;
        if(fill!=previousFill||edge!=previousEdge||strength!=previousStrength||adapt!=previousAdapt){
            previousFill=fill;previousEdge=edge;previousStrength=strength;previousAdapt=adapt;
            outerColor=adapt?mix(fill,edge,25):edge;middleColor=adapt?mix(fill,edge,55):edge;
        }
        int alpha=edge>>>24;
        paint.setStrokeWidth(stroke*(1.6f+strength*.020f));
        paint.setColor((outerColor&0xffffff)|(Math.round(alpha*strength*.0016f)<<24));canvas.drawPath(path,paint);
        paint.setStrokeWidth(stroke*(1.2f+strength*.010f));
        paint.setColor((middleColor&0xffffff)|(Math.round(alpha*strength*.0032f)<<24));canvas.drawPath(path,paint);
        paint.setStrokeWidth(stroke);paint.setColor(edge);
    }
    public static int mix(int a,int b,int percent){
        int r=((a>>>16)&255)+(((b>>>16)&255)-((a>>>16)&255))*percent/100;
        int g=((a>>>8)&255)+(((b>>>8)&255)-((a>>>8)&255))*percent/100;
        int blue=(a&255)+((b&255)-(a&255))*percent/100;
        return (b&0xff000000)|(r<<16)|(g<<8)|blue;
    }
}
