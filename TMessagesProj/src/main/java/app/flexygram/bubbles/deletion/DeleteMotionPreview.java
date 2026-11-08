package app.flexygram.bubbles.deletion;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.RectF;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.widget.FrameLayout;
import android.widget.TextView;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.NotificationCenter;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import app.flexygram.preview.SignatureWallpaperPreview;
import java.util.Collections;

/** Compact real-renderer demo. Wallpaper fills the segment, including behind its label. */
public final class DeleteMotionPreview extends FrameLayout implements NotificationCenter.NotificationCenterDelegate {
    private final int style;
    private final Theme.ResourcesProvider provider;
    private final SignatureWallpaperPreview wallpaper;
    private final TextView sample,label;
    private final GradientDrawable bubble=new GradientDrawable(),badge=new GradientDrawable();
    DeleteMotionPreview(Context context,int style,Theme.ResourcesProvider provider){
        super(context);this.style=style;this.provider=provider;setWillNotDraw(false);setClipChildren(true);
        wallpaper=new SignatureWallpaperPreview(this,null,this::invalidate);
        label=new TextView(context);label.setTextSize(13);label.setTypeface(AndroidUtilities.bold());label.setMaxLines(2);
        label.setPadding(dp(8),dp(3),dp(8),dp(3));label.setBackground(badge);
        FrameLayout.LayoutParams title=new FrameLayout.LayoutParams(-2,-2,Gravity.TOP|Gravity.START);title.setMargins(dp(8),dp(8),dp(8),0);addView(label,title);
        sample=new TextView(context);sample.setText(LocaleController.getString(R.string.FlexyDeleteSample));sample.setTextSize(14);sample.setMaxLines(2);sample.setMaxWidth(dp(240));
        sample.setPadding(dp(12),dp(8),dp(12),dp(8));sample.setBackground(bubble);
        FrameLayout.LayoutParams message=new FrameLayout.LayoutParams(-2,-2,Gravity.BOTTOM|Gravity.CENTER_HORIZONTAL);message.bottomMargin=dp(12);addView(sample,message);
        bind(false);
    }
    private static int dp(int value){return AndroidUtilities.dp(value);}
    void bind(boolean selected){
        label.setText((selected?"✓  ":"")+DeleteMotionSettings.labels()[style]);
        label.setTextColor(Theme.getColor(selected?Theme.key_windowBackgroundWhiteBlueText:Theme.key_windowBackgroundWhiteBlackText,provider));
        badge.setColor((Theme.getColor(Theme.key_windowBackgroundWhite,provider)&0xffffff)|0xe6000000);badge.setCornerRadius(dp(12));
        sample.setTextColor(Theme.getColor(Theme.key_chat_messageTextOut,provider));bubble.setColor(Theme.getColor(Theme.key_chat_outBubble,provider));bubble.setCornerRadius(dp(18));
        requestLayout();invalidate();
    }
    void play(){
        stop();if(style==DeleteMotionSettings.DEFAULT)return;
        if(!isAttachedToWindow() || sample.getWidth()<1 || sample.getHeight()<1)return;
        int started=DeleteMotionOverlay.runNativeDelete(this,Collections.singletonList(new DeleteMotionOverlay.Target(sample,new RectF(0,0,sample.getWidth(),sample.getHeight()))),style,
                ()->sample.setAlpha(0f),()->sample.setAlpha(1f));
        if(started==0)sample.setAlpha(1f);
    }
    void stop(){DeleteMotionOverlay.cancel(sample);sample.setAlpha(1f);}
    @Override protected void onMeasure(int widthSpec,int heightSpec){
        int width=MeasureSpec.getSize(widthSpec);
        label.measure(MeasureSpec.makeMeasureSpec(Math.max(1,width-dp(16)),MeasureSpec.AT_MOST),MeasureSpec.makeMeasureSpec(0,MeasureSpec.UNSPECIFIED));
        sample.measure(MeasureSpec.makeMeasureSpec(Math.max(1,Math.min(dp(240),width-dp(32))),MeasureSpec.AT_MOST),MeasureSpec.makeMeasureSpec(0,MeasureSpec.UNSPECIFIED));
        int height=Math.max(dp(108),dp(32)+label.getMeasuredHeight()+sample.getMeasuredHeight());
        super.onMeasure(widthSpec,MeasureSpec.makeMeasureSpec(height,MeasureSpec.EXACTLY));
    }
    @Override protected void onSizeChanged(int w,int h,int oldw,int oldh){super.onSizeChanged(w,h,oldw,oldh);wallpaper.resize(w,h);}
    @Override protected void onDraw(Canvas canvas){canvas.drawColor(Theme.getColor(Theme.key_windowBackgroundGray,provider));wallpaper.draw(canvas);}
    @Override protected void onAttachedToWindow(){
        super.onAttachedToWindow();wallpaper.attach();NotificationCenter nc=NotificationCenter.getGlobalInstance();
        nc.addObserver(this,NotificationCenter.didSetNewTheme);nc.addObserver(this,NotificationCenter.didApplyNewTheme);nc.addObserver(this,NotificationCenter.didSetNewWallpapper);
    }
    @Override protected void onDetachedFromWindow(){
        stop();wallpaper.close();NotificationCenter nc=NotificationCenter.getGlobalInstance();
        nc.removeObserver(this,NotificationCenter.didSetNewTheme);nc.removeObserver(this,NotificationCenter.didApplyNewTheme);nc.removeObserver(this,NotificationCenter.didSetNewWallpapper);super.onDetachedFromWindow();
    }
    @Override public void didReceivedNotification(int id,int account,Object...args){wallpaper.refresh();bind(DeleteMotionSettings.get(getContext())==style);}
}
