/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import android.content.Context;
import android.view.Gravity;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.TextView;
import app.flexygram.icons.ExactIcons;
import app.flexygram.icons.IosOriginalAssets;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.Theme;
import org.telegram.ui.Components.LayoutHelper;
import org.telegram.ui.Components.blur3.BlurredBackgroundDrawableViewFactory;

/** Passive search entrance: one native search controller, no duplicate editor or query pipeline. */
public final class IosHomeSearch extends FrameLayout {
    private final IosHomeSurface surface;
    private final TextView hint;
    private final ImageView icon;
    private final Theme.ResourcesProvider provider;
    private int lastColor;
    private boolean colored;
    public IosHomeSearch(Context context,int account,Theme.ResourcesProvider provider,
            BlurredBackgroundDrawableViewFactory factory,Runnable activate){
        super(context);this.provider=provider;
        surface=new IosHomeSurface(context,account,provider,factory);
        addView(surface,LayoutHelper.createFrame(-1,44,Gravity.TOP,16,2,16,0));
        boolean rtl=LocaleController.isRTL;
        icon=new ImageView(context);icon.setScaleType(ImageView.ScaleType.CENTER);
        icon.setImageDrawable(ExactIcons.original(IosOriginalAssets.TAB_NAV_SEARCH));
        surface.addView(icon,LayoutHelper.createFrame(40,44,(rtl?Gravity.RIGHT:Gravity.LEFT)|Gravity.TOP,4,0,4,0));
        hint=new TextView(context);hint.setTextSize(17);hint.setGravity(Gravity.CENTER_VERTICAL|(rtl?Gravity.RIGHT:Gravity.LEFT));
        hint.setText(LocaleController.getString(R.string.Search));hint.setSingleLine(true);
        surface.addView(hint,LayoutHelper.createFrame(-1,-1,Gravity.TOP,rtl?16:44,0,rtl?44:16,0));
        // The whole 54dp row activates search, including its visual margins.
        setOnClickListener(v->activate.run());setContentDescription(LocaleController.getString(R.string.Search));
        surface.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO_HIDE_DESCENDANTS);
        updateColors();
    }
    public void updateColors(){
        int ink=Theme.getColor(Theme.key_windowBackgroundWhiteGrayText,provider);
        if(!colored||lastColor!=ink){colored=true;lastColor=ink;hint.setTextColor(ink);icon.setColorFilter(ink);}
        surface.updateColors();
    }
}
