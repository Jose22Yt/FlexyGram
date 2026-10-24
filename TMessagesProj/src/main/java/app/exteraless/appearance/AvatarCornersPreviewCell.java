package app.exteraless.appearance;

import android.annotation.SuppressLint;
import android.content.Context;
import android.graphics.Canvas;
import android.view.Gravity;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.util.TypedValue;

import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.AvatarDrawable;
import org.telegram.ui.Components.LayoutHelper;

/**
 * Avatar corner preview using the same AvatarDrawable as the real dialog rows.
 * No bitmap snapshots, dummy gray bars, account photos, blur or per-frame animation.
 */
@SuppressLint("ViewConstructor")
public class AvatarCornersPreviewCell extends FrameLayout {
    public interface OnChanged {
        void run();
    }

    private final FrameLayout preview;
    private final AvatarCornersSeekBar seekBar;
    private final AvatarDrawable avatarDrawable;
    private final ImageView avatarView;
    private final TextView titleView;
    private final TextView messageView;
    private boolean needDivider;

    public AvatarCornersPreviewCell(Context context, OnChanged onChanged) {
        super(context);
        setWillNotDraw(false);
        setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundWhite));

        seekBar = new AvatarCornersSeekBar(context, value -> {
            AppearanceConfig.avatarCorners.setConfigInt(value);
            updateAvatarCorners();
            if (onChanged != null) {
                onChanged.run();
            }
        }, 0, AppearanceConfig.AVATAR_CORNERS_MAX,
                LocaleController.getString(R.string.OEAppearanceAvatarCorners),
                LocaleController.getString(R.string.OEAppearanceAvatarCornersLeft),
                LocaleController.getString(R.string.OEAppearanceAvatarCornersRight));
        seekBar.setValue(AppearanceConfig.avatarCorners());
        addView(seekBar, LayoutHelper.createFrame(LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT));

        preview = new FrameLayout(context);
        preview.setBackground(new PreviewBackgroundDrawable());
        addView(preview, LayoutHelper.createFrame(LayoutHelper.MATCH_PARENT, LayoutHelper.MATCH_PARENT,
                Gravity.TOP | Gravity.CENTER, 21, 112, 21, 21));

        avatarDrawable = new AvatarDrawable();
        // Deterministic local sample: real Telegram avatar renderer, no account data.
        avatarDrawable.setInfo(1L, "FlexyGram", "");
        avatarView = new ImageView(context);
        avatarView.setImageDrawable(avatarDrawable);
        preview.addView(avatarView, LayoutHelper.createFrame(56, 56,
                Gravity.START | Gravity.CENTER_VERTICAL, 16, 0, 0, 0));

        LinearLayout labels = new LinearLayout(context);
        labels.setOrientation(LinearLayout.VERTICAL);
        labels.setGravity(Gravity.CENTER_VERTICAL);
        titleView = new TextView(context);
        titleView.setText(LocaleController.getString(R.string.FlexyBrandName));
        titleView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 15);
        titleView.setTypeface(AndroidUtilities.bold());
        titleView.setSingleLine(true);
        titleView.setEllipsize(android.text.TextUtils.TruncateAt.END);
        labels.addView(titleView, new LinearLayout.LayoutParams(
                LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT));

        messageView = new TextView(context);
        messageView.setText(LocaleController.getString(R.string.FlexyAppearancePreviewMessage));
        messageView.setTextSize(TypedValue.COMPLEX_UNIT_SP, 13);
        messageView.setSingleLine(true);
        messageView.setEllipsize(android.text.TextUtils.TruncateAt.END);
        labels.addView(messageView, new LinearLayout.LayoutParams(
                LayoutHelper.MATCH_PARENT, LayoutHelper.WRAP_CONTENT));

        preview.addView(labels, LayoutHelper.createFrame(LayoutHelper.MATCH_PARENT,
                LayoutHelper.MATCH_PARENT, Gravity.START | Gravity.CENTER_VERTICAL,
                86, 0, 16, 0));
        updateAvatarCorners();
        updatePalette();
    }

    private void updateAvatarCorners() {
        if (avatarDrawable == null) {
            return;
        }
        // A positive radius represents a nearly square avatar at the slider minimum;
        // the same AvatarDrawable renders the current setting in production.
        avatarDrawable.setRoundRadius(Math.max(1,
                AppearanceConfig.getAvatarCorners(AndroidUtilities.dp(56))));
        avatarView.invalidate();
        preview.invalidate();
    }

    private void updatePalette() {
        if (titleView == null) return;
        setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundWhite));
        titleView.setTextColor(Theme.getColor(Theme.key_chats_name));
        messageView.setTextColor(Theme.getColor(Theme.key_chats_message));
    }

    public void setNeedDivider(boolean needDivider) {
        this.needDivider = needDivider;
        invalidate();
    }

    @Override
    public void invalidate() {
        super.invalidate();
        if (seekBar != null) seekBar.invalidate();
        if (avatarDrawable != null) {
            updateAvatarCorners();
            updatePalette();
        }
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        if (needDivider) {
            canvas.drawLine(LocaleController.isRTL ? 0 : AndroidUtilities.dp(21),
                    getMeasuredHeight() - 1,
                    getMeasuredWidth() - (LocaleController.isRTL ? AndroidUtilities.dp(21) : 0),
                    getMeasuredHeight() - 1, Theme.dividerPaint);
        }
    }

    @Override
    protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec) {
        super.onMeasure(
                MeasureSpec.makeMeasureSpec(MeasureSpec.getSize(widthMeasureSpec), MeasureSpec.EXACTLY),
                MeasureSpec.makeMeasureSpec(AndroidUtilities.dp(112 + 89 + 21), MeasureSpec.EXACTLY));
    }
}
