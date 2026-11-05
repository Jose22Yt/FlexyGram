/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

/** Window-coordinate placement, independent of density, keyboard and message type. */
public final class ContextPreviewPlacement {
    /** Keep a message scrim above the live input, including keyboard/position changes. */
    public static float scrimBottom(float height, float inputTop, boolean messageSelected, boolean inputVisible) {
        return messageSelected && inputVisible ? Math.max(0, Math.min(height, inputTop)) : height;
    }

    public final float scale, offsetY, scrollRange;
    public final int popupY, gapHeight;
    private ContextPreviewPlacement(float scale, float offsetY, float range, int y, int gap) {
        this.scale=scale; this.offsetY=offsetY; scrollRange=range; popupY=y; gapHeight=gap;
    }
    public static float animatedScale(float target, float progress, float spring) {
        float phase=Math.max(0f,Math.min(1f,progress));
        float motion=Math.max(.01f,spring);
        if (target<1f) motion=Math.min(1f,motion);
        return ((1f-phase)+target*phase)*motion;
    }
    public static ContextPreviewPlacement fit(float sourceTop, float sourceHeight, int safeTop,
            int safeBottom, int chromeHeight, int gapTop, int padding) {
        float height=Math.max(1f,sourceHeight);
        int available=Math.max(1,safeBottom-safeTop);
        int gap=Math.max(1,Math.min((int)Math.ceil(height)+2*padding,available-chromeHeight));
        int inset=Math.min(Math.max(0,padding),Math.max(0,(gap-1)/2));
        // Fit the complete bubble/photo into the reserved gap; never crop at an arbitrary scale floor.
        float scale=Math.min(1f,Math.max(1,gap-2*inset)/height);
        int total=Math.min(available,chromeHeight+gap);
        int y=Math.max(safeTop,Math.min(Math.round(sourceTop)-gapTop-inset,safeBottom-total));
        float offset=y+gapTop+inset-(sourceTop+height*(1f-scale)*.5f);
        return new ContextPreviewPlacement(scale,offset,Math.max(0,height*scale-Math.max(1,gap-2*inset)),y,gap);
    }
}
