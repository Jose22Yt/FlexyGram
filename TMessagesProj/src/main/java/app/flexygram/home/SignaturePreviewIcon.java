/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.text.style.ReplacementSpan;
import org.telegram.messenger.AndroidUtilities;

/** Small, fixed native line icons. Geometry is shared and never rebuilt in draw(). */
public final class SignaturePreviewIcon extends ReplacementSpan {
    private static final Path[] ICONS = new Path[28];
    static {
        for (int i = 1; i < ICONS.length; i++) ICONS[i] = new Path();
        Path p = ICONS[1]; // File
        p.moveTo(3, 1); p.lineTo(8, 1); p.lineTo(10, 3); p.lineTo(10, 11); p.lineTo(3, 11); p.close();
        p.moveTo(8, 1); p.lineTo(8, 4); p.lineTo(10, 4);
        p.moveTo(4.5f, 6); p.lineTo(8.5f, 6);
        p.moveTo(4.5f, 8); p.lineTo(8, 8);

        p = ICONS[2]; // Mic / Voice
        p.moveTo(5, 2); p.lineTo(5, 6.5f); p.lineTo(6, 7.5f); p.lineTo(7, 6.5f); p.lineTo(7, 2); p.lineTo(5, 2);
        p.moveTo(3, 5.5f); p.lineTo(3, 7); p.lineTo(5, 9); p.lineTo(7, 9); p.lineTo(9, 7); p.lineTo(9, 5.5f);
        p.moveTo(6, 9); p.lineTo(6, 11);

        p = ICONS[3]; // Music note
        p.moveTo(5, 9); p.lineTo(5, 3); p.lineTo(9, 2); p.lineTo(9, 7.5f);
        p.moveTo(5, 8); p.lineTo(3, 8.5f); p.lineTo(3, 10); p.lineTo(5, 9);
        p.moveTo(9, 7); p.lineTo(7, 7.5f); p.lineTo(7, 9); p.lineTo(9, 8);

        p = ICONS[4]; // Link
        p.moveTo(5, 4); p.lineTo(3, 4); p.lineTo(1.5f, 6); p.lineTo(3, 8); p.lineTo(5, 8);
        p.moveTo(7, 4); p.lineTo(9, 4); p.lineTo(10.5f, 6); p.lineTo(9, 8); p.lineTo(7, 8);
        p.moveTo(4, 6); p.lineTo(8, 6);

        p = ICONS[5]; // Event / Group
        p.moveTo(2, 3); p.lineTo(10, 3); p.lineTo(10, 10); p.lineTo(2, 10); p.close();
        p.moveTo(4, 1); p.lineTo(4, 4);
        p.moveTo(8, 1); p.lineTo(8, 4);
        p.moveTo(2, 5); p.lineTo(10, 5);

        p = ICONS[6]; // Photo
        p.moveTo(1.5f, 2); p.lineTo(10.5f, 2); p.lineTo(10.5f, 10); p.lineTo(1.5f, 10); p.close();
        p.moveTo(2, 9); p.lineTo(5, 6); p.lineTo(6.5f, 7.5f); p.lineTo(8, 6); p.lineTo(10, 8);

        p = ICONS[7]; // Video
        p.moveTo(2, 2); p.lineTo(10, 2); p.lineTo(10, 10); p.lineTo(2, 10); p.close();
        p.moveTo(5, 4); p.lineTo(8, 6); p.lineTo(5, 8); p.close();

        p = ICONS[8]; // Location
        p.moveTo(6, 11); p.lineTo(3, 7); p.lineTo(2.5f, 5); p.lineTo(3.5f, 2.5f); p.lineTo(6, 1.5f);
        p.lineTo(8.5f, 2.5f); p.lineTo(9.5f, 5); p.lineTo(9, 7); p.close();
        p.moveTo(5, 4.5f); p.lineTo(7, 4.5f);

        p = ICONS[9]; // Contact
        p.moveTo(4, 2.5f); p.lineTo(5, 1.5f); p.lineTo(7, 1.5f); p.lineTo(8, 2.5f); p.lineTo(8, 4.5f);
        p.lineTo(7, 5.5f); p.lineTo(5, 5.5f); p.lineTo(4, 4.5f); p.close();
        p.moveTo(2, 10); p.lineTo(2.5f, 8); p.lineTo(4, 7); p.lineTo(8, 7); p.lineTo(9.5f, 8); p.lineTo(10, 10);

        p = ICONS[10]; // Archive / Zip
        p.moveTo(1.5f, 2.5f); p.lineTo(10.5f, 2.5f); p.lineTo(10.5f, 5f); p.lineTo(1.5f, 5f); p.close();
        p.moveTo(2.5f, 5f); p.lineTo(2.5f, 10.5f); p.lineTo(9.5f, 10.5f); p.lineTo(9.5f, 5f);
        p.moveTo(4.5f, 7.5f); p.lineTo(7.5f, 7.5f);

        p = ICONS[11]; // PDF: folded page with a vector PDF mark.
        page(p);
        p.moveTo(2.5f,8.5f);p.lineTo(2.5f,5.5f);p.lineTo(4,5.5f);p.lineTo(4,7);p.lineTo(2.5f,7);
        p.moveTo(5,8.5f);p.lineTo(5,5.5f);p.lineTo(6,5.5f);p.lineTo(6.7f,6.3f);p.lineTo(6.7f,7.7f);p.lineTo(6,8.5f);p.close();
        p.moveTo(8,8.5f);p.lineTo(8,5.5f);p.lineTo(9.5f,5.5f);p.moveTo(8,7);p.lineTo(9.2f,7);

        p = ICONS[12]; // Text document.
        page(p);p.moveTo(3.5f,5.5f);p.lineTo(8.5f,5.5f);p.moveTo(3.5f,7.5f);p.lineTo(8.5f,7.5f);p.moveTo(3.5f,9.5f);p.lineTo(7,9.5f);
        p = ICONS[13]; // Animation: film frame with a loop arrow.
        p.addRect(1,2,11,10,Path.Direction.CW);p.moveTo(3,2);p.lineTo(3,10);p.moveTo(9,2);p.lineTo(9,10);
        p.moveTo(7.5f,4.5f);p.cubicTo(4,2.5f,3.5f,9,7.5f,7.5f);p.moveTo(7.5f,7.5f);p.lineTo(7.5f,5.8f);p.moveTo(7.5f,7.5f);p.lineTo(5.8f,7.5f);
        p = ICONS[14]; // Sticker with peeled corner.
        p.moveTo(2,1.5f);p.lineTo(10,1.5f);p.lineTo(10,7);p.lineTo(6,11);p.lineTo(2,11);p.close();p.moveTo(6,11);p.lineTo(6,7);p.lineTo(10,7);
        p.moveTo(4,4);p.lineTo(4.1f,4);p.moveTo(7,4);p.lineTo(7.1f,4);p.moveTo(4,6);p.quadTo(5.5f,7,7,6);
        p = ICONS[15]; // Poll bars.
        p.moveTo(2,1.5f);p.lineTo(2,10.5f);p.lineTo(11,10.5f);p.moveTo(4,8);p.lineTo(4,6);p.moveTo(7,8);p.lineTo(7,3);p.moveTo(10,8);p.lineTo(10,5);
        p = ICONS[16]; // Pin.
        p.moveTo(4,1.5f);p.lineTo(9,3);p.lineTo(7,5);p.lineTo(7,8);p.lineTo(3,6.5f);p.lineTo(5,4.5f);p.close();p.moveTo(4.5f,7);p.lineTo(2,11);
        p = ICONS[17]; // Edit pencil.
        p.moveTo(2,8);p.lineTo(8.5f,1.5f);p.lineTo(10.5f,3.5f);p.lineTo(4,10);p.lineTo(1.5f,10.5f);p.close();p.moveTo(7,3);p.lineTo(9,5);
        p = ICONS[18]; // Channel megaphone.
        p.moveTo(2,4.5f);p.lineTo(5,4.5f);p.lineTo(10,2);p.lineTo(10,9);p.lineTo(5,6.5f);p.lineTo(2,6.5f);p.close();p.moveTo(4,6.5f);p.lineTo(5,10);
        p = ICONS[19]; // Admin shield with check.
        p.moveTo(6,1);p.lineTo(10,2.5f);p.lineTo(10,6);p.quadTo(10,9,6,11);p.quadTo(2,9,2,6);p.lineTo(2,2.5f);p.close();p.moveTo(4,5.5f);p.lineTo(5.5f,7);p.lineTo(8,4.5f);
        p = ICONS[20]; // Owner crown.
        p.moveTo(2,9);p.lineTo(1,3);p.lineTo(4,5);p.lineTo(6,1.5f);p.lineTo(8,5);p.lineTo(11,3);p.lineTo(10,9);p.close();p.moveTo(2,11);p.lineTo(10,11);
        p = ICONS[21]; // Deleted message: trash bin.
        p.moveTo(2,3);p.lineTo(10,3);p.moveTo(4,3);p.lineTo(4,1);p.lineTo(8,1);p.lineTo(8,3);p.moveTo(3,3);p.lineTo(3.5f,11);p.lineTo(8.5f,11);p.lineTo(9,3);p.moveTo(5,5);p.lineTo(5,9);p.moveTo(7,5);p.lineTo(7,9);
        p = ICONS[22]; // Joined: arrow entering a door.
        p.moveTo(6,1);p.lineTo(10,1);p.lineTo(10,11);p.lineTo(6,11);p.moveTo(1,6);p.lineTo(7,6);p.moveTo(4.5f,3.5f);p.lineTo(7,6);p.lineTo(4.5f,8.5f);
        p = ICONS[23]; // Left: arrow exiting a door.
        p.moveTo(5,1);p.lineTo(1,1);p.lineTo(1,11);p.lineTo(5,11);p.moveTo(5,6);p.lineTo(11,6);p.moveTo(8.5f,3.5f);p.lineTo(11,6);p.lineTo(8.5f,8.5f);
        p = ICONS[24]; // Android package.
        p.moveTo(3,4);p.quadTo(6,1,9,4);p.lineTo(9,10);p.lineTo(3,10);p.close();p.moveTo(4,3);p.lineTo(3,1);p.moveTo(8,3);p.lineTo(9,1);p.moveTo(5,5);p.lineTo(5.1f,5);p.moveTo(7,5);p.lineTo(7.1f,5);p.moveTo(1,5);p.lineTo(1,8);p.moveTo(11,5);p.lineTo(11,8);
        p = ICONS[25]; // Spreadsheet grid.
        p.addRect(1.5f,1.5f,10.5f,10.5f,Path.Direction.CW);p.moveTo(1.5f,4.5f);p.lineTo(10.5f,4.5f);p.moveTo(1.5f,7.5f);p.lineTo(10.5f,7.5f);p.moveTo(4.5f,1.5f);p.lineTo(4.5f,10.5f);p.moveTo(7.5f,4.5f);p.lineTo(7.5f,10.5f);
        p = ICONS[26]; // Presentation screen.
        p.addRect(1,2,11,8,Path.Direction.CW);p.moveTo(6,8);p.lineTo(6,10);p.moveTo(3.5f,11);p.lineTo(6,10);p.lineTo(8.5f,11);p.moveTo(3,6);p.lineTo(5,4);p.lineTo(7,5);p.lineTo(9,3.5f);
        p = ICONS[27]; // Word-processing document.
        page(p);p.moveTo(3.5f,5.5f);p.lineTo(4.5f,9);p.lineTo(6,6.5f);p.lineTo(7.5f,9);p.lineTo(8.5f,5.5f);
    }

    private static void page(Path p) {
        p.moveTo(1.5f,1);p.lineTo(8,1);p.lineTo(10.5f,3.5f);p.lineTo(10.5f,11);p.lineTo(1.5f,11);p.close();
        p.moveTo(8,1);p.lineTo(8,3.5f);p.lineTo(10.5f,3.5f);
    }

    private static final Paint sharedIconPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    static {
        sharedIconPaint.setStyle(Paint.Style.STROKE);
        sharedIconPaint.setStrokeWidth(1.2f);
        sharedIconPaint.setStrokeCap(Paint.Cap.ROUND);
        sharedIconPaint.setStrokeJoin(Paint.Join.ROUND);
    }

    private static final android.graphics.drawable.Drawable[] originalIcons = new android.graphics.drawable.Drawable[28];
    private static final int[] originalColors = new int[28];
    private static final boolean[] originalTintSet = new boolean[28];
    private static float originalDensity = -1;

    private static boolean drawOriginal(Canvas canvas, int kind, float x, float y, float size, Paint ink) {
        if (!app.flexygram.icons.ExactIcons.isEnabled()) return false;
        if (originalDensity != AndroidUtilities.density) {
            java.util.Arrays.fill(originalIcons, null);
            java.util.Arrays.fill(originalTintSet, false);
            originalDensity = AndroidUtilities.density;
        }
        android.graphics.drawable.Drawable icon = originalIcons[kind];
        if (icon == null) {
            icon = app.flexygram.icons.ExactIcons.direct(app.flexygram.icons.IosOriginalAssets.PREVIEW[kind]);
            if (icon == null) return false;
            originalIcons[kind] = icon;
        }
        if (!originalTintSet[kind] || originalColors[kind] != ink.getColor()) {
            icon.setTint(ink.getColor()); originalColors[kind] = ink.getColor(); originalTintSet[kind] = true;
        }
        icon.setAlpha(ink.getAlpha());
        int side = Math.round(size);
        icon.setBounds(0, 0, side, side);
        canvas.save(); canvas.translate(x, y); icon.draw(canvas); canvas.restore();
        return true;
    }

    private final int kind;
    public SignaturePreviewIcon(int kind) { this.kind = kind >= 1 && kind < ICONS.length ? kind : 1; }
    @Override public int getSize(Paint paint, CharSequence text, int start, int end, Paint.FontMetricsInt fm) { return AndroidUtilities.dp(16); }
    @Override public void draw(Canvas c, CharSequence text, int start, int end, float x, int top, int y, int bottom, Paint p) {
        float size = AndroidUtilities.dp(12);
        draw(c, kind, x, (top + bottom - size) * .5f, size, p);
    }
    public static void draw(Canvas c, int iconKind, float x, float y, float size, Paint p) {
        int index = iconKind >= 1 && iconKind < ICONS.length && ICONS[iconKind] != null ? iconKind : 1;
        if (drawOriginal(c, index, x, y, size, p)) return;
        float factor = size / 12f;
        sharedIconPaint.setColor(p.getColor());
        sharedIconPaint.setAlpha(p.getAlpha());
        c.save();
        c.translate(x, y);
        c.scale(factor, factor);
        c.drawPath(ICONS[index], sharedIconPaint);
        c.restore();
    }
}
