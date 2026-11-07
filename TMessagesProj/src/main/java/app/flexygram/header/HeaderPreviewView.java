package app.flexygram.header;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.view.View;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;

/** Shared header geometry and surfaces; wallpaper observers exist only while attached. */
public final class HeaderPreviewView extends View implements org.telegram.messenger.NotificationCenter.NotificationCenterDelegate {
    private final HeaderGeometry geometry = new HeaderGeometry();
    private final HeaderSurface surface = new HeaderSurface();
    private final Paint text = new Paint(Paint.ANTI_ALIAS_FLAG), avatar = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final android.graphics.drawable.Drawable back, more;
    private final Paint countText=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final String name, status;
    private int iconColor;
    private static final class FusionPreview {
        final app.flexygram.header.fusion.SignatureFusionGeometry.Layout geometry = new app.flexygram.header.fusion.SignatureFusionGeometry.Layout();
        final app.flexygram.header.fusion.SignatureFusionSurface surface = new app.flexygram.header.fusion.SignatureFusionSurface();
        final app.flexygram.header.fusion.SignatureFusionAvatarMask mask = new app.flexygram.header.fusion.SignatureFusionAvatarMask();
        final android.graphics.Path clip = new android.graphics.Path();
        final android.graphics.drawable.Drawable phone, more;
        int color = Integer.MIN_VALUE;
        FusionPreview(Context c) { phone=app.flexygram.icons.ConversationControlIcons.load(c,R.drawable.flexy_ios_call);more=app.flexygram.icons.ConversationControlIcons.load(c,R.drawable.flexy_ios_more); }
    }
    private FusionPreview fusion;
    private boolean fusionMode;
    private float fusionTop, fusionTitleX, fusionStatusX, previewScale = 1f;
    private float titlePx, subtitlePx, previewHeight, titleBaseline, subtitleBaseline;
    private final Paint.FontMetricsInt fontMetrics = new Paint.FontMetricsInt();
    private final android.text.TextPaint scratchPaint = new android.text.TextPaint();
    private String displayName = "", displayStatus = "";
    private final int forcedStyle;
    private final app.flexygram.preview.SignatureWallpaperPreview wallpaperPreview;
    public HeaderPreviewView(Context context) { this(context, -1); }
    public HeaderPreviewView(Context context, int style) {
        super(context); forcedStyle=style;
        wallpaperPreview=new app.flexygram.preview.SignatureWallpaperPreview(this,null,this::invalidate);
        setLayoutParams(new androidx.recyclerview.widget.RecyclerView.LayoutParams(android.view.ViewGroup.LayoutParams.MATCH_PARENT, android.view.ViewGroup.LayoutParams.WRAP_CONTENT));
        text.setTextAlign(Paint.Align.CENTER);
        back = app.flexygram.icons.ConversationControlIcons.load(context,R.drawable.flexy_ios_back);more=app.flexygram.icons.ConversationControlIcons.load(context,R.drawable.flexy_ios_more);
        name = LocaleController.getString(R.string.FlexyHeaderPreviewName); status = LocaleController.getString(R.string.Online);
        setContentDescription(name + ", " + status); setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_YES);
    }
    private int previewStyle(){return forcedStyle<0?HeaderConfig.style():forcedStyle;}
    private boolean previewFusion(){return previewStyle()==2||previewStyle()==3||previewStyle()==4;}
    private boolean previewFloating(){return previewStyle()==4;}
    private boolean previewPortrait(){return previewStyle()==3;}
    @Override protected void onAttachedToWindow(){super.onAttachedToWindow();wallpaperPreview.attach();var center=org.telegram.messenger.NotificationCenter.getGlobalInstance();center.addObserver(this,org.telegram.messenger.NotificationCenter.didSetNewTheme);center.addObserver(this,org.telegram.messenger.NotificationCenter.didApplyNewTheme);center.addObserver(this,org.telegram.messenger.NotificationCenter.didSetNewWallpapper);}
    @Override protected void onDetachedFromWindow(){var center=org.telegram.messenger.NotificationCenter.getGlobalInstance();center.removeObserver(this,org.telegram.messenger.NotificationCenter.didSetNewTheme);center.removeObserver(this,org.telegram.messenger.NotificationCenter.didApplyNewTheme);center.removeObserver(this,org.telegram.messenger.NotificationCenter.didSetNewWallpapper);wallpaperPreview.close();super.onDetachedFromWindow();}
    @Override public void didReceivedNotification(int id,int account,Object... args){wallpaperPreview.refresh();settingsChanged();}
    public void settingsChanged() { requestLayout(); invalidate(); }
    @Override protected void onMeasure(int widthSpec, int heightSpec) {
        if(Theme.dialogs_countTextPaint!=null)countText.set(Theme.dialogs_countTextPaint);else{countText.setTextSize(AndroidUtilities.dp(12));countText.setTypeface(AndroidUtilities.bold());}
        int width=MeasureSpec.getSize(widthSpec); var metrics=getResources().getDisplayMetrics();
        titlePx=android.util.TypedValue.applyDimension(android.util.TypedValue.COMPLEX_UNIT_SP,previewFloating()?app.flexygram.header.fusion.SignatureFusionGeometry.FLOATING_TITLE_SP:previewFusion()||HeaderConfig.compact()?16f:17.5f,metrics);
        subtitlePx=android.util.TypedValue.applyDimension(android.util.TypedValue.COMPLEX_UNIT_SP,previewFloating()?app.flexygram.header.fusion.SignatureFusionGeometry.FLOATING_SUBTITLE_SP:12f,metrics);
        text.setTextSize(titlePx); text.getFontMetricsInt(fontMetrics); int titleLine=fontMetrics.descent-fontMetrics.ascent;
        text.setTextSize(subtitlePx); text.getFontMetricsInt(fontMetrics); int subtitleLine=fontMetrics.descent-fontMetrics.ascent;
        fusionMode=false;
        previewScale=previewFloating()&&forcedStyle>=0&&width>0?Math.min(1f,width/(360f*AndroidUtilities.density)):1f;
        if(previewFusion()){
            if(fusion==null)fusion=new FusionPreview(getContext());
            var g=previewFloating() ? app.flexygram.header.fusion.SignatureFusionGeometry.updateFloating(fusion.geometry,width/previewScale,AndroidUtilities.density,LocaleController.isRTL,true,0) : previewPortrait() ? app.flexygram.header.fusion.SignatureFusionGeometry.updatePortrait(fusion.geometry,width,AndroidUtilities.density,LocaleController.isRTL,true) : app.flexygram.header.fusion.SignatureFusionGeometry.update(fusion.geometry,width,AndroidUtilities.density,LocaleController.isRTL,true);
            if(g.fits&&(titleLine+subtitleLine+AndroidUtilities.dp(2))<=g.height-AndroidUtilities.dp(8)){
                fusionMode=true;previewHeight=g.height;
                int h=Math.round(previewHeight)+AndroidUtilities.dp(forcedStyle<0?80:12);setMeasuredDimension(width,Math.round(h*previewScale));fusionTop=(h-previewHeight)/2;
                text.setTextSize(titlePx); scratchPaint.set(text); displayName=android.text.TextUtils.ellipsize(name,scratchPaint,g.text.width(),android.text.TextUtils.TruncateAt.END).toString();
                fusionTitleX=app.flexygram.header.fusion.SignatureFusionGeometry.titleCenterX(
                        g, text.measureText(displayName));
                text.setTextSize(subtitlePx); scratchPaint.set(text); displayStatus=android.text.TextUtils.ellipsize(previewFloating()?LocaleController.getString(R.string.FlexyHeaderFloatingPreviewStatus):status,scratchPaint,g.text.width(),android.text.TextUtils.TruncateAt.END).toString();
                fusionStatusX=g.text.centerX();
                fusion.clip.rewind();fusion.clip.addRoundRect(g.center.left,g.center.top,g.center.right,g.center.bottom,g.center.height()/2,g.center.height()/2,android.graphics.Path.Direction.CW);
                // Preview contact has initials only: keep the initial in the small native left slot.
                float placeholderW = Math.min(g.portrait.width(), AndroidUtilities.dp(73));
                float previewStart = g.rtl ? g.portrait.width()-placeholderW*.45f : placeholderW*.55f;
                float previewEnd = g.rtl ? g.portrait.width()-placeholderW : placeholderW;
                if(previewFloating())fusion.mask.prepare(g.fadeStartX,g.fadeEndX,g.fadeSafeStop,g.rtl);
                else if (!previewPortrait()) fusion.mask.prepare(previewStart,previewEnd,.9f,g.rtl);
                return;
            }
        }
        previewHeight=HeaderGeometry.height(width,titleLine,subtitleLine,AndroidUtilities.density,HeaderConfig.compact());
        float fit=Math.min(1f,(previewHeight-AndroidUtilities.dp(8))/(titleLine+subtitleLine));titlePx*=fit;subtitlePx*=fit;
        titlePx=Math.min(titlePx,previewHeight-AndroidUtilities.dp(8));
        int h=Math.round(previewHeight)+AndroidUtilities.dp(forcedStyle<0?80:12);setMeasuredDimension(width,h);
        if(previewStyle()==1){prepareClassicText(width);return;}
        text.setTextSize(titlePx); float preferred = text.measureText(name);
        text.setTextSize(subtitlePx); preferred = Math.max(preferred, text.measureText(status)) + AndroidUtilities.dp(24);
        float numberWidth = 0;
        int mode = HeaderConfig.counter() ? HeaderConfig.counterMode() : 0;
        if (mode != 0) {
            numberWidth = countText.measureText("10");
        }
        geometry.update(width,(h-previewHeight)/2,previewHeight,numberWidth,AndroidUtilities.density,LocaleController.isRTL,mode,preferred);
        text.setTextSize(titlePx); scratchPaint.set(text); displayName=android.text.TextUtils.ellipsize(name,scratchPaint,Math.max(0,geometry.title.width()-AndroidUtilities.dp(24)),android.text.TextUtils.TruncateAt.END).toString();
        text.setTextSize(subtitlePx); scratchPaint.set(text); displayStatus=android.text.TextUtils.ellipsize(status,scratchPaint,Math.max(0,geometry.title.width()-AndroidUtilities.dp(24)),android.text.TextUtils.TruncateAt.END).toString();
    }
    @Override protected void onSizeChanged(int w, int h, int oldw, int oldh) { super.onSizeChanged(w,h,oldw,oldh); }
    @Override protected void onDraw(Canvas canvas) {
        float d = AndroidUtilities.density, height = previewHeight;
        canvas.drawColor(Theme.getColor(Theme.key_chat_wallpaper));
        wallpaperPreview.resize(getWidth(),getHeight());wallpaperPreview.draw(canvas);
        if(previewStyle()==1){drawClassic(canvas);return;}
        if (fusionMode && previewFusion()) { int save=canvas.save();canvas.scale(previewScale,previewScale);drawFusion(canvas);canvas.restoreToCount(save);return; }
        surface.draw(canvas, geometry, d, null);
        int color = Theme.getColor(Theme.key_actionBarDefaultTitle);
        if(iconColor!=color){iconColor=color;back.setColorFilter(color, android.graphics.PorterDuff.Mode.SRC_IN);}
        float arrow = LocaleController.isRTL ? geometry.back.right-height/2 : geometry.back.left+height/2;
        int side=AndroidUtilities.dp(24), y=Math.round(geometry.back.centerY());
        back.setBounds(Math.round(arrow)-side/2,y-side/2,Math.round(arrow)+side/2,y+side/2); back.draw(canvas);
        if (geometry.countVisible) {
            Paint countPaint = countText;
            countPaint.setColor(color);
            float countY = geometry.back.centerY() - (countPaint.descent() + countPaint.ascent()) / 2f;
            float countX = LocaleController.isRTL
                    ? geometry.back.left + AndroidUtilities.dp(8)
                    : geometry.back.right - AndroidUtilities.dp(8) - countPaint.measureText("10");
            if (geometry.separateCount) {
                countX = geometry.badge.centerX() - countPaint.measureText("10") / 2f;
                countY = geometry.badge.centerY() - (countPaint.descent() + countPaint.ascent()) / 2f;
            }
            canvas.drawText("10", countX, countY, countPaint);
        }
        text.setColor(color);
        text.setTextSize(titlePx); float titleHeight=text.descent()-text.ascent(), titleAscent=text.ascent();
        text.setTextSize(subtitlePx); float subtitleHeight=text.descent()-text.ascent();
        float blockTop=geometry.title.centerY()-(titleHeight+subtitleHeight+AndroidUtilities.dp(2))/2;
        text.setTextSize(titlePx); canvas.drawText(displayName,geometry.title.centerX(),blockTop-titleAscent,text);
        text.setTextSize(subtitlePx);canvas.drawText(displayStatus,geometry.title.centerX(),blockTop+titleHeight+AndroidUtilities.dp(2)-text.ascent(),text);
        avatar.setColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));canvas.drawCircle(geometry.avatar.centerX(),geometry.avatar.centerY(),height/2-AndroidUtilities.dp(1),avatar);
        text.setColor(0xffffffff);text.setTextSize(AndroidUtilities.dp(20));canvas.drawText("A",geometry.avatar.centerX(),geometry.avatar.centerY()+AndroidUtilities.dp(7),text);
    }
    private void prepareClassicText(float width) {
        float available = Math.max(0, width - 122 * AndroidUtilities.density);
        text.setTextSize(titlePx); scratchPaint.set(text);
        displayName = android.text.TextUtils.ellipsize(name, scratchPaint, available, android.text.TextUtils.TruncateAt.END).toString();
        text.setTextSize(subtitlePx); scratchPaint.set(text);
        displayStatus = android.text.TextUtils.ellipsize(status, scratchPaint, available, android.text.TextUtils.TruncateAt.END).toString();
    }
    private void drawClassic(Canvas canvas){
        float y=getHeight()/2f,d=AndroidUtilities.density;boolean rtl=LocaleController.isRTL;
        avatar.setColor(Theme.getColor(Theme.key_actionBarDefault));canvas.drawRect(0,y-28*d,getWidth(),y+28*d,avatar);
        int color=Theme.getColor(Theme.key_actionBarDefaultTitle);
        back.setColorFilter(color,android.graphics.PorterDuff.Mode.SRC_IN);more.setColorFilter(color,android.graphics.PorterDuff.Mode.SRC_IN);
        int size=AndroidUtilities.dp(24),backX=Math.round(rtl?getWidth()-20*d:20*d),menuX=Math.round(rtl?20*d:getWidth()-20*d);
        back.setBounds(backX-size/2,(int)y-size/2,backX+size/2,(int)y+size/2);int save=canvas.save();if(rtl)canvas.rotate(180,backX,y);back.draw(canvas);canvas.restoreToCount(save);
        more.setBounds(menuX-size/2,(int)y-size/2,menuX+size/2,(int)y+size/2);save=canvas.save();more.draw(canvas);canvas.restoreToCount(save);
        float avatarX=rtl?getWidth()-58*d:58*d,textX=rtl?getWidth()-86*d:86*d;
        avatar.setColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));canvas.drawCircle(avatarX,y,20*d,avatar);
        text.setColor(color);text.setTextAlign(rtl?Paint.Align.RIGHT:Paint.Align.LEFT);text.setTextSize(titlePx);
        canvas.drawText(displayName,textX,y-2*d,text);text.setTextSize(subtitlePx);text.setColor(Theme.getColor(Theme.key_actionBarDefaultSubtitle));
        canvas.drawText(displayStatus,textX,y+15*d,text);text.setTextAlign(Paint.Align.CENTER);
    }
    private void drawFusion(Canvas canvas) {
        var g=fusion.geometry;float d=AndroidUtilities.density;
        int color=Theme.getColor(Theme.key_actionBarDefaultTitle);
        if(fusion.color!=color){fusion.color=color;iconColor=color;fusion.phone.setColorFilter(color,android.graphics.PorterDuff.Mode.SRC_IN);fusion.more.setColorFilter(color,android.graphics.PorterDuff.Mode.SRC_IN);back.setColorFilter(color,android.graphics.PorterDuff.Mode.SRC_IN);}
        int fill=(Theme.getColor(Theme.key_windowBackgroundWhite)&0xffffff)|((previewPortrait()?255:Math.round(HeaderConfig.opacity()*2.55f))<<24);
        int edge=(Theme.getColor(Theme.key_divider)&0xffffff)|0x66000000;
        int outer=canvas.save();canvas.translate(0,fusionTop);
        fusion.surface.drawBackdrop(canvas,g,fill,edge,edge,d);
        int clip=canvas.save();canvas.clipPath(fusion.clip);
        int photoLayer=previewFloating()?fusion.mask.begin(canvas,g.portrait.left,g.portrait.top,g.portrait.right,g.portrait.bottom):0;
        avatar.setColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));
        if(previewFloating())canvas.drawRect(g.portrait.left,g.portrait.top,g.portrait.right,g.portrait.bottom,avatar);
        else canvas.drawCircle(g.portrait.centerX(),g.portrait.centerY(),g.portrait.height()*.5f,avatar);
        text.setTextSize(AndroidUtilities.dp(20));text.setColor(0xffffffff);
        float initialX=previewFloating()?(g.rtl?g.portrait.right-g.portrait.height()/2:g.portrait.left+g.portrait.height()/2):g.portrait.centerX();
        canvas.drawText("A",initialX,g.portrait.centerY()+AndroidUtilities.dp(7),text);
        if(previewFloating())fusion.mask.finish(canvas,photoLayer,g.portrait.right,g.portrait.bottom,g.fadeStartX,g.fadeEndX,g.fadeSafeStop,g.rtl);
        canvas.restoreToCount(clip);
        text.setColor(color);text.setTextSize(titlePx);float th=text.descent()-text.ascent(),ta=text.ascent();text.setTextSize(subtitlePx);float sh=text.descent()-text.ascent();
        float top=g.text.centerY()-(th+sh+AndroidUtilities.dp(2))/2;
        text.setTextSize(titlePx);canvas.drawText(displayName,fusionTitleX,top-ta,text);
        text.setTextSize(subtitlePx);text.setColor(previewFloating()?Theme.getColor(Theme.key_actionBarDefaultSubtitle):color);
        canvas.drawText(displayStatus,fusionStatusX,top+th+AndroidUtilities.dp(2)-text.ascent(),text);
        int icon=AndroidUtilities.dp(24),x=Math.round(g.back.centerX()),y=Math.round(g.back.centerY());back.setBounds(x-icon/2,y-icon/2,x+icon/2,y+icon/2);
        int transform=canvas.save();if(g.rtl)canvas.scale(-1,1,g.back.centerX(),g.back.centerY());back.draw(canvas);canvas.restoreToCount(transform);
        x=Math.round(g.call.centerX());y=Math.round(g.call.centerY());fusion.phone.setBounds(x-icon/2,y-icon/2,x+icon/2,y+icon/2);fusion.phone.draw(canvas);
        x=Math.round(g.more.centerX());y=Math.round(g.more.centerY());fusion.more.setBounds(x-icon/2,y-icon/2,x+icon/2,y+icon/2);transform=canvas.save();fusion.more.draw(canvas);canvas.restoreToCount(transform);
        fusion.surface.drawCenterBorder(canvas,g,edge,d);canvas.restoreToCount(outer);
    }

}
