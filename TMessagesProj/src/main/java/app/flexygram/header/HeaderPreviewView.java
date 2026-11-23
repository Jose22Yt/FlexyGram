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
    private final Paint countBadge = new Paint(Paint.ANTI_ALIAS_FLAG);
    private static final String PREVIEW_COUNT = "10";
    private float previewCountWidth, classicPreviewExtra;
    private final String name, status;
    private int iconColor;
    private static final class FusionPreview {
        final app.flexygram.header.fusion.SignatureFusionGeometry.Layout geometry = new app.flexygram.header.fusion.SignatureFusionGeometry.Layout();
        final app.flexygram.header.fusion.SignatureFusionSurface surface = new app.flexygram.header.fusion.SignatureFusionSurface();
        final app.flexygram.header.fusion.SignatureFusionAvatarMask mask = new app.flexygram.header.fusion.SignatureFusionAvatarMask();
        final android.graphics.Path clip = new android.graphics.Path();
        final android.graphics.drawable.Drawable phone, more;
        int color = Integer.MIN_VALUE;
        FusionPreview(Context c) { phone=app.flexygram.icons.ConversationControlIcons.loadBitmap(c,R.drawable.msg_callback);more=app.flexygram.icons.ConversationControlIcons.loadBitmap(c,R.drawable.ic_ab_other); }
    }
    private FusionPreview fusion;
    private boolean fusionMode;
    private float fusionTop, fusionTitleX, fusionStatusX, previewScale = 1f;
    private float titlePx, subtitlePx, previewHeight, titleBaseline, subtitleBaseline;
    private final Paint.FontMetricsInt fontMetrics = new Paint.FontMetricsInt();
    private final android.text.TextPaint scratchPaint = new android.text.TextPaint();
    private String displayName = "", displayStatus = "";
    private final int forcedStyle;
    private final boolean miniature;
    private boolean conversationStage;
    public void useConversationStage() { conversationStage=true;requestLayout(); }
    private final app.flexygram.preview.SignatureWallpaperPreview wallpaperPreview;
    public HeaderPreviewView(Context context) { this(context, -1); }
    public HeaderPreviewView(Context context, int style) { this(context, style, false); }
    public HeaderPreviewView(Context context, int style, boolean miniature) {
        super(context); forcedStyle=style; this.miniature=miniature;
        wallpaperPreview=new app.flexygram.preview.SignatureWallpaperPreview(this,null,this::invalidate);
        setLayoutParams(new androidx.recyclerview.widget.RecyclerView.LayoutParams(android.view.ViewGroup.LayoutParams.MATCH_PARENT, android.view.ViewGroup.LayoutParams.WRAP_CONTENT));
        text.setTextAlign(Paint.Align.CENTER);
        back = app.flexygram.icons.ConversationControlIcons.load(context,R.drawable.flexy_ios_back);more=app.flexygram.icons.ConversationControlIcons.loadBitmap(context,R.drawable.ic_ab_other);
        name = LocaleController.getString(R.string.FlexyHeaderPreviewName); status = LocaleController.getString(R.string.Online);
        setContentDescription(name + ", " + status); setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_YES);
    }
    private int previewStyle(){return forcedStyle<0?HeaderConfig.style():forcedStyle;}
    private boolean previewFusion(){return previewStyle()==2||previewStyle()==3||previewStyle()==4;}
    private boolean previewFloating(){return previewStyle()==4;}
    private boolean previewPortrait(){return previewStyle()==3;}
    @Override protected void onAttachedToWindow(){super.onAttachedToWindow();if(miniature||conversationStage)return;wallpaperPreview.attach();var center=org.telegram.messenger.NotificationCenter.getGlobalInstance();center.addObserver(this,org.telegram.messenger.NotificationCenter.didSetNewTheme);center.addObserver(this,org.telegram.messenger.NotificationCenter.didApplyNewTheme);center.addObserver(this,org.telegram.messenger.NotificationCenter.didSetNewWallpapper);}
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
        int mode = HeaderConfig.counterMode();
        float numberWidth = mode == 0 ? 0 : countText.measureText(PREVIEW_COUNT);
        previewCountWidth = numberWidth;
        classicPreviewExtra = mode == 1 && width >= AndroidUtilities.dp(240)
                ? Math.max(AndroidUtilities.dp(12), numberWidth) + AndroidUtilities.dp(15) : 0;
        float extra = app.flexygram.header.fusion.SignatureFusionGeometry.unreadWidthExtra(
                numberWidth, mode, AndroidUtilities.density);
        fusionMode=false;
        previewScale=previewFloating()&&forcedStyle>=0&&width>0?Math.min(1f,width/(360f*AndroidUtilities.density)):1f;
        if(previewFusion()){
            if(fusion==null)fusion=new FusionPreview(getContext());
            var g=previewFloating() ? app.flexygram.header.fusion.SignatureFusionGeometry.updateFloating(fusion.geometry,width/previewScale,AndroidUtilities.density,LocaleController.isRTL,true,extra) : previewPortrait() ? app.flexygram.header.fusion.SignatureFusionGeometry.updatePortrait(fusion.geometry,width,AndroidUtilities.density,LocaleController.isRTL,true,extra) : app.flexygram.header.fusion.SignatureFusionGeometry.update(fusion.geometry,width,AndroidUtilities.density,LocaleController.isRTL,true,extra);
            if(g.fits&&(titleLine+subtitleLine+AndroidUtilities.dp(2))<=g.height-AndroidUtilities.dp(8)){
                app.flexygram.header.fusion.SignatureFusionGeometry.placeUnread(g, numberWidth, mode, AndroidUtilities.density);
                fusionMode=true;previewHeight=g.height;
                int h=Math.round(previewHeight)+AndroidUtilities.dp(forcedStyle<0&&!conversationStage?80:12);setMeasuredDimension(width,Math.round(h*previewScale));fusionTop=(h-previewHeight)/2;
                text.setTextSize(titlePx); scratchPaint.set(text); displayName=android.text.TextUtils.ellipsize(name,scratchPaint,g.text.width(),android.text.TextUtils.TruncateAt.END).toString();
                fusionTitleX=app.flexygram.header.fusion.SignatureFusionGeometry.titleCenterX(
                        g, text.measureText(displayName));
                text.setTextSize(subtitlePx); scratchPaint.set(text); displayStatus=android.text.TextUtils.ellipsize(previewFloating()?LocaleController.getString(R.string.FlexyHeaderFloatingPreviewStatus):status,scratchPaint,g.text.width(),android.text.TextUtils.TruncateAt.END).toString();
                fusionStatusX=g.text.centerX();
                fusion.clip.rewind();fusion.clip.addRoundRect(g.center.left,g.center.top,g.center.right,g.center.bottom,g.center.height()/2,g.center.height()/2,android.graphics.Path.Direction.CW);
                return;
            }
        }
        previewHeight=HeaderGeometry.height(width,titleLine,subtitleLine,AndroidUtilities.density,HeaderConfig.compact());
        float fit=Math.min(1f,(previewHeight-AndroidUtilities.dp(8))/(titleLine+subtitleLine));titlePx*=fit;subtitlePx*=fit;
        titlePx=Math.min(titlePx,previewHeight-AndroidUtilities.dp(8));
        int h=Math.round(previewHeight)+AndroidUtilities.dp(forcedStyle<0&&!conversationStage?80:12);setMeasuredDimension(width,h);
        if(previewStyle()==1){prepareClassicText(width);return;}
        text.setTextSize(titlePx); float preferred = (float) Math.ceil(text.measureText(name)) + AndroidUtilities.dp(24);
        geometry.update(width,(h-previewHeight)/2,previewHeight,numberWidth,AndroidUtilities.density,LocaleController.isRTL,mode,preferred,HeaderConfig.adaptiveBubbleForStyle(previewStyle()));
        text.setTextSize(titlePx); scratchPaint.set(text); displayName=android.text.TextUtils.ellipsize(name,scratchPaint,Math.max(0,geometry.title.width()-AndroidUtilities.dp(24)),android.text.TextUtils.TruncateAt.END).toString();
        text.setTextSize(subtitlePx); scratchPaint.set(text); displayStatus=android.text.TextUtils.ellipsize(status,scratchPaint,Math.max(0,geometry.title.width()-AndroidUtilities.dp(24)),android.text.TextUtils.TruncateAt.END).toString();
    }
    @Override protected void onSizeChanged(int w, int h, int oldw, int oldh) { super.onSizeChanged(w,h,oldw,oldh); }
    @Override protected void onDraw(Canvas canvas) {
        float d = AndroidUtilities.density, height = previewHeight;
        if(!miniature&&!conversationStage){
            canvas.drawColor(Theme.getColor(Theme.key_chat_wallpaper));
            wallpaperPreview.resize(getWidth(),getHeight());wallpaperPreview.draw(canvas);
        }
        if(previewStyle()==1){drawClassic(canvas);return;}
        if (fusionMode && previewFusion()) { int save=canvas.save();canvas.scale(previewScale,previewScale);drawFusion(canvas);canvas.restoreToCount(save);return; }
        surface.draw(canvas, geometry, d, null);
        int color = Theme.getColor(Theme.key_actionBarDefaultTitle);
        if(iconColor!=color){iconColor=color;back.setColorFilter(color, android.graphics.PorterDuff.Mode.SRC_IN);}
        float arrow = LocaleController.isRTL ? geometry.back.right-height/2 : geometry.back.left+height/2;
        int side=AndroidUtilities.dp(24), y=Math.round(geometry.back.centerY());
        back.setBounds(Math.round(arrow)-side/2,y-side/2,Math.round(arrow)+side/2,y+side/2); back.draw(canvas);
        if (geometry.countVisible) {
            float center = geometry.separateCount ? geometry.badge.centerX()
                    : integratedCountCenter(geometry.back.left, geometry.back.right, LocaleController.isRTL);
            drawCount(canvas, center, geometry.back.centerY());
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
    private float integratedCountCenter(float left, float right, boolean rtl) {
        float halfWidth = Math.max(AndroidUtilities.dp(23), previewCountWidth + AndroidUtilities.dp(12)) * .5f;
        return rtl ? left + AndroidUtilities.dp(7) + halfWidth : right - AndroidUtilities.dp(7) - halfWidth;
    }

    private void drawCount(Canvas canvas, float centerX, float centerY) {
        int accent = Theme.getColor(Theme.key_telegram_color);
        countBadge.setColor(accent);
        countText.setColor(androidx.core.graphics.ColorUtils.calculateContrast(0xffffffff, accent | 0xff000000)
                >= androidx.core.graphics.ColorUtils.calculateContrast(0xff000000, accent | 0xff000000) ? 0xffffffff : 0xff000000);
        float radius = AndroidUtilities.dp(23) * .5f;
        float halfWidth = Math.max(radius, previewCountWidth * .5f + AndroidUtilities.dp(6));
        canvas.drawRoundRect(centerX - halfWidth, centerY - radius, centerX + halfWidth,
                centerY + radius, radius, radius, countBadge);
        float baseline = centerY - (countText.ascent() + countText.descent()) * .5f;
        canvas.drawText(PREVIEW_COUNT, centerX - previewCountWidth * .5f, baseline, countText);
    }

    private void prepareClassicText(float width) {
        float available = Math.max(0, width - 136 * AndroidUtilities.density - classicPreviewExtra);
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
        float extra = classicPreviewExtra;
        int size = AndroidUtilities.dp(24), backX = Math.round(rtl ? getWidth() - 27*d : 27*d);
        int menuX = Math.round(rtl ? 20*d : getWidth() - 20*d);
        float left = rtl ? getWidth() - 50*d - extra : 4*d;
        float right = rtl ? getWidth() - 4*d : 50*d + extra;
        avatar.setColor(app.flexygram.effects.ChatChromePalette.surface(Theme.isCurrentThemeDark()));
        canvas.drawRoundRect(left, y - 23*d, right, y + 23*d, 23*d, 23*d, avatar);
        if (HeaderConfig.counter()) {
            float badgeX = extra > 0 ? integratedCountCenter(left, right, rtl) : backX + (rtl ? -8*d : 8*d);
            drawCount(canvas, badgeX, extra > 0 ? y : y - 15*d);
        }
        back.setBounds(backX-size/2,(int)y-size/2,backX+size/2,(int)y+size/2);int save=canvas.save();if(rtl)canvas.rotate(180,backX,y);back.draw(canvas);canvas.restoreToCount(save);
        more.setBounds(menuX-size/2,(int)y-size/2,menuX+size/2,(int)y+size/2);save=canvas.save();canvas.rotate(90,menuX,y);more.draw(canvas);canvas.restoreToCount(save);
        float avatarX=rtl?getWidth()-72*d-extra:72*d+extra,textX=rtl?getWidth()-100*d-extra:100*d+extra;
        avatar.setColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));canvas.drawCircle(avatarX,y,20*d,avatar);
        text.setColor(color);text.setTextAlign(rtl?Paint.Align.RIGHT:Paint.Align.LEFT);text.setTextSize(titlePx);
        canvas.drawText(displayName,textX,y-2*d,text);text.setTextSize(subtitlePx);text.setColor(Theme.getColor(Theme.key_actionBarDefaultSubtitle));
        canvas.drawText(displayStatus,textX,y+15*d,text);text.setTextAlign(Paint.Align.CENTER);
    }
    private void drawFusion(Canvas canvas) {
        var g=fusion.geometry;float d=AndroidUtilities.density;
        int color=Theme.getColor(Theme.key_actionBarDefaultTitle);
        if(fusion.color!=color){fusion.color=color;iconColor=color;fusion.phone.setColorFilter(color,android.graphics.PorterDuff.Mode.SRC_IN);fusion.more.setColorFilter(color,android.graphics.PorterDuff.Mode.SRC_IN);back.setColorFilter(color,android.graphics.PorterDuff.Mode.SRC_IN);}
        final boolean dark = Theme.isCurrentThemeDark();
        final boolean translucent = org.telegram.messenger.SharedConfig.chatBlurEnabled() && !previewPortrait();
        int fill = app.flexygram.effects.ChatChromePalette.surface(dark);
        if (translucent) fill = Theme.multAlpha(fill, HeaderConfig.opacity() / 100f);
        final int edge = app.flexygram.effects.ChatChromePalette.outline(dark);
        int outer=canvas.save();canvas.translate(0,fusionTop);
        fusion.surface.drawBackdrop(canvas,g,fill,edge,edge,d);
        int clip=canvas.save();canvas.clipPath(fusion.clip);
        float diameter = previewFloating() ? Math.min(AndroidUtilities.dp(38), g.portrait.height()) : g.portrait.height();
        float left = previewFloating() && g.rtl ? g.portrait.right - diameter : g.portrait.left;
        float photoTop = g.portrait.centerY() - diameter * .5f;
        canvas.translate(left, photoTop);
        int photoLayer = previewFloating() ? fusion.mask.begin(canvas, 0, 0, diameter, diameter) : 0;
        avatar.setColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));
        canvas.drawCircle(diameter * .5f, diameter * .5f, diameter * .5f, avatar);
        text.setTextSize(AndroidUtilities.dp(20));text.setColor(0xffffffff);
        canvas.drawText("A",diameter * .5f,diameter * .5f+AndroidUtilities.dp(7),text);
        if (previewFloating()) fusion.mask.finishFloating(canvas, photoLayer, diameter, diameter, g.rtl);
        canvas.restoreToCount(clip);
        text.setColor(color);text.setTextSize(titlePx);float th=text.descent()-text.ascent(),ta=text.ascent();text.setTextSize(subtitlePx);float sh=text.descent()-text.ascent();
        float top=g.text.centerY()-(th+sh+AndroidUtilities.dp(2))/2;
        text.setTextSize(titlePx);canvas.drawText(displayName,fusionTitleX,top-ta,text);
        text.setTextSize(subtitlePx);text.setColor(previewFloating()?Theme.getColor(Theme.key_actionBarDefaultSubtitle):color);
        canvas.drawText(displayStatus,fusionStatusX,top+th+AndroidUtilities.dp(2)-text.ascent(),text);
        float arrowCenter = g.rtl ? g.back.right - g.back.height() * .5f : g.back.left + g.back.height() * .5f;
        int icon=AndroidUtilities.dp(24),x=Math.round(arrowCenter),y=Math.round(g.back.centerY());back.setBounds(x-icon/2,y-icon/2,x+icon/2,y+icon/2);
        int transform=canvas.save();if(g.rtl)canvas.scale(-1,1,arrowCenter,g.back.centerY());back.draw(canvas);canvas.restoreToCount(transform);
        if (HeaderConfig.counter()) {
            float badgeX = g.separateUnread ? g.unread.centerX() : integratedCountCenter(g.back.left, g.back.right, g.rtl);
            drawCount(canvas, badgeX, g.back.centerY());
        }
        x=Math.round(g.call.centerX());y=Math.round(g.call.centerY());fusion.phone.setBounds(x-icon/2,y-icon/2,x+icon/2,y+icon/2);fusion.phone.draw(canvas);
        x=Math.round(g.more.centerX());y=Math.round(g.more.centerY());fusion.more.setBounds(x-icon/2,y-icon/2,x+icon/2,y+icon/2);transform=canvas.save();if(!app.flexygram.icons.ExactIcons.isEnabled())canvas.rotate(90,x,y);fusion.more.draw(canvas);canvas.restoreToCount(transform);
        fusion.surface.drawCenterBorder(canvas,g,edge,d);canvas.restoreToCount(outer);
    }

}
