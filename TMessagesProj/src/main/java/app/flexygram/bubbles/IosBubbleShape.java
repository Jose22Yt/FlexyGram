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
    private static final int MAX_TEMPLATE_CACHE = 32;
    private static final float[] SOURCE_X = {0, 18, 19, 43};
    private static final float[] SOURCE_Y = {0, 19, 20, 37};
    private static final java.util.LinkedHashMap<Long, TemplateEntry> TEMPLATE_CACHE =
            new java.util.LinkedHashMap<Long, TemplateEntry>(16, 0.75f, true) {
                @Override
                protected boolean removeEldestEntry(java.util.Map.Entry<Long, TemplateEntry> eldest) {
                    return size() > MAX_TEMPLATE_CACHE;
                }
            };

    private static final class TemplateEntry {
        final Path template;
        final Path[] pieces;
        final boolean[] nonEmpty;
        TemplateEntry(Path template, Path[] pieces, boolean[] nonEmpty) {
            this.template = template;
            this.pieces = pieces;
            this.nonEmpty = nonEmpty;
        }
    }

    private final Matrix mirror = new Matrix();
    private final float[] corners = new float[8];
    private final Path cached = new Path();
    private final Path piece = new Path();
    private final RectF rect = new RectF();
    private final RectF sourceRect = new RectF(), targetRect = new RectF();
    private final Matrix stretch = new Matrix();
    private final float[] targetX = new float[4], targetY = new float[4];
    private int width = -1, height, lastFlags;
    private float lastDensity, lastMain, lastNear;

    public void build(Path result, Rect bounds, float density, float mainRadius, float auxiliaryRadius, boolean outgoing, boolean topNear,
                      boolean bottomNear, boolean media, boolean noTail, boolean buttons) {
        int flags = (outgoing ? 1 : 0) | (topNear ? 2 : 0) | (bottomNear ? 4 : 0) | (media ? 8 : 0) | (noTail ? 16 : 0) | (buttons ? 32 : 0);
        if (width != bounds.width() || height != bounds.height() || lastFlags != flags || lastDensity != density || lastMain != mainRadius || lastNear != auxiliaryRadius) {
            width = bounds.width(); height = bounds.height(); lastFlags = flags; lastDensity = density; lastMain = mainRadius; lastNear = auxiliaryRadius;
            float mainPt = mainRadius / density;
            float auxPt = auxiliaryRadius / density;
            boolean hasTail = !media && !noTail && !bottomNear && !buttons;
            float d = Math.min(density, Math.min(width / 43f, height / 37f));
            float radiusPt = Math.min(mainPt, 16f);
            float nearPt = Math.min(auxPt, radiusPt);
            float bottomRightPt = (bottomNear || buttons) ? nearPt : radiusPt;
            if (width <= 0 || height <= 0) {
                cached.rewind();
            } else if (!hasTail && radiusPt <= 15f && bottomRightPt <= 15f) {
                // Fast analytic path: when there is no tail and bottom corners stay strictly inside
                // the [20..35] cap, 9-slicing is geometrically identical to a single scaled round rect.
                float r = radiusPt * d;
                float topR = (topNear ? nearPt : radiusPt) * d;
                float botR = bottomRightPt * d;
                corners[0] = corners[1] = r;
                corners[2] = corners[3] = topR;
                corners[4] = corners[5] = botR;
                corners[6] = corners[7] = r;
                float rightInset = (media ? 2f : 8f) * d;
                rect.set(2f * d, 2f * d, width - rightInset, height - 2f * d);
                cached.rewind();
                cached.addRoundRect(rect, corners, Path.Direction.CW);
            } else {
                TemplateEntry entry = obtainTemplate(flags & ~1, mainPt, auxPt, topNear, bottomNear, media, noTail, buttons);
                if (Math.abs(width - 43f * d) < 0.01f && Math.abs(height - 37f * d) < 0.01f) {
                    cached.set(entry.template);
                    stretch.setScale(d, d);
                    cached.transform(stretch);
                } else {
                    stretchTemplate(entry, width, height, d);
                }
            }
            if (!outgoing && !cached.isEmpty()) {
                mirror.setScale(-1, 1);
                mirror.postTranslate(width, 0);
                cached.transform(mirror);
            }
        }
        result.set(cached);
        result.offset(bounds.left, bounds.top);
    }

    private static TemplateEntry obtainTemplate(int templateFlags, float mainRadius, float auxiliaryRadius, boolean topNear,
                                                boolean bottomNear, boolean media, boolean noTail, boolean buttons) {
        int mainKey = Math.round(Math.min(mainRadius, 16f) * 100f);
        int auxKey = Math.round(Math.min(auxiliaryRadius, Math.min(mainRadius, 16f)) * 100f);
        long key = ((long) templateFlags << 32) | (((long) (mainKey & 0xFFFF)) << 16) | (auxKey & 0xFFFF);
        synchronized (TEMPLATE_CACHE) {
            TemplateEntry existing = TEMPLATE_CACHE.get(key);
            if (existing != null) return existing;
        }
        Path template = new Path();
        RectF tmpRect = new RectF();
        float left = 2, right = 41, top = 2, bottom = 35, edge = media ? right : 35;
        float radius = Math.min(mainRadius, 16), near = Math.min(auxiliaryRadius, radius);
        float[] radii = {radius, radius, topNear ? near : radius, topNear ? near : radius,
                bottomNear || buttons ? near : radius, bottomNear || buttons ? near : radius, radius, radius};
        tmpRect.set(left, top, edge, bottom);
        template.addRoundRect(tmpRect, radii, Path.Direction.CW);
        if (!media && !noTail && !bottomNear && !buttons) {
            Path tail = new Path();
            // Exact formContext quadratics of the lower half of (24,16,27,17), translated by (2,2).
            if (radius >= 14) {
                tail.moveTo(26, 26.5f); tail.quadTo(26, 35, 39.5f, 35); tail.quadTo(53, 35, 53, 26.5f); tail.close();
            } else {
                tmpRect.set(24, 26.5f, 53, 35); tail.addRect(tmpRect, Path.Direction.CW);
            }
            tmpRect.set(18.5f, 18, 35, 27); tail.addRect(tmpRect, Path.Direction.CW);
            template.op(tail, Path.Op.UNION);
            // Exact upper ellipse cutout (33,14,23,21), translated by (2,2).
            Path cutout = new Path();
            tmpRect.set(35, 16, 58, 37); cutout.addOval(tmpRect, Path.Direction.CW);
            template.op(cutout, Path.Op.DIFFERENCE);
            Path clip = new Path();
            tmpRect.set(0, 0, 43, 37); clip.addRect(tmpRect, Path.Direction.CW);
            template.op(clip, Path.Op.INTERSECT);
        }
        Path[] pieces = new Path[9];
        boolean[] nonEmpty = new boolean[9];
        Path slice = new Path();
        for (int y = 0; y < 3; y++) {
            for (int x = 0; x < 3; x++) {
                int idx = y * 3 + x;
                tmpRect.set(SOURCE_X[x], SOURCE_Y[y], SOURCE_X[x + 1], SOURCE_Y[y + 1]);
                slice.rewind();
                slice.addRect(tmpRect, Path.Direction.CW);
                Path p = new Path(template);
                p.op(slice, Path.Op.INTERSECT);
                pieces[idx] = p;
                nonEmpty[idx] = !p.isEmpty();
            }
        }
        TemplateEntry created = new TemplateEntry(template, pieces, nonEmpty);
        synchronized (TEMPLATE_CACHE) {
            TemplateEntry race = TEMPLATE_CACHE.get(key);
            if (race != null) return race;
            TEMPLATE_CACHE.put(key, created);
            return created;
        }
    }

    private void stretchTemplate(TemplateEntry entry, int width, int height, float d) {
        cached.rewind();
        if (width <= 0 || height <= 0) return;
        // UIImage.stretchableImage: outgoing cap point (18,19), one-point center.
        // Keep the native caps, including the subtle corner segments crossing those points.
        targetX[0] = 0; targetX[1] = 18 * d; targetX[2] = width - 24 * d; targetX[3] = width;
        targetY[0] = 0; targetY[1] = 19 * d; targetY[2] = height - 17 * d; targetY[3] = height;
        for (int y = 0; y < 3; y++) {
            if (targetY[y + 1] <= targetY[y]) continue;
            for (int x = 0; x < 3; x++) {
                if (targetX[x + 1] <= targetX[x]) continue;
                int idx = y * 3 + x;
                if (!entry.nonEmpty[idx]) continue;
                sourceRect.set(SOURCE_X[x], SOURCE_Y[y], SOURCE_X[x + 1], SOURCE_Y[y + 1]);
                targetRect.set(targetX[x], targetY[y], targetX[x + 1], targetY[y + 1]);
                piece.set(entry.pieces[idx]);
                stretch.setRectToRect(sourceRect, targetRect, Matrix.ScaleToFit.FILL);
                piece.transform(stretch);
                if (cached.isEmpty()) cached.set(piece);
                else cached.op(piece, Path.Op.UNION);
            }
        }
    }
}
