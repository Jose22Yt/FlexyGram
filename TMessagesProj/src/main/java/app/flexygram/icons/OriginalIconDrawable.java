/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.icons;

import android.content.res.ColorStateList;
import android.content.res.Resources;
import android.graphics.Canvas;
import android.graphics.ColorFilter;
import android.graphics.PorterDuff;
import android.graphics.Rect;
import android.graphics.drawable.Drawable;

/** Retains the source point size/aspect ratio inside an Android control. Never enlarges it. */
final class OriginalIconDrawable extends Drawable implements Drawable.Callback {
    private final Drawable source;
    OriginalIconDrawable(Drawable source) { this.source=source;source.setCallback(this); }
    @Override protected void onBoundsChange(Rect bounds) {
        int w=source.getIntrinsicWidth(),h=source.getIntrinsicHeight();
        if(w<=0||h<=0){source.setBounds(bounds);return;}
        float scale=Math.min(1f,Math.min(bounds.width()/(float)w,bounds.height()/(float)h));
        int width=Math.round(w*scale),height=Math.round(h*scale);
        int left=bounds.left+(bounds.width()-width)/2,top=bounds.top+(bounds.height()-height)/2;
        source.setBounds(left,top,left+width,top+height);
    }
    @Override public void draw(Canvas canvas) { source.draw(canvas); }
    @Override public int getIntrinsicWidth() { return source.getIntrinsicWidth(); }
    @Override public int getIntrinsicHeight() { return source.getIntrinsicHeight(); }
    @Override public void setAlpha(int alpha) { source.setAlpha(alpha); }
    @Override public int getAlpha() { return source.getAlpha(); }
    @Override public void setColorFilter(ColorFilter filter) { source.setColorFilter(filter); }
    @Override public ColorFilter getColorFilter() { return source.getColorFilter(); }
    @Override public void setTint(int color) { source.setTint(color); }
    @Override public void setTintList(ColorStateList colors) { source.setTintList(colors); }
    @Override public void setTintMode(PorterDuff.Mode mode) { source.setTintMode(mode); }
    @Override public void setAutoMirrored(boolean mirrored) { source.setAutoMirrored(mirrored); }
    @Override public boolean isAutoMirrored() { return source.isAutoMirrored(); }
    @Override public boolean onLayoutDirectionChanged(int direction) { return source.setLayoutDirection(direction); }
    @Override public boolean isStateful() { return source.isStateful(); }
    @Override protected boolean onStateChange(int[] state) { return source.setState(state); }
    @Override protected boolean onLevelChange(int level) { return source.setLevel(level); }
    @Override public int getOpacity() { return source.getOpacity(); }
    @Override public void invalidateDrawable(Drawable who) { invalidateSelf(); }
    @Override public void scheduleDrawable(Drawable who,Runnable what,long when) { scheduleSelf(what,when); }
    @Override public void unscheduleDrawable(Drawable who,Runnable what) { unscheduleSelf(what); }
    @Override public ConstantState getConstantState() {
        ConstantState state=source.getConstantState();
        return state==null?null:new State(state);
    }
    private static final class State extends ConstantState {
        private final ConstantState source;
        State(ConstantState source) { this.source=source; }
        @Override public Drawable newDrawable() { return new OriginalIconDrawable(source.newDrawable().mutate()); }
        @Override public Drawable newDrawable(Resources resources) { return new OriginalIconDrawable(source.newDrawable(resources).mutate()); }
        @Override public int getChangingConfigurations() { return source.getChangingConfigurations(); }
        @Override public boolean canApplyTheme() { return source.canApplyTheme(); }
    }
}
