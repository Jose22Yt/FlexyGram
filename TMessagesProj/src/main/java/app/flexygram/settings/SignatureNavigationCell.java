package app.flexygram.settings;
import android.content.Context;
import android.view.View;
import android.view.MotionEvent;
import app.flexygram.motion.FlexyTouchFeedback;
import android.widget.ImageView;
import android.widget.TextView;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Cells.TextSettingsCell;
/** Native settings title, existing line icons and trailing chevron. No colored icon tile. */
public final class SignatureNavigationCell extends TextSettingsCell {
    private final ImageView icon, arrow;
    private final FlexyTouchFeedback motionFeedback;
    private final Theme.ResourcesProvider provider;
    public SignatureNavigationCell(Context context, Theme.ResourcesProvider provider) {
        super(context, provider);this.provider=provider;
        motionFeedback = new FlexyTouchFeedback(this);
        icon=new ImageView(context);arrow=new ImageView(context);
        arrow.setImageResource(R.drawable.round_keyboard_arrow_right_24);addView(icon);addView(arrow);
        icon.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        arrow.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        getTextView().setSingleLine(false);getTextView().setMaxLines(Integer.MAX_VALUE);getTextView().setEllipsize(null);
    }
    public void bind(String text,int resource,boolean divider) {
        motionFeedback.reset();
        setText(text,divider);icon.setImageResource(resource);
        icon.setColorFilter(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText,provider));
        arrow.setColorFilter(Theme.getColor(Theme.key_windowBackgroundWhiteGrayIcon,provider));setContentDescription(text);
    }
    @Override public boolean dispatchTouchEvent(MotionEvent event) {
        motionFeedback.onTouch(event);
        return super.dispatchTouchEvent(event);
    }
    @Override protected void dispatchDraw(android.graphics.Canvas canvas) {
        int save=canvas.save();motionFeedback.transform(canvas);super.dispatchDraw(canvas);canvas.restoreToCount(save);
    }
    @Override protected void onWindowVisibilityChanged(int visibility) {
        super.onWindowVisibilityChanged(visibility);if(visibility!=View.VISIBLE&&motionFeedback!=null)motionFeedback.reset();
    }
    @Override protected void onDetachedFromWindow() {
        motionFeedback.reset();
        super.onDetachedFromWindow();
    }
    @Override protected void onMeasure(int w,int h) {
        int width=MeasureSpec.getSize(w),d=AndroidUtilities.dp(22);
        getTextView().measure(MeasureSpec.makeMeasureSpec(Math.max(0,width-AndroidUtilities.dp(104)),MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(0,MeasureSpec.UNSPECIFIED));
        icon.measure(MeasureSpec.makeMeasureSpec(d,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(d,MeasureSpec.EXACTLY));
        arrow.measure(MeasureSpec.makeMeasureSpec(d,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(d,MeasureSpec.EXACTLY));
        setMeasuredDimension(width,Math.max(AndroidUtilities.dp(56),getTextView().getMeasuredHeight()+AndroidUtilities.dp(24))+(needDivider?1:0));
    }
    @Override protected void onLayout(boolean changed,int l,int t,int r,int b) {
        int width=getMeasuredWidth(),height=getMeasuredHeight(),d=icon.getMeasuredWidth();boolean rtl=LocaleController.isRTL;
        int x=rtl?width-AndroidUtilities.dp(20)-d:AndroidUtilities.dp(20);icon.layout(x,(height-d)/2,x+d,(height+d)/2);
        x=rtl?AndroidUtilities.dp(16):width-AndroidUtilities.dp(16)-d;arrow.layout(x,(height-d)/2,x+d,(height+d)/2);arrow.setScaleX(rtl?-1:1);
        TextView title=getTextView();x=rtl?AndroidUtilities.dp(44):AndroidUtilities.dp(60);int y=(height-title.getMeasuredHeight())/2;
        title.layout(x,y,x+title.getMeasuredWidth(),y+title.getMeasuredHeight());
    }
}
