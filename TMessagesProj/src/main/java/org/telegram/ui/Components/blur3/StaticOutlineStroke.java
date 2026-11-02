/* SPDX-License-Identifier: GPL-3.0-or-later */
package org.telegram.ui.Components.blur3;

import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Shader;
import org.telegram.messenger.AndroidUtilities;

/** Complete the existing static blur3 path: default untouched, hidden absent, solid drawn once.
 * No bitmap, blur, worker, View/Context reference or per-frame Java allocation.
 */
public final class StaticOutlineStroke {
    private static final class Scratch {
        final RectF rect=new RectF();
        final Path path=new Path();
        final float[] radii=new float[8];
    }
    private static final ThreadLocal<Scratch> SCRATCH=ThreadLocal.withInitial(Scratch::new);
    private StaticOutlineStroke(){}
    private static boolean skip(GlassOutlineStyle mode,boolean top){return mode==GlassOutlineStyle.HIDDEN||!top;}
    public static boolean drawOverride(Canvas c,float l,float t,float r,float b,float radius,boolean top,Paint p,GlassOutlineStyle mode){
        if(mode==GlassOutlineStyle.GLARE)return false;
        if(skip(mode,top)||r<=l||b<=t)return true;
        float width=Math.min(AndroidUtilities.dpf2(1),Math.min(r-l,b-t)),half=width*.5f;
        Paint.Style style=p.getStyle();float oldWidth=p.getStrokeWidth();Shader shader=p.getShader();
        try{p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(width);p.setShader(null);
            float round=Math.max(0,Math.min(radius,Math.min(r-l,b-t)*.5f)-half);
            c.drawRoundRect(l+half,t+half,r-half,b-half,round,round,p);
        }finally{p.setShader(shader);p.setStrokeWidth(oldWidth);p.setStyle(style);}
        return true;
    }
    public static boolean drawOverride(Canvas c,float l,float t,float r,float b,float[] radii,boolean top,Paint p,GlassOutlineStyle mode){
        if(mode==GlassOutlineStyle.GLARE)return false;
        if(skip(mode,top)||r<=l||b<=t)return true;
        Scratch s=SCRATCH.get();float width=Math.min(AndroidUtilities.dpf2(1),Math.min(r-l,b-t)),half=width*.5f;
        s.rect.set(l+half,t+half,r-half,b-half);
        for(int i=0;i<8;i++)s.radii[i]=Math.max(0,radii[i]-half);
        s.path.rewind();s.path.addRoundRect(s.rect,s.radii,Path.Direction.CW);
        Paint.Style style=p.getStyle();float oldWidth=p.getStrokeWidth();Shader shader=p.getShader();
        try{p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(width);p.setShader(null);c.drawPath(s.path,p);}
        finally{p.setShader(shader);p.setStrokeWidth(oldWidth);p.setStyle(style);}
        return true;
    }
}
