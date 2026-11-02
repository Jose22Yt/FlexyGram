package app.flexygram.bubbles;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.text.TextPaint;
import android.view.View;
import android.widget.LinearLayout;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.NotificationCenter;
import org.telegram.ui.ActionBar.MessageDrawable;
import org.telegram.ui.ActionBar.Theme;

/** Four selectable samples drawn with the same cached native bubble paths as the chat. */
final class BubbleSkinPickerView extends LinearLayout implements NotificationCenter.NotificationCenterDelegate {
    private static final int[] SKINS = {1, 3, 5, 9};
    private final SkinTile[] tiles = new SkinTile[4];

    BubbleSkinPickerView(Context context, String[] names, Runnable onChange) {
        super(context);
        setOrientation(VERTICAL);
        setPadding(AndroidUtilities.dp(12), AndroidUtilities.dp(6), AndroidUtilities.dp(12), AndroidUtilities.dp(6));
        for (int row = 0; row < 2; row++) {
            LinearLayout line = new LinearLayout(context);
            addView(line, new LayoutParams(LayoutParams.MATCH_PARENT, AndroidUtilities.dp(108)));
            for (int col = 0; col < 2; col++) {
                int index = row * 2 + col;
                SkinTile tile = new SkinTile(context, SKINS[index], names[index]);
                tiles[index] = tile;
                line.addView(tile, new LayoutParams(0, LayoutParams.MATCH_PARENT, 1f));
                tile.setOnClickListener(v -> {
                    BubbleConfig.setSkin(tile.skin);
                    settingsChanged();
                    onChange.run();
                });
            }
        }
        settingsChanged();
    }

    void settingsChanged() { for (SkinTile tile : tiles) tile.invalidate(); }

    @Override protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        NotificationCenter center = NotificationCenter.getGlobalInstance();
        center.addObserver(this, NotificationCenter.didSetNewTheme);
        center.addObserver(this, NotificationCenter.didApplyNewTheme);
    }

    @Override protected void onDetachedFromWindow() {
        NotificationCenter center = NotificationCenter.getGlobalInstance();
        center.removeObserver(this, NotificationCenter.didSetNewTheme);
        center.removeObserver(this, NotificationCenter.didApplyNewTheme);
        super.onDetachedFromWindow();
    }

    @Override public void didReceivedNotification(int id, int account, Object... args) { settingsChanged(); }

    private static final class SkinTile extends View {
        private final int skin;
        private final String name;
        private final MessageDrawable incoming = new MessageDrawable(MessageDrawable.TYPE_TEXT, false, false);
        private final MessageDrawable outgoing = new MessageDrawable(MessageDrawable.TYPE_TEXT, true, false);
        private final MessageDrawable.PathDrawParams inCache = new MessageDrawable.PathDrawParams();
        private final MessageDrawable.PathDrawParams outCache = new MessageDrawable.PathDrawParams();
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final TextPaint label = new TextPaint(Paint.ANTI_ALIAS_FLAG);
        private final RectF rect = new RectF();

        SkinTile(Context context, int skin, String name) {
            super(context);
            this.skin = skin;
            this.name = name;
            incoming.setFlexySkinPreview(skin);
            outgoing.setFlexySkinPreview(skin);
            label.setTextSize(13 * getResources().getDisplayMetrics().scaledDensity);
            setContentDescription(name);
            setFocusable(true);
        }

        @Override protected void onDraw(Canvas canvas) {
            int w = getWidth(), h = getHeight(), pad = AndroidUtilities.dp(6);
            boolean selected = BubbleConfig.skin() == skin || (BubbleConfig.skin() == 0 && skin == 1);
            rect.set(pad, pad, w - pad, h - pad);
            paint.setStyle(Paint.Style.FILL);
            paint.setColor(Theme.getColor(Theme.key_windowBackgroundWhite));
            canvas.drawRoundRect(rect, AndroidUtilities.dp(15), AndroidUtilities.dp(15), paint);
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(AndroidUtilities.dp(selected ? 2 : 1));
            paint.setColor(Theme.getColor(selected ? Theme.key_windowBackgroundWhiteBlueText : Theme.key_divider));
            canvas.drawRoundRect(rect, AndroidUtilities.dp(15), AndroidUtilities.dp(15), paint);
            paint.setStyle(Paint.Style.FILL);
            label.setColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText));
            canvas.drawText(name, pad + AndroidUtilities.dp(13), h - AndroidUtilities.dp(14), label);
            int left = pad + AndroidUtilities.dp(12), top = pad + AndroidUtilities.dp(10);
            int bh = AndroidUtilities.dp(23), bw = Math.max(AndroidUtilities.dp(32), Math.min(AndroidUtilities.dp(65), w - AndroidUtilities.dp(60)));
            incoming.setBounds(left, top, left + bw, top + bh);
            incoming.setTop(top, w, h, false, true);
            incoming.drawCached(canvas, inCache);
            int outLeft = w - pad - AndroidUtilities.dp(12) - bw;
            outgoing.setBounds(outLeft, top + AndroidUtilities.dp(25), outLeft + bw, top + AndroidUtilities.dp(25) + bh);
            outgoing.setTop(top + AndroidUtilities.dp(25), w, h, false, true);
            outgoing.drawCached(canvas, outCache);
        }
    }
}
