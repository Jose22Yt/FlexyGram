package app.flexygram.settings.signature;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.drawable.GradientDrawable;
import android.view.View;
import android.view.accessibility.AccessibilityNodeInfo;
import android.widget.LinearLayout;
import android.widget.TextView;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.ui.ActionBar.Theme;

/** The whole preview is one accessible radio choice; previews never write preferences. */
public final class StylePreviewCard extends LinearLayout {
    private final View preview;
    private final TextView label;
    private final Theme.ResourcesProvider provider;
    private final String name;
    private final GradientDrawable frame = new GradientDrawable();
    private int surface, ink, accent;
    public StylePreviewCard(Context context, Theme.ResourcesProvider provider, String name, View preview, Runnable choose) {
        this(context, provider, name, preview, choose, false);
    }
    public StylePreviewCard(Context context, Theme.ResourcesProvider provider, String name, View preview, Runnable choose, boolean compact) {
        super(context);this.provider=provider;this.name=name;this.preview=preview;
        setOrientation(VERTICAL);setPadding(dp(compact?6:8),dp(compact?6:8),dp(compact?6:8),dp(compact?6:8));setFocusable(true);setWillNotDraw(false);
        frame.setCornerRadius(dp(18));setBackground(frame);
        preview.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO_HIDE_DESCENDANTS);
        addView(preview,new LayoutParams(-1,-2));
        label=new TextView(context);label.setTextSize(compact?15:16);label.setTypeface(AndroidUtilities.bold());label.setPadding(dp(12),dp(compact?6:10),dp(12),dp(compact?6:10));
        label.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);addView(label,new LayoutParams(-1,-2));
        setContentDescription(name);setOnClickListener(v->choose.run());updateColors();
    }
    private int dp(int v){return AndroidUtilities.dp(v);}
    public void bind(boolean selected){setSelected(selected);label.setText((selected?"✓  ":"")+name);updateColors();preview.invalidate();}
    public void refreshPreview(){preview.invalidate();}
    private void updateColors(){
        surface=Theme.getColor(Theme.key_windowBackgroundWhite,provider);ink=Theme.getColor(Theme.key_windowBackgroundWhiteBlackText,provider);accent=Theme.getColor(Theme.key_windowBackgroundWhiteBlueText,provider);
        frame.setColor(surface);frame.setStroke(dp(isSelected()?2:1),isSelected()?accent:Theme.getColor(Theme.key_divider,provider));label.setTextColor(isSelected()?accent:ink);
    }
    @Override protected void dispatchDraw(Canvas canvas){
        if(surface!=Theme.getColor(Theme.key_windowBackgroundWhite,provider)||ink!=Theme.getColor(Theme.key_windowBackgroundWhiteBlackText,provider)||accent!=Theme.getColor(Theme.key_windowBackgroundWhiteBlueText,provider))updateColors();
        super.dispatchDraw(canvas);
    }
    @Override public void onInitializeAccessibilityNodeInfo(AccessibilityNodeInfo info){super.onInitializeAccessibilityNodeInfo(info);info.setClassName("android.widget.RadioButton");info.setCheckable(true);info.setChecked(isSelected());}
}
