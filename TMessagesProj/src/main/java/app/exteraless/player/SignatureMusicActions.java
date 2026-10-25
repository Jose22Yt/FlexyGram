package app.exteraless.player;

import android.content.Context;
import android.view.View;
import android.widget.LinearLayout;
import static org.telegram.messenger.AndroidUtilities.dp;

/** Four native actions, one row normally; narrow/large-font windows reflow without shrinking labels. */
public final class SignatureMusicActions extends LinearLayout {
    public SignatureMusicActions(Context context) { super(context); }
    private int columns(int width) {
        float scale=getResources().getConfiguration().fontScale;
        int minimum=Math.round(dp(72)*Math.max(1f,scale));
        return width>=minimum*4?4:width>=minimum*2?2:1;
    }
    @Override protected void onMeasure(int widthSpec,int heightSpec) {
        int width=MeasureSpec.getSize(widthSpec),columns=columns(width);
        int cellHeight=Math.max(dp(72),(int)Math.ceil(dp(38)+16*getResources().getDisplayMetrics().scaledDensity));
        for(int i=0;i<getChildCount();i++) {
            View child=getChildAt(i);LayoutParams lp=(LayoutParams)child.getLayoutParams();
            int cellWidth=(i%columns+1)*width/columns-(i%columns)*width/columns;
            child.measure(MeasureSpec.makeMeasureSpec(Math.max(0,cellWidth-lp.leftMargin-lp.rightMargin),MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(cellHeight,MeasureSpec.EXACTLY));
        }
        int rows=(getChildCount()+columns-1)/columns;
        setMeasuredDimension(width,resolveSize(rows*cellHeight+Math.max(0,rows-1)*dp(8),heightSpec));
    }
    @Override protected void onLayout(boolean changed,int left,int top,int right,int bottom) {
        int width=right-left,columns=columns(width);boolean rtl=getLayoutDirection()==LAYOUT_DIRECTION_RTL;
        for(int i=0;i<getChildCount();i++) {
            View child=getChildAt(i);LayoutParams lp=(LayoutParams)child.getLayoutParams();
            int col=rtl?columns-1-i%columns:i%columns;
            int x=col*width/columns+lp.leftMargin,y=(i/columns)*(child.getMeasuredHeight()+dp(8));
            child.layout(x,y,x+child.getMeasuredWidth(),y+child.getMeasuredHeight());
        }
    }
}
