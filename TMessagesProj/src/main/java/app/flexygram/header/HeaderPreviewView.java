package app.flexygram.header;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.view.View;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;

/** Synthetic local preview; same geometry/surface as the live header, no accounts or observers. */
public final class HeaderPreviewView extends View {
    private final HeaderGeometry geometry = new HeaderGeometry();
    private final HeaderSurface surface = new HeaderSurface();
    private final Paint text = new Paint(Paint.ANTI_ALIAS_FLAG), avatar = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final android.graphics.drawable.Drawable back, more;
    private final String name, status;
    private int iconColor;
    private float titlePx, subtitlePx, previewHeight;
    private String displayName = "", displayStatus = "";
    public HeaderPreviewView(Context context) {
        super(context); text.setTextAlign(Paint.Align.CENTER);
        back = context.getDrawable(R.drawable.ic_ab_back).mutate(); more = context.getDrawable(R.drawable.ic_ab_other).mutate();
        name = LocaleController.getString(R.string.FlexyHeaderPreviewName); status = LocaleController.getString(R.string.Online);
        setContentDescription(name + ", " + status); setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_YES);
    }
    public void settingsChanged() { requestLayout(); invalidate(); }
    @Override protected void onMeasure(int widthSpec, int heightSpec) {
        int width=MeasureSpec.getSize(widthSpec); var metrics=getResources().getDisplayMetrics();
        titlePx=android.util.TypedValue.applyDimension(android.util.TypedValue.COMPLEX_UNIT_SP,17.5f,metrics);
        subtitlePx=android.util.TypedValue.applyDimension(android.util.TypedValue.COMPLEX_UNIT_SP,13.5f,metrics);
        previewHeight=HeaderGeometry.height(width,titlePx,subtitlePx,AndroidUtilities.density,HeaderConfig.compact());
        titlePx=Math.min(titlePx,previewHeight-AndroidUtilities.dp(8));
        int h=Math.round(previewHeight)+AndroidUtilities.dp(80);setMeasuredDimension(width,h);
        text.setTextSize(AndroidUtilities.dp(16));geometry.update(width,(h-previewHeight)/2,previewHeight,HeaderConfig.counter()?text.measureText("3"):0,AndroidUtilities.density,LocaleController.isRTL);
        text.setTextSize(titlePx);displayName=android.text.TextUtils.ellipsize(name,new android.text.TextPaint(text),Math.max(0,geometry.title.width()-AndroidUtilities.dp(64)),android.text.TextUtils.TruncateAt.END).toString();
        text.setTextSize(subtitlePx);displayStatus=android.text.TextUtils.ellipsize(status,new android.text.TextPaint(text),Math.max(0,geometry.title.width()-AndroidUtilities.dp(64)),android.text.TextUtils.TruncateAt.END).toString();
    }
    @Override protected void onSizeChanged(int w, int h, int oldw, int oldh) { super.onSizeChanged(w,h,oldw,oldh); }
    @Override protected void onDraw(Canvas canvas) {
        float d = AndroidUtilities.density, height = previewHeight;
        canvas.drawColor(Theme.getColor(Theme.key_windowBackgroundGray));
        text.setTextSize(AndroidUtilities.dp(16)); geometry.update(getWidth(), (getHeight()-height)/2, height, HeaderConfig.counter() ? text.measureText("3") : 0, d, LocaleController.isRTL);
        if (!HeaderConfig.signature()) { text.setColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText)); canvas.drawText(name, getWidth()/2f, getHeight()/2f, text); return; }
        surface.draw(canvas, geometry, d, null);
        int color = Theme.getColor(Theme.key_actionBarDefaultTitle);
        if(iconColor!=color){iconColor=color;back.setColorFilter(color, android.graphics.PorterDuff.Mode.SRC_IN); more.setColorFilter(color, android.graphics.PorterDuff.Mode.SRC_IN);}
        float arrow = LocaleController.isRTL ? geometry.back.right-height/2 : geometry.back.left+height/2;
        int side=AndroidUtilities.dp(24), y=Math.round(geometry.back.centerY());
        back.setBounds(Math.round(arrow)-side/2,y-side/2,Math.round(arrow)+side/2,y+side/2); back.draw(canvas);
        text.setColor(color); if (geometry.countVisible) canvas.drawText("3",LocaleController.isRTL ? geometry.back.left+(geometry.back.width()-height)/2 : geometry.back.left+height+(geometry.back.width()-height)/2, y+AndroidUtilities.dp(5),text);
        boolean statusFits=titlePx+subtitlePx+AndroidUtilities.dp(12)<=height;
        text.setTextSize(titlePx); canvas.drawText(displayName,geometry.title.centerX(),statusFits?y-AndroidUtilities.dp(1):y-(text.ascent()+text.descent())/2,text);
        if(statusFits){text.setTextSize(subtitlePx);canvas.drawText(displayStatus,geometry.title.centerX(),y+subtitlePx+AndroidUtilities.dp(2),text);}
        int mx=LocaleController.isRTL ? Math.round(geometry.title.left)+AndroidUtilities.dp(14):Math.round(geometry.title.right)-AndroidUtilities.dp(14);
        more.setBounds(mx-side/2,y-side/2,mx+side/2,y+side/2);more.draw(canvas);
        avatar.setColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));canvas.drawCircle(geometry.avatar.centerX(),geometry.avatar.centerY(),height/2-AndroidUtilities.dp(1),avatar);
        text.setColor(0xffffffff);text.setTextSize(AndroidUtilities.dp(20));canvas.drawText("A",geometry.avatar.centerX(),geometry.avatar.centerY()+AndroidUtilities.dp(7),text);
    }
}
