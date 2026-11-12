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
        new Page("motion",R.string.CompactMotion,R.drawable.fg_ios_original_chat_context_menu_reorderitems),
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
    static boolean hasOverview(String category){return category.equals("home")||category.equals("chat");}
    static Page[] pages(String category){if(!hasOverview(category))throw new IllegalArgumentException("Unknown compact category");return (category.equals("home")?HOME:CHAT).clone();}
    static Page page(String category,String id){for(Page page:pages(category))if(page.id.equals(id))return page;throw new IllegalArgumentException("Unknown compact settings section");}
    static String segment(String category,String route){
        for(Page page:pages(category))if(page.id.equals(route))return route;
        if(category.equals("home")){
            if(route.equals("scroll_effects"))return "motion";
            if(route.equals("smart_previews"))return "pills";
            if(route.equals("avatars")||route.equals("folders")||route.equals("visible"))return route;
            if(route.startsWith("appearance_extra"))return "extras";
            return "list";
        }
        if(route.startsWith("media"))return "media";
        if(route.startsWith("stickers"))return "stickers";
        if(route.equals("menus"))return "menus";
        return "messages";
    }
    private CompactSettingsPlan(){}
}
