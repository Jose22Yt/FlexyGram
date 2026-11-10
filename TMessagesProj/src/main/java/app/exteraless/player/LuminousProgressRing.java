/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.exteraless.player;

import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.graphics.RadialGradient;
import android.graphics.Shader;
import android.graphics.SweepGradient;
import org.telegram.messenger.AndroidUtilities;

/** Theme-accent progress. Cached gradients, no bitmap, blur, animator or private frame loop. */
final class LuminousProgressRing {
    private final Paint trackPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint arcPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint glowPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Matrix rotation = new Matrix(), glowPosition = new Matrix();
    private Shader arc, glow;
    private int accent, track;
    private int width = -1, height = -1;
    private float density = -1, inset, glowRadius;
    private boolean colorsSet;
    void setColors(int accent, int track) {
        if (colorsSet && this.accent == accent && this.track == track) return;
        colorsSet = true;this.accent = accent;this.track = track;width = -1;
    }
    private void prepare(int w, int h) {
        if (width == w && height == h && density == AndroidUtilities.density) return;
        width = w;height = h;density = AndroidUtilities.density;
        inset = AndroidUtilities.dpf2(6);glowRadius = AndroidUtilities.dpf2(7);
        float stroke = AndroidUtilities.dpf2(2.5f);
        arcPaint.setStyle(Paint.Style.STROKE);arcPaint.setStrokeCap(Paint.Cap.ROUND);arcPaint.setStrokeWidth(stroke);
        trackPaint.setStyle(Paint.Style.STROKE);trackPaint.setStrokeWidth(AndroidUtilities.dpf2(1.5f));trackPaint.setColor(track);
        int bright = blend(accent, Color.WHITE, .72f);
        arc = new SweepGradient(w*.5f,h*.5f,new int[]{accent,accent,blend(accent,Color.WHITE,.32f),bright},new float[]{0,.88f,.96f,1});
        glow = new RadialGradient(0,0,glowRadius,new int[]{(accent&0xffffff)|0x48000000,accent&0xffffff},null,Shader.TileMode.CLAMP);
        arcPaint.setShader(arc);glowPaint.setShader(glow);
    }
    private static int blend(int a,int b,float fraction) {
        return Color.rgb(Math.round(Color.red(a)+(Color.red(b)-Color.red(a))*fraction),
                Math.round(Color.green(a)+(Color.green(b)-Color.green(a))*fraction),
                Math.round(Color.blue(a)+(Color.blue(b)-Color.blue(a))*fraction));
    }
    void draw(Canvas canvas,int w,int h,float value,float opacity) {
        if(w<=0||h<=0||opacity<=0)return;
        prepare(w,h);
        float progress=Float.isFinite(value)?Math.max(0,Math.min(1,value)):0;
        int alpha=Math.round(Math.max(0,Math.min(1,opacity))*255);
        trackPaint.setAlpha(alpha);arcPaint.setAlpha(alpha);glowPaint.setAlpha(alpha);
        canvas.drawArc(inset,inset,w-inset,h-inset,-90,360,false,trackPaint);
        if(progress<=0)return;
        float end=progress*360-90;
        rotation.setRotate(end+.25f,w*.5f,h*.5f);arc.setLocalMatrix(rotation);
        double angle=Math.toRadians(end);
        float x=w*.5f+(w*.5f-inset)*(float)Math.cos(angle),y=h*.5f+(h*.5f-inset)*(float)Math.sin(angle);
        glowPosition.setTranslate(x,y);glow.setLocalMatrix(glowPosition);
        canvas.drawCircle(x,y,glowRadius,glowPaint);
        canvas.drawArc(inset,inset,w-inset,h-inset,-90,progress*360,false,arcPaint);
    }
}
