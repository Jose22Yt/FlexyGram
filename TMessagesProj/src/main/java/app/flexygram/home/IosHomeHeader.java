/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.TextView;
import app.flexygram.icons.ExactIcons;
import app.flexygram.icons.IosOriginalAssets;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.messenger.SharedConfig;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.LayoutHelper;
import org.telegram.ui.Components.blur3.BlurredBackgroundDrawableViewFactory;
import org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawable;
import org.telegram.ui.Components.blur3.drawable.color.impl.BlurredBackgroundProviderImpl;

/** Android port of the pinned official ChatListNavigationBar's 3 + 44 + 9 pt row.
 * UIKit's material is rendered by FlexyGram's existing shared glass source. */
public final class IosHomeHeader extends FrameLayout {
    private final IosHomeSurface editSurface,composeSurface;
    private final TextView edit,title;
    private final ImageView compose;
    private final Theme.ResourcesProvider provider;
    private final BlurredBackgroundDrawableViewFactory factory;
    private final int account;
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    private BlurredBackgroundDrawable glass;
    private float scrollProgress;
    private int lastInk,lastAccent,lastSurface;
    private boolean colored;

    public IosHomeHeader(Context context,int account,Theme.ResourcesProvider provider,
            BlurredBackgroundDrawableViewFactory factory,Runnable beginEditing,Runnable newMessage,
            Runnable openMenu,Runnable switchAccount){
        super(context);this.account=account;this.provider=provider;this.factory=factory;setWillNotDraw(false);
        boolean rtl=LocaleController.isRTL;
        editSurface=new IosHomeSurface(context,account,provider,factory);
        composeSurface=new IosHomeSurface(context,account,provider,factory);
        // 44pt visual controls; the surrounding row expands the touch targets to 48dp.
        addView(editSurface,LayoutHelper.createFrame(76,44,(rtl?Gravity.RIGHT:Gravity.LEFT)|Gravity.TOP,16,3,16,0));
        addView(composeSurface,LayoutHelper.createFrame(44,44,(rtl?Gravity.LEFT:Gravity.RIGHT)|Gravity.TOP,16,3,16,0));
        edit=new TextView(context);edit.setTextSize(17);edit.setGravity(Gravity.CENTER);
        edit.setText(LocaleController.getString(R.string.Edit));edit.setSingleLine(true);edit.setEllipsize(TextUtils.TruncateAt.END);
        editSurface.addView(edit,LayoutHelper.createFrame(-1,-1));editSurface.setOnClickListener(v->beginEditing.run());
        editSurface.setOnLongClickListener(v->{openMenu.run();return true;});
        editSurface.setContentDescription(LocaleController.getString(R.string.Edit));
        compose=new ImageView(context);compose.setScaleType(ImageView.ScaleType.CENTER);
        compose.setImageDrawable(ExactIcons.original(IosOriginalAssets.HOME_COMPOSE));
        composeSurface.addView(compose,LayoutHelper.createFrame(-1,-1));
        composeSurface.setOnClickListener(v->newMessage.run());
        composeSurface.setOnLongClickListener(v->{openMenu.run();return true;});
        composeSurface.setContentDescription(LocaleController.getString(R.string.NewMessageTitle));
        title=new TextView(context);title.setTextSize(17);title.setTypeface(AndroidUtilities.bold());
        title.setGravity(Gravity.CENTER);title.setSingleLine(true);title.setEllipsize(TextUtils.TruncateAt.END);
        title.setText(LocaleController.getString(R.string.Chats));
        addView(title,LayoutHelper.createFrame(-1,44,Gravity.TOP,100,3,100,0));
        title.setOnClickListener(v->switchAccount.run());
        title.setOnLongClickListener(v->{openMenu.run();return true;});
        title.setContentDescription(LocaleController.getString(R.string.Chats)+", "+LocaleController.getString(R.string.AccDescrMoreOptions));
        updateColors();
    }
    @Override protected void onLayout(boolean changed,int l,int t,int r,int b){
        super.onLayout(changed,l,t,r,b);
        if(changed){
            android.graphics.Rect editBounds=new android.graphics.Rect(),composeBounds=new android.graphics.Rect();
            editSurface.getHitRect(editBounds);composeSurface.getHitRect(composeBounds);
            editBounds.inset(0,-AndroidUtilities.dp(2));composeBounds.inset(-AndroidUtilities.dp(2),-AndroidUtilities.dp(2));
            android.view.TouchDelegate editTouch=new android.view.TouchDelegate(editBounds,editSurface);
            android.view.TouchDelegate composeTouch=new android.view.TouchDelegate(composeBounds,composeSurface);
            setTouchDelegate(new android.view.TouchDelegate(editBounds,this){
                private android.view.TouchDelegate active;
                @Override public boolean onTouchEvent(android.view.MotionEvent event){
                    int action=event.getActionMasked();
                    if(action==android.view.MotionEvent.ACTION_DOWN){
                        int x=(int)event.getX(),y=(int)event.getY();
                        active=editBounds.contains(x,y)?editTouch:composeBounds.contains(x,y)?composeTouch:null;
                    }
                    boolean handled=active!=null&&active.onTouchEvent(event);
                    if(action==android.view.MotionEvent.ACTION_UP||action==android.view.MotionEvent.ACTION_CANCEL)active=null;
                    return handled;
                }
            });
        }
    }
    public View getMenuAnchor(){return composeSurface;}
    public View getAccountAnchor(){return title;}
    public void setScrollProgress(float progress){
        float value=Math.max(0f,Math.min(1f,progress));
        if(value!=scrollProgress){scrollProgress=value;invalidate();}
    }
    public void updateColors(){
        int ink=Theme.getColor(Theme.key_windowBackgroundWhiteBlackText,provider);
        int accent=Theme.getColor(Theme.key_windowBackgroundWhiteBlueText,provider);
        int surface=Theme.getColor(Theme.key_windowBackgroundWhite,provider);
        if(colored&&ink==lastInk&&accent==lastAccent&&surface==lastSurface)return;
        colored=true;lastInk=ink;lastAccent=accent;lastSurface=surface;
        title.setTextColor(ink);edit.setTextColor(accent);compose.setColorFilter(accent);
        if(glass!=null)glass.updateColors();editSurface.updateColors();composeSurface.updateColors();invalidate();
    }
    @Override protected void onDraw(Canvas canvas){
        if(scrollProgress>0){
            if(factory!=null&&canvas.isHardwareAccelerated()&&SharedConfig.chatBlurEnabled()
                    &&BlurredBackgroundProviderImpl.checkBlurEnabled(account,provider)){
                if(glass==null)glass=factory.create(this,BlurredBackgroundProviderImpl.topPanel(provider)).setPadding(0);
                glass.setAlpha(Math.round(255*scrollProgress));glass.setBounds(0,0,getWidth(),getHeight());glass.draw(canvas);
            }else{
                paint.setColor(Theme.getColor(Theme.key_windowBackgroundWhite,provider)|0xff000000);
                paint.setAlpha(Math.round(255*scrollProgress));canvas.drawRect(0,0,getWidth(),getHeight(),paint);
            }
        }
        super.onDraw(canvas);
    }
    @Override protected void onDetachedFromWindow(){glass=null;super.onDetachedFromWindow();}
}
