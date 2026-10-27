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
    private final android.graphics.drawable.Drawable back;
    private final String name, status;
    private int iconColor;
    private static final class FusionPreview {
        final app.flexygram.header.fusion.SignatureFusionGeometry.Layout geometry = new app.flexygram.header.fusion.SignatureFusionGeometry.Layout();
        final app.flexygram.header.fusion.SignatureFusionSurface surface = new app.flexygram.header.fusion.SignatureFusionSurface();
        final app.flexygram.header.fusion.SignatureFusionAvatarMask mask = new app.flexygram.header.fusion.SignatureFusionAvatarMask();
        final android.graphics.Path clip = new android.graphics.Path();
        final android.graphics.drawable.Drawable phone, more;
        int color = Integer.MIN_VALUE;
        FusionPreview(Context c) { phone=c.getDrawable(R.drawable.msg_callback).mutate();more=c.getDrawable(R.drawable.ic_ab_other).mutate(); }
    }
    private FusionPreview fusion;
    private boolean fusionMode;
    private float fusionTop, fusionTitleX, fusionStatusX;
    private float titlePx, subtitlePx, previewHeight, titleBaseline, subtitleBaseline;
    private final Paint.FontMetricsInt fontMetrics = new Paint.FontMetricsInt();
    private String displayName = "", displayStatus = "";
    public HeaderPreviewView(Context context) {
        super(context); text.setTextAlign(Paint.Align.CENTER);
        back = context.getDrawable(R.drawable.ic_ab_back).mutate();
        name = LocaleController.getString(R.string.FlexyHeaderPreviewName); status = LocaleController.getString(R.string.Online);
        setContentDescription(name + ", " + status); setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_YES);
    }
    public void settingsChanged() { requestLayout(); invalidate(); }
    @Override protected void onMeasure(int widthSpec, int heightSpec) {
        int width=MeasureSpec.getSize(widthSpec); var metrics=getResources().getDisplayMetrics();
        titlePx=android.util.TypedValue.applyDimension(android.util.TypedValue.COMPLEX_UNIT_SP,HeaderConfig.fusion()||HeaderConfig.compact()?16f:17.5f,metrics);
        subtitlePx=android.util.TypedValue.applyDimension(android.util.TypedValue.COMPLEX_UNIT_SP,12f,metrics);
        text.setTextSize(titlePx); text.getFontMetricsInt(fontMetrics); int titleLine=fontMetrics.descent-fontMetrics.ascent;
        text.setTextSize(subtitlePx); text.getFontMetricsInt(fontMetrics); int subtitleLine=fontMetrics.descent-fontMetrics.ascent;
        fusionMode=false;
        if(HeaderConfig.fusion()){
            if(fusion==null)fusion=new FusionPreview(getContext());
            var g=app.flexygram.header.fusion.SignatureFusionGeometry.update(fusion.geometry,width,AndroidUtilities.density,LocaleController.isRTL,true);
            if(g.fits&&titleLine+subtitleLine+AndroidUtilities.dp(2)<=g.height-AndroidUtilities.dp(8)){
                fusionMode=true;previewHeight=g.height;
                int h=Math.round(previewHeight)+AndroidUtilities.dp(80);setMeasuredDimension(width,h);fusionTop=(h-previewHeight)/2;
                text.setTextSize(titlePx);displayName=android.text.TextUtils.ellipsize(name,new android.text.TextPaint(text),g.text.width(),android.text.TextUtils.TruncateAt.END).toString();
                fusionTitleX=app.flexygram.header.fusion.SignatureFusionGeometry.titleCenterX(
                        g, text.measureText(displayName));
                text.setTextSize(subtitlePx);displayStatus=android.text.TextUtils.ellipsize(status,new android.text.TextPaint(text),g.text.width(),android.text.TextUtils.TruncateAt.END).toString();
                fusionStatusX=g.text.centerX();
                fusion.clip.rewind();fusion.clip.addRoundRect(g.center.left,g.center.top,g.center.right,g.center.bottom,g.center.height()/2,g.center.height()/2,android.graphics.Path.Direction.CW);
                // Preview contact has initials only: keep the initial in the small native left slot.
                float placeholderW = Math.min(g.portrait.width(), AndroidUtilities.dp(73));
                float previewStart = g.rtl ? g.portrait.width()-placeholderW*.45f : placeholderW*.55f;
                float previewEnd = g.rtl ? g.portrait.width()-placeholderW : placeholderW;
                fusion.mask.prepare(previewStart,previewEnd,.9f,g.rtl);
                return;
            }
        }
        previewHeight=HeaderGeometry.height(width,titleLine,subtitleLine,AndroidUtilities.density,HeaderConfig.compact());
        float fit=Math.min(1f,(previewHeight-AndroidUtilities.dp(8))/(titleLine+subtitleLine));titlePx*=fit;subtitlePx*=fit;
        titlePx=Math.min(titlePx,previewHeight-AndroidUtilities.dp(8));
        int h=Math.round(previewHeight)+AndroidUtilities.dp(80);setMeasuredDimension(width,h);
        text.setTextSize(titlePx); float preferred = text.measureText(name);
        text.setTextSize(subtitlePx); preferred = Math.max(preferred, text.measureText(status)) + AndroidUtilities.dp(24);
        geometry.update(width,(h-previewHeight)/2,previewHeight,0,AndroidUtilities.density,LocaleController.isRTL,0,preferred);
        text.setTextSize(titlePx);displayName=android.text.TextUtils.ellipsize(name,new android.text.TextPaint(text),Math.max(0,geometry.title.width()-AndroidUtilities.dp(24)),android.text.TextUtils.TruncateAt.END).toString();
        text.setTextSize(subtitlePx);displayStatus=android.text.TextUtils.ellipsize(status,new android.text.TextPaint(text),Math.max(0,geometry.title.width()-AndroidUtilities.dp(24)),android.text.TextUtils.TruncateAt.END).toString();
    }
    @Override protected void onSizeChanged(int w, int h, int oldw, int oldh) { super.onSizeChanged(w,h,oldw,oldh); }
    @Override protected void onDraw(Canvas canvas) {
        float d = AndroidUtilities.density, height = previewHeight;
        canvas.drawColor(Theme.getColor(Theme.key_windowBackgroundGray));
        if (!HeaderConfig.signature()) { text.setColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText)); canvas.drawText(name, getWidth()/2f, getHeight()/2f, text); return; }
        if(fusionMode&&HeaderConfig.fusion()){drawFusion(canvas);return;}
        surface.draw(canvas, geometry, d, null);
        int color = Theme.getColor(Theme.key_actionBarDefaultTitle);
        if(iconColor!=color){iconColor=color;back.setColorFilter(color, android.graphics.PorterDuff.Mode.SRC_IN);}
        float arrow = LocaleController.isRTL ? geometry.back.right-height/2 : geometry.back.left+height/2;
        int side=AndroidUtilities.dp(24), y=Math.round(geometry.back.centerY());
        back.setBounds(Math.round(arrow)-side/2,y-side/2,Math.round(arrow)+side/2,y+side/2); back.draw(canvas);
        text.setColor(color);
        text.setTextSize(titlePx); float titleHeight=text.descent()-text.ascent(), titleAscent=text.ascent();
        text.setTextSize(subtitlePx); float subtitleHeight=text.descent()-text.ascent();
        float blockTop=geometry.title.centerY()-(titleHeight+subtitleHeight+AndroidUtilities.dp(2))/2;
        text.setTextSize(titlePx); canvas.drawText(displayName,geometry.title.centerX(),blockTop-titleAscent,text);
        text.setTextSize(subtitlePx);canvas.drawText(displayStatus,geometry.title.centerX(),blockTop+titleHeight+AndroidUtilities.dp(2)-text.ascent(),text);
        avatar.setColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));canvas.drawCircle(geometry.avatar.centerX(),geometry.avatar.centerY(),height/2-AndroidUtilities.dp(1),avatar);
        text.setColor(0xffffffff);text.setTextSize(AndroidUtilities.dp(20));canvas.drawText("A",geometry.avatar.centerX(),geometry.avatar.centerY()+AndroidUtilities.dp(7),text);
    }
    private void drawFusion(Canvas canvas) {
        var g=fusion.geometry;float d=AndroidUtilities.density;
        int color=Theme.getColor(Theme.key_actionBarDefaultTitle);
        if(fusion.color!=color){fusion.color=color;iconColor=color;fusion.phone.setColorFilter(color,android.graphics.PorterDuff.Mode.SRC_IN);fusion.more.setColorFilter(color,android.graphics.PorterDuff.Mode.SRC_IN);back.setColorFilter(color,android.graphics.PorterDuff.Mode.SRC_IN);}
        int fill=(Theme.getColor(Theme.key_windowBackgroundWhite)&0xffffff)|(Math.round(HeaderConfig.opacity()*2.55f)<<24);
        int edge=(Theme.getColor(Theme.key_divider)&0xffffff)|0x66000000;
        int outer=canvas.save();canvas.translate(0,fusionTop);
        fusion.surface.drawBackdrop(canvas,g,fill,edge,edge,d);
        int clip=canvas.save();canvas.clipPath(fusion.clip);
        int layer=fusion.mask.begin(canvas,g.portrait.left,g.portrait.top,g.portrait.right,g.portrait.bottom);
        // The synthetic preview has no real bitmap; mimic the same initials fallback as ChatAvatarContainer.
        float placeholderW = Math.min(g.portrait.width(), AndroidUtilities.dp(73));
        float placeholderLeft = g.rtl ? g.portrait.right-placeholderW : g.portrait.left;
        avatar.setColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlueText));
        canvas.drawRect(placeholderLeft,g.portrait.top,placeholderLeft+placeholderW,g.portrait.bottom,avatar);
        text.setTextSize(AndroidUtilities.dp(22));text.setColor(0xffffffff);
        canvas.drawText("A",placeholderLeft+placeholderW*.5f,g.portrait.centerY()+AndroidUtilities.dp(7),text);
        float fadeStart = g.rtl ? g.portrait.width()-placeholderW*.45f : placeholderW*.55f;
        float fadeEnd = g.rtl ? g.portrait.width()-placeholderW : placeholderW;
        canvas.translate(g.portrait.left,g.portrait.top);
        fusion.mask.finish(canvas,layer,g.portrait.width(),g.portrait.height(),
                fadeStart,fadeEnd,.9f,g.rtl);canvas.restoreToCount(clip);
        text.setColor(color);text.setTextSize(titlePx);float th=text.descent()-text.ascent(),ta=text.ascent();text.setTextSize(subtitlePx);float sh=text.descent()-text.ascent();
        float top=g.text.centerY()-(th+sh+AndroidUtilities.dp(2))/2;
        text.setTextSize(titlePx);canvas.drawText(displayName,fusionTitleX,top-ta,text);text.setTextSize(subtitlePx);canvas.drawText(displayStatus,fusionStatusX,top+th+AndroidUtilities.dp(2)-text.ascent(),text);
        int icon=AndroidUtilities.dp(24),x=Math.round(g.back.centerX()),y=Math.round(g.back.centerY());back.setBounds(x-icon/2,y-icon/2,x+icon/2,y+icon/2);
        int transform=canvas.save();if(g.rtl)canvas.scale(-1,1,g.back.centerX(),g.back.centerY());back.draw(canvas);canvas.restoreToCount(transform);
        x=Math.round(g.call.centerX());y=Math.round(g.call.centerY());fusion.phone.setBounds(x-icon/2,y-icon/2,x+icon/2,y+icon/2);fusion.phone.draw(canvas);
        x=Math.round(g.more.centerX());y=Math.round(g.more.centerY());fusion.more.setBounds(x-icon/2,y-icon/2,x+icon/2,y+icon/2);transform=canvas.save();canvas.rotate(90,x,y);fusion.more.draw(canvas);canvas.restoreToCount(transform);
        fusion.surface.drawCenterBorder(canvas,g,edge,d);canvas.restoreToCount(outer);
    }

}
