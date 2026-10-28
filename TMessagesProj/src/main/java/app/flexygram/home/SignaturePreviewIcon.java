/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.text.style.ReplacementSpan;
import org.telegram.messenger.AndroidUtilities;

/** Small, fixed native line icons. Geometry is shared and never rebuilt in draw(). */
public final class SignaturePreviewIcon extends ReplacementSpan {
    private static final Path[] ICONS = new Path[10];
    static {
        for (int i = 1; i < ICONS.length; i++) ICONS[i] = new Path();
        Path p=ICONS[1]; p.moveTo(3,1);p.lineTo(8,1);p.lineTo(10,3);p.lineTo(10,11);p.lineTo(3,11);p.close();p.moveTo(8,1);p.lineTo(8,4);p.lineTo(10,4);p.moveTo(4.5f,6);p.lineTo(8.5f,6);p.moveTo(4.5f,8);p.lineTo(8,8);
        p=ICONS[2];p.moveTo(5,2);p.lineTo(5,6.5f);p.lineTo(6,7.5f);p.lineTo(7,6.5f);p.lineTo(7,2);p.lineTo(5,2);p.moveTo(3,5.5f);p.lineTo(3,7);p.lineTo(5,9);p.lineTo(7,9);p.lineTo(9,7);p.lineTo(9,5.5f);p.moveTo(6,9);p.lineTo(6,11);
        p=ICONS[3];p.moveTo(5,9);p.lineTo(5,3);p.lineTo(9,2);p.lineTo(9,7.5f);p.moveTo(5,8);p.lineTo(3,8.5f);p.lineTo(3,10);p.lineTo(5,9);p.moveTo(9,7);p.lineTo(7,7.5f);p.lineTo(7,9);p.lineTo(9,8);
        p=ICONS[4];p.moveTo(5,4);p.lineTo(3,4);p.lineTo(1.5f,6);p.lineTo(3,8);p.lineTo(5,8);p.moveTo(7,4);p.lineTo(9,4);p.lineTo(10.5f,6);p.lineTo(9,8);p.lineTo(7,8);p.moveTo(4,6);p.lineTo(8,6);
        p=ICONS[5];p.moveTo(2,3);p.lineTo(10,3);p.lineTo(10,10);p.lineTo(2,10);p.close();p.moveTo(4,1);p.lineTo(4,4);p.moveTo(8,1);p.lineTo(8,4);p.moveTo(2,5);p.lineTo(10,5);
        p=ICONS[6];p.moveTo(1.5f,2);p.lineTo(10.5f,2);p.lineTo(10.5f,10);p.lineTo(1.5f,10);p.close();p.moveTo(2,9);p.lineTo(5,6);p.lineTo(6.5f,7.5f);p.lineTo(8,6);p.lineTo(10,8);
        p=ICONS[7];p.moveTo(2,2);p.lineTo(10,2);p.lineTo(10,10);p.lineTo(2,10);p.close();p.moveTo(5,4);p.lineTo(8,6);p.lineTo(5,8);p.close();
        p=ICONS[8];p.moveTo(6,11);p.lineTo(3,7);p.lineTo(2.5f,5);p.lineTo(3.5f,2.5f);p.lineTo(6,1.5f);p.lineTo(8.5f,2.5f);p.lineTo(9.5f,5);p.lineTo(9,7);p.close();p.moveTo(5,4.5f);p.lineTo(7,4.5f);
        p=ICONS[9];p.moveTo(4,2.5f);p.lineTo(5,1.5f);p.lineTo(7,1.5f);p.lineTo(8,2.5f);p.lineTo(8,4.5f);p.lineTo(7,5.5f);p.lineTo(5,5.5f);p.lineTo(4,4.5f);p.close();p.moveTo(2,10);p.lineTo(2.5f,8);p.lineTo(4,7);p.lineTo(8,7);p.lineTo(9.5f,8);p.lineTo(10,10);
    }
    private final int kind;
    public SignaturePreviewIcon(int kind) { this.kind = kind >= 1 && kind < ICONS.length ? kind : 1; }
    @Override public int getSize(Paint paint, CharSequence text, int start, int end, Paint.FontMetricsInt fm) { return AndroidUtilities.dp(16); }
    @Override public void draw(Canvas c, CharSequence text, int start, int end, float x, int top, int y, int bottom, Paint p) {
        float size=AndroidUtilities.dp(12), factor=size/12f;
        Paint.Style style=p.getStyle();float stroke=p.getStrokeWidth();Paint.Cap cap=p.getStrokeCap();Paint.Join join=p.getStrokeJoin();
        c.save();c.translate(x,(top+bottom-size)*.5f);c.scale(factor,factor);
        p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(1.15f);p.setStrokeCap(Paint.Cap.ROUND);p.setStrokeJoin(Paint.Join.ROUND);
        c.drawPath(ICONS[kind],p);c.restore();p.setStyle(style);p.setStrokeWidth(stroke);p.setStrokeCap(cap);p.setStrokeJoin(join);
    }
}
