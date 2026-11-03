package app.flexygram.effects;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.graphics.drawable.Drawable;
import android.view.View;
import app.exteraless.appearance.GlassContrastPolicy;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.messenger.Utilities;

/** Local fictional scenes. Two fixed 180x100 wallpaper buffers, reused across slider changes.
 * Blur is coalesced to a frame and only recomputed when its radius or wallpaper changes.
 * No accounts, messages, image loaders, timers, continuous animation or application theme mutation. */
public class GlassPreviewView extends View {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
    private final RectF rect = new RectF();
    private final Path clip = new Path();
    private final Drawable[] icons;
    private final int[] iconColors;
    private final String[] names = {"Sofía Mar", "", "Mateo Ruiz", "", "Luna Ríos"};
    private final String[] profileLabels;
    private final String input, online, received, sent, preview;
    private GlassSettings settings = GlassSettings.defaults();
    private Bitmap wallpaper, blurred;
    private Canvas blurCanvas;
    private int cachedRadius = -1, scene, accent = 0xff449b35;
    private boolean dark, cachedDark, scheduled;
    private final Runnable prepareFrame = () -> {
        scheduled = false;
        prepareWallpaper();
        invalidate();
    };

    public GlassPreviewView(Context context) {
        super(context);
        int[] resources = {R.drawable.ic_ab_back, R.drawable.msg_search, R.drawable.input_attach,
                R.drawable.input_mic, R.drawable.fg_settings_chat, R.drawable.msg_mute,
                R.drawable.outline_profile_call_24, R.drawable.input_gift_s, R.drawable.fg_settings_settings, R.drawable.input_smile};
        icons = new Drawable[resources.length];
        iconColors = new int[resources.length];
        for (int i = 0; i < resources.length; i++) icons[i] = context.getResources().getDrawable(resources[i]).mutate();
        input = text(R.string.FlexyCrystalDemoInput); online = text(R.string.FlexyCrystalDemoOnline);
        received = text(R.string.FlexyCrystalDemoReceived); sent = text(R.string.FlexyCrystalDemoSent);
        preview = text(R.string.FlexyCrystalPreview);
        names[1] = text(R.string.FlexyCrystalDemoGroup); names[3] = text(R.string.FlexyCrystalDemoNotes);
        profileLabels = new String[]{text(R.string.FlexyCrystalDemoMessage), text(R.string.FlexyCrystalDemoMute),
                text(R.string.FlexyCrystalDemoCall), text(R.string.FlexyCrystalDemoGift)};
        setContentDescription(text(R.string.FlexyCrystalPreviewDescription));
        setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_YES);
    }
    private static String text(int id) { return LocaleController.getString(id); }
    public void update(GlassSettings value, int scene, boolean dark, int accent) {
        settings = value; this.scene = scene; this.dark = dark; this.accent = accent;
        if (!scheduled) { scheduled = true; postOnAnimation(prepareFrame); }
    }
    private void prepareWallpaper() {
        if (wallpaper == null || cachedDark != dark) {
            if (wallpaper == null) {
                wallpaper = Bitmap.createBitmap(180, 100, Bitmap.Config.ARGB_8888);
                blurred = Bitmap.createBitmap(180, 100, Bitmap.Config.ARGB_8888);
                blurCanvas = new Canvas(blurred);
            }
            Canvas c = new Canvas(wallpaper);
            c.drawColor(dark ? 0xff16372d : 0xfff3d8a2);
            paint.setStyle(Paint.Style.FILL);
            for (int i = 0; i < 28; i++) {
                paint.setColor(dark ? 0xff336148 : 0xffbcc58d);
                float x = (i * 47 % 190) - 5, y = (i * 29 % 110) - 5;
                c.save(); c.rotate(i * 31, x, y);
                c.drawOval(x, y, x + 10, y + 3, paint);
                c.restore();
                paint.setColor(dark ? 0xff254c42 : 0xffe9b58b);
                c.drawCircle((i * 61 % 180), (i * 17 % 100), 2, paint);
            }
            cachedDark = dark; cachedRadius = -1;
        }
        int radius = settings.enabled && settings.zones != 0 && (dark || settings.opacity < 100) ? settings.blur : 0;
        if (radius != cachedRadius) {
            blurCanvas.drawBitmap(wallpaper, 0, 0, null);
            if (radius > 0) Utilities.stackBlurBitmap(blurred, Math.max(1, radius / 2));
            cachedRadius = radius;
        }
    }
    @Override protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        update(settings, scene, dark, accent);
    }
    @Override protected void onDetachedFromWindow() {
        removeCallbacks(prepareFrame); scheduled = false;
        // Small view-owned buffers can be reclaimed with this view; never recycle a texture in use.
        super.onDetachedFromWindow();
    }
    @Override protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (wallpaper == null) return;
        canvas.save();
        rect.set(0, 0, getWidth(), getHeight()); clip.rewind();
        float corner = Math.min(getWidth() / 360f, getHeight() / 200f) * 16;
        clip.addRoundRect(rect, corner, corner, Path.Direction.CW); canvas.clipPath(clip);
        canvas.drawBitmap(wallpaper, null, rect, null);
        float scale = Math.min(getWidth() / 360f, getHeight() / 200f);
        canvas.translate((getWidth() - 360 * scale) / 2, (getHeight() - 200 * scale) / 2);
        canvas.scale(scale, scale);
        if (scene == 0) drawChat(canvas);
        else if (scene == 1) drawHome(canvas);
        else drawProfile(canvas);
        label(canvas, preview, 275, 13, 9, false, ink());
        canvas.restore();
    }
    private int ink() { return dark ? 0xfff2f5f3 : 0xff18221e; }
    private void label(Canvas c, String text, float x, float y, float size, boolean bold, int color) {
        paint.setStyle(Paint.Style.FILL); paint.setColor(color); paint.setTextSize(size);
        paint.setTypeface(bold ? Typeface.DEFAULT_BOLD : Typeface.DEFAULT);
        c.drawText(text, x, y, paint);
    }
    private void icon(Canvas c, int which, float x, float y, float size, int color) {
        Drawable d = icons[which];
        if (iconColors[which] != color) { d.setTint(color); iconColors[which] = color; }
        d.setBounds((int)x, (int)y, (int)(x + size), (int)(y + size)); d.draw(c);
    }
    private void surface(Canvas c, float l, float t, float r, float b, float round, int zone) {
        boolean effect = settings.enabled && (settings.zones & zone) != 0;
        rect.set(l, t, r, b);
        c.save(); clip.rewind(); clip.addRoundRect(rect, round, round, Path.Direction.CW); c.clipPath(clip);
        if (effect && (dark || settings.opacity < 100)) {
            rect.set(0, 0, 360, 200); c.drawBitmap(blurred, null, rect, null);
        }
        int tint = dark ? 0xff172a24 : 0xfffdfcfa;
        int color = !effect ? tint : dark ? (tint & 0xffffff) | (Math.round(settings.opacity * 2.55f * .85f) << 24)
                : GlassContrastPolicy.lightSurface(tint, Math.round(settings.opacity * 2.55f));
        paint.setColor(color); paint.setStyle(Paint.Style.FILL); rect.set(l, t, r, b);
        c.drawRoundRect(rect, round, round, paint); c.restore();
        if (effect && settings.width > 0 && settings.edge > 0) {
            int border = settings.color == 0 ? accent : settings.color;
            float style = settings.style == 0 ? .55f : settings.style == 2 ? 1f : .85f;
            paint.setColor((border & 0xffffff) | (Math.round(settings.edge * 2.55f * style) << 24));
            paint.setStyle(Paint.Style.STROKE); float width = settings.width / 10f; paint.setStrokeWidth(width);
            rect.inset(width / 2, width / 2); c.drawRoundRect(rect, round, round, paint); paint.setStyle(Paint.Style.FILL);
        }
    }
    private void avatar(Canvas c, float x, float y, float radius, String initial, int color) {
        paint.setColor(color); paint.setStyle(Paint.Style.FILL); c.drawCircle(x, y, radius, paint);
        label(c, initial, x - radius * .3f, y + radius * .35f, radius, true, Color.WHITE);
    }
    private void bubble(Canvas c, String message, float l, float t, float r, int color) {
        paint.setStyle(Paint.Style.FILL); paint.setColor(color); rect.set(l, t, r, t + 28); c.drawRoundRect(rect, 13, 13, paint);
        c.save(); c.clipRect(l + 8, t, r - 5, t + 28); label(c, message, l + 9, t + 18, 11, false, ink()); c.restore();
    }
    private void drawChat(Canvas c) {
        surface(c, 9, 22, 351, 65, 22, 2);
        icon(c, 0, 17, 34, 18, ink()); avatar(c, 75, 43, 14, "S", 0xffb27757);
        label(c, "12", 40, 47, 10, true, accent); label(c, names[0], 96, 40, 12, true, ink());
        label(c, online, 96, 54, 9, false, accent); icon(c, 1, 304, 34, 18, ink());
        bubble(c, received, 13, 78, 219, dark ? 0xff284238 : 0xfffdfbf4);
        bubble(c, sent, 125, 115, 347, dark ? 0xff315d39 : 0xffd9edbd);
        surface(c, 9, 158, 44, 193, 18, 1); icon(c, 2, 17, 166, 19, ink());
        surface(c, 51, 158, 307, 193, 18, 1); icon(c, 9, 62, 167, 17, ink());
        label(c, input, 87, 180, 12, false, ink());
        surface(c, 314, 158, 349, 193, 18, 1); icon(c, 3, 323, 166, 19, accent);
    }
    private void drawHome(Canvas c) {
        label(c, "FlexyGram", 14, 37, 19, true, accent);
        surface(c, 284, 19, 316, 51, 16, 8); icon(c, 1, 292, 27, 16, ink());
        surface(c, 322, 19, 354, 51, 16, 8); icon(c, 8, 330, 27, 16, ink());
        for (int i = 0; i < 3; i++) {
            float x = 10 + i * 116;
            surface(c, x, 58, x + 109, 83, 13, 32);
            label(c, i == 0 ? text(R.string.FilterAllChats) : i == 1 ? text(R.string.FilterGroups) : "Bots", x + 14, 75, 10, i == 0, ink());
        }
        paint.setColor(dark ? 0xe519241f : 0xe5ffffff); rect.set(0, 88, 360, 200); c.drawRect(rect, paint);
        for (int i = 0; i < 3; i++) {
            float y = 108 + i * 29;
            avatar(c, 25, y, 11, i == 0 ? "S" : i == 1 ? "D" : "M", 0xff6d9179);
            label(c, names[i], 44, y - 2, 10, true, ink()); label(c, i == 0 ? sent : received, 44, y + 11, 8, false, ink());
        }
        surface(c, 44, 171, 316, 197, 13, 4);
        for (int i = 0; i < 4; i++) icon(c, i == 0 ? 4 : i == 1 ? 6 : i == 2 ? 7 : 8, 72 + i * 64, 177, 15, i == 0 ? accent : ink());
    }
    private void drawProfile(Canvas c) {
        surface(c, 10, 20, 42, 52, 16, 64); icon(c, 0, 18, 28, 16, ink());
        surface(c, 318, 20, 350, 52, 16, 64); icon(c, 8, 326, 28, 16, ink());
        avatar(c, 180, 52, 29, "L", 0xffa77f57); label(c, names[4], 147, 97, 13, true, ink());
        label(c, online, 163, 110, 9, false, ink());
        for (int i = 0; i < 4; i++) {
            float x = 10 + i * 88;
            surface(c, x, 120, x + 80, 163, 12, 64); icon(c, i + 4, x + 30, 125, 18, ink());
            label(c, profileLabels[i], x + 8, 155, 9, true, ink());
        }
        surface(c, 10, 172, 350, 197, 13, 64);
        label(c, text(R.string.FlexyCrystalDemoPosts), 36, 189, 10, true, accent);
        label(c, text(R.string.FlexyCrystalDemoArchived), 129, 189, 10, false, ink());
        label(c, text(R.string.FlexyCrystalDemoGifts), 265, 189, 10, false, ink());
    }
}
