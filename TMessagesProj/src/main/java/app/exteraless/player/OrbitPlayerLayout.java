package app.exteraless.player;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.drawable.GradientDrawable;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import static org.telegram.messenger.AndroidUtilities.dp;

/** Orbit scene. Scroll is the single animation clock; the artwork has one retained owner. */
public final class OrbitPlayerLayout extends FrameLayout {
    private final ScrollView scroll;
    private final LinearLayout content;
    private final View artworkSlot;
    private final OrbitArtwork artwork;
    private final Header header;
    private final View lyricsPanel, titleRow, controls, group, queue;
    private final LinearLayout lyricsControls;
    private final MusicBlurSurface[] surfaces = new MusicBlurSurface[3];
    private final View[] surfaceViews;
    private final TextView sourceLabel, sourceTitle, compactSong;
    private final TextView queueSearch;
    private final GradientDrawable searchBackground = new GradientDrawable();
    private final ImageView compactPlay, compactNext;
    private PlayerIcon playIcon=PlayerIcon.fill(PlayerIcon.PAUSE,20),nextIcon=PlayerIcon.fill(PlayerIcon.NEXT,20);
    private boolean lyrics;
    private int topInset,bottomInset,diameter;
    private float collapse;
    private PlayerColors colors;
    private String song="";

    public OrbitPlayerLayout(Context context,CoverImage cover,TextView sourceLabel,TextView sourceTitle,
            View back,View more,View titleRow,View times,ControlsRow controls,View group,View queue,
            View lyricsPanel,Runnable toggle,Runnable next,Runnable openSearch) {
        super(context);setClipChildren(false);this.sourceLabel=sourceLabel;this.sourceTitle=sourceTitle;
        this.lyricsPanel=lyricsPanel;this.titleRow=titleRow;this.controls=controls;this.group=group;this.queue=queue;
        scroll=new ScrollView(context);scroll.setFillViewport(true);scroll.setClipToPadding(false);scroll.setVerticalScrollBarEnabled(false);
        content=new LinearLayout(context);content.setOrientation(LinearLayout.VERTICAL);scroll.addView(content,new ScrollView.LayoutParams(-1,-2));addView(scroll,new LayoutParams(-1,-1));
        queueSearch=new TextView(context);queueSearch.setTextSize(16);queueSearch.setGravity(Gravity.CENTER_VERTICAL);
        queueSearch.setSingleLine(true);queueSearch.setEllipsize(TextUtils.TruncateAt.END);
        queueSearch.setText(LocaleController.getString(R.string.FlexyQueueSearch));queueSearch.setContentDescription(queueSearch.getText());
        queueSearch.setPadding(dp(18),0,dp(18),0);queueSearch.setCompoundDrawablePadding(dp(12));
        queueSearch.setBackground(searchBackground);queueSearch.setOnClickListener(v->openSearch.run());queueSearch.setFocusable(true);
        LinearLayout.LayoutParams searchParams=new LinearLayout.LayoutParams(-1,dp(48));searchParams.bottomMargin=dp(20);
        content.addView(queueSearch,searchParams);
        artworkSlot=new View(context);content.addView(artworkSlot,new LinearLayout.LayoutParams(-1,dp(280)));
        move(times,content,new LinearLayout.LayoutParams(-1,-2));
        move(titleRow,content,new LinearLayout.LayoutParams(-1,-2));
        LinearLayout.LayoutParams titleParams=(LinearLayout.LayoutParams)titleRow.getLayoutParams();titleParams.topMargin=dp(16);titleParams.bottomMargin=dp(12);
        move(controls,content,new LinearLayout.LayoutParams(-1,-2));
        LinearLayout.LayoutParams utility=new LinearLayout.LayoutParams(-1,-2);utility.topMargin=dp(20);utility.bottomMargin=dp(20);move(group,content,utility);
        move(queue,content,new LinearLayout.LayoutParams(-1,-2));
        compactPlay=button(context,playIcon,LocaleController.getString(R.string.AccActionPause),toggle);
        compactNext=button(context,nextIcon,LocaleController.getString(R.string.Next),next);
        compactSong=new TextView(context);compactSong.setTextSize(11);compactSong.setSingleLine(true);compactSong.setEllipsize(TextUtils.TruncateAt.END);
        header=new Header(context,back,more);addView(header,new LayoutParams(-1,dp(56)));
        surfaceViews=new View[]{back,more,header.pill};
        MusicBlurCapture sharedCapture=new MusicBlurCapture(this);
        for(int i=0;i<surfaces.length;i++){surfaces[i]=new MusicBlurSurface(surfaceViews[i],dp(28),true,sharedCapture);surfaceViews[i].setBackground(surfaces[i]);}
        artwork=new OrbitArtwork(context,cover);
        addView(artwork,new LayoutParams(dp(280),dp(280)));
        remove(lyricsPanel);addView(lyricsPanel,new LayoutParams(-1,-1));lyricsPanel.setVisibility(GONE);
        lyricsControls=new LinearLayout(context);lyricsControls.setGravity(Gravity.CENTER);addView(lyricsControls,new LayoutParams(-1,dp(64)));
        ImageView lyricsPlay=button(context,PlayerIcon.fill(PlayerIcon.PAUSE,24),LocaleController.getString(R.string.AccActionPause),toggle);
        ImageView lyricsNext=button(context,PlayerIcon.fill(PlayerIcon.NEXT,24),LocaleController.getString(R.string.Next),next);
        lyricsControls.addView(lyricsPlay,new LinearLayout.LayoutParams(dp(56),dp(56)));lyricsControls.addView(lyricsNext,new LinearLayout.LayoutParams(dp(56),dp(56)));ImageView returnButton=button(context,PlayerIcon.stroke(PlayerIcon.LYRICS,22),LocaleController.getString(R.string.FlexyMusicLyrics),()->back.performClick());lyricsControls.addView(returnButton,new LinearLayout.LayoutParams(dp(56),dp(56)));lyricsControls.setVisibility(GONE);
        scroll.setOnScrollChangeListener((v,x,y,oldX,oldY)->updateCollapse());
    }
    private static void remove(View view){if(view.getParent() instanceof ViewGroup)((ViewGroup)view.getParent()).removeView(view);}
    private static void move(View view,ViewGroup host,ViewGroup.LayoutParams lp){remove(view);host.addView(view,lp);}
    private static ImageView button(Context context,PlayerIcon icon,String description,Runnable click){ImageView v=new ImageView(context);v.setScaleType(ImageView.ScaleType.CENTER);v.setImageDrawable(icon);v.setContentDescription(description);v.setOnClickListener(w->click.run());return v;}
    public OrbitArtwork getArtwork(){return artwork;}
    public int getScrollYPosition(){return scroll.getScrollY();}
    public float getCollapseFraction(){return collapse;}
    public void setInsets(int top,int bottom){if(topInset!=top||bottomInset!=bottom){topInset=top;bottomInset=bottom;requestLayout();}}
    public void bindSong(String title,String artist){song=title;compactSong.setText(title+" · "+artist);artwork.setContentDescription(title+", "+artist);header.requestLayout();}
    public void setPlaying(boolean playing){playIcon=PlayerIcon.fill(playing?PlayerIcon.PAUSE:PlayerIcon.PLAY,20);if(colors!=null)playIcon.setColor(colors.primary);compactPlay.setImageDrawable(playIcon);compactPlay.setContentDescription(LocaleController.getString(playing?R.string.AccActionPause:R.string.AccActionPlay));ImageView play=(ImageView)lyricsControls.getChildAt(0);play.setImageDrawable(PlayerIcon.fill(playing?PlayerIcon.PAUSE:PlayerIcon.PLAY,24));play.setContentDescription(compactPlay.getContentDescription());if(colors!=null)((PlayerIcon)play.getDrawable()).setColor(colors.primary);}
    public void setLyricsMode(boolean value){
        lyrics=value;
        scroll.setVisibility(value?INVISIBLE:VISIBLE);
        artwork.setVisibility(value?INVISIBLE:VISIBLE);
        lyricsPanel.setVisibility(value?VISIBLE:GONE);
        lyricsControls.setVisibility(value?VISIBLE:GONE);
        if(lyrics){
            lyricsPanel.bringToFront();
            lyricsControls.bringToFront();
            header.bringToFront();
        }else{
            header.bringToFront();
            artwork.bringToFront();
        }
        requestLayout();
    }
    public void setColors(PlayerColors value){colors=value;
        searchBackground.setColor(value.surfaceHigh);searchBackground.setCornerRadius(dp(24));queueSearch.setTextColor(value.onSurfaceVariant);
        android.graphics.drawable.Drawable searchIcon=getResources().getDrawable(R.drawable.msg_search).mutate();
        searchIcon.setColorFilter(new android.graphics.PorterDuffColorFilter(value.onSurfaceVariant,android.graphics.PorterDuff.Mode.SRC_IN));
        searchIcon.setBounds(0,0,dp(22),dp(22));queueSearch.setCompoundDrawablesRelative(searchIcon,null,null,null);
setBackgroundColor(value.surface);artwork.setColors(value);for(MusicBlurSurface s:surfaces)s.setColors(value);compactSong.setTextColor(value.onSurfaceVariant);playIcon.setColor(value.primary);nextIcon.setColor(value.onSurface);for(int i=0;i<lyricsControls.getChildCount();i++)((PlayerIcon)((ImageView)lyricsControls.getChildAt(i)).getDrawable()).setColor(value.primary);header.invalidate();}
    @Override protected void onAttachedToWindow(){super.onAttachedToWindow();for(MusicBlurSurface s:surfaces)s.attach();}
    @Override protected void onDetachedFromWindow(){for(MusicBlurSurface s:surfaces)s.detach();super.onDetachedFromWindow();}
    @Override protected void onMeasure(int ws,int hs){
        int width=MeasureSpec.getSize(ws),height=MeasureSpec.getSize(hs);
        diameter=Math.max(dp(120),Math.min(dp(280),width-dp(72)));
        int headerHeight=Math.max(dp(56),Math.round(dp(30)+sourceTitle.getTextSize()*1.4f));if(width<dp(320)||getResources().getConfiguration().fontScale>1.6f)headerHeight+=dp(52);
        header.measure(MeasureSpec.makeMeasureSpec(width,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(headerHeight,MeasureSpec.EXACTLY));
        content.setPadding(dp(24),topInset+headerHeight+dp(16),dp(24),bottomInset+dp(28));
        ViewGroup.LayoutParams slot=artworkSlot.getLayoutParams();slot.height=diameter;
        scroll.measure(MeasureSpec.makeMeasureSpec(width,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(height,MeasureSpec.EXACTLY));
        // A short queue can still be inspected with a fully docked player.
        int distance=diameter+titleRow.getMeasuredHeight()+controls.getMeasuredHeight()+dp(36);
        content.setMinimumHeight(height+Math.max(dp(48),distance));
        scroll.measure(MeasureSpec.makeMeasureSpec(width,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(height,MeasureSpec.EXACTLY));
        artwork.measure(MeasureSpec.makeMeasureSpec(diameter,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(diameter,MeasureSpec.EXACTLY));
        lyricsPanel.measure(MeasureSpec.makeMeasureSpec(Math.max(0,width-dp(40)),MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(Math.max(dp(80),height-topInset-headerHeight-bottomInset-dp(92)),MeasureSpec.EXACTLY));
        lyricsControls.measure(MeasureSpec.makeMeasureSpec(width,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(dp(64),MeasureSpec.EXACTLY));setMeasuredDimension(width,height);
    }
    @Override protected void onLayout(boolean changed,int l,int t,int r,int b){
        scroll.layout(0,0,r-l,b-t);header.layout(0,topInset,r-l,topInset+header.getMeasuredHeight());
        artwork.layout(0,0,diameter,diameter);artwork.setPivotX(0);artwork.setPivotY(0);
        int lyricTop=header.getBottom()+dp(12);lyricsPanel.layout(dp(20),lyricTop,r-l-dp(20),lyricTop+lyricsPanel.getMeasuredHeight());
        lyricsControls.layout(0,b-t-bottomInset-dp(72),r-l,b-t-bottomInset-dp(8));updateCollapse();
    }
    private void updateCollapse(){
        if(diameter==0)return;
        float distance=Math.max(dp(96),artworkSlot.getTop()+diameter-header.getBottom()-dp(12));
        collapse=lyrics?1:OrbitMotion.fraction(scroll.getScrollY(),distance);
        header.place(collapse);
        float size=OrbitMotion.mix(diameter,dp(36),collapse),scale=size/diameter;
        float startX=(getWidth()-diameter)*.5f,startY=artworkSlot.getTop();
        float endX=header.pill.getLeft()+dp(8),endY=header.getTop()+header.pill.getTop()+(header.pill.getHeight()-dp(36))*.5f;
        if(getLayoutDirection()==LAYOUT_DIRECTION_RTL)endX=header.pill.getRight()-dp(44);
        artwork.setTranslationX(OrbitMotion.mix(startX,endX,collapse));
        artwork.setTranslationY(Math.max(endY,OrbitMotion.mix(startY,endY,collapse)));
        artwork.setScaleX(scale);artwork.setScaleY(scale);artwork.setRingAlpha(1-collapse);
        artwork.setEnabled(!lyrics&&collapse<.1f);artwork.setImportantForAccessibility(collapse>.1f?IMPORTANT_FOR_ACCESSIBILITY_NO_HIDE_DESCENDANTS:IMPORTANT_FOR_ACCESSIBILITY_YES);
        titleRow.setAlpha(1-collapse);controls.setAlpha(1-collapse);
        titleRow.setImportantForAccessibility(collapse>.5f?IMPORTANT_FOR_ACCESSIBILITY_NO_HIDE_DESCENDANTS:IMPORTANT_FOR_ACCESSIBILITY_AUTO);
        controls.setImportantForAccessibility(collapse>.5f?IMPORTANT_FOR_ACCESSIBILITY_NO_HIDE_DESCENDANTS:IMPORTANT_FOR_ACCESSIBILITY_AUTO);
        boolean docked=collapse>=.85f;
        controls.setEnabled(!docked);
        controls.setVisibility(docked?INVISIBLE:VISIBLE);
    }
    private final class Header extends ViewGroup {
        private final View back,more;
        private int desiredWidth;
        private boolean stacked;
        private final FrameLayout pill;
        private final LinearLayout labels;
        Header(Context c,View back,View more){super(c);this.back=back;this.more=more;remove(back);remove(more);addView(back);addView(more);
            pill=new FrameLayout(c);pill.setClipChildren(true);pill.setClickable(true);addView(pill);labels=new LinearLayout(c);labels.setOrientation(LinearLayout.VERTICAL);labels.setGravity(Gravity.CENTER);remove(sourceLabel);remove(sourceTitle);labels.addView(sourceLabel);labels.addView(sourceTitle);labels.addView(compactSong);pill.addView(labels);pill.addView(compactPlay);pill.addView(compactNext);}
        @Override public void draw(Canvas canvas){if(!MusicBlurSurface.isCapturing())super.draw(canvas);}
        @Override protected void onMeasure(int ws,int hs){int w=MeasureSpec.getSize(ws),h=MeasureSpec.getSize(hs);stacked=w<dp(320)||getResources().getConfiguration().fontScale>1.6f;desiredWidth=Math.max(dp(100),Math.round(Math.max(sourceTitle.getPaint().measureText(sourceTitle.getText().toString()),sourceLabel.getPaint().measureText(sourceLabel.getText().toString()))+dp(28)));int p48=MeasureSpec.makeMeasureSpec(dp(48),MeasureSpec.EXACTLY);back.measure(p48,p48);more.measure(p48,p48);pill.measure(MeasureSpec.makeMeasureSpec(Math.max(1,w-dp(120)),MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec((stacked?h-dp(52):h)-dp(4),MeasureSpec.EXACTLY));compactPlay.measure(MeasureSpec.makeMeasureSpec(dp(48),MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(dp(48),MeasureSpec.EXACTLY));compactNext.measure(MeasureSpec.makeMeasureSpec(dp(48),MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(dp(48),MeasureSpec.EXACTLY));setMeasuredDimension(w,h);}
        @Override protected void onLayout(boolean changed,int l,int t,int r,int b){place(collapse);}
        void place(float fraction){
            if(getWidth()==0)return;boolean rtl=getLayoutDirection()==LAYOUT_DIRECTION_RTL;int w=getWidth(),h=stacked?getHeight()-dp(52):getHeight(),max=Math.max(1,w-dp(stacked?16:120));
            int expanded=Math.min(max,desiredWidth);
            int pw=Math.round(OrbitMotion.mix(expanded,max,fraction)),left=(w-pw)/2;back.layout(rtl?w-dp(56):dp(8),(h-dp(48))/2,rtl?w-dp(8):dp(56),(h+dp(48))/2);more.layout(rtl?dp(8):w-dp(56),(h-dp(48))/2,rtl?dp(56):w-dp(8),(h+dp(48))/2);
            pill.layout(left,stacked?dp(52):dp(2),left+pw,stacked?getHeight()-dp(2):h-dp(2));
            boolean docked=fraction>.88f;int actionCount=w>=dp(360)?2:1;int start=dp(12)+Math.round(dp(36)*fraction),end=dp(12)+Math.round(dp(48)*actionCount*fraction);
            sourceLabel.setVisibility(docked||getResources().getConfiguration().fontScale>1.6f?GONE:VISIBLE);compactSong.setVisibility(docked&&getResources().getConfiguration().fontScale<=1.6f?VISIBLE:GONE);
            int textWidth=Math.max(dp(12),pw-start-end);labels.measure(MeasureSpec.makeMeasureSpec(textWidth,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(pill.getHeight(),MeasureSpec.AT_MOST));int tx=rtl?end:start,ty=(pill.getHeight()-labels.getMeasuredHeight())/2;labels.layout(tx,ty,tx+textWidth,ty+labels.getMeasuredHeight());
            compactPlay.setVisibility(docked?VISIBLE:INVISIBLE);compactNext.setVisibility(docked&&actionCount==2?VISIBLE:INVISIBLE);
            compactPlay.setEnabled(docked);compactNext.setEnabled(docked&&actionCount==2);
            int px=rtl?dp(2):pw-dp(48)*actionCount;compactPlay.layout(px,(pill.getHeight()-dp(48))/2,px+dp(48),(pill.getHeight()+dp(48))/2);int nx=rtl?dp(50):pw-dp(48);compactNext.layout(nx,(pill.getHeight()-dp(48))/2,nx+dp(48),(pill.getHeight()+dp(48))/2);
            compactPlay.setAlpha(fraction);compactNext.setAlpha(fraction);
        }
    }
}
