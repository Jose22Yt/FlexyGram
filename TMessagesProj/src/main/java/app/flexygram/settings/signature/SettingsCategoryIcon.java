package app.flexygram.settings.signature;

import android.content.Context;
import android.graphics.*;
import android.graphics.drawable.Drawable;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.R;
import org.telegram.ui.SettingsActivity;

/** Reuses Telegram's own coloured Settings icon background and filled native glyphs. */
public final class SettingsCategoryIcon extends Drawable implements Drawable.Callback {
    private final Drawable glyph;
    private final SettingsActivity.SettingCell.Background background=new SettingsActivity.SettingCell.Background();
    private int alpha=255;
    public static Drawable create(Context context,int resource){return resource<=0?null:new SettingsCategoryIcon(context,resource);}
    public static Drawable create(Context context,int resource,int top,int bottom){if(resource<=0)return null;SettingsCategoryIcon icon=new SettingsCategoryIcon(context,resource);icon.background.setColor(top,bottom);return icon;}
    private SettingsCategoryIcon(Context context,int resource){
        String name=context.getResources().getResourceEntryName(resource);
        int color=0xff168edb, filled=resource;
        if(name.contains("chat")||name.contains("discussion")){color=0xff26a542;filled=R.drawable.settings_chat;}
        else if(name.contains("plugin")){color=0xffa253df;filled=R.drawable.plugins_filled_solar;}
        else if(name.contains("palette")||name.contains("theme")){color=0xffa253df;}
        else if(name.contains("file")||name.contains("folder")){color=0xffd78010;filled=R.drawable.msg_filled_data_files_solar;}
        else if(name.contains("download")){color=0xffd78010;}
        else if((name.endsWith("_settings")||name.contains("settings_solar"))){filled=R.drawable.filled_profile_settings_solar;}
        else if(name.contains("history")||name.contains("recent")){color=0xffdd6150;}
        else if(name.contains("layers")){color=0xff6961da;}
        else if(name.contains("info")){filled=R.drawable.msg_info_filled_solar;}
        glyph=context.getDrawable(filled).mutate();glyph.setColorFilter(Color.WHITE,PorterDuff.Mode.SRC_IN);
        int top=androidx.core.graphics.ColorUtils.blendARGB(color,Color.WHITE,.16f);
        background.setColor(top,color);background.setCircle(false);background.setDrawBorder(true);
        background.setCallback(this);glyph.setCallback(this);
    }
    @Override protected void onBoundsChange(Rect bounds){background.setBounds(bounds);int inset=Math.round(bounds.width()*.125f);glyph.setBounds(bounds.left+inset,bounds.top+inset,bounds.right-inset,bounds.bottom-inset);}
    @Override public void draw(Canvas canvas){int save=alpha<255?canvas.saveLayerAlpha(getBounds().left,getBounds().top,getBounds().right,getBounds().bottom,alpha):-1;background.draw(canvas);glyph.draw(canvas);if(save>=0)canvas.restoreToCount(save);}
    @Override public void setAlpha(int alpha){this.alpha=alpha;invalidateSelf();}
    @Override public void setColorFilter(ColorFilter filter){} // Keep the native white symbol over the colour tile.
    @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
    @Override public int getIntrinsicWidth(){return AndroidUtilities.dp(SettingsCardStyle.ICON);}
    @Override public int getIntrinsicHeight(){return AndroidUtilities.dp(SettingsCardStyle.ICON);}
    @Override public void invalidateDrawable(Drawable who){invalidateSelf();}
    @Override public void scheduleDrawable(Drawable who,Runnable what,long when){scheduleSelf(what,when);}
    @Override public void unscheduleDrawable(Drawable who,Runnable what){unscheduleSelf(what);}
}
