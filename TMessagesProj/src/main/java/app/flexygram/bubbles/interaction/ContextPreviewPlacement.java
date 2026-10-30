/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

/** Window-coordinate placement, independent of density, keyboard and message type. */
public final class ContextPreviewPlacement {
    public final float scale, offsetY, scrollRange;
    public final int popupY, gapHeight;
    private ContextPreviewPlacement(float scale, float offsetY, float range, int y, int gap) {
        this.scale=scale; this.offsetY=offsetY; scrollRange=range; popupY=y; gapHeight=gap;
    }
    public static ContextPreviewPlacement fit(float sourceTop, float sourceHeight, int safeTop,
            int safeBottom, int chromeHeight, int gapTop, int padding) {
        float height=Math.max(1f,sourceHeight);
        int available=Math.max(1,safeBottom-safeTop);
        int gap=Math.max(1,Math.min((int)Math.ceil(height)+2*padding,available-chromeHeight));
        // Extremely tall messages scroll in a viewport instead of shrinking to illegibility.
        float scale=Math.min(1f,Math.max(.72f,Math.max(1,gap-2*padding)/height));
        int total=Math.min(available,chromeHeight+gap);
        int y=Math.max(safeTop,Math.min(Math.round(sourceTop)-gapTop-padding,safeBottom-total));
        float offset=y+gapTop+padding-(sourceTop+height*(1f-scale)*.5f);
        return new ContextPreviewPlacement(scale,offset,Math.max(0,height*scale-Math.max(1,gap-2*padding)),y,gap);
    }
}
