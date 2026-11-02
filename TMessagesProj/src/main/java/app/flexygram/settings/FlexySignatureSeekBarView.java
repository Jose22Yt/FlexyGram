package app.flexygram.settings;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.SeekBarView;
/** A paint-only settings skin. Native SeekBarView retains gestures and accessibility delegates. */
public final class FlexySignatureSeekBarView extends SeekBarView {
    private final Paint signaturePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Theme.ResourcesProvider provider;
    private int lastBgColor = Integer.MIN_VALUE, lastTrackColor;
    public FlexySignatureSeekBarView(Context c) { this(c, false, null); }
    public FlexySignatureSeekBarView(Context c, boolean percent, Theme.ResourcesProvider p) {
        super(c, percent, p); provider = p;
    }
    @Override protected void onDraw(Canvas canvas) {
        float left = AndroidUtilities.dp(16), right = getWidth() - left;
        float y = getHeight() * .5f, half = AndroidUtilities.dp(7), gap = AndroidUtilities.dp(8);
        float x = left + (right-left)*Math.max(0,Math.min(1,getProgress()));
        int bg = Theme.getColor(Theme.key_windowBackgroundWhiteBlackText, provider);
        if (bg != lastBgColor) {
            lastBgColor = bg;
            lastTrackColor = Theme.multAlpha(bg, .16f);
        }
        int accent = Theme.getColor(Theme.key_windowBackgroundWhiteBlueText, provider);
        signaturePaint.setColor(lastTrackColor);
        if(x+gap<right) canvas.drawRoundRect(x+gap,y-half,right,y+half,half,half,signaturePaint);
        signaturePaint.setColor(accent);
        if(x-gap>left) canvas.drawRoundRect(left,y-half,x-gap,y+half,half,half,signaturePaint);
        float handleW = AndroidUtilities.dp(2), handleH = AndroidUtilities.dp(13);
        canvas.drawRoundRect(x-handleW,y-handleH,x+handleW,y+handleH,handleW,handleW,signaturePaint);
    }
}
