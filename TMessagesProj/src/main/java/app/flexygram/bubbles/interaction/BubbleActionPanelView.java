/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.content.Context;
import android.content.res.ColorStateList;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.RippleDrawable;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.View;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.EnumSet;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;

/** Shared live menu/miniature renderer. Native ChatActivity retains permissions and dispatch. */
public final class BubbleActionPanelView extends LinearLayout {
    public enum Action { REPLY, COPY, STICKER, FORWARD, EDIT, PIN, DELETE, SELECT, SAVE, SHARE, LINK, MORE }
    public interface Listener { void onAction(Action action); }
    public interface SurfaceFactory { android.graphics.drawable.Drawable create(View view, float radius); }
    private SurfaceFactory surfaceFactory;
    /** Set before actions are built. All cards share the chat popup capture. */
    public void setSurfaceFactory(SurfaceFactory factory) { surfaceFactory = factory; }
    private Listener listener;
    private EnumSet<Action> allowed = EnumSet.noneOf(Action.class);
    private final EnumSet<Action> chosen;
    private final int style, textColor, surface, deleteColor;
    static int dp(Context c, float v) { return (int)(c.getResources().getDisplayMetrics().density*v+.5f); }

    public BubbleActionPanelView(Context context, Theme.ResourcesProvider provider) {
        this(context,provider,BubbleMenuConfig.layout(context),BubbleMenuConfig.actions(context));
    }
    public BubbleActionPanelView(Context context, Theme.ResourcesProvider provider, int style, EnumSet<Action> chosen) {
        super(context);setOrientation(VERTICAL);
        this.style=Math.max(BubbleMenuConfig.LIST,Math.min(BubbleMenuConfig.TOOLBAR,style));this.chosen=chosen.clone();
        textColor=Theme.getColor(Theme.key_actionBarDefaultSubmenuItem,provider);
        surface=Theme.getColor(Theme.key_actionBarDefaultSubmenuBackground,provider);
        deleteColor=Theme.getColor(Theme.key_text_RedRegular,provider);
        setMinimumWidth(dp(context,244));
    }
    public void setListener(Listener value){listener=value;}
    public int presentation(){return style;}
    public static String label(Action action) {
        int id;
        switch(action){
            case REPLY:id=R.string.Reply;break;case COPY:id=R.string.Copy;break;
            case STICKER:id=R.string.FlexyMenuSticker;break;case FORWARD:id=R.string.Forward;break;
            case EDIT:id=R.string.Edit;break;case PIN:id=R.string.FlexyMenuPin;break;
            case DELETE:id=R.string.Delete;break;case SELECT:id=R.string.FlexyContextSelect;break;
            case SAVE:id=R.string.Save;break;case SHARE:id=R.string.ShareFile;break;
            case LINK:id=R.string.CopyLink;break;default:id=R.string.FlexyContextMore;
        }
        return LocaleController.getString(id);
    }
    public void setAllowedActions(EnumSet<Action> actions) {
        allowed=BubbleMenuConfig.visible(actions==null?EnumSet.noneOf(Action.class):actions,chosen);
        allowed.add(Action.MORE);removeAllViews();
        if (style == BubbleMenuConfig.LIST) setBackground(surface(this, false));
        if(style==BubbleMenuConfig.GRID){
            LinearLayout grid=card(false);ArrayList<Action> items=new ArrayList<>(allowed);items.remove(Action.MORE);
            for(int i=0;i<items.size();i+=3){
                LinearLayout strip=new LinearLayout(getContext());strip.setOrientation(HORIZONTAL);
                for(int column=0;column<3;column++){
                    if(column>0){View separator=new View(getContext());separator.setBackgroundColor((textColor&0xffffff)|0x14000000);LayoutParams line=new LayoutParams(Math.max(1,dp(getContext(),.5f)),-1);line.topMargin=line.bottomMargin=dp(getContext(),8);strip.addView(separator,line);}
                    int index=i+column;View cell=index<items.size()?button(items.get(index),true,false):new View(getContext());
                    strip.addView(cell,new LayoutParams(0,-2,1f));
                }
                if(grid.getChildCount()>0)divider(grid,0);grid.addView(strip,new LayoutParams(-1,-2));
            }
            if(!items.isEmpty())addView(grid,new LayoutParams(-1,-2));
            LinearLayout footer=card(false);footer.addView(button(Action.MORE,false,true));addCard(footer,!items.isEmpty());
        }else if(style==BubbleMenuConfig.GROUPS){
            group(EnumSet.of(Action.REPLY,Action.COPY));
            group(EnumSet.of(Action.STICKER,Action.FORWARD,Action.EDIT,Action.PIN,Action.SELECT,Action.SAVE,Action.SHARE,Action.LINK));
            group(EnumSet.of(Action.DELETE,Action.MORE));
        }else if(style==BubbleMenuConfig.TOOLBAR){
            LinearLayout bar=card(false);bar.setOrientation(HORIZONTAL);int count=0;
            for(Action action:new Action[]{Action.REPLY,Action.COPY,Action.FORWARD})if(allowed.contains(action)){
                bar.addView(button(action,true,false),new LayoutParams(0,-2,1));count++;
            }
            if(count>0)addView(bar,new LayoutParams(-1,-2));
            LinearLayout rest=card(true);
            for(Action action:allowed)if(action!=Action.REPLY&&action!=Action.COPY&&action!=Action.FORWARD)append(rest,action,true);
            addCard(rest,count>0);
        }else{
            for(Action action:allowed)append(this,action,false);
        }
    }
    private LinearLayout card(boolean translucent){
        LinearLayout card=new LinearLayout(getContext());card.setOrientation(VERTICAL);
        card.setBackground(surface(card, translucent));card.setClipToOutline(true);return card;
    }
    private android.graphics.drawable.Drawable surface(View view, boolean translucent) {
        if (surfaceFactory != null) return surfaceFactory.create(view, dp(getContext(), 20));
        GradientDrawable fill=new GradientDrawable();fill.setColor(translucent?(surface&0xffffff)|0xe6000000:surface);fill.setCornerRadius(dp(getContext(),20));
        if(translucent)fill.setStroke(dp(getContext(),1),(textColor&0xffffff)|0x18000000);
        return fill;
    }
    private void addCard(LinearLayout card,boolean gap){LayoutParams lp=new LayoutParams(-1,-2);if(gap)lp.topMargin=dp(getContext(),8);addView(card,lp);}
    private void group(EnumSet<Action> members){
        members.retainAll(allowed);if(members.isEmpty())return;
        LinearLayout group=card(false);for(Action action:members)append(group,action,false);addCard(group,getChildCount()>0);
    }
    private void append(LinearLayout parent,Action action,boolean trailingIcon){
        if(parent.getChildCount()>0)divider(parent,trailingIcon?12:44);
        parent.addView(button(action,false,trailingIcon),new LayoutParams(-1,-2));
    }
    private void divider(LinearLayout parent,int start){
        View line=new View(getContext());line.setBackgroundColor((textColor&0xffffff)|0x14000000);
        LayoutParams lp=new LayoutParams(-1,Math.max(1,dp(getContext(),.5f)));lp.setMarginStart(dp(getContext(),start));lp.setMarginEnd(dp(getContext(),12));parent.addView(line,lp);
    }
    private View button(Action action,boolean tile,boolean trailingIcon){
        Context context=getContext();int color=action==Action.DELETE?deleteColor:textColor;
        LinearLayout row=new LinearLayout(context);row.setOrientation(tile?VERTICAL:HORIZONTAL);
        boolean centeredFooter=style==BubbleMenuConfig.GRID&&action==Action.MORE;
        row.setGravity(tile||centeredFooter?Gravity.CENTER:Gravity.CENTER_VERTICAL);row.setMinimumHeight(dp(context,tile?80:44));
        row.setPadding(dp(context,tile?4:14),dp(context,8),dp(context,tile?4:14),dp(context,8));
        ImageView icon=new ImageView(context);icon.setScaleType(ImageView.ScaleType.FIT_CENTER);android.graphics.drawable.Drawable symbol=app.flexygram.icons.CupertinoIcons.create(context.getResources(),iconResource(action));
        if(symbol==null)symbol=new BubbleMenuIcon(action,color);
        else symbol.setColorFilter(new android.graphics.PorterDuffColorFilter(color,android.graphics.PorterDuff.Mode.SRC_IN));
        icon.setImageDrawable(symbol);
        TextView title=new TextView(context);title.setText(label(action));title.setTextSize(tile?12:14.5f);title.setTextColor(color);
        title.setTypeface(org.telegram.messenger.AndroidUtilities.bold());
        title.setGravity(tile?Gravity.CENTER:Gravity.START|Gravity.CENTER_VERTICAL);title.setMaxLines(2);title.setEllipsize(TextUtils.TruncateAt.END);
        if(tile){
            row.addView(icon,new LayoutParams(dp(context,24),dp(context,24)));LayoutParams text=new LayoutParams(-1,-2);text.topMargin=dp(context,6);row.addView(title,text);
        }else if(centeredFooter){
            row.addView(icon,new LayoutParams(dp(context,22),dp(context,22)));LayoutParams text=new LayoutParams(-2,-2);text.setMarginStart(dp(context,10));row.addView(title,text);
        }else if(trailingIcon){
            row.addView(title,new LayoutParams(0,-2,1));LayoutParams image=new LayoutParams(dp(context,22),dp(context,22));image.setMarginStart(dp(context,10));row.addView(icon,image);
        }else{
            row.addView(icon,new LayoutParams(dp(context,22),dp(context,22)));LayoutParams text=new LayoutParams(0,-2,1);text.setMarginStart(dp(context,12));row.addView(title,text);
        }
        row.setBackground(new RippleDrawable(ColorStateList.valueOf((textColor&0xffffff)|0x18000000),null,null));
        row.setContentDescription(label(action));row.setTag(action);row.setFocusable(true);
        row.setOnClickListener(view->{if(listener!=null&&allowed.contains(action))listener.onAction(action);});return row;
    }
    private static int iconResource(Action action){
        switch(action){
            case REPLY:return R.drawable.menu_reply;
            case COPY:return R.drawable.msg_copy;
            case STICKER:return R.drawable.msg_sticker;
            case FORWARD:return R.drawable.msg_forward;
            case EDIT:return R.drawable.msg_edit;
            case PIN:return R.drawable.msg_pin;
            case DELETE:return R.drawable.msg_delete;
            case SELECT:return R.drawable.msg_select;
            case SAVE:return R.drawable.msg_download;
            case SHARE:return R.drawable.msg_share;
            case LINK:return R.drawable.msg_link;
            default:return R.drawable.ic_ab_other;
        }
    }
    @Override protected void onDetachedFromWindow(){listener=null;super.onDetachedFromWindow();}
}
