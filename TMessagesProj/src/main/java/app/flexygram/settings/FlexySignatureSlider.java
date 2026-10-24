package app.flexygram.settings;

import android.content.Context;
import android.graphics.drawable.GradientDrawable;
import android.widget.SeekBar;
import androidx.core.graphics.ColorUtils;
import app.flexygram.composer.ComposerSliderTrack;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.ui.ActionBar.Theme;

/** Settings only. Native SeekBar owns touch, RTL, keyboard, TalkBack and exact progress. */
public final class FlexySignatureSlider extends SeekBar {
    private int drawnProgress = -1, drawnMax = -1;
    private final ComposerSliderTrack track = new ComposerSliderTrack();
    private final GradientDrawable marker = new GradientDrawable();
    public FlexySignatureSlider(Context context) {
        super(context);
        setProgressDrawable(track); setSplitTrack(false);
        marker.setCornerRadius(AndroidUtilities.dp(2));
        marker.setSize(AndroidUtilities.dp(4), AndroidUtilities.dp(26));
        setThumb(marker); setThumbOffset(AndroidUtilities.dp(2));
        setPadding(AndroidUtilities.dp(2), 0, AndroidUtilities.dp(2), 0);
        setMinimumHeight(AndroidUtilities.dp(48));
        updateColors();
    }
    @Override public synchronized void setProgress(int value) {
        super.setProgress(value);
        if (track != null) track.setFraction(getProgress(), getMax());
    }
    @Override protected void onDraw(android.graphics.Canvas canvas) {
        if (drawnProgress != getProgress() || drawnMax != getMax()) {
            drawnProgress = getProgress(); drawnMax = getMax(); track.setFraction(drawnProgress, drawnMax);
        }
        super.onDraw(canvas);
    }
    public void updateColors() {
        int accent = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText);
        track.configure(accent, ColorUtils.blendARGB(Theme.getColor(Theme.key_windowBackgroundWhite),
            Theme.getColor(Theme.key_windowBackgroundWhiteBlackText), .16f));
        marker.setColor(accent);
    }
}
