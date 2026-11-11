/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.widget.FrameLayout;
import org.telegram.messenger.SharedConfig;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.blur3.BlurredBackgroundDrawableViewFactory;
import org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawable;
import org.telegram.ui.Components.blur3.drawable.color.impl.BlurredBackgroundProviderImpl;

public final class IosHomeSurface extends FrameLayout {
        private final Theme.ResourcesProvider provider;
        private final BlurredBackgroundDrawableViewFactory factory;
        private final int account;
        private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
        private final RectF rect=new RectF();
        private BlurredBackgroundDrawable glass;
        private int lastColor;
        IosHomeSurface(Context c,int account,Theme.ResourcesProvider provider,BlurredBackgroundDrawableViewFactory factory){super(c);this.account=account;this.provider=provider;this.factory=factory;setWillNotDraw(false);}
        public void updateColors(){if(glass!=null)glass.updateColors();invalidate();}
        @Override protected void onDraw(Canvas canvas){
            int color=Theme.getColor(Theme.key_windowBackgroundWhite,provider);
            if(factory!=null&&canvas.isHardwareAccelerated()&&SharedConfig.chatBlurEnabled()&&BlurredBackgroundProviderImpl.checkBlurEnabled(account,provider)){
                if(glass==null){glass=factory.create(this,BlurredBackgroundProviderImpl.topPanel(provider)).setPadding(0);glass.setRadius(getHeight()/2f);lastColor=color;}
                if(lastColor!=color){lastColor=color;glass.updateColors();}
                glass.setBounds(0,0,getWidth(),getHeight());glass.draw(canvas);
            }else{paint.setColor(Theme.getColor(Theme.key_windowBackgroundGray,provider)|0xff000000);rect.set(0,0,getWidth(),getHeight());canvas.drawRoundRect(rect,getHeight()/2f,getHeight()/2f,paint);}
            super.onDraw(canvas);
        }
        @Override protected void onDetachedFromWindow(){glass=null;super.onDetachedFromWindow();}
    }
