package app.flexygram.icons;

import android.content.res.ColorStateList;
import android.content.res.Resources;
import android.graphics.*;
import android.graphics.drawable.Drawable;
import android.view.View;

/** One native, cached font glyph. No Flutter runtime, bitmap conversion or per-frame allocation. */
public final class CupertinoGlyphDrawable extends Drawable implements IconPressFeedback.Target {
    private static Typeface typeface;
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.SUBPIXEL_TEXT_FLAG);
    private final Rect unitBounds = new Rect();
    private final Path outline;
    private float outlineScale;
    private final String glyph;
    private final int spec, width, height, defaultColor;
    private ColorStateList tint;
    private int color=Color.BLACK, alpha=255;
    private float x, baseline;
    private boolean mirrored;
    private float pressScale=1;
    public void setPressScale(float scale){if(pressScale!=scale){pressScale=scale;invalidateSelf();}}
    public float getPressScale(){return pressScale;}
    @Override public void setIconPressScale(float scale){setPressScale(scale);}
    private static synchronized Typeface font(Resources resources) {
        if (typeface == null) typeface = Typeface.createFromAsset(resources.getAssets(), "cupertino/CupertinoIcons.ttf");
        return typeface;
    }
    public CupertinoGlyphDrawable(Resources resources, int spec) { this(resources,spec,Color.BLACK); }
    public CupertinoGlyphDrawable(Resources resources, int spec, int defaultColor) {
        this(spec, Math.max(1, Math.round(((spec >>> 16) & 255) * resources.getDisplayMetrics().density)),
                Math.max(1, Math.round(((spec >>> 24)&127) * resources.getDisplayMetrics().density)), font(resources),defaultColor);
    }
    private CupertinoGlyphDrawable(int spec, int width, int height, Typeface face, int defaultColor) {
        this.spec = spec;this.width = width;this.height = height;this.defaultColor=defaultColor;color=defaultColor;mirrored=(spec&0x80000000)!=0;
        glyph = String.valueOf((char)(spec & 0xffff));
        outline=CupertinoSupplement.path(spec&0xffff);
        paint.setTypeface(face);paint.setColor(defaultColor);paint.setTextSize(1000);
        if(outline==null)paint.getTextBounds(glyph, 0, glyph.length(), unitBounds);
        else{unitBounds.set(0,0,24,24);paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(1.5f);paint.setStrokeCap(Paint.Cap.ROUND);paint.setStrokeJoin(Paint.Join.ROUND);}
    }
    @Override protected void onBoundsChange(Rect bounds) {
        float scale = .92f * Math.min(bounds.width() / (float)Math.max(1, unitBounds.width()),
                bounds.height() / (float)Math.max(1, unitBounds.height()));
        outlineScale=scale;
        paint.setTextSize(1000 * scale);
        x = bounds.exactCenterX() - (unitBounds.left + unitBounds.right) * scale / 2;
        baseline = bounds.exactCenterY() - (unitBounds.top + unitBounds.bottom) * scale / 2;
    }
    @Override public void draw(Canvas canvas) {
        int pulseSave=-1;
        if(pressScale!=1){pulseSave=canvas.save();canvas.scale(pressScale,pressScale,getBounds().exactCenterX(),getBounds().exactCenterY());}
        if(outline!=null){int save=canvas.save();canvas.translate(x,baseline);canvas.scale(outlineScale,outlineScale);canvas.drawPath(outline,paint);canvas.restoreToCount(save);}
        else if (mirrored && getLayoutDirection() == View.LAYOUT_DIRECTION_RTL) {
            int save = canvas.save();canvas.scale(-1, 1, getBounds().exactCenterX(), getBounds().exactCenterY());
            canvas.drawText(glyph, x, baseline, paint);canvas.restoreToCount(save);
        } else canvas.drawText(glyph, x, baseline, paint);
        if(pulseSave>=0)canvas.restoreToCount(pulseSave);
    }
    @Override public void setAlpha(int alpha) { this.alpha=Math.max(0,Math.min(255,alpha));applyColor(); }
    @Override public int getAlpha() { return alpha; }
    @Override public void setColorFilter(ColorFilter filter) { paint.setColorFilter(filter);invalidateSelf(); }
    @Override public ColorFilter getColorFilter() { return paint.getColorFilter(); }
    @Override public void setTint(int color) { setTintList(ColorStateList.valueOf(color)); }
    @Override public void setTintList(ColorStateList colors) {
        tint = colors;
        if(colors==null){color=defaultColor;applyColor();}else onStateChange(getState());
    }
    @Override protected boolean onStateChange(int[] state) {
        if (tint == null) return false;
        int next = tint.getColorForState(state, tint.getDefaultColor());
        if (next == color) return false;
        color=next;applyColor();return true;
    }
    private void applyColor(){
        int sourceAlpha=Color.alpha(defaultColor);
        int fillAlpha=tint==null?sourceAlpha:Math.round(sourceAlpha*Color.alpha(color)/255f);
        paint.setColor(color);paint.setAlpha(Math.round(fillAlpha*alpha/255f));invalidateSelf();
    }
    @Override public boolean isStateful() { return tint != null && tint.isStateful(); }
    @Override public void setAutoMirrored(boolean value) { mirrored = value;invalidateSelf(); }
    @Override public boolean isAutoMirrored() { return mirrored; }
    @Override public boolean onLayoutDirectionChanged(int direction) { if(mirrored)invalidateSelf();return mirrored; }
    @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
    @Override public int getIntrinsicWidth() { return width; }
    @Override public int getIntrinsicHeight() { return height; }
    @Override public ConstantState getConstantState() {
        return new ConstantState() {
            @Override public Drawable newDrawable() { return new CupertinoGlyphDrawable(spec, width, height, typeface,defaultColor); }
            @Override public Drawable newDrawable(Resources resources) { return new CupertinoGlyphDrawable(resources, spec,defaultColor); }
            @Override public int getChangingConfigurations() { return 0; }
        };
    }
}
