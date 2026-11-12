package app.flexygram.settings;
import android.content.Context;
import android.view.View;
import android.widget.ImageView;
import android.widget.TextView;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.TextSettingsCell;
/** Native settings title, compact line icons. No colored icon tile. */
public final class SignatureNavigationCell extends TextSettingsCell {
    private final ImageView icon;
    private final Theme.ResourcesProvider provider;
    public SignatureNavigationCell(Context context, Theme.ResourcesProvider provider) {
        super(context, provider);this.provider=provider;
        icon=new ImageView(context);addView(icon);
        icon.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        getTextView().setTextSize(15);getTextView().setSingleLine(false);getTextView().setMaxLines(Integer.MAX_VALUE);getTextView().setEllipsize(null);
    }
    public void bind(String text,int resource,boolean divider) {
        setText(text,divider);icon.setImageDrawable(app.flexygram.settings.signature.SettingsCategoryIcon.create(getContext(),app.exteraless.settings.utils.SettingsIcons.resolve(getContext(),resource),provider));
        icon.setColorFilter(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText,provider));setContentDescription(text);
    }
    @Override protected void onMeasure(int w,int h) {
        int width=MeasureSpec.getSize(w),d=AndroidUtilities.dp(22);
        getTextView().measure(MeasureSpec.makeMeasureSpec(Math.max(0,width-AndroidUtilities.dp(64)),MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(0,MeasureSpec.UNSPECIFIED));
        icon.measure(MeasureSpec.makeMeasureSpec(d,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(d,MeasureSpec.EXACTLY));
        setMeasuredDimension(width,Math.max(AndroidUtilities.dp(48),getTextView().getMeasuredHeight()+AndroidUtilities.dp(16))+(needDivider?1:0));
    }
    @Override protected void onLayout(boolean changed,int l,int t,int r,int b) {
        int width=getMeasuredWidth(),height=getMeasuredHeight(),d=icon.getMeasuredWidth();boolean rtl=LocaleController.isRTL;
        int x=rtl?width-AndroidUtilities.dp(14)-d:AndroidUtilities.dp(14);icon.layout(x,(height-d)/2,x+d,(height+d)/2);
        TextView title=getTextView();x=rtl?AndroidUtilities.dp(16):AndroidUtilities.dp(50);int y=(height-title.getMeasuredHeight())/2;
        title.layout(x,y,x+title.getMeasuredWidth(),y+title.getMeasuredHeight());
    }
}
