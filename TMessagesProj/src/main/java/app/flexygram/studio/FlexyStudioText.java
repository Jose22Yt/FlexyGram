/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.studio;
import org.telegram.messenger.R;
/** Stable identifiers are never translated; only the presentation is localized. */
public final class FlexyStudioText {
    private FlexyStudioText(){}
    public static int section(String id) {
        switch(id){case "appearance":return R.string.FlexyStudioAppearance;case "theme":return R.string.FlexyStudioTheme;
            case "chat":return R.string.FlexyStudioChat;case "home":return R.string.FlexyStudioHome;
            case "navigation":return R.string.FlexyStudioNavigation;case "general":return R.string.FlexyStudioGeneral;
            case "ai":return R.string.FlexyStudioAi;case "plugins":return R.string.FlexyStudioPlugins;
            case "client":return R.string.FlexyStudioClientSettings;case "bubbles":return R.string.FlexyStudioBubbles;case "header":return R.string.FlexyStudioHeader;
            case "composer":return R.string.FlexyStudioComposer;case "icon":return R.string.FlexyStudioIcon;default:throw new IllegalArgumentException("section");}
    }
    public static String setting(String file,String key){
        if(key.equals("style")){
            if(file.equals("flexygram_header"))return org.telegram.messenger.LocaleController.getString(R.string.FlexyHeaderStyle);
            if(file.equals("flexygram_composer"))return org.telegram.messenger.LocaleController.getString(R.string.FlexyComposerStyle);
        }
        int label=0;
        switch(key){
            case "transparency":label=R.string.FlexyBubblesTransparency;break;
            case "signature_cached_blur":case "cachedBlur":label=R.string.FlexyBubbleBackgroundBlur;break;
            case "signature_outline_enabled":case "outlineEnabled":label=R.string.FlexyBubbleOutlineEnabled;break;
            case "signature_outline_style":case "outlineStyle":label=R.string.FlexyBubbleOutlineStyle;break;
            case "signature_border_tenths":case "borderTenths":label=R.string.FlexyBubbleBorderWidth;break;
            case "surface_effect":case "surfaceEffect":label=R.string.FlexyBubbleSurfaceEffect;break;
            case "small_timestamp":case "smallTimestamp":label=R.string.FlexyBubbleSmallTimestamp;break;
            case "compactLevel":case "density":label=R.string.FlexyComposerLevel;break;
            case "verticalPosition":case "position":label=R.string.FlexyComposerPosition;break;
            case "pearlGlass":label=R.string.FlexyComposerGlass;break;
        }
        if(label!=0)return org.telegram.messenger.LocaleController.getString(label);
        String localized=org.telegram.messenger.LocaleController.getString(key,0);
        if(localized!=null&&!localized.startsWith("LOC_ERR"))return localized;
        String name=key.replaceFirst("^(OE|Neko|Flexy)", "").replace('_',' ');
        return name.replaceAll("([a-z])([A-Z])", "$1 $2");
    }
    public static String choice(String file,String key,Object value){
        if(!(value instanceof Number))return null;int n=((Number)value).intValue();int label=0;
        if(key.equals("style")&&file.equals("flexygram_header")&&n>=0&&n<=4)label=new int[]{R.string.FlexyHeaderSignature,R.string.FlexyHeaderClassic,R.string.FlexyHeaderFusion,R.string.FlexyHeaderPortrait,R.string.FlexyHeaderFloating}[n];
        else if(key.equals("style")&&file.equals("flexygram_composer")&&n>=0&&n<=1)label=n==0?R.string.FlexyComposerClassic:R.string.FlexyComposerCompact;
        else if((key.equals("surface_effect")||key.equals("surfaceEffect"))&&n>=0&&n<=1)label=n==0?R.string.FlexyBubbleAdaptiveSurface:R.string.FlexyBubbleLegacySurface;
        else if((key.equals("compactLevel")||key.equals("density"))&&file.equals("flexygram_composer")&&n>=0&&n<=2)label=new int[]{R.string.FlexyComposerDefault,R.string.FlexyComposerSmall,R.string.FlexyComposerExtraSmall}[n];
        return label==0?null:org.telegram.messenger.LocaleController.getString(label);
    }
    public static int icon(String id) {
        switch(id){case "client":return R.drawable.msg_theme;case "bubbles":return R.drawable.msg_discussion;case "header":return R.drawable.msg_contacts;
            case "composer":return R.drawable.msg_edit;case "icon":return R.drawable.msg_theme;default:throw new IllegalArgumentException("section");}
    }
}
