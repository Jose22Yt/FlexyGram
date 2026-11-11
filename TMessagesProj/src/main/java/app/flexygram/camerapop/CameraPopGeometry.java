/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.camerapop;

/** Pure window-local geometry, independent of density and a particular phone model. */
public final class CameraPopGeometry {
    private CameraPopGeometry() {}
    public static boolean contains(float left,float top,float right,float bottom,float radius,float x,float y) {
        if(x<left || x>=right || y<top || y>=bottom)return false;
        float r=Math.max(0,Math.min(radius,Math.min(right-left,bottom-top)/2));
        float cx=Math.max(left+r,Math.min(x,right-r)),cy=Math.max(top+r,Math.min(y,bottom-r));
        float dx=x-cx,dy=y-cy;return dx*dx+dy*dy<=r*r;
    }
    public static final class Island {
        public float x,y,anchorX,anchorY,compactLeft;
        public int width,height,compactWidth,compactHeight;
        public boolean cutout;
    }
    public static Island island(int width,int height,int safeLeft,int safeTop,int safeRight,int safeBottom,
            float density,int rows,float left,float top,float right,float bottom) {
        Island p=new Island();float d=Math.max(.1f,density);
        p.cutout=right>left && bottom>top && left>=0 && right<=width && top>=0 && bottom<height/2f
                && right-left<=80*d && bottom-top<=64*d;
        float origin=p.cutout?(left+right)/2f:width/2f;
        p.compactHeight=Math.round(p.cutout?Math.max(32*d,bottom-top+8*d):36*d);
        p.width=Math.max(1,Math.min(Math.round(360*d),width-safeLeft-safeRight-Math.round(24*d)));
        p.compactWidth=Math.min(p.width,Math.round(Math.max(132*d,(p.cutout?right-left:0)+112*d)));
        p.x=Math.max(safeLeft+12*d,Math.min(origin-p.width/2f,width-safeRight-12*d-p.width));
        p.y=p.cutout?Math.max(0,(top+bottom)/2f-p.compactHeight/2f):safeTop+6*d;
        p.anchorX=origin-p.x;p.anchorY=p.cutout?(top+bottom)/2f-p.y:0;
        p.compactLeft=Math.max(0,Math.min(p.anchorX-p.compactWidth/2f,p.width-p.compactWidth));
        p.height=Math.max(p.compactHeight,Math.min(height-safeBottom-Math.round(p.y)-Math.round(12*d),
                p.compactHeight+Math.round(48*d)+Math.round(64*d)*Math.min(5,Math.max(1,rows))));
        return p;
    }
}
