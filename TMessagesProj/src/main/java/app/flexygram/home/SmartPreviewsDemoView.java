/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import android.content.Context;
import android.content.res.Configuration;
import android.graphics.Canvas;
import android.text.TextPaint;
import android.view.View;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;

/** Local examples through the production span, icon and palette. No messages, media or services. */
public final class SmartPreviewsDemoView extends View implements Theme.Colorable {
    private final Theme.ResourcesProvider provider;
    private final TextPaint ink=new TextPaint(android.graphics.Paint.ANTI_ALIAS_FLAG);
    private final int[] kinds={SignatureSmartPreviewPalette.PHOTO,SignatureSmartPreviewPalette.VIDEO,
            SignatureSmartPreviewPalette.ZIP,SignatureSmartPreviewPalette.VOICE,SignatureSmartPreviewPalette.LINK};
    private final SignatureSmartPillSpan[] pills=new SignatureSmartPillSpan[5];
    private final String[] labels=new String[5];
    private final float[] left=new float[5],top=new float[5];
    private final int[] widths=new int[5];
    private int measuredWidth=-1,lastMode=-1;
    public SmartPreviewsDemoView(Context context,Theme.ResourcesProvider provider){
        super(context);this.provider=provider;setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_YES);
        SignatureSmartPreviews.mode();
    }
    public void styleChanged(int previous,int next){
        if(previous==SignatureSmartPreviewPalette.OFF || next==SignatureSmartPreviewPalette.OFF){measuredWidth=-1;requestLayout();}
        invalidate();
    }
    @Override public void updateColors(){invalidate();}
    @Override protected void onConfigurationChanged(Configuration c){super.onConfigurationChanged(c);measuredWidth=-1;requestLayout();}
    @Override protected void onMeasure(int widthSpec,int heightSpec){
        int width=MeasureSpec.getSize(widthSpec),mode=SignatureSmartPreviews.mode();
        int padding=AndroidUtilities.dp(20),gap=AndroidUtilities.dp(8),row=AndroidUtilities.dp(28);
        if(width!=measuredWidth || (mode==SignatureSmartPreviewPalette.OFF)!=(lastMode==SignatureSmartPreviewPalette.OFF)){
            measuredWidth=width;lastMode=mode;ink.setTextSize(AndroidUtilities.dp(15));
            labels[0]=LocaleController.getString(R.string.FlexySmartPhoto);
            labels[1]=LocaleController.getString(R.string.FlexySmartVideo)+" · 0:39";
            labels[2]=LocaleController.getString(R.string.FlexySmartDemoArchive);
            labels[3]=LocaleController.getString(R.string.FlexyPillVoice)+" · 0:24";
            labels[4]=LocaleController.getString(R.string.FlexySmartLink);
            int available=Math.max(1,width-padding*2),x=0,y=AndroidUtilities.dp(10);
            for(int i=0;i<kinds.length;i++){
                pills[i]=new SignatureSmartPillSpan(kinds[i],labels[i],available,provider,i==2);
                widths[i]=mode==SignatureSmartPreviewPalette.OFF?Math.min(available,(int)Math.ceil(ink.measureText(labels[i]))):pills[i].getSize(ink,"\ufffc",0,1,null);
                if(x>0 && x+widths[i]>available){x=0;y+=row;}
                left[i]=LocaleController.isRTL?width-padding-x-widths[i]:padding+x;top[i]=y;x+=widths[i]+gap;
            }
            setContentDescription(android.text.TextUtils.join(", ",labels));
        }
        setMeasuredDimension(width,(int)top[4]+row+AndroidUtilities.dp(10));
    }
    @Override protected void onDraw(Canvas canvas){
        super.onDraw(canvas);int mode=SignatureSmartPreviews.drawingMode();
        ink.setColor(Theme.getColor(Theme.key_windowBackgroundWhiteBlackText,provider));
        ink.setTextSize(AndroidUtilities.dp(15));
        for(int i=0;i<pills.length;i++){
            if(pills[i]==null)continue;
            int y=(int)top[i];
            if(mode==SignatureSmartPreviewPalette.OFF){
                int save=canvas.save();canvas.clipRect(left[i],y,left[i]+widths[i],y+AndroidUtilities.dp(24));
                canvas.drawText(labels[i],left[i],y+AndroidUtilities.dp(17),ink);canvas.restoreToCount(save);
            }else pills[i].draw(canvas,"\ufffc",0,1,left[i],y,y+AndroidUtilities.dp(17),y+AndroidUtilities.dp(24),ink);
        }
    }
}
