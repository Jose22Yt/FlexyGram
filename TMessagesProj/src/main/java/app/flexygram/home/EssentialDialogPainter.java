/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;

/** One reusable paint/path rectangle per recycled row. No shadow layers, captures or new child views. */
public final class EssentialDialogPainter {
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF bounds=new RectF();
    public void draw(Canvas canvas,int width,int height,float density,int page,int card){
        paint.setColor(page);canvas.drawRect(0,0,width,height,paint);
        bounds.set(8*density,3*density,Math.max(8*density,width-8*density),Math.max(3*density,height-3*density));
        paint.setColor(card);canvas.drawRoundRect(bounds,14*density,14*density,paint);
    }
}
