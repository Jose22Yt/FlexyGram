package org.telegram.ui.Components.blur3.drawable;

import static org.telegram.messenger.AndroidUtilities.dp;

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
import org.telegram.ui.Components.blur3.LiquidGlassEffect;
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

    private LiquidGlassEffect liquidGlassEffect;

    @RequiresApi(api = Build.VERSION_CODES.TIRAMISU)
    public void setLiquidGlassEffectAllowed() {
        setLiquidGlassEffectAllowed(true);
    }

    /** Policy changes reuse this native drawable; an OFF transition must clear the old GPU effect. */
    private boolean nativeLiquidGlassAllowed;
    private int materialProfile = -1;
    private static boolean iosShaderUnavailable;

    @RequiresApi(api = Build.VERSION_CODES.TIRAMISU)
    public void setLiquidGlassEffectAllowed(boolean allowed) {
        if (nativeLiquidGlassAllowed == allowed) {
            if (liquidGlassEffect != null) syncMaterialProfile();
            return;
        }
        nativeLiquidGlassAllowed = allowed;
        // A newly created surface receives its target tag before allocating a GPU program.
        if (liquidGlassEffect != null) syncMaterialProfile();
        invalidateDisplayList();
        invalidateSelf();
    }

    private void syncMaterialProfile() {
        if (Build.VERSION.SDK_INT < 33) return;
        final boolean requested = app.flexygram.glass.IosGlassConfig.requested(iosGlassSurface);
        final boolean ios = requested && app.flexygram.glass.IosGlassConfig.active(iosGlassSurface) && !iosShaderUnavailable;
        final int profile = ios ? 2 : requested ? 0 : nativeLiquidGlassAllowed ? 1 : 0;
        if (materialProfile == profile) return;
        materialProfile = profile;
        liquidGlassEffect = null;
        renderNodeFill.setRenderEffect(null);
        if (profile != 0) {
            try {
                liquidGlassEffect = ios ? new LiquidGlassEffect(renderNodeFill, true) : new LiquidGlassEffect(renderNodeFill);
            } catch (RuntimeException unavailable) {
                if (!ios) throw unavailable;
                iosShaderUnavailable = true;
                org.telegram.messenger.FileLog.e(unavailable);
            }
        }
        updateColors();
        invalidateDisplayList();
        invalidateSelf();
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
        syncMaterialProfile();
        final float offsetX = sourceOffsetX;
        final float offsetY = sourceOffsetY;

        Canvas c;

        final float sL = boundProps.boundsWithPadding.left + offsetX;
        final float sT = boundProps.boundsWithPadding.top + offsetY;
        final float sR = boundProps.boundsWithPadding.right + offsetX;
        final float sB = boundProps.boundsWithPadding.bottom + offsetY;

        // An opaque surface never samples the backdrop. Keep the previous fill node
        // available; a later transparent color change invalidates and records it again.
        if (Color.alpha(backgroundColor) != 255) {
            c = renderNodeFill.beginRecording();
            c.save();
            c.translate(-sL, -sT);
            if (liquidGlassEffect != null && Build.VERSION.SDK_INT >= 33) {
                final int thickness = Math.max(Math.min(
                    materialProfile == 2 ? dp(8) : boundProps.liquidThickness <= 0 ? dp(11) : boundProps.liquidThickness,
                    Math.min(boundProps.boundsWithPadding.width(), boundProps.boundsWithPadding.height()) / 5), 1);

                if (materialProfile == 2) liquidGlassEffect.setDarkAppearance(
                        colorProvider != null ? colorProvider.isDarkAppearance() : Theme.isCurrentThemeDark());
                liquidGlassEffect.update(
                    0, 0, boundProps.boundsWithPadding.width(), boundProps.boundsWithPadding.height(),
                    boundProps.shaderRadii[0], boundProps.shaderRadii[2], boundProps.shaderRadii[4], boundProps.shaderRadii[6],
                    thickness,
                    materialProfile == 2 ? 0.85f : boundProps.liquidIntensity,
                    materialProfile == 2 ? 1.6f : boundProps.liquidIndex,
                    backgroundColor
                );
            }
            source.draw(c, sL, sT, sR, sB);
            c.restore();
            renderNodeFill.endRecording();
        }


        c = renderNode.beginRecording();
        if (Color.alpha(backgroundColor) == 255) {
            c.drawColor(backgroundColor);
        } else {
            c.drawRenderNode(renderNodeFill);
            if (liquidGlassEffect == null && Color.alpha(backgroundColor) != 0) {
                c.drawColor(backgroundColor);
            }
        }
        if (!boundProps.useFullStroke) {
            if (strokeColorTop != 0) {
                drawStrokeRaw(c, 0, 0, boundProps.boundsWithPadding.width(),
                        boundProps.boundsWithPadding.height(), boundProps.radii,
                        boundProps.strokeWidthTop, true, paintStrokeTop);
            }
            if (strokeColorBottom != 0) {
                drawStrokeRaw(c, 0, 0, boundProps.boundsWithPadding.width(),
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
        if (!iosShaderUnavailable && app.flexygram.glass.IosGlassConfig.active(iosGlassSurface) && colorProvider != null) {
            backgroundColor = androidx.core.graphics.ColorUtils.setAlphaComponent(colorProvider.getBackgroundColor(), 38);
            shadowColor = strokeColorTop = strokeColorBottom = strokeColorFull = 0;
            if (boundProps.useFullStroke || boundProps.microContour) {
                boundProps.useFullStroke = boundProps.microContour = false;
                boundProps.build();
                onBoundPropsChanged();
            }
        }

        updateShadowLayer(shadowColor);
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

        syncMaterialProfile();
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
        renderNode.setAlpha(alpha / 255f);
        // RenderNode alpha is a composition property, not display-list content.

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
