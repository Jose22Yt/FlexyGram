package org.telegram.ui.Components.blur3.drawable;

import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Outline;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.RenderNode;
import android.os.Build;

import androidx.annotation.NonNull;
import androidx.annotation.RequiresApi;

import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.blur3.source.BlurredBackgroundSource;

@RequiresApi(api = Build.VERSION_CODES.Q)
public class BlurredBackgroundDrawableRenderNode extends BlurredBackgroundDrawable {
    private final BlurredBackgroundSource source;
    private final Outline outline = new Outline();
    private final Rect outlineRect = new Rect();

    private final RenderNode renderNode;
    private final RenderNode renderNodeFill;

    private final Paint paintShadow = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint paintStrokeTop = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint paintStrokeBottom = new Paint(Paint.ANTI_ALIAS_FLAG);
    // Сплошной контур заливкой
    private final Paint paintStrokeFull = new Paint(Paint.ANTI_ALIAS_FLAG);

    private int appliedShadowColor;
    private float appliedShadowRadius = Float.NaN, appliedShadowDx, appliedShadowDy;

    private void updateShadowLayer(int color) {
        if (appliedShadowColor == color && appliedShadowRadius == shadowLayerRadius
                && appliedShadowDx == shadowLayerDx && appliedShadowDy == shadowLayerDy) return;
        paintShadow.setShadowLayer(shadowLayerRadius, shadowLayerDx, shadowLayerDy, color);
        appliedShadowColor = color;
        appliedShadowRadius = shadowLayerRadius;
        appliedShadowDx = shadowLayerDx;
        appliedShadowDy = shadowLayerDy;
    }

    private boolean renderNodeInvalidated;

    public BlurredBackgroundDrawableRenderNode(BlurredBackgroundSource source) {
        this.renderNode = new RenderNode("BlurredNode");
        this.renderNodeFill = new RenderNode("BlurredFill");
        this.renderNode.setClipToOutline(true);
        this.renderNode.setClipToBounds(true);

        this.source = source;

        this.paintShadow.setColor(0);
        this.paintStrokeTop.setStyle(Paint.Style.STROKE);
        this.paintStrokeBottom.setStyle(Paint.Style.STROKE);
        this.paintStrokeFull.setStyle(Paint.Style.FILL);
    }

    @Override
    public BlurredBackgroundDrawable setClipToOutline(boolean clipToOutline) {
        renderNode.setClipToOutline(clipToOutline);
        return super.setClipToOutline(clipToOutline);
    }

    /** Compatibility entry point: the optimized material never installs a refractive shader. */
    @Deprecated
    public void setLiquidGlassEffectAllowed() {
    }

    /** Compatibility with the live material policy; refraction stays disabled. */
    @Deprecated
    public void setLiquidGlassEffectAllowed(boolean allowed) {
    }

    @Override
    public BlurredBackgroundSource getSource() {
        return source;
    }

    @Override
    protected void onBoundPropsChanged() {
        super.onBoundPropsChanged();

        if (boundProps.useFullStroke) {
            paintStrokeTop.setStrokeWidth(boundProps.strokeWidthFull);
        } else {
            paintStrokeTop.setStrokeWidth(boundProps.strokeWidthTop);
            paintStrokeBottom.setStrokeWidth(boundProps.strokeWidthBottom);
        }

        outlineRect.set(0, 0,
            boundProps.boundsWithPadding.width(),
            boundProps.boundsWithPadding.height()
        );
        getOutline(outline, outlineRect, boundProps.radii);
        outline.setAlpha(1);

        if (!boundProps.boundsWithPadding.isEmpty()) {
            renderNodeFill.setPosition(0, 0, boundProps.boundsWithPadding.width(), boundProps.boundsWithPadding.height());
            renderNode.setPosition(0, 0, boundProps.boundsWithPadding.width(), boundProps.boundsWithPadding.height());
            renderNode.setOutline(outline);

            renderNodeInvalidated = true;
        }
    }

    @Override
    protected void onSourceOffsetChange(float sourceOffsetX, float sourceOffsetY) {
        super.onSourceOffsetChange(sourceOffsetX, sourceOffsetY);
        renderNodeInvalidated = true;
    }

    @Override
    public boolean hasDisplayList() {
        return renderNode.hasDisplayList();
    }

    @Override
    public void updateDisplayList() {
        final float offsetX = sourceOffsetX;
        final float offsetY = sourceOffsetY;

        Canvas c;

        final float sL = boundProps.boundsWithPadding.left + offsetX;
        final float sT = boundProps.boundsWithPadding.top + offsetY;
        final float sR = boundProps.boundsWithPadding.right + offsetX;
        final float sB = boundProps.boundsWithPadding.bottom + offsetY;

        // Opaque fallbacks do not need a backdrop display list at all.
        if (Color.alpha(backgroundColor) < 255) {
            c = renderNodeFill.beginRecording();
            c.save();
            c.translate(-sL, -sT);
            source.draw(c, sL, sT, sR, sB);
            c.restore();
            renderNodeFill.endRecording();
        }


        c = renderNode.beginRecording();
        if (Color.alpha(backgroundColor) == 255) {
            c.drawColor(backgroundColor);
        } else {
            c.drawRenderNode(renderNodeFill);
            if (Color.alpha(backgroundColor) != 0) {
                c.drawColor(backgroundColor);
            }
        }
        if (!boundProps.useFullStroke) {
            if (strokeColorTop != 0) {
                drawStroke(c, 0, 0, boundProps.boundsWithPadding.width(),
                        boundProps.boundsWithPadding.height(), boundProps.radii,
                        boundProps.strokeWidthTop, true, paintStrokeTop);
            }
            if (strokeColorBottom != 0) {
                drawStroke(c, 0, 0, boundProps.boundsWithPadding.width(),
                        boundProps.boundsWithPadding.height(), boundProps.radii,
                        boundProps.strokeWidthBottom, false, paintStrokeBottom);
            }
        } else if (Color.alpha(strokeColorFull) != 0) {
            c.save();
            c.translate(-boundProps.boundsWithPadding.left, -boundProps.boundsWithPadding.top);
            c.drawPath(boundProps.strokePathTop, paintStrokeFull);
            c.restore();
        }
        renderNode.endRecording();
    }

    @Override
    public void updateColors() {
        super.updateColors();

        if (boundProps.useFullStroke) {
            paintStrokeFull.setColor(strokeColorFull);
        } else {
            paintStrokeTop.setColor(strokeColorTop);
            paintStrokeBottom.setColor(strokeColorBottom);
        }

        renderNodeInvalidated = true;
    }

    @Override
    public void draw(@NonNull Canvas canvas) {
        if (boundProps.boundsWithPadding.isEmpty()) {
            return;
        }

        if (!canvas.isHardwareAccelerated()) {
            drawSource(canvas, source);
            return;
        }

        if (!renderNode.hasDisplayList()) {
            source.dispatchOnDrawablesRelativePositionChange();
            updateDisplayList();
        } else if (renderNodeInvalidated) {
            updateDisplayList();
        }
        renderNodeInvalidated = false;

        int color = Theme.multAlpha(shadowColor, renderNode.getAlpha() * shadowAlpha);
        if (Color.alpha(color) != 0) {
            updateShadowLayer(color);
            boundProps.drawShadows(canvas, paintShadow, inAppKeyboardOptimization);
        }

        canvas.save();
        canvas.translate(boundProps.boundsWithPadding.left, boundProps.boundsWithPadding.top);
        canvas.drawRenderNode(renderNode);
        canvas.restore();
    }

    public void invalidateDisplayList() {
        renderNodeInvalidated = true;
    }

    @Override
    public void setAlpha(int alpha) {
        final int oldAlpha = getAlpha();

        if (oldAlpha == alpha) return;
        super.setAlpha(alpha);
        // RenderNode applies opacity when replayed; fading does not change recorded content.
        renderNode.setAlpha(alpha / 255f);

        if (oldAlpha == 0 && alpha > 0) {
            source.dispatchOnDrawablesRelativePositionChange();
        }
    }

    @Override
    protected void onSourceRelativePositionChanged(RectF position) {
        super.onSourceRelativePositionChanged(position);
        source.dispatchOnDrawablesRelativePositionChange();
    }
}
