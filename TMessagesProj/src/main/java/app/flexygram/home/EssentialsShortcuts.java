/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import android.content.Context;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.text.TextUtils;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.LayoutHelper;

/** Two real navigation actions; the only favorites editor gesture is long-press. */
public final class EssentialsShortcuts extends LinearLayout {
    private final TextView saved,favorites;
    private final Theme.ResourcesProvider provider;
    private int lastPage,lastCard,lastAccent,lastText,lastUnread=-1;
    private boolean lastSelected;
    public EssentialsShortcuts(Context context,Theme.ResourcesProvider provider,Runnable openSaved,Runnable openFavorites,Runnable editFavorites){
        super(context);this.provider=provider;setGravity(Gravity.CENTER_VERTICAL);setPadding(AndroidUtilities.dp(10),0,AndroidUtilities.dp(10),0);
        saved=button(context);favorites=button(context);
        saved.setOnClickListener(v->openSaved.run());favorites.setOnClickListener(v->openFavorites.run());favorites.setOnLongClickListener(v->{editFavorites.run();return true;});
        addView(saved,LayoutHelper.createLinear(0,48,1f,0,0,4,0));addView(favorites,LayoutHelper.createLinear(0,48,1f,4,0,0,0));refresh(false,0);
    }
    private TextView button(Context c){TextView text=new TextView(c);text.setTextSize(14);text.setTypeface(AndroidUtilities.bold());text.setGravity(Gravity.CENTER);text.setSingleLine(true);text.setEllipsize(TextUtils.TruncateAt.END);return text;}
    private GradientDrawable background(int fill,int edge){GradientDrawable result=new GradientDrawable();result.setColor(fill);result.setCornerRadius(AndroidUtilities.dp(14));if(edge!=0)result.setStroke(AndroidUtilities.dp(1),edge);return result;}
    public void refresh(boolean selected,int unread){
        int page=Theme.getColor(Theme.key_windowBackgroundGray,provider),card=Theme.getColor(Theme.key_windowBackgroundWhite,provider),accent=Theme.getColor(Theme.key_windowBackgroundWhiteBlueText,provider),ink=Theme.getColor(Theme.key_windowBackgroundWhiteBlackText,provider);
        unread=Math.max(0,unread);
        if(page!=lastPage||card!=lastCard||accent!=lastAccent||ink!=lastText||selected!=lastSelected||lastUnread<0){
            setBackgroundColor(page);saved.setBackground(background(card,0));favorites.setBackground(background(selected?androidx.core.graphics.ColorUtils.blendARGB(card,accent,.12f):card,selected?accent:0));
            saved.setTextColor(ink);favorites.setTextColor(selected?accent:ink);
            saved.setCompoundDrawablePadding(AndroidUtilities.dp(4));favorites.setCompoundDrawablePadding(AndroidUtilities.dp(4));
            saved.setText(LocaleController.getString(R.string.FlexyHomeSaved));saved.setContentDescription(LocaleController.getString(R.string.SavedMessages));
            android.graphics.drawable.Drawable bookmark=getContext().getDrawable(R.drawable.chats_saved).mutate(),star=getContext().getDrawable(R.drawable.msg_fave).mutate();
            bookmark.setTint(ink);star.setTint(selected?accent:ink);int size=AndroidUtilities.dp(20);bookmark.setBounds(0,0,size,size);star.setBounds(0,0,size,size);
            saved.setCompoundDrawablesRelative(bookmark,null,null,null);favorites.setCompoundDrawablesRelative(star,null,null,null);
            saved.setPadding(AndroidUtilities.dp(12),0,AndroidUtilities.dp(8),0);favorites.setPadding(AndroidUtilities.dp(12),0,AndroidUtilities.dp(8),0);
            lastPage=page;lastCard=card;lastAccent=accent;lastText=ink;lastSelected=selected;
        }
        if(lastUnread!=unread){favorites.setText(LocaleController.getString(R.string.FlexyHomeFavorites)+(unread>0?" · "+unread:""));lastUnread=unread;}
        favorites.setSelected(selected);
    }
}
