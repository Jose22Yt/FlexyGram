package org.telegram.ui.Components.blur3;

import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import org.telegram.messenger.AndroidUtilities;

/** Two cached paths, no blur/capture/animation and no allocation in draw. */
public final class GlassContourRenderer {
    private final Paint outer = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint inner = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path outerPath = new Path(), innerPath = new Path();
    private final RectF bounds = new RectF(), work = new RectF();
    private final float[] previousRadii = new float[8], workRadii = new float[8], roundRadii = new float[8];
    private float density = -1;
    private boolean geometryReady, dark, contrastReady;

    public GlassContourRenderer() { outer.setStyle(Paint.Style.STROKE); inner.setStyle(Paint.Style.STROKE); }
    public static boolean supports(GlassOutlineStyle mode) {
        return mode == GlassOutlineStyle.DOUBLE || mode == GlassOutlineStyle.ADAPTIVE;
    }
    public void draw(Canvas canvas, float l, float t, float r, float b, float radius,
                     GlassOutlineStyle mode, int surface, int alpha) {
        for (int i=0;i<8;i++) roundRadii[i]=radius;
        draw(canvas,l,t,r,b,roundRadii,mode,surface,alpha);
    }
    public void draw(Canvas canvas, float l, float t, float r, float b, float[] radii,
                     GlassOutlineStyle mode, int surface, int alpha) {
        if (!supports(mode) || alpha <= 0 || r <= l || b <= t) return;
        float d=AndroidUtilities.dpf2(1);
        boolean rebuild=!geometryReady || density!=d || bounds.left!=l || bounds.top!=t || bounds.right!=r || bounds.bottom!=b;
        for (int i=0;i<8;i++) if(previousRadii[i]!=radii[i]) rebuild=true;
        if (rebuild) {
            bounds.set(l,t,r,b);density=d;geometryReady=true;
            System.arraycopy(radii,0,previousRadii,0,8);
            outer.setStrokeWidth(Math.min(d,Math.min(r-l,b-t)*.2f));
            inner.setStrokeWidth(outer.getStrokeWidth()*.7f);
            path(outerPath,outer.getStrokeWidth()*.5f);
            path(innerPath,outer.getStrokeWidth()*1.7f);
        }
        int primary=Color.WHITE,secondary=Color.BLACK,primaryAlpha=145,secondaryAlpha=70;
        if (mode==GlassOutlineStyle.ADAPTIVE) {
            float luminance=(Color.red(surface)*.2126f+Color.green(surface)*.7152f+Color.blue(surface)*.0722f)/255f;
            // Hysteresis prevents white/black chatter as a patterned background moves.
            if (!contrastReady || luminance<.42f || luminance>.58f) dark=luminance<.5f;
            contrastReady=true;
            primary=dark?Color.WHITE:Color.BLACK;
            secondary=dark?Color.BLACK:Color.WHITE;
            primaryAlpha=Math.round(160+45*(1-Math.abs(luminance-.5f)*2));
            secondaryAlpha=48;
        }
        outer.setColor((primary&0xffffff)|((primaryAlpha*alpha/255)<<24));
        inner.setColor((secondary&0xffffff)|((secondaryAlpha*alpha/255)<<24));
        canvas.drawPath(outerPath,outer);
        canvas.drawPath(innerPath,inner);
    }
    private void path(Path path,float inset) {
        path.rewind();work.set(bounds);work.inset(inset,inset);
        if (work.isEmpty()) return;
        for(int i=0;i<8;i++) workRadii[i]=Math.max(0,previousRadii[i]-inset);
        path.addRoundRect(work,workRadii,Path.Direction.CW);
    }
}
