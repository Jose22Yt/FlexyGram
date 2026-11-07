/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.text.TextUtils;
import android.view.Gravity;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.TextView;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.ImageLocation;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.messenger.SharedConfig;
import org.telegram.tgnet.TLRPC;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.AvatarDrawable;
import org.telegram.ui.Components.BackupImageView;
import org.telegram.ui.Components.LayoutHelper;
import org.telegram.ui.Components.blur3.BlurredBackgroundDrawableViewFactory;
import org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawable;
import org.telegram.ui.Components.blur3.drawable.color.impl.BlurredBackgroundProviderImpl;

/** Fixed brand and a shared two-action pill. The native search editor owns search and its transition. */
public final class EssentialsSearchHeader extends FrameLayout {
    private final Surface profile,actions;
    private final ImageView search;
    private final android.view.View more;
    private final TextView hint;
    private final BackupImageView avatar;
    private final ImageView menu;
    private final Theme.ResourcesProvider provider;
    private int lastInk,lastSurface;private boolean colored;
    public EssentialsSearchHeader(Context context,int account,Theme.ResourcesProvider provider,BlurredBackgroundDrawableViewFactory factory,TLRPC.User user,Runnable openProfile,Runnable openSearch,Runnable openMenu,Runnable switchAccount){
        super(context);this.provider=provider;
        profile=new Surface(context,account,provider,factory);
        actions=new Surface(context,account,provider,factory);
        boolean rtl=LocaleController.isRTL;
        addView(profile,LayoutHelper.createFrame(48,48,(rtl?Gravity.RIGHT:Gravity.LEFT)|Gravity.CENTER_VERTICAL,8,0,8,0));
        addView(actions,LayoutHelper.createFrame(96,48,(rtl?Gravity.LEFT:Gravity.RIGHT)|Gravity.CENTER_VERTICAL,8,0,8,0));
        avatar=new BackupImageView(context);avatar.getImageReceiver().setCurrentAccount(account);avatar.setRoundRadius(AndroidUtilities.dp(20));
        setUser(user);
        profile.addView(avatar,LayoutHelper.createFrame(40,40,Gravity.CENTER));
        profile.setOnClickListener(v->openProfile.run());
        profile.setOnLongClickListener(v->{switchAccount.run();return true;});
        profile.setContentDescription(LocaleController.getString(R.string.MyProfile));
        hint=new TextView(context);hint.setTextSize(21);hint.setTypeface(AndroidUtilities.bold());
        hint.setGravity(Gravity.CENTER_VERTICAL|(rtl?Gravity.RIGHT:Gravity.LEFT));
        hint.setSingleLine(true);hint.setEllipsize(TextUtils.TruncateAt.END);hint.setText("FlexyGram");
        addView(hint,LayoutHelper.createFrame(-1,48,Gravity.CENTER_VERTICAL,rtl?112:68,0,rtl?68:112,0));
        search=new ImageView(context);search.setImageResource(R.drawable.flexy_ios_search);search.setScaleType(ImageView.ScaleType.CENTER);
        actions.addView(search,LayoutHelper.createFrame(48,48,(rtl?Gravity.RIGHT:Gravity.LEFT)|Gravity.CENTER_VERTICAL));
        search.setOnClickListener(v->openSearch.run());search.setContentDescription(LocaleController.getString(R.string.Search));
        menu=new ImageView(context);menu.setImageResource(R.drawable.flexy_ios_more);menu.setScaleType(ImageView.ScaleType.CENTER);
        more=menu;actions.addView(menu,LayoutHelper.createFrame(48,48,(rtl?Gravity.LEFT:Gravity.RIGHT)|Gravity.CENTER_VERTICAL));
        menu.setOnClickListener(v->openMenu.run());menu.setContentDescription(LocaleController.getString(R.string.AccDescrMoreOptions));
        updateColors();
    }
    public void setUser(TLRPC.User user){if(user!=null)avatar.setImage(ImageLocation.getForUser(user,ImageLocation.TYPE_SMALL),"50_50",new AvatarDrawable(user),user);}
    public android.view.View getProfileAnchor(){return profile;}
    public android.view.View getMenuAnchor(){return more;}
    public void updateColors(){
        int ink=Theme.getColor(Theme.key_windowBackgroundWhiteBlackText,provider),surface=Theme.getColor(Theme.key_windowBackgroundWhite,provider);
        if(colored&&lastInk==ink&&lastSurface==surface)return;colored=true;lastInk=ink;lastSurface=surface;
        hint.setTextColor(ink);menu.setColorFilter(ink);search.setColorFilter(ink);
        profile.invalidate();actions.invalidate();
    }
    private static final class Surface extends FrameLayout {
        private final Theme.ResourcesProvider provider;
        private final BlurredBackgroundDrawableViewFactory factory;
        private final int account;
        private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
        private final RectF rect=new RectF();
        private BlurredBackgroundDrawable glass;
        private int lastColor;
        Surface(Context c,int account,Theme.ResourcesProvider provider,BlurredBackgroundDrawableViewFactory factory){super(c);this.account=account;this.provider=provider;this.factory=factory;setWillNotDraw(false);}
        @Override protected void onDraw(Canvas canvas){
            int color=Theme.getColor(Theme.key_windowBackgroundWhite,provider);
            if(factory!=null&&canvas.isHardwareAccelerated()&&SharedConfig.chatBlurEnabled()&&BlurredBackgroundProviderImpl.checkBlurEnabled(account,provider)){
                if(glass==null){glass=factory.create(this,BlurredBackgroundProviderImpl.topPanel(provider)).setPadding(0);glass.setRadius(AndroidUtilities.dp(24));lastColor=color;}
                if(lastColor!=color){lastColor=color;glass.updateColors();}
                glass.setBounds(0,0,getWidth(),getHeight());glass.draw(canvas);
            }else{paint.setColor(color|0xff000000);rect.set(0,0,getWidth(),getHeight());canvas.drawRoundRect(rect,AndroidUtilities.dp(24),AndroidUtilities.dp(24),paint);}
            super.onDraw(canvas);
        }
        @Override protected void onDetachedFromWindow(){glass=null;super.onDetachedFromWindow();}
    }
}
