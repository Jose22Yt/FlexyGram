package app.flexygram.bubbles;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.text.TextPaint;
import android.text.TextUtils;
import android.view.View;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.MessageDrawable;
import org.telegram.ui.ActionBar.Theme;
/** Two synthetic native bubbles; no accounts, observers or permanent draw loop. */
public final class BubblePreviewView extends View {
    private final MessageDrawable incoming=new MessageDrawable(MessageDrawable.TYPE_TEXT,false,false);
    private final MessageDrawable outgoing=new MessageDrawable(MessageDrawable.TYPE_TEXT,true,false);
    private final MessageDrawable.PathDrawParams inCache=new MessageDrawable.PathDrawParams(),outCache=new MessageDrawable.PathDrawParams();
    private final TextPaint text=new TextPaint(Paint.ANTI_ALIAS_FLAG);
    private final String inLabel=LocaleController.getString(R.string.FlexyBubblePreviewIncoming),outLabel=LocaleController.getString(R.string.FlexyBubblePreviewOutgoing);
    private String visibleIn="",visibleOut="";
    private int rowHeight;
    public BubblePreviewView(Context context){super(context);setContentDescription(inLabel+". "+outLabel);}
    @Override protected void onMeasure(int w,int h){
        text.setTextSize(14*getResources().getDisplayMetrics().scaledDensity);
        rowHeight=Math.max(AndroidUtilities.dp(52),Math.round(text.getFontSpacing())+AndroidUtilities.dp(24));
        setMeasuredDimension(MeasureSpec.getSize(w),rowHeight*2+AndroidUtilities.dp(40));
    }
    @Override protected void onSizeChanged(int w,int h,int oldw,int oldh){
        int side=AndroidUtilities.dp(16),offset=AndroidUtilities.dp(40),top=AndroidUtilities.dp(12);
        incoming.setBounds(side,top,w-side-offset,top+rowHeight);
        outgoing.setBounds(side+offset,top+rowHeight+AndroidUtilities.dp(8),w-side,top+rowHeight*2+AndroidUtilities.dp(8));
        incoming.setTop(0,w,h,false,false);outgoing.setTop(0,w,h,false,false);
        visibleIn=TextUtils.ellipsize(inLabel,text,Math.max(0,incoming.getBounds().width()-AndroidUtilities.dp(32)),TextUtils.TruncateAt.END).toString();
        visibleOut=TextUtils.ellipsize(outLabel,text,Math.max(0,outgoing.getBounds().width()-AndroidUtilities.dp(32)),TextUtils.TruncateAt.END).toString();
    }
    @Override protected void onDraw(Canvas canvas){
        incoming.drawCached(canvas,inCache);outgoing.drawCached(canvas,outCache);
        text.setColor(Theme.getColor(Theme.key_chat_messageTextIn));
        float y=incoming.getBounds().centerY()-(text.ascent()+text.descent())/2;
        canvas.drawText(visibleIn,incoming.getBounds().left+AndroidUtilities.dp(16),y,text);
        text.setColor(Theme.getColor(Theme.key_chat_messageTextOut));y=outgoing.getBounds().centerY()-(text.ascent()+text.descent())/2;
        canvas.drawText(visibleOut,outgoing.getBounds().left+AndroidUtilities.dp(16),y,text);
    }
}
