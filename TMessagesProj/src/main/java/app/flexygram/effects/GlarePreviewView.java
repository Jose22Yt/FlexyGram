/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.effects;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import app.flexygram.preview.SignatureWallpaperPreview;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.NotificationCenter;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.RecyclerListView;
import org.telegram.ui.Components.blur3.GlassOutlineStyle;
import org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawable;
import org.telegram.ui.Components.blur3.drawable.color.BlurredBackgroundColorProviderThemed;

/** One static 64dp segment. Three neutral shapes use the native outline renderer. */
public final class GlarePreviewView extends View implements NotificationCenter.NotificationCenterDelegate, GlassOutlineStyle.Listener {
    private final SignatureWallpaperPreview wallpaper;
    private final Theme.ResourcesProvider provider;
    private final BlurredBackgroundColorProviderThemed colors;
    private final Paint fill=new Paint(Paint.ANTI_ALIAS_FLAG),stroke=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF[] shapes={new RectF(),new RectF(),new RectF()};
    private final float[] radii=new float[3];
    private final Path clip=new Path();
    private final RectF frame=new RectF();
    private int lastColor;
    public GlarePreviewView(Context context,Theme.ResourcesProvider provider){
        super(context);this.provider=provider;
        colors=new BlurredBackgroundColorProviderThemed(provider,Theme.key_windowBackgroundWhite);
        wallpaper=new SignatureWallpaperPreview(this,null,this::invalidate);
        setTag(RecyclerListView.TAG_NOT_SECTION);
        RecyclerView.LayoutParams params=new RecyclerView.LayoutParams(-1,-2);
        params.setMargins(dp(12),dp(4),dp(12),dp(4));setLayoutParams(params);
        setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        stroke.setStyle(Paint.Style.STROKE);stroke.setStrokeWidth(AndroidUtilities.dpf2(1));
    }
    private int dp(float value){return AndroidUtilities.dp(value);}
    @Override protected void onMeasure(int w,int h){setMeasuredDimension(MeasureSpec.getSize(w),dp(64));}
    @Override protected void onSizeChanged(int w,int h,int ow,int oh){
        super.onSizeChanged(w,h,ow,oh);
        frame.set(dp(2),dp(2),Math.max(dp(2),w-dp(2)),Math.max(dp(2),h-dp(2)));
        clip.rewind();clip.addRoundRect(frame,dp(26),dp(26),Path.Direction.CW);
        wallpaper.resize(w,h);
        float unit=Math.min(AndroidUtilities.density,Math.max(0,w-dp(24))/240f),cx=w*.5f,cy=h*.5f;
        shapes[0].set(cx-112*unit,cy-16*unit,cx-80*unit,cy+16*unit);radii[0]=16*unit;
        shapes[1].set(cx-62*unit,cy-16*unit,cx+42*unit,cy+16*unit);radii[1]=16*unit;
        shapes[2].set(cx+60*unit,cy-20*unit,cx+112*unit,cy+20*unit);radii[2]=8*unit;
    }
    @Override protected void onDraw(Canvas canvas){
        int surface=Theme.getColor(Theme.key_windowBackgroundWhite,provider);
        if(surface!=lastColor){lastColor=surface;colors.updateColors();}
        fill.setColor(surface);canvas.drawRoundRect(0,0,getWidth(),getHeight(),dp(28),dp(28),fill);
        int save=canvas.save();canvas.clipPath(clip);
        fill.setColor(Theme.getColor(Theme.key_chat_wallpaper,provider));canvas.drawRect(frame,fill);wallpaper.draw(canvas);
        for(int i=0;i<shapes.length;i++){
            RectF bounds=shapes[i];fill.setColor(colors.getBackgroundColor());canvas.drawRoundRect(bounds,radii[i],radii[i],fill);
            boolean solid=GlassOutlineStyle.current()==GlassOutlineStyle.SOLID;
            stroke.setColor(solid?colors.getStrokeColorFull():colors.getStrokeColorTop());
            BlurredBackgroundDrawable.drawStroke(canvas,bounds,radii[i],AndroidUtilities.dpf2(1),true,stroke);
            stroke.setColor(solid?colors.getStrokeColorFull():colors.getStrokeColorBottom());
            BlurredBackgroundDrawable.drawStroke(canvas,bounds,radii[i],AndroidUtilities.dpf2(1),false,stroke);
        }
        canvas.restoreToCount(save);
    }
    @Override protected void onAttachedToWindow(){
        super.onAttachedToWindow();wallpaper.attach();GlassOutlineStyle.addListener(this);
        NotificationCenter center=NotificationCenter.getGlobalInstance();
        center.addObserver(this,NotificationCenter.didSetNewTheme);center.addObserver(this,NotificationCenter.didApplyNewTheme);center.addObserver(this,NotificationCenter.didSetNewWallpapper);
    }
    @Override protected void onDetachedFromWindow(){
        NotificationCenter center=NotificationCenter.getGlobalInstance();
        center.removeObserver(this,NotificationCenter.didSetNewTheme);center.removeObserver(this,NotificationCenter.didApplyNewTheme);center.removeObserver(this,NotificationCenter.didSetNewWallpapper);
        wallpaper.close();super.onDetachedFromWindow();
    }
    @Override public void onGlassOutlineStyleChanged(){if(isAttachedToWindow())invalidate();}
    @Override public void didReceivedNotification(int id,int account,Object...args){colors.updateColors();wallpaper.refresh();invalidate();}
}
