/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles;

import android.graphics.Matrix;
import android.graphics.Path;
import android.graphics.Rect;
import android.graphics.RectF;

/** Telegram-iOS 24638bc: 33pt body, 6pt tail column, 16/8pt corners.
 * Port of ChatMessageBubbleImages.swift's formContext; see tools/ios_bubbles.
 * Paths are rebuilt only when MessageDrawable's per-cell geometry cache changes. */
public final class IosBubbleShape {
    private final Path tail = new Path(), cutout = new Path(), clip = new Path();
    private final RectF rect = new RectF();
    private final Matrix mirror = new Matrix();
    private final float[] corners = new float[8];
    private final Path cached = new Path();
    private final Path template = new Path(), piece = new Path(), slice = new Path();
    private final RectF sourceRect = new RectF(), targetRect = new RectF();
    private final Matrix stretch = new Matrix();
    private final float[] sourceX={0,18,19,43},sourceY={0,19,20,37};
    private final float[] targetX=new float[4],targetY=new float[4];
    private int width=-1,height,lastFlags;
    private float lastDensity,lastMain,lastNear;

    public void build(Path result, Rect bounds, float density, float mainRadius, float auxiliaryRadius, boolean outgoing, boolean topNear,
                      boolean bottomNear, boolean media, boolean noTail, boolean buttons) {
        int flags=(outgoing?1:0)|(topNear?2:0)|(bottomNear?4:0)|(media?8:0)|(noTail?16:0)|(buttons?32:0);
        if(width!=bounds.width()||height!=bounds.height()||lastFlags!=flags||lastDensity!=density||lastMain!=mainRadius||lastNear!=auxiliaryRadius) {
            width=bounds.width();height=bounds.height();lastFlags=flags;lastDensity=density;lastMain=mainRadius;lastNear=auxiliaryRadius;
            buildTemplate(template,mainRadius/density,auxiliaryRadius/density,topNear,bottomNear,media,noTail,buttons);
            stretchTemplate(width,height,density);
            if(!outgoing){mirror.setScale(-1,1);mirror.postTranslate(width,0);cached.transform(mirror);}
        }
        result.set(cached);result.offset(bounds.left,bounds.top);
    }
    private void buildTemplate(Path result, float mainRadius, float auxiliaryRadius, boolean topNear,
                      boolean bottomNear, boolean media, boolean noTail, boolean buttons) {
        float left=2,right=41,top=2,bottom=35,edge=media?right:35;
        float radius=Math.min(mainRadius,16),near=Math.min(auxiliaryRadius,radius);
        corners[0]=corners[1]=radius;corners[2]=corners[3]=topNear?near:radius;
        corners[4]=corners[5]=bottomNear||buttons?near:radius;corners[6]=corners[7]=radius;
        rect.set(left,top,edge,bottom);result.rewind();result.addRoundRect(rect,corners,Path.Direction.CW);
        if(!media&&!noTail&&!bottomNear&&!buttons){
            tail.rewind();
            // Exact formContext quadratics of the lower half of (24,16,27,17), translated by (2,2).
            if(radius>=14){
                tail.moveTo(26,26.5f);tail.quadTo(26,35,39.5f,35);tail.quadTo(53,35,53,26.5f);tail.close();
            }else{rect.set(24,26.5f,53,35);tail.addRect(rect,Path.Direction.CW);}
            rect.set(18.5f,18,35,27);tail.addRect(rect,Path.Direction.CW);result.op(tail,Path.Op.UNION);
            // Exact upper ellipse cutout (33,14,23,21), translated by (2,2).
            cutout.rewind();rect.set(35,16,58,37);cutout.addOval(rect,Path.Direction.CW);result.op(cutout,Path.Op.DIFFERENCE);
            clip.rewind();rect.set(0,0,43,37);clip.addRect(rect,Path.Direction.CW);result.op(clip,Path.Op.INTERSECT);
        }
    }
    private void stretchTemplate(int width,int height,float density){
        cached.rewind();if(width<=0||height<=0)return;
        // UIImage.stretchableImage: outgoing cap point (18,19), one-point center.
        // Keep the native caps, including the subtle corner segments crossing those points.
        float d=Math.min(density,Math.min(width/43f,height/37f));
        targetX[0]=0;targetX[1]=18*d;targetX[2]=width-24*d;targetX[3]=width;
        targetY[0]=0;targetY[1]=19*d;targetY[2]=height-17*d;targetY[3]=height;
        for(int y=0;y<3;y++)for(int x=0;x<3;x++){
            sourceRect.set(sourceX[x],sourceY[y],sourceX[x+1],sourceY[y+1]);
            targetRect.set(targetX[x],targetY[y],targetX[x+1],targetY[y+1]);
            slice.rewind();slice.addRect(sourceRect,Path.Direction.CW);
            piece.set(template);piece.op(slice,Path.Op.INTERSECT);
            stretch.setRectToRect(sourceRect,targetRect,Matrix.ScaleToFit.FILL);piece.transform(stretch);
            if(cached.isEmpty())cached.set(piece);else cached.op(piece,Path.Op.UNION);
        }
    }
}
