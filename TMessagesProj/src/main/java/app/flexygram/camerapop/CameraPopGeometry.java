/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.camerapop;

/** Pure window-local geometry, independent of density and a particular phone model. */
public final class CameraPopGeometry {
    private CameraPopGeometry() {}
    public static final class Placement {
        public final float x, y, originX, originY;
        public final int width;
        public final boolean cutout;
        Placement(float x, float y, float originX, float originY, int width,boolean cutout) {
            this.x=x; this.y=y; this.originX=originX; this.originY=originY; this.width=width;
            this.cutout=cutout;
        }
    }
    public static Placement place(int width, int height, int safeLeft, int safeTop, int safeRight,
            int safeBottom, int desiredWidth, int cardHeight, int margin, int gap,
            float left, float top, float right, float bottom) {
        float minX = safeLeft + margin, maxX = width - safeRight - margin;
        int cardWidth = Math.max(1, Math.min(desiredWidth, Math.round(maxX-minX)));
        boolean valid = right > left && bottom > top && left >= 0 && top >= 0
                && right <= width && bottom <= height && top < height / 2f;
        float originX = valid ? (left+right)/2f : width/2f;
        float originY = valid ? (top+bottom)/2f : safeTop;
        float x = Math.max(minX, Math.min(originX-cardWidth/2f, maxX-cardWidth));
        float y = Math.max(safeTop, valid?bottom:safeTop) + gap;
        y = Math.max(safeTop, Math.min(y, height-safeBottom-cardHeight-margin));
        return new Placement(x, y, originX, originY, cardWidth,valid);
    }
}
