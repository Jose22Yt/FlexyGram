package app.flexygram.effects;

import android.graphics.Canvas;
import android.graphics.LinearGradient;
import android.graphics.Matrix;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.RuntimeShader;
import android.graphics.Shader;
import android.os.Build;

import androidx.annotation.RequiresApi;
import org.telegram.messenger.AndroidUtilities;

/** A perimeter reflection with stronger highlights at the top and bottom. */
public final class ChatEdgeReflection {
    private static final int[] DARK = {
            0x46ffffff, 0x21ffffff, 0x00ffffff, 0x00ffffff, 0x20ffffff, 0x50ffffff
    };
    private static final int[] LIGHT = {
            0x240d2237, 0x70ffffff, 0x00ffffff, 0x000d2237, 0x190d2237, 0x3b0d2237
    };
    private static final int[] SUBTLE_DARK = {
            0x24ffffff, 0x19ffffff, 0x00ffffff, 0x00ffffff, 0x16ffffff, 0x20ffffff
    };
    private static final int[] SUBTLE_LIGHT = {
            0xe8ffffff, 0x70ffffff, 0x00ffffff, 0x00474747, 0x07474747, 0x24474747
    };
    private static final int[] DARK_SIDES = {0x00ffffff, 0x48ffffff, 0x48ffffff, 0x00ffffff};
    private static final int[] LIGHT_SIDES = {0x000d2237, 0x400d2237, 0x400d2237, 0x000d2237};
    private static final int[] COLOROS_DARK_STROKE = {
            0x44f4f9ff, 0x18f4f9ff, 0x14f4f9ff, 0x18f4f9ff, 0x52f4f9ff
    };
    private static final int[] COLOROS_LIGHT_STROKE = {
            0x200f172a, 0x140f172a, 0x120f172a, 0x160f172a, 0x2a0f172a
    };
    private static final int[] COLOROS_LIGHT_INNER = {
            0x88ffffff, 0x22ffffff, 0x00ffffff, 0x1effffff, 0x60ffffff
    };
    private static final float[] COLOROS_STROKE_STOPS = {0f, 0.22f, 0.5f, 0.78f, 1f};
    private static final float[] SIDE_BANDS = {1f, .63f, .28f};
    private static final float[] SIDE_OPACITY = {.23f, .30f, .47f};
    // A view normally uses up to four heights (including separate counters and actions).
    private final float[] heights = new float[4];
    private final float[] stops = {0f, 0f, 0f, 0f, 0f, 1f};
    private final float[] sideStops = new float[4];
    private final LinearGradient[] shaders = new LinearGradient[4];
    private final LinearGradient[] sideShaders = new LinearGradient[4];
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint sidePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Matrix colorOsMatrix = new Matrix();
    private final float[] colorOsInsetRadii = new float[8];
    private LinearGradient colorOsFallbackDark;
    private LinearGradient colorOsFallbackLight;
    private LinearGradient colorOsFallbackLightInner;
    private Path localShape;
    private CurvedEdge curvedEdge;
    private ColorOsGlassEdge colorOsEdge;
    private boolean darkTheme;
    private float gradientDensity;
    private boolean satin;
    private boolean colorOsGlass;
    private SatinEdgeMaterial satinMaterial;

    public void setSatin(boolean satin) {
        this.satin = satin;
    }

    public void setColorOsGlass(boolean colorOsGlass) {
        if (this.colorOsGlass == colorOsGlass) return;
        this.colorOsGlass = colorOsGlass;
        resetGradients();
    }

    private boolean subtle;
    private int nextSlot;

    public ChatEdgeReflection() {
        sidePaint.setStyle(Paint.Style.STROKE);
    }

    public void setSubtle(boolean subtle) {
        if (this.subtle == subtle) return;
        this.subtle = subtle;
        resetGradients();
    }

    private void resetGradients() {
        java.util.Arrays.fill(shaders, null);
        java.util.Arrays.fill(sideShaders, null);
        nextSlot = 0;
    }

    public void draw(Canvas canvas, RectF bounds, float radius, boolean dark, int alpha) {
        draw(canvas, bounds.left, bounds.top, bounds.right, bounds.bottom, radius, dark, alpha);
    }

    public void draw(Canvas canvas, float left, float top, float right, float bottom,
            float radius, boolean dark, int alpha) {
        draw(canvas, left, top, right, bottom, radius, null, null, dark, alpha);
    }

    public void drawClipped(Canvas canvas, float left, float top, float right, float bottom,
            Path shape, boolean dark, int alpha) {
        draw(canvas, left, top, right, bottom, 0f, shape, null, dark, alpha);
    }

    public void drawClipped(Canvas canvas, float left, float top, float right, float bottom,
            Path shape, float[] radii, boolean dark, int alpha) {
        draw(canvas, left, top, right, bottom, 0f, shape, radii, dark, alpha);
    }

    private void draw(Canvas canvas, float left, float top, float right, float bottom,
            float radius, Path shape, float[] radii, boolean dark, int alpha) {
        final float width = right - left;
        final float height = bottom - top;
        if (height <= 0 || width <= 0 || alpha == 0) return;
        final float maxR = Math.min(height, width) * .5f;
        final float r = Math.min(radius, maxR);
        if (satin) {
            if (satinMaterial == null) satinMaterial = new SatinEdgeMaterial();
            satinMaterial.draw(canvas, left, top, right, bottom, r, shape, dark, alpha);
            return;
        }
        final boolean canUseRuntimeShader = Build.VERSION.SDK_INT >= 33
                && canvas.isHardwareAccelerated() && !org.telegram.messenger.LiteMode.isThermalPressureHigh();
        if (colorOsGlass) {
            final boolean hasRectGeometry = shape == null || (radii != null && radii.length >= 8);
            if (canUseRuntimeShader && hasRectGeometry) {
                if (colorOsEdge == null) colorOsEdge = new ColorOsGlassEdge();
                if (shape == null) {
                    colorOsEdge.draw(canvas, left, top, width, height, r, r, r, r, dark, alpha);
                } else {
                    colorOsEdge.draw(canvas, left, top, width, height,
                            Math.min(radii[0], maxR), Math.min(radii[2], maxR),
                            Math.min(radii[4], maxR), Math.min(radii[6], maxR), dark, alpha);
                }
            } else {
                drawColorOsFallback(canvas, left, top, width, height, r, shape, radii, dark, alpha);
            }
            return;
        }
        if (subtle && shape == null && canUseRuntimeShader) {
            if (curvedEdge == null) curvedEdge = new CurvedEdge();
            curvedEdge.draw(canvas, left, top, width, height, r, dark, alpha);
            return;
        }
        // View translations can introduce insignificant float differences in the height.
        final float shaderHeight = Math.max(1f, Math.round(height * 16f) / 16f);
        final float density = AndroidUtilities.dpf2(1f);
        if (darkTheme != dark || gradientDensity != density) {
            gradientDensity = density;
            darkTheme = dark;
            resetGradients();
        }
        int slot = -1;
        for (int i = 0; i < shaders.length; i++) {
            if (heights[i] == shaderHeight && shaders[i] != null) {
                slot = i;
                break;
            }
        }
        if (slot < 0) {
            // Keep the falloff close to the edge even when the message field grows.
            final float topDepthDp = subtle ? (dark ? 4.25f : 2f) : 5f;
            final float bottomDepthDp = subtle ? (dark ? 3.4f : 1f) : 5f;
            final float topRamp = Math.min(.14f, AndroidUtilities.dpf2(topDepthDp) / shaderHeight);
            final float bottomRamp = Math.min(.14f, AndroidUtilities.dpf2(bottomDepthDp) / shaderHeight);
            stops[1] = topRamp * .2f;
            stops[2] = topRamp;
            stops[3] = 1f - bottomRamp;
            stops[4] = 1f - bottomRamp * .26f;
            slot = nextSlot;
            heights[slot] = shaderHeight;
            final int[] colors = subtle ? (dark ? SUBTLE_DARK : SUBTLE_LIGHT) : (dark ? DARK : LIGHT);
            shaders[slot] = new LinearGradient(0, 0, 0, shaderHeight, colors, stops, Shader.TileMode.CLAMP);
            if (!subtle) {
                // The side reflection takes over as the original highlights fall off.
                sideStops[0] = topRamp * .15f;
                sideStops[1] = topRamp * 2f;
                sideStops[2] = 1f - sideStops[1];
                sideStops[3] = 1f - sideStops[0];
                sideShaders[slot] = new LinearGradient(0, 0, 0, shaderHeight, dark ? DARK_SIDES : LIGHT_SIDES,
                        sideStops, Shader.TileMode.CLAMP);
            }
            nextSlot = (nextSlot + 1) % shaders.length;
        }

        if (paint.getShader() != shaders[slot]) paint.setShader(shaders[slot]);
        if (paint.getAlpha() != alpha) paint.setAlpha(alpha);
        final int save = canvas.save();
        if (shape != null) {
            canvas.clipPath(shape);
            if (!subtle) {
                if (localShape == null) localShape = new Path();
                shape.offset(0f, -top, localShape);
            }
        }
        canvas.translate(0, top);
        canvas.drawRoundRect(left, 0, right, height, r, r, paint);
        if (!subtle) {
            drawSides(canvas, left, right, height, r, shape != null, sideShaders[slot], alpha);
        }
        canvas.restoreToCount(save);
    }

    /** Zero-allocation, zero-overdraw stroke renderer for API < 33, thermal throttling, or custom paths. */
    private void drawColorOsFallback(Canvas canvas, float left, float top, float width, float height,
            float radius, Path shape, float[] radii, boolean dark, int alpha) {
        final float minSide = Math.min(width, height);
        final float stroke = Math.min(AndroidUtilities.dpf2(dark ? 1.15f : 0.95f), minSide * .18f);
        final float inset = stroke * .5f;
        final LinearGradient outerShader;
        if (dark) {
            if (colorOsFallbackDark == null) {
                colorOsFallbackDark = new LinearGradient(0f, 0f, 0f, 1f,
                        COLOROS_DARK_STROKE, COLOROS_STROKE_STOPS, Shader.TileMode.CLAMP);
            }
            outerShader = colorOsFallbackDark;
        } else {
            if (colorOsFallbackLight == null) {
                colorOsFallbackLight = new LinearGradient(0f, 0f, 0f, 1f,
                        COLOROS_LIGHT_STROKE, COLOROS_STROKE_STOPS, Shader.TileMode.CLAMP);
            }
            outerShader = colorOsFallbackLight;
        }
        colorOsMatrix.setScale(1f, Math.max(1f, height));
        outerShader.setLocalMatrix(colorOsMatrix);

        if (sidePaint.getShader() != outerShader) sidePaint.setShader(outerShader);
        if (sidePaint.getAlpha() != alpha) sidePaint.setAlpha(alpha);
        sidePaint.setStrokeWidth(stroke);

        final int save = canvas.save();
        if (shape != null && (radii == null || radii.length < 8)) {
            canvas.clipPath(shape);
            if (localShape == null) localShape = new Path();
            shape.offset(-left, -top, localShape);
            canvas.translate(left, top);
            sidePaint.setStrokeWidth(stroke * 2f);
            canvas.drawPath(localShape, sidePaint);
        } else if (shape != null) {
            canvas.translate(left, top);
            buildInsetPath(width, height, radii, inset);
            canvas.drawPath(localShape, sidePaint);
            if (!dark && minSide > stroke * 4f) {
                drawColorOsLightInnerFallback(canvas, width, height, 0f, radii, stroke, alpha);
            }
        } else {
            canvas.translate(left, top);
            final float r = Math.max(0f, radius - inset);
            canvas.drawRoundRect(inset, inset, width - inset, height - inset, r, r, sidePaint);
            if (!dark && minSide > stroke * 4f) {
                drawColorOsLightInnerFallback(canvas, width, height, radius, null, stroke, alpha);
            }
        }
        canvas.restoreToCount(save);
    }

    private void drawColorOsLightInnerFallback(Canvas canvas, float width, float height, float radius,
            float[] radii, float outerStroke, int alpha) {
        if (colorOsFallbackLightInner == null) {
            colorOsFallbackLightInner = new LinearGradient(0f, 0f, 0f, 1f,
                    COLOROS_LIGHT_INNER, COLOROS_STROKE_STOPS, Shader.TileMode.CLAMP);
        }
        colorOsFallbackLightInner.setLocalMatrix(colorOsMatrix);
        final float innerStroke = AndroidUtilities.dpf2(1.0f);
        final float innerInset = outerStroke + innerStroke * .5f;
        if (width <= innerInset * 2f || height <= innerInset * 2f) return;
        sidePaint.setShader(colorOsFallbackLightInner);
        sidePaint.setAlpha(alpha);
        sidePaint.setStrokeWidth(innerStroke);
        if (radii != null) {
            buildInsetPath(width, height, radii, innerInset);
            canvas.drawPath(localShape, sidePaint);
        } else {
            final float r = Math.max(0f, radius - innerInset);
            canvas.drawRoundRect(innerInset, innerInset, width - innerInset, height - innerInset, r, r, sidePaint);
        }
    }

    private void buildInsetPath(float width, float height, float[] radii, float inset) {
        if (localShape == null) localShape = new Path();
        localShape.rewind();
        final float maxR = Math.min(width - inset * 2f, height - inset * 2f) * .5f;
        for (int i = 0; i < 8; i++) {
            colorOsInsetRadii[i] = Math.min(maxR, Math.max(0f, radii[i] - inset));
        }
        localShape.addRoundRect(inset, inset, width - inset, height - inset, colorOsInsetRadii, Path.Direction.CW);
    }

    @RequiresApi(33)
    private static final class CurvedEdge {
        private static final String EFFECT = """
                uniform float2 size;
                uniform float radius;
                uniform float density;
                uniform float dark;

                half4 main(float2 position) {
                    float2 centered = position - 0.5 * size;
                    bool upper = centered.y < 0.0;
                    float depth = min(0.14 * size.y, density *
                            (dark > 0.5 ? (upper ? 3.7 : 4.2) : (upper ? 2.0 : 1.0)));
                    float fromHorizontalEdge = 0.5 * size.y - abs(centered.y);
                    // A point in the straight span cannot receive light from the curved caps.
                    if (abs(centered.x) <= 0.5 * size.x - radius && fromHorizontalEdge >= depth) {
                        return half4(0.0);
                    }
                    float2 q = abs(centered) - (0.5 * size - radius);
                    float2 arc = max(q, float2(0.0));
                    float arcLength = length(arc);
                    float distance = arcLength + min(max(q.x, q.y), 0.0) - radius;
                    float vertical = arcLength > 0.0 ? arc.y / arcLength : step(q.x, q.y);
                    float direction = smoothstep(0.05, 0.95, vertical);
                    float fade = 1.0 - smoothstep(0.0, depth, max(0.0, -distance));
                    float strength = dark > 0.5 ? (upper ? 0.24 : 0.29) : (upper ? 0.90 : 0.14);
                    float opacity = strength * fade * fade * direction * direction;
                    float tone = dark > 0.5 || upper ? 1.0 : 0.2784;
                    return half4(half3(tone * opacity), half(opacity));
                }
                """;

        private final RuntimeShader shader = new RuntimeShader(EFFECT);
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private float width, height, radius = -1f, density;
        private boolean dark;

        CurvedEdge() {
            paint.setShader(shader);
        }

        void draw(Canvas canvas, float left, float top, float width, float height, float radius,
                boolean dark, int alpha) {
            if (this.width != width || this.height != height) {
                shader.setFloatUniform("size", width, height);
                this.width = width;
                this.height = height;
            }
            if (this.radius != radius) {
                shader.setFloatUniform("radius", radius);
                this.radius = radius;
            }
            final float density = AndroidUtilities.dpf2(1f);
            if (this.density != density || this.dark != dark) {
                shader.setFloatUniform("density", density);
                shader.setFloatUniform("dark", dark ? 1f : 0f);
                this.density = density;
                this.dark = dark;
            }
            if (paint.getAlpha() != alpha) paint.setAlpha(alpha);
            final int save = canvas.save();
            canvas.translate(left, top);
            canvas.drawRoundRect(0f, 0f, width, height, radius, radius, paint);
            canvas.restoreToCount(save);
        }
    }

    /**
     * ColorOS 17 optical glass rim shader (API 33+).
     * Drawn as a perimeter STROKE band so interior pixels incur zero fragment overdraw,
     * with exact 4-corner SDF (no diagonal cutouts on circles/pills) and a 4-slot shader cache
     * to prevent uniform thrashing when one instance paints multiple surfaces per frame.
     */
    @RequiresApi(33)
    private static final class ColorOsGlassEdge {
        private static final int POOL_SIZE = 4;
        private static final String EFFECT = """
                uniform float2 size;
                uniform float4 radii;
                uniform float density;
                uniform float dark;

                half4 main(float2 position) {
                    float2 halfSize = 0.5 * size;
                    float2 centered = position - halfSize;
                    float rTop = centered.x < 0.0 ? radii.x : radii.y;
                    float rBot = centered.x < 0.0 ? radii.w : radii.z;
                    float r = min(centered.y < 0.0 ? rTop : rBot, min(halfSize.x, halfSize.y));

                    float2 q = abs(centered) - (halfSize - r);
                    float2 arc = max(q, float2(0.0));
                    float arcLen = length(arc);
                    float d = -(arcLen + min(max(q.x, q.y), 0.0) - r);
                    float maxDepth = min(0.5 * min(size.x, size.y), 3.6 * density);
                    if (d <= 0.0 || d >= maxDepth) {
                        return half4(0.0);
                    }

                    float signY = centered.y < 0.0 ? -1.0 : 1.0;
                    float ny;
                    if (arcLen > 0.0001) {
                        ny = (arc.y / arcLen) * signY;
                    } else {
                        ny = (q.y >= q.x) ? signY : 0.0;
                    }
                    float topCurve = smoothstep(0.0, 0.92, clamp(-ny, 0.0, 1.0));
                    float botCurve = smoothstep(0.0, 0.92, clamp(ny, 0.0, 1.0));

                    if (dark > 0.5) {
                        float rimWidth = (0.90 + 0.25 * topCurve + 0.45 * botCurve) * density;
                        float rim = 1.0 - smoothstep(0.32 * density, rimWidth, d);
                        float topFade = 1.0 - smoothstep(0.0, min(maxDepth, 1.5 * density), d);
                        float botFade = 1.0 - smoothstep(0.0, min(maxDepth, 3.0 * density), d);
                        float rimAlpha = rim * (0.085 + 0.165 * topCurve + 0.205 * botCurve);
                        float glowAlpha = 0.025 * topFade * topFade * topCurve
                                + 0.075 * botFade * botFade * botCurve * botCurve;
                        float opacity = clamp(rimAlpha + glowAlpha, 0.0, 0.42);
                        half3 tint = half3(0.95, 0.975, 1.0);
                        return half4(tint * half(opacity), half(opacity));
                    } else {
                        float outerLine = 1.0 - smoothstep(0.30 * density, 0.95 * density, d);
                        float slateA = outerLine * (0.07 + 0.03 * topCurve + 0.08 * botCurve);
                        float innerBand = (1.0 - smoothstep(0.65 * density, (1.55 + 0.45 * botCurve) * density, d))
                                * smoothstep(0.35 * density, 0.85 * density, d);
                        float whiteA = clamp(innerBand * (0.18 + 0.48 * topCurve + 0.30 * botCurve), 0.0, 0.72);
                        // Porter-Duff source-over: pure white specular over crisp cool-slate hairline.
                        float outA = whiteA + slateA * (1.0 - whiteA);
                        half3 slatePremul = half3(0.06, 0.09, 0.16) * half(slateA * (1.0 - whiteA));
                        half3 outPremul = half3(half(whiteA)) + slatePremul;
                        return half4(outPremul, half(clamp(outA, 0.0, 0.85)));
                    }
                }
                """;

        private final RuntimeShader[] shaders = new RuntimeShader[POOL_SIZE];
        private final float[] widths = new float[POOL_SIZE];
        private final float[] heights = new float[POOL_SIZE];
        private final float[] rTLs = new float[POOL_SIZE];
        private final float[] rTRs = new float[POOL_SIZE];
        private final float[] rBRs = new float[POOL_SIZE];
        private final float[] rBLs = new float[POOL_SIZE];
        private final float[] densities = new float[POOL_SIZE];
        private final boolean[] darks = new boolean[POOL_SIZE];
        private final Paint strokePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Paint fillPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final Path asymmetricPath = new Path();
        private final float[] insetRadii = new float[8];
        private int nextSlot;

        ColorOsGlassEdge() {
            strokePaint.setStyle(Paint.Style.STROKE);
        }

        private RuntimeShader acquireShader(float width, float height,
                float rTL, float rTR, float rBR, float rBL, float density, boolean dark) {
            for (int i = 0; i < POOL_SIZE; i++) {
                RuntimeShader cached = shaders[i];
                if (cached != null
                        && widths[i] == width && heights[i] == height
                        && rTLs[i] == rTL && rTRs[i] == rTR && rBRs[i] == rBR && rBLs[i] == rBL
                        && densities[i] == density && darks[i] == dark) {
                    return cached;
                }
            }
            int slot = -1;
            for (int i = 0; i < POOL_SIZE; i++) {
                if (shaders[i] == null) {
                    slot = i;
                    break;
                }
            }
            if (slot < 0) {
                slot = nextSlot;
                nextSlot = (nextSlot + 1) % POOL_SIZE;
            }
            RuntimeShader shader = shaders[slot];
            if (shader == null) {
                shader = new RuntimeShader(EFFECT);
                shaders[slot] = shader;
            }
            if (widths[slot] != width || heights[slot] != height) {
                shader.setFloatUniform("size", width, height);
                widths[slot] = width;
                heights[slot] = height;
            }
            if (rTLs[slot] != rTL || rTRs[slot] != rTR || rBRs[slot] != rBR || rBLs[slot] != rBL) {
                shader.setFloatUniform("radii", rTL, rTR, rBR, rBL);
                rTLs[slot] = rTL;
                rTRs[slot] = rTR;
                rBRs[slot] = rBR;
                rBLs[slot] = rBL;
            }
            if (densities[slot] != density || darks[slot] != dark) {
                shader.setFloatUniform("density", density);
                shader.setFloatUniform("dark", dark ? 1f : 0f);
                densities[slot] = density;
                darks[slot] = dark;
            }
            return shader;
        }

        void draw(Canvas canvas, float left, float top, float width, float height,
                float rTL, float rTR, float rBR, float rBL, boolean dark, int alpha) {
            final float density = AndroidUtilities.dpf2(1f);
            final RuntimeShader shader = acquireShader(width, height, rTL, rTR, rBR, rBL, density, dark);
            final float minSide = Math.min(width, height);
            final float band = Math.min(3.6f * density, minSide * .5f);
            final float inset = band * .5f;
            final boolean uniform = rTL == rTR && rTR == rBR && rBR == rBL;
            final float minCorner = Math.min(Math.min(rTL, rTR), Math.min(rBR, rBL));

            final int save = canvas.save();
            canvas.translate(left, top);
            if (minCorner >= inset && width > band && height > band) {
                if (strokePaint.getShader() != shader) strokePaint.setShader(shader);
                if (strokePaint.getAlpha() != alpha) strokePaint.setAlpha(alpha);
                if (strokePaint.getStrokeWidth() != band) strokePaint.setStrokeWidth(band);
                if (uniform) {
                    final float innerR = Math.max(0f, rTL - inset);
                    canvas.drawRoundRect(inset, inset, width - inset, height - inset, innerR, innerR, strokePaint);
                } else {
                    final float maxR = Math.min(width - band, height - band) * .5f;
                    insetRadii[0] = insetRadii[1] = Math.min(maxR, Math.max(0f, rTL - inset));
                    insetRadii[2] = insetRadii[3] = Math.min(maxR, Math.max(0f, rTR - inset));
                    insetRadii[4] = insetRadii[5] = Math.min(maxR, Math.max(0f, rBR - inset));
                    insetRadii[6] = insetRadii[7] = Math.min(maxR, Math.max(0f, rBL - inset));
                    asymmetricPath.rewind();
                    asymmetricPath.addRoundRect(inset, inset, width - inset, height - inset, insetRadii, Path.Direction.CW);
                    canvas.drawPath(asymmetricPath, strokePaint);
                }
            } else {
                if (fillPaint.getShader() != shader) fillPaint.setShader(shader);
                if (fillPaint.getAlpha() != alpha) fillPaint.setAlpha(alpha);
                if (uniform) {
                    canvas.drawRoundRect(0f, 0f, width, height, rTL, rTL, fillPaint);
                } else {
                    insetRadii[0] = insetRadii[1] = rTL;
                    insetRadii[2] = insetRadii[3] = rTR;
                    insetRadii[4] = insetRadii[5] = rBR;
                    insetRadii[6] = insetRadii[7] = rBL;
                    asymmetricPath.rewind();
                    asymmetricPath.addRoundRect(0f, 0f, width, height, insetRadii, Path.Direction.CW);
                    canvas.drawPath(asymmetricPath, fillPaint);
                }
            }
            canvas.restoreToCount(save);
        }
    }

    private void drawSides(Canvas canvas, float left, float right, float height, float radius,
            boolean clipped, LinearGradient gradient, int alpha) {
        if (sidePaint.getShader() != gradient) sidePaint.setShader(gradient);
        final float depth = Math.min(AndroidUtilities.dpf2(5f), Math.min(height, right - left) * .14f);
        for (int i = 0; i < SIDE_BANDS.length; i++) {
            final float band = depth * SIDE_BANDS[i];
            sidePaint.setAlpha(Math.round(alpha * SIDE_OPACITY[i]));
            if (clipped) {
                sidePaint.setStrokeWidth(band * 2f);
                canvas.drawPath(localShape, sidePaint);
            } else {
                final float inset = band * .5f;
                final float r = Math.max(0f, radius - inset);
                sidePaint.setStrokeWidth(band);
                canvas.drawRoundRect(left + inset, inset, right - inset, height - inset, r, r, sidePaint);
            }
        }
    }
}
