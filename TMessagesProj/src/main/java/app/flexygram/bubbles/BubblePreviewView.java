package app.flexygram.bubbles;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.drawable.BitmapDrawable;
import android.graphics.drawable.Drawable;
import android.text.Layout;
import android.text.StaticLayout;
import android.text.TextPaint;
import android.text.TextUtils;
import android.view.View;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.NotificationCenter;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.MessageDrawable;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.ChatBackgroundDrawable;
import org.telegram.ui.Components.AnimatedFileDrawable;
import org.telegram.ui.Components.MotionBackgroundDrawable;

/** Synthetic conversation using the real bubble renderer and current theme wallpaper.
 * No messages/accounts, private chat loading, background animation or permanent draw loop. */
public final class BubblePreviewView extends View implements NotificationCenter.NotificationCenterDelegate {
    private final MessageDrawable[] bubbles = new MessageDrawable[4];
    private final MessageDrawable.PathDrawParams[] caches = new MessageDrawable.PathDrawParams[4];
    private final StaticLayout[] labels = new StaticLayout[4];
    private final int[] tops = new int[4];
    private final String[] samples;
    private final TextPaint text = new TextPaint(Paint.ANTI_ALIAS_FLAG);
    private final TextPaint time = new TextPaint(Paint.ANTI_ALIAS_FLAG);
    private final Paint backdrop = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path frame = new Path();
    private final RectF frameBounds = new RectF();
    private final Rect wallpaperBounds = new Rect();
    private final Drawable check, halfCheck;
    private Drawable wallpaper;
    private boolean wallpaperMotion;
    private SignatureWallpaperBlur.Owner blurOwner;
    private final MessageDrawable.GlassSource cachedWallpaper = (canvas, shape) ->
            blurOwner != null && blurOwner.draw(canvas, shape, 0, 0);
    public void settingsChanged() {
        if (blurOwner != null) blurOwner.prepare(wallpaper, wallpaperMotion, Theme.getColor(Theme.key_windowBackgroundGray));
        invalidate();
    }
    private int checkColor;
    private static final String TIME = "09:41";

    public BubblePreviewView(Context context) {
        super(context);
        samples = new String[]{LocaleController.getString(R.string.FlexyBubblePreviewIncoming),
                LocaleController.getString(R.string.FlexyBubblePreviewGroupIncoming),
                LocaleController.getString(R.string.FlexyBubblePreviewOutgoing),
                LocaleController.getString(R.string.FlexyBubblePreviewGroupOutgoing)};
        for (int i = 0; i < 4; i++) {
            bubbles[i] = new MessageDrawable(i % 2 == 0 ? MessageDrawable.TYPE_MEDIA : MessageDrawable.TYPE_TEXT, i >= 2, false);
            caches[i] = new MessageDrawable.PathDrawParams();
        }
        check = context.getResources().getDrawable(R.drawable.msg_check_s).mutate();
        halfCheck = context.getResources().getDrawable(R.drawable.msg_halfcheck).mutate();
        setContentDescription(String.join(". ", samples));
        refreshTheme();
    }

    private void refreshTheme() {
        Theme.createChatResources(getContext(), false);
        if (Theme.chat_msgTextPaint != null) text.set(Theme.chat_msgTextPaint);
        else text.setTextSize(14 * getResources().getDisplayMetrics().scaledDensity);
        if (Theme.chat_timePaint != null) time.set(Theme.chat_timePaint);
        else time.setTextSize(11 * getResources().getDisplayMetrics().scaledDensity);
        checkColor = Theme.getColor(Theme.key_chat_outSentCheckRead);
        check.setTint(checkColor); halfCheck.setTint(checkColor);
        Drawable source = Theme.getCachedWallpaperNonBlocking();
        wallpaperMotion = Theme.isWallpaperMotion() || source instanceof MotionBackgroundDrawable || source instanceof AnimatedFileDrawable;
        if (source instanceof ChatBackgroundDrawable) source = ((ChatBackgroundDrawable) source).getDrawable(false);
        // Borrow only a still bitmap from animated gradients. Never attach/start their renderer.
        if (source instanceof MotionBackgroundDrawable) {
            android.graphics.Bitmap bitmap = ((MotionBackgroundDrawable) source).getBitmap();
            wallpaper = bitmap != null && !bitmap.isRecycled() ? new BitmapDrawable(getResources(), bitmap) : null;
        } else if (source instanceof AnimatedFileDrawable) {
            wallpaper = null;
        } else if (source != null && source.getConstantState() != null) {
            wallpaper = source.getConstantState().newDrawable(getResources()).mutate();
        } else wallpaper = null;
        if (wallpaper instanceof BitmapDrawable) ((BitmapDrawable) wallpaper).setFilterBitmap(true);
        updateWallpaperBounds(getWidth(), getHeight());
        settingsChanged();
        requestLayout();
        invalidate();
    }

    @Override protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        blurOwner = new SignatureWallpaperBlur.Owner(this);
        for (MessageDrawable bubble : bubbles) bubble.setFlexyGlassSource(cachedWallpaper);
        NotificationCenter center = NotificationCenter.getGlobalInstance();
        center.addObserver(this, NotificationCenter.didSetNewTheme);
        center.addObserver(this, NotificationCenter.didApplyNewTheme);
        center.addObserver(this, NotificationCenter.didSetNewWallpapper);
        refreshTheme();
    }
    @Override protected void onDetachedFromWindow() {
        NotificationCenter center = NotificationCenter.getGlobalInstance();
        center.removeObserver(this, NotificationCenter.didSetNewTheme);
        center.removeObserver(this, NotificationCenter.didApplyNewTheme);
        center.removeObserver(this, NotificationCenter.didSetNewWallpapper);
        if (blurOwner != null) { blurOwner.close(); blurOwner = null; }
        for (MessageDrawable bubble : bubbles) bubble.setFlexyGlassSource(null);
        wallpaper = null; // Never recycle the theme owner's original bitmap.
        super.onDetachedFromWindow();
    }
    @Override public void didReceivedNotification(int id, int account, Object... args) { refreshTheme(); }

    private StaticLayout layout(String sample, int width) {
        return StaticLayout.Builder.obtain(sample, 0, sample.length(), text, Math.max(1, width))
                .setAlignment(Layout.Alignment.ALIGN_NORMAL).setIncludePad(false)
                .setMaxLines(2).setEllipsize(TextUtils.TruncateAt.END).build();
    }
    @Override protected void onMeasure(int widthSpec, int heightSpec) {
        int width = MeasureSpec.getSize(widthSpec), side = AndroidUtilities.dp(16);
        int maximum = Math.max(1, Math.min(width - side * 2, Math.round(width * .78f)));
        int y = AndroidUtilities.dp(12), inset = AndroidUtilities.dp(14);
        int metadata = Math.round(time.getFontSpacing()) + AndroidUtilities.dp(10);
        for (int i = 0; i < 4; i++) {
            StaticLayout measured = layout(samples[i], maximum - inset * 2);
            float longest = 0;
            for (int line = 0; line < measured.getLineCount(); line++) longest = Math.max(longest, measured.getLineWidth(line));
            int bubbleWidth = Math.min(maximum, Math.max(AndroidUtilities.dp(i >= 2 ? 98 : 82), (int) Math.ceil(longest) + inset * 2));
            labels[i] = layout(samples[i], bubbleWidth - inset * 2);
            int height = Math.max(AndroidUtilities.dp(48), labels[i].getHeight() + metadata + AndroidUtilities.dp(20));
            int left = i < 2 ? side : Math.max(side, width - side - bubbleWidth);
            tops[i] = y;
            bubbles[i].setBounds(left, y, left + bubbleWidth, y + height);
            y += height + (i == 1 ? AndroidUtilities.dp(6) : 0);
        }
        int height = y + AndroidUtilities.dp(12);
        for (int i = 0; i < 4; i++) bubbles[i].setTop(tops[i], width, height, i % 2 != 0, i % 2 == 0);
        setMeasuredDimension(width, height);
    }
    private void updateWallpaperBounds(int width, int height) {
        frameBounds.set(AndroidUtilities.dp(8), 0, Math.max(AndroidUtilities.dp(8), width - AndroidUtilities.dp(8)), height);
        frame.rewind();frame.addRoundRect(frameBounds, AndroidUtilities.dp(16), AndroidUtilities.dp(16), Path.Direction.CW);
        if (wallpaper == null) return;
        int iw = wallpaper.getIntrinsicWidth(), ih = wallpaper.getIntrinsicHeight();
        if (iw > 0 && ih > 0) {
            float scale = Math.max((float) width / iw, (float) height / ih);
            int w = (int) Math.ceil(iw * scale), h = (int) Math.ceil(ih * scale);
            wallpaperBounds.set((width - w) / 2, (height - h) / 2, (width + w) / 2, (height + h) / 2);
        } else wallpaperBounds.set(0, 0, width, height);
        wallpaper.setBounds(wallpaperBounds);
    }
    @Override protected void onSizeChanged(int w, int h, int oldw, int oldh) { updateWallpaperBounds(w, h); }
    @Override protected void onDraw(Canvas canvas) {
        int save = canvas.save();canvas.clipPath(frame);
        backdrop.setColor(Theme.getColor(Theme.key_windowBackgroundGray));canvas.drawRect(frameBounds, backdrop);
        if (wallpaper != null && (!(wallpaper instanceof BitmapDrawable)
                || !((BitmapDrawable) wallpaper).getBitmap().isRecycled())) wallpaper.draw(canvas);
        for (int i = 0; i < 4; i++) {
            boolean out = i >= 2;
            bubbles[i].drawCached(canvas, caches[i]);
            Rect bounds = bubbles[i].getBounds();
            text.setColor(Theme.getColor(out ? Theme.key_chat_messageTextOut : Theme.key_chat_messageTextIn));
            int labelSave = canvas.save();canvas.translate(bounds.left + AndroidUtilities.dp(14), bounds.top + AndroidUtilities.dp(10));
            labels[i].draw(canvas);canvas.restoreToCount(labelSave);
            time.setColor(Theme.getColor(out ? Theme.key_chat_outTimeText : Theme.key_chat_inTimeText));
            float baseline = bounds.bottom - AndroidUtilities.dp(8) - time.descent();
            float x = bounds.right - AndroidUtilities.dp(out ? 34 : 14) - time.measureText(TIME);
            canvas.drawText(TIME, x, baseline, time);
            if (out) {
                int right = bounds.right - AndroidUtilities.dp(11), top = Math.round(baseline - AndroidUtilities.dp(10));
                int h = AndroidUtilities.dp(11), w = AndroidUtilities.dp(10);
                halfCheck.setBounds(right - w - AndroidUtilities.dp(5), top, right - AndroidUtilities.dp(5), top + h);halfCheck.draw(canvas);
                check.setBounds(right - w, top, right, top + h);check.draw(canvas);
            }
        }
        canvas.restoreToCount(save);
    }
}
