/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.settings.signature;
import org.telegram.messenger.R;
/** Small immutable navigation plan. Editors are created only after a section is opened. */
final class CompactSettingsPlan {
    static final class Page {
        final String id; final int title, icon;
        Page(String id,int title,int icon){this.id=id;this.title=title;this.icon=icon;}
    }
    private static final Page[] HOME={
        new Page("list",R.string.CompactList,R.drawable.fg_ios_original_chat_context_menu_list),
        new Page("pills",R.string.CompactPills,R.drawable.fg_ios_original_chat_context_menu_tagfilter),
        new Page("avatars",R.string.CompactAvatars,R.drawable.fg_ios_original_chat_context_menu_user),
        new Page("folders",R.string.CompactFolders,R.drawable.fg_ios_original_chat_context_menu_folder),
        new Page("visible",R.string.CompactVisible,R.drawable.fg_ios_original_chat_context_menu_eyelocked),
        new Page("extras",R.string.CompactExtras,R.drawable.fg_ios_original_chat_context_menu_palette)
    };
    private static final Page[] CHAT={
        new Page("messages",R.string.CompactMessages,R.drawable.fg_ios_original_chat_context_menu_message),
        new Page("menus",R.string.CompactMenus,R.drawable.fg_ios_original_chat_context_menu_list),
        new Page("media",R.string.CompactMedia,R.drawable.fg_ios_original_chat_context_menu_videocall),
        new Page("stickers",R.string.CompactStickers,R.drawable.fg_ios_original_chat_context_menu_sticker),
        new Page("glare",R.string.CompactGlare,R.drawable.fg_ios_original_media_editor_blur),
        new Page("members",R.string.CompactMembers,R.drawable.fg_ios_original_chat_context_menu_groups),
        new Page("conversion",R.string.CompactConversion,R.drawable.fg_ios_original_chat_context_menu_replace),
        new Page("animations",R.string.CompactAnimations,R.drawable.fg_ios_original_chat_context_menu_timer)
    };
    private static final Page[] UNIVERSAL={
        new Page("general",R.string.CompactBehavior,R.drawable.fg_ios_original_chat_context_menu_settings),
        new Page("network",R.string.CompactNetwork,R.drawable.fg_ios_original_chat_context_menu_browser),
        new Page("notifications",R.string.CompactNotifications,R.drawable.fg_ios_original_chat_context_menu_unmute),
        new Page("maps",R.string.CompactMaps,R.drawable.fg_ios_original_location_sendlocationicon),
        new Page("profile",R.string.CompactProfile,R.drawable.fg_ios_original_chat_context_menu_user),
        new Page("archive",R.string.CompactArchive,R.drawable.fg_ios_original_chat_context_menu_archive),
        new Page("fonts",R.string.CompactFonts,R.drawable.fg_ios_original_media_editor_addtext),
        new Page("effects",R.string.CompactEffects,R.drawable.fg_ios_original_media_editor_blur),
        new Page("launcher",R.string.CompactLauncher,R.drawable.fg_ios_original_location_homeicon),
        new Page("advanced",R.string.CompactAdvanced,R.drawable.fg_ios_original_chat_context_menu_eyelocked),
        new Page("extras",R.string.CompactSystemExtras,R.drawable.fg_ios_original_chat_context_menu_more)
    };
    private static final Page[] NAVIGATION={
        new Page("tabs",R.string.CompactTabs,R.drawable.fg_ios_original_chat_context_menu_reorderitems),
        new Page("controls",R.string.CompactNavigationControls,R.drawable.fg_ios_original_chat_context_menu_settings),
        new Page("gestures",R.string.CompactGestures,R.drawable.fg_ios_original_chat_context_menu_reply),
        new Page("extras",R.string.CompactNavigationExtras,R.drawable.fg_ios_original_chat_context_menu_more)
    };
    private static final Page[] AYU={
        new Page("ghost",R.string.CompactGhost,R.drawable.fg_ios_original_chat_context_menu_eyelocked),
        new Page("privacy",R.string.CompactStoryPrivacy,R.drawable.fg_ios_original_chat_context_menu_touchid),
        new Page("saving",R.string.CompactHistory,R.drawable.fg_ios_original_chat_context_menu_archive),
        new Page("tools",R.string.CompactHistoryTools,R.drawable.fg_ios_original_chat_context_menu_settings),
        new Page("maintenance",R.string.CompactMaintenance,R.drawable.fg_ios_original_chat_context_menu_delete)
    };
    private static final Page[] PLUGINS={
        new Page("translation",R.string.CompactTranslation,R.drawable.fg_ios_original_chat_context_menu_caption)
    };
    static boolean hasOverview(String category){return category.equals("home")||category.equals("chat")||category.equals("universal")||category.equals("navigation")||category.equals("ayu")||category.equals("plugins");}
    static Page[] pages(String category){
        switch(category){
            case "home":return HOME.clone();case "chat":return CHAT.clone();
            case "universal":return UNIVERSAL.clone();case "navigation":return NAVIGATION.clone();
            case "ayu":return AYU.clone();case "plugins":return PLUGINS.clone();
            default:throw new IllegalArgumentException("Unknown compact category");
        }
    }
    static Page page(String category,String id){for(Page page:pages(category))if(page.id.equals(id))return page;throw new IllegalArgumentException("Unknown compact settings section");}
    static String segment(String category,String route){
        for(Page page:pages(category))if(page.id.equals(route))return route;
        if(category.equals("home")){
            if(route.equals("smart_previews"))return "pills";
            if(route.equals("avatars")||route.equals("folders")||route.equals("visible"))return route;
            if(route.startsWith("appearance_extra"))return "extras";
            return "list";
        }
        if(category.equals("universal")){
            if(route.equals("general_network"))return "network";
            if(route.equals("general_notifications"))return "notifications";
            if(route.equals("general_maps"))return "maps";
            if(route.equals("general_behavior")||route.equals("general_controls"))return "general";
            if(route.equals("surfaces"))return "effects";
            if(route.startsWith("advanced"))return "advanced";
            if(route.startsWith("general_extra")||route.startsWith("appearance_extra"))return "extras";
            return "general";
        }
        if(category.equals("navigation")){
            if(route.equals("bottom_tabs"))return "tabs";
            if(route.startsWith("navigation_extra"))return "extras";
            return "controls";
        }
        if(category.equals("ayu")){
            if(route.equals("ayu_privacy"))return "privacy";
            if(route.equals("ayu_tools"))return "tools";
            if(route.equals("ayu_maintenance")||route.equals("ClearMessageDatabase"))return "maintenance";
            return "saving";
        }
        if(category.equals("plugins"))return "translation";
        if(route.startsWith("media"))return "media";
        if(route.startsWith("stickers"))return "stickers";
        if(route.equals("menus"))return "menus";
        return "messages";
    }
    private CompactSettingsPlan(){}
}
