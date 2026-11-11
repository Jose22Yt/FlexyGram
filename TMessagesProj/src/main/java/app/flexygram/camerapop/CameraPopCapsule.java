/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.camerapop;

import static org.telegram.messenger.AndroidUtilities.dp;
import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.os.Build;
import android.text.TextUtils;
import android.view.Choreographer;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.ImageView;
import java.util.ArrayList;
import java.util.List;
import java.util.function.LongConsumer;
import org.telegram.messenger.*;
import org.telegram.tgnet.TLRPC;
import org.telegram.ui.Components.AvatarDrawable;
import org.telegram.ui.Components.BackupImageView;

/** Compact island + recycled chat list. No fullscreen overlay, blur or idle frame loop. */
final class CameraPopCapsule extends FrameLayout {
    private final FrameLayout root,compact;
    private final LinearLayout panel;
    private final TextView left,right,heading;
    private final ListView list;
    private final Rows adapter=new Rows();
    private final Paint surface=new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path clip=new Path();
    private final RectF bounds=new RectF();
    private final CameraPopSpring presence=new CameraPopSpring(),expansion=new CameraPopSpring();
    private final View.OnLayoutChangeListener layoutListener;
    private final Runnable reposition=this::position;
    private Choreographer.FrameCallback frame;
    private Runnable completed,expandedChanged;
    private LongConsumer rowClick;
    private List<CameraPopInbox.Row> rows=new ArrayList<>();
    private int account,compactHeight,fullHeight,compactWidth;
    private float anchorX,anchorY,compactLeft,terminal=.01f,hitRadius;
    private boolean names,expanded,cutout,exiting;
    private long previousFrame,started;

    CameraPopCapsule(FrameLayout root) {
        super(root.getContext());this.root=root;Context c=getContext();
        setWillNotDraw(false);setClickable(true);setFocusable(true);
        setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_YES);
        setAccessibilityLiveRegion(ACCESSIBILITY_LIVE_REGION_POLITE);
        surface.setColor(Color.rgb(18,18,20));
        compact=new FrameLayout(c);left=label(c,12);right=label(c,13);
        left.setGravity(Gravity.CENTER);right.setGravity(Gravity.CENTER);
        compact.addView(left);compact.addView(right);addView(compact);
        compact.setOnClickListener(v->toggleExpanded());
        panel=new LinearLayout(c);panel.setOrientation(LinearLayout.VERTICAL);
        LinearLayout toolbar=new LinearLayout(c);toolbar.setGravity(Gravity.CENTER_VERTICAL);
        toolbar.setMinimumHeight(dp(48));
        toolbar.setPadding(dp(16),0,dp(8),0);heading=label(c,14);
        toolbar.addView(heading,new LinearLayout.LayoutParams(0,LayoutParams.WRAP_CONTENT,1));heading.setGravity(Gravity.CENTER_VERTICAL);
        ImageView close=new ImageView(c);close.setImageResource(R.drawable.fg_ios_original_chat_context_menu_collapse);
        close.setColorFilter(Color.WHITE);close.setScaleType(ImageView.ScaleType.CENTER);
        close.setContentDescription(LocaleController.getString(R.string.CameraPopCollapse));
        toolbar.addView(close,new LinearLayout.LayoutParams(dp(48),dp(48)));close.setOnClickListener(v->toggleExpanded());
        panel.addView(toolbar);
        list=new ListView(c);list.setDivider(null);list.setCacheColorHint(Color.TRANSPARENT);list.setAdapter(adapter);
        list.setOnItemClickListener((parent,v,p,id)->{if(p<rows.size() && rowClick!=null)rowClick.accept(rows.get(p).dialog);});
        panel.addView(list,new LinearLayout.LayoutParams(LayoutParams.MATCH_PARENT,0,1));
        addView(panel);panel.setVisibility(GONE);
        layoutListener=(v,l,t,r,b,ol,ot,or,ob)->{if(r-l!=or-ol || b-t!=ob-ot)position();};
        root.addOnLayoutChangeListener(layoutListener);
        setOnApplyWindowInsetsListener((v,insets)->{removeCallbacks(reposition);post(reposition);return insets;});
    }
    private TextView label(Context c,int size) {
        TextView t=new TextView(c);t.setTextColor(Color.WHITE);t.setTextSize(size);
        t.setTypeface(AndroidUtilities.bold());t.setSingleLine(true);t.setEllipsize(TextUtils.TruncateAt.END);return t;
    }
    void bindRows(int account,boolean names,List<CameraPopInbox.Row> rows,LongConsumer onRow,Runnable onExpansion) {
        boolean resize=Math.min(5,this.rows.size())!=Math.min(5,rows.size()) || getWidth()==0;
        this.account=account;this.names=names;this.rows=rows;rowClick=onRow;expandedChanged=onExpansion;
        long total=0;for(CameraPopInbox.Row row:rows)total+=row.unread;
        String chats=LocaleController.formatPluralString("CameraPopChats",rows.size());
        String messages=LocaleController.formatPluralString("CameraPopUnread",(int)Math.min(Integer.MAX_VALUE,total));
        left.setText(Integer.toString(rows.size()));right.setText(Long.toString(total));
        heading.setText(chats+" · "+messages);setContentDescription(chats+". "+messages+". "+LocaleController.getString(R.string.CameraPopExpand));
        compact.setContentDescription(getContentDescription());
        if(panel.getVisibility()==VISIBLE)adapter.notifyDataSetChanged();
        if(resize)position();
    }
    boolean isExpanded() {return expanded;}
    boolean isExiting() {return exiting;}
    void toggleExpanded() {
        exiting=false;
        expanded=!expanded;if(expanded)adapter.notifyDataSetChanged();panel.setVisibility(VISIBLE);
        animateTo(1f,expanded?1f:0f,null);
        if(expandedChanged!=null)expandedChanged.run();
    }
    void position() {
        if(getLayoutParams()==null || root.getWidth()<=0 || root.getHeight()<=0)return;
        CameraPopCutout.Anchor a=CameraPopCutout.read(root);
        RectF hole=a.bounds;int width=root.getWidth(),height=root.getHeight();
        CameraPopGeometry.Island p=CameraPopGeometry.island(width,height,a.left,a.top,a.right,a.bottom,
                getResources().getDisplayMetrics().density,rows.size(),hole.left,hole.top,hole.right,hole.bottom);
        cutout=p.cutout;compactHeight=p.compactHeight;compactWidth=p.compactWidth;fullHeight=p.height;
        int fullWidth=p.width;float x=p.x,y=p.y;anchorX=p.anchorX;anchorY=p.anchorY;compactLeft=p.compactLeft;
        terminal=cutout?Math.min(.2f,Math.max(1f,Math.min(hole.width(),hole.height())*.35f)/Math.max(fullWidth,fullHeight)):.01f;
        LayoutParams lp=(LayoutParams)getLayoutParams();
        if(lp.width!=fullWidth || lp.height!=fullHeight || lp.leftMargin!=Math.round(x) || lp.topMargin!=Math.round(y)) {
            lp.width=fullWidth;lp.height=fullHeight;lp.leftMargin=Math.round(x);lp.topMargin=Math.round(y);setLayoutParams(lp);
        }
        LayoutParams cp=new LayoutParams(compactWidth,compactHeight);cp.leftMargin=Math.round(compactLeft);compact.setLayoutParams(cp);
        int gap=cutout?Math.round(hole.width())+dp(12):dp(16);
        int middle=Math.round(anchorX-compactLeft);
        int leftWidth=Math.max(0,middle-gap/2),rightStart=Math.min(compactWidth,middle+gap/2);
        LayoutParams l=new LayoutParams(leftWidth,compactHeight);left.setLayoutParams(l);left.setVisibility(leftWidth>=dp(24)?VISIBLE:INVISIBLE);
        LayoutParams r=new LayoutParams(Math.max(0,compactWidth-rightStart),compactHeight);r.leftMargin=rightStart;right.setLayoutParams(r);
        LayoutParams pp=new LayoutParams(fullWidth,Math.max(0,fullHeight-compactHeight));pp.topMargin=compactHeight;panel.setLayoutParams(pp);
        setPivotX(anchorX);setPivotY(anchorY);apply();
    }
    @Override protected void onDraw(Canvas c) {
        super.onDraw(c);float e=expansion.value;
        bounds.set(compactLeft*(1-e),0,compactLeft+compactWidth+(getWidth()-compactLeft-compactWidth)*e,
                compactHeight+(fullHeight-compactHeight)*e);
        clip.rewind();float radius=compactHeight/2f+(dp(26)-compactHeight/2f)*e;hitRadius=radius;
        clip.addRoundRect(bounds,radius,radius,Path.Direction.CW);c.drawPath(clip,surface);
    }
    @Override protected void dispatchDraw(Canvas c) {int save=c.save();c.clipPath(clip);super.dispatchDraw(c);c.restoreToCount(save);}
    @Override public boolean dispatchTouchEvent(MotionEvent e) {
        if(e.getActionMasked()==MotionEvent.ACTION_DOWN && !CameraPopGeometry.contains(bounds.left,bounds.top,bounds.right,bounds.bottom,hitRadius,e.getX(),e.getY()))return false;
        return super.dispatchTouchEvent(e);
    }
    void enter() {exiting=false;position();animateTo(1f,expanded?1f:0f,null);}
    void exit(Runnable done) {exiting=true;animateTo(0f,expansion.value,done);}
    private boolean reducedMotion() {
        return !SharedConfig.animationsEnabled() || AndroidUtilities.isAccessibilityScreenReaderEnabled()
                || (Build.VERSION.SDK_INT>=26 && !ValueAnimator.areAnimatorsEnabled());
    }
    private void animateTo(float visible,float expand,Runnable done) {
        completed=done;presence.target(visible);expansion.target(expand);
        if(reducedMotion()) {cancelFrame();presence.snap(visible);expansion.snap(expand);apply();finish();return;}
        if(frame!=null){started=0;return;} // Retarget without losing position/velocity.
        previousFrame=0;started=0;
        frame=time->{
            if(started==0)started=time;
            float dt=previousFrame==0?1f/60f:(time-previousFrame)/1_000_000_000f;previousFrame=time;
            boolean p=presence.step(dt),e=expansion.step(dt);apply();
            if((p||e) && time-started<1_200_000_000L)Choreographer.getInstance().postFrameCallback(frame);
            else {presence.snap(presence.target);expansion.snap(expansion.target);frame=null;apply();finish();}
        };
        Choreographer.getInstance().postFrameCallback(frame);
    }
    private void apply() {
        float p=presence.value;
        setScaleX(terminal+(1-terminal)*(float)Math.pow(p,1.25));
        setScaleY(terminal+(1-terminal)*(float)Math.pow(p,.85));
        setAlpha(cutout?(p==0?0:1):Math.min(1,p*4));
        panel.setAlpha(expansion.value);compact.setAlpha(Math.min(1,p*3));invalidate();
    }
    private void finish() {if(!expanded)panel.setVisibility(GONE);Runnable done=completed;completed=null;if(done!=null)done.run();}
    private void cancelFrame() {if(frame!=null)Choreographer.getInstance().removeFrameCallback(frame);frame=null;}
    void cancelMotion() {cancelFrame();completed=null;}
    void release() {
        cancelMotion();removeCallbacks(reposition);root.removeOnLayoutChangeListener(layoutListener);
        setOnApplyWindowInsetsListener(null);setOnClickListener(null);rowClick=null;expandedChanged=null;
        list.setAdapter(null);root.removeView(this);
    }
    private final class Rows extends BaseAdapter {
        @Override public int getCount(){return rows.size();}
        @Override public Object getItem(int p){return rows.get(p);}
        @Override public long getItemId(int p){return rows.get(p).dialog;}
        @Override public boolean hasStableIds(){return true;}
        @Override public View getView(int p,View convert,ViewGroup parent) {
            RowView row=convert instanceof RowView?(RowView)convert:new RowView(getContext());
            CameraPopInbox.Row item=rows.get(p);Object peer=null;String title=LocaleController.getString(R.string.CameraPopPrivateName);
            if(names && item.dialog!=0) {
                if(DialogObject.isUserDialog(item.dialog)){TLRPC.User user=MessagesController.getInstance(account).getUser(item.dialog);peer=user;if(user!=null)title=UserObject.getUserName(user);}
                else {TLRPC.Chat chat=MessagesController.getInstance(account).getChat(-item.dialog);peer=chat;if(chat!=null)title=chat.title;}
            }
            row.title.setText(title);row.subtitle.setText(LocaleController.formatPluralString("CameraPopUnread",item.unread));
            AvatarDrawable placeholder=new AvatarDrawable();
            if(peer instanceof TLRPC.User){TLRPC.User user=(TLRPC.User)peer;placeholder.setInfo(account,user);row.image.setImage(ImageLocation.getForUser(user,ImageLocation.TYPE_SMALL),"46_46",placeholder,user);}
            else if(peer instanceof TLRPC.Chat){TLRPC.Chat chat=(TLRPC.Chat)peer;placeholder.setInfo(account,chat);row.image.setImage(ImageLocation.getForChat(chat,ImageLocation.TYPE_SMALL),"46_46",placeholder,chat);}
            else {placeholder.setInfo(0,"F","G");row.image.setImageDrawable(placeholder);}
            row.setContentDescription(row.title.getText()+". "+row.subtitle.getText());return row;
        }
    }
    private final class RowView extends LinearLayout {
        final BackupImageView image;final TextView title,subtitle;
        RowView(Context c) {
            super(c);setOrientation(HORIZONTAL);setGravity(Gravity.CENTER_VERTICAL);setPadding(dp(16),dp(8),dp(16),dp(8));
            setMinimumHeight(dp(64));setLayoutParams(new android.widget.AbsListView.LayoutParams(LayoutParams.MATCH_PARENT,LayoutParams.WRAP_CONTENT));
            image=new BackupImageView(c);image.setRoundRadius(dp(22));addView(image,new LinearLayout.LayoutParams(dp(44),dp(44)));
            LinearLayout text=new LinearLayout(c);text.setOrientation(VERTICAL);LinearLayout.LayoutParams tp=new LinearLayout.LayoutParams(0,LayoutParams.WRAP_CONTENT,1);tp.setMarginStart(dp(12));addView(text,tp);
            title=label(c,15);subtitle=label(c,12);subtitle.setTextColor(0xffbdbdc5);text.addView(title);text.addView(subtitle);
        }
    }
}
