package app.flexygram.settings.signature;

import android.content.Context;
import android.graphics.*;
import android.graphics.drawable.Drawable;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.R;
import org.telegram.ui.SettingsActivity;

/** Reuses Telegram's own coloured Settings icon background and filled native glyphs. */
public final class SettingsCategoryIcon extends Drawable implements Drawable.Callback, app.flexygram.icons.IconPressFeedback.Target {
    private final Drawable glyph;
    private final SettingsActivity.SettingCell.Background background=new SettingsActivity.SettingCell.Background();
    private int alpha=255;
    private final boolean standalone;

    public boolean isStandalone() {
        return standalone;
    }

    @Override public void setIconPressScale(float scale){}
    public static Drawable create(Context context,int resource){return resource<=0?null:new SettingsCategoryIcon(context,resource);}
    public static Drawable create(Context context,int resource,int top,int bottom){if(resource<=0)return null;SettingsCategoryIcon icon=new SettingsCategoryIcon(context,resource);icon.background.setColor(top,bottom);return icon;}
    private SettingsCategoryIcon(Context context,int resource){
        String name="";
        try {
            name=context.getResources().getResourceEntryName(resource);
        } catch (Throwable ignored) {}
        if ("fg_settings_home".equals(name)) {
            int mapped = context.getResources().getIdentifier("fg_settings_apariencia", "drawable", context.getPackageName());
            if (mapped != 0) {
                resource = mapped;
                name = "fg_settings_apariencia";
            }
        } else if ("fg_settings_plugins".equals(name)) {
            int mapped = context.getResources().getIdentifier("fg_settings_plugin", "drawable", context.getPackageName());
            if (mapped != 0) {
                resource = mapped;
                name = "fg_settings_plugin";
            }
        }
        if (isUserPackIcon(name)) {
            standalone=true;
            Drawable d=context.getDrawable(resource);
            glyph=d!=null?d.mutate():null;
            if(glyph!=null){
                glyph.setColorFilter(null);
                glyph.setCallback(this);
            }
            return;
        }
        standalone=false;
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
        glyph=context.getDrawable(app.exteraless.icons.BaseIconPacks.getSelected()==app.exteraless.icons.BaseIconPacks.BASE_DEFAULT?resource:filled).mutate();glyph.setColorFilter(Color.WHITE,PorterDuff.Mode.SRC_IN);
        int top=androidx.core.graphics.ColorUtils.blendARGB(color,Color.WHITE,.16f);
        background.setColor(top,color);background.setCircle(false);background.setDrawBorder(true);
        background.setCallback(this);glyph.setCallback(this);
    }
    @Override protected void onBoundsChange(Rect bounds){
        if(standalone){
            if(glyph!=null)glyph.setBounds(bounds);
            return;
        }
        background.setBounds(bounds);int inset=Math.round(bounds.width()*.125f);
        if(glyph!=null)glyph.setBounds(bounds.left+inset,bounds.top+inset,bounds.right-inset,bounds.bottom-inset);
    }
    @Override public void draw(Canvas canvas){
        if(standalone){
            if(glyph!=null)glyph.draw(canvas);
            return;
        }
        int save=alpha<255?canvas.saveLayerAlpha(getBounds().left,getBounds().top,getBounds().right,getBounds().bottom,alpha):-1;
        background.draw(canvas);
        if(glyph!=null)glyph.draw(canvas);
        if(save>=0)canvas.restoreToCount(save);
    }
    @Override public void setAlpha(int alpha){this.alpha=alpha;if(glyph!=null)glyph.setAlpha(alpha);invalidateSelf();}
    @Override public void setColorFilter(ColorFilter filter){if(!standalone&&glyph!=null)glyph.setColorFilter(filter);} // Keep the native white symbol over the colour tile.
    @Override public int getOpacity(){return PixelFormat.TRANSLUCENT;}
    @Override public int getIntrinsicWidth(){return AndroidUtilities.dp(SettingsCardStyle.ICON);}
    @Override public int getIntrinsicHeight(){return AndroidUtilities.dp(SettingsCardStyle.ICON);}
    @Override public void invalidateDrawable(Drawable who){invalidateSelf();}
    @Override public void scheduleDrawable(Drawable who,Runnable what,long when){scheduleSelf(what,when);}
    @Override public void unscheduleDrawable(Drawable who,Runnable what){unscheduleSelf(what);}
    private static boolean isUserPackIcon(String name) {
        return "fg_settings_apariencia".equals(name)
            || "fg_settings_canales".equals(name)
            || "fg_settings_chats".equals(name)
            || "fg_settings_comunidad".equals(name)
            || "fg_settings_estilo_de_interfaz".equals(name)
            || "fg_settings_general".equals(name)
            || "fg_settings_iconos".equals(name)
            || "fg_settings_otros".equals(name)
            || "fg_settings_plugin".equals(name)
            || "fg_settings_plugins".equals(name);
    }
}
