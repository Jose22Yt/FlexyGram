/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.settings.signature;
import java.util.*;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.BaseFragment;
import tw.nekomimi.nekogram.settings.BaseNekoSettingsActivity;
import app.exteraless.settings.*;
/** Navigation and presentation only. A factory never toggles, copies or resets preferences. */
public final class SignatureSettingsRegistry {
    public static final class Entry {
        public final String id,parent; public final int group,title,description,icon,color;
        Entry(String i,String p,int g,int t,int d,int icon,int c){id=i;parent=p;group=g;title=t;description=d;this.icon=icon;color=c;}
    }
    private static final Map<String,Entry> ENTRIES=new LinkedHashMap<>();
    static {
        add(new Entry("appearance","root",R.string.Settings2Group_personal,R.string.Settings2_appearance,R.string.Settings2Desc_appearance,R.drawable.msg_palette,0xFF8B50DE));
        add(new Entry("navigation","root",R.string.Settings2Group_personal,R.string.Settings2_navigation,R.string.Settings2Desc_navigation,R.drawable.settings2_gesture,0xFF168BEA));
        add(new Entry("conversations","root",R.string.Settings2Group_personal,R.string.Settings2_conversations,R.string.Settings2Desc_conversations,R.drawable.settings2_messages,0xFF21BC65));
        add(new Entry("studio","root",R.string.Settings2Group_tools,R.string.Settings2_studio,R.string.Settings2Desc_studio,R.drawable.settings2_studio,0xFF7372DF));
        add(new Entry("files","root",R.string.Settings2Group_tools,R.string.Settings2_files,R.string.Settings2Desc_files,R.drawable.settings2_files,0xFF12A8DB));
        add(new Entry("extensions","root",R.string.Settings2Group_tools,R.string.Settings2_extensions,R.string.Settings2Desc_extensions,R.drawable.msg_plugins,0xFFDF408B));
        add(new Entry("general","root",R.string.Settings2Group_system,R.string.Settings2_general,R.string.Settings2Desc_general,R.drawable.msg_language,0xFFF39A22));
        add(new Entry("advanced","root",R.string.Settings2Group_system,R.string.Settings2_advanced,R.string.Settings2Desc_advanced,R.drawable.settings2_advanced,0xFF8198BE));
        add(new Entry("chat_list","appearance",R.string.Settings2Group_home,R.string.Settings2_chat_list,R.string.Settings2Desc_chat_list,R.drawable.msg_media,0xFF8B50DE));
        add(new Entry("avatars","appearance",R.string.Settings2Group_home,R.string.Settings2_avatars,R.string.Settings2Desc_avatars,R.drawable.msg_contacts,0xFF198DE4));
        add(new Entry("folders","appearance",R.string.Settings2Group_home,R.string.Settings2_folders,R.string.Settings2Desc_folders,R.drawable.msg_folders,0xFFDB4092));
        add(new Entry("visible","appearance",R.string.Settings2Group_home,R.string.Settings2_visible,R.string.Settings2Desc_visible,R.drawable.msg_info,0xFF8B50DE));
        add(new Entry("bubbles","appearance",R.string.Settings2Group_chat,R.string.Settings2_bubbles,R.string.Settings2Desc_bubbles,R.drawable.msg_sticker,0xFF12A8DB));
        add(new Entry("header","appearance",R.string.Settings2Group_chat,R.string.Settings2_header,R.string.Settings2Desc_header,R.drawable.msg_contacts,0xFF21BC65));
        add(new Entry("composer","appearance",R.string.Settings2Group_chat,R.string.Settings2_composer,R.string.Settings2Desc_composer,R.drawable.msg_settings_old,0xFF8B50DE));
        add(new Entry("post_appearance","appearance",R.string.Settings2Group_chat,R.string.Settings2_post_appearance,R.string.Settings2Desc_post_appearance,R.drawable.msg_media,0xFF8B50DE));
        add(new Entry("icons","appearance",R.string.Settings2Group_custom,R.string.Settings2_icons,R.string.Settings2Desc_icons,R.drawable.msg_emoji_smiles,0xFF198DE4));
        add(new Entry("fonts","appearance",R.string.Settings2Group_custom,R.string.Settings2_fonts,R.string.Settings2Desc_fonts,R.drawable.msg_settings_old,0xFF8B50DE));
        add(new Entry("effects","appearance",R.string.Settings2Group_custom,R.string.Settings2_effects,R.string.Settings2Desc_effects,R.drawable.msg_palette,0xFF8B50DE));
        add(new Entry("appearance_extra","appearance",R.string.Settings2Group_custom,R.string.Settings2_appearance_extra,R.string.Settings2Desc_appearance_extra,R.drawable.msg_settings_old,0xFF8B50DE));
        add(new Entry("bottom_tabs","navigation",R.string.Settings2Group_tabs,R.string.Settings2_bottom_tabs,R.string.Settings2Desc_bottom_tabs,R.drawable.msg_folders,0xFF198DE4));
        add(new Entry("app_navigation","navigation",R.string.Settings2Group_nav,R.string.Settings2_app_navigation,R.string.Settings2Desc_app_navigation,R.drawable.msg_settings_old,0xFF8B50DE));
        add(new Entry("gestures","navigation",R.string.Settings2Group_gestures,R.string.Settings2_gestures,R.string.Settings2Desc_gestures,R.drawable.msg_settings_old,0xFF8B50DE));
        add(new Entry("navigation_extra","navigation",R.string.Settings2Group_nav,R.string.Settings2_navigation_extra,R.string.Settings2Desc_navigation_extra,R.drawable.msg_settings_old,0xFF8B50DE));
        add(new Entry("messages","conversations",R.string.Settings2Group_messages,R.string.Settings2_messages,R.string.Settings2Desc_messages,R.drawable.msg_sticker,0xFF21BC65));
        add(new Entry("context","conversations",R.string.Settings2Group_interaction,R.string.Settings2_context,R.string.Settings2Desc_context,R.drawable.msg_media,0xFF8B50DE));
        add(new Entry("menus","conversations",R.string.Settings2Group_interaction,R.string.Settings2_menus,R.string.Settings2Desc_menus,R.drawable.msg_settings_old,0xFF8B50DE));
        add(new Entry("stickers","conversations",R.string.Settings2Group_interaction,R.string.Settings2_stickers,R.string.Settings2Desc_stickers,R.drawable.msg_emoji_smiles,0xFF8B50DE));
        add(new Entry("media","conversations",R.string.Settings2Group_media,R.string.Settings2_media,R.string.Settings2Desc_media,R.drawable.msg_media,0xFF198DE4));
        add(new Entry("profile","conversations",R.string.Settings2Group_chat,R.string.Settings2_profile,R.string.Settings2Desc_profile,R.drawable.msg_contacts,0xFF8B50DE));
        add(new Entry("archive","conversations",R.string.Settings2Group_chat,R.string.Settings2_archive,R.string.Settings2Desc_archive,R.drawable.msg_archive,0xFF8B50DE));
        add(new Entry("messages_extra","conversations",R.string.Settings2Group_messages,R.string.Settings2_messages_extra,R.string.Settings2Desc_messages_extra,R.drawable.msg_settings_old,0xFF8B50DE));
        add(new Entry("stickers_extra","conversations",R.string.Settings2Group_interaction,R.string.Settings2_stickers_extra,R.string.Settings2Desc_stickers_extra,R.drawable.msg_sticker,0xFF8B50DE));
        add(new Entry("media_extra","conversations",R.string.Settings2Group_media,R.string.Settings2_media_extra,R.string.Settings2Desc_media_extra,R.drawable.msg_media,0xFF8B50DE));
        add(new Entry("plugins","extensions",R.string.Settings2Group_modules,R.string.Settings2_plugins,R.string.Settings2Desc_plugins,R.drawable.msg_plugins,0xFF8B50DE));
        add(new Entry("ai","extensions",R.string.Settings2Group_modules,R.string.Settings2_ai,R.string.Settings2Desc_ai,R.drawable.msg_info,0xFF198DE4));
        add(new Entry("translation","extensions",R.string.Settings2Group_modules,R.string.Settings2_translation,R.string.Settings2Desc_translation,R.drawable.msg_translate,0xFF21BC65));
        add(new Entry("pillstack","extensions",R.string.Settings2Group_capsules,R.string.Settings2_pillstack,R.string.Settings2Desc_pillstack,R.drawable.msg_info,0xFFF39A22));
        add(new Entry("translator","translation",R.string.Settings2Group_modules,R.string.Settings2_translator,R.string.Settings2Desc_translator,R.drawable.msg_translate,0xFF8B50DE));
        add(new Entry("translation_options","translation",R.string.Settings2Group_modules,R.string.Settings2_translation_options,R.string.Settings2Desc_translation_options,R.drawable.msg_translate,0xFF8B50DE));
        add(new Entry("layout","chat_list",R.string.Settings2Group_home,R.string.Settings2_layout,R.string.Settings2Desc_layout,R.drawable.msg_media,0xFF8B50DE));
        add(new Entry("smart_previews","chat_list",R.string.Settings2Group_home,R.string.Settings2_smart_previews,R.string.Settings2Desc_smart_previews,R.drawable.msg_media,0xFF8B50DE));
        add(new Entry("launcher","icons",R.string.Settings2Group_custom,R.string.Settings2_launcher,R.string.Settings2Desc_launcher,R.drawable.msg_info,0xFF198DE4));
        add(new Entry("icon_packs","icons",R.string.Settings2Group_custom,R.string.Settings2_icon_packs,R.string.Settings2Desc_icon_packs,R.drawable.msg_settings_old,0xFF8B50DE));
        add(new Entry("emoji","icons",R.string.Settings2Group_custom,R.string.Settings2_emoji,R.string.Settings2Desc_emoji,R.drawable.msg_emoji_smiles,0xFF8B50DE));
        add(new Entry("surfaces","effects",R.string.Settings2Group_custom,R.string.Settings2_surfaces,R.string.Settings2Desc_surfaces,R.drawable.msg_settings_old,0xFF8B50DE));
        add(new Entry("animations","effects",R.string.Settings2Group_custom,R.string.Settings2_animations,R.string.Settings2Desc_animations,R.drawable.msg_sticker,0xFF8B50DE));
        add(new Entry("general_controls","general",R.string.Settings2Group_general,R.string.Settings2_general_controls,R.string.Settings2Desc_general_controls,R.drawable.msg_language,0xFFF39A22));
        add(new Entry("general_extra","general",R.string.Settings2Group_general,R.string.Settings2_general_extra,R.string.Settings2Desc_general_extra,R.drawable.msg_settings_old,0xFF8B50DE));
        add(new Entry("advanced_controls","advanced",R.string.Settings2Group_privacy,R.string.Settings2_advanced_controls,R.string.Settings2Desc_advanced_controls,R.drawable.msg_settings_old,0xFF8B50DE));
        add(new Entry("advanced_extra","advanced",R.string.Settings2Group_diagnostics,R.string.Settings2_advanced_extra,R.string.Settings2Desc_advanced_extra,R.drawable.msg_settings_old,0xFF8B50DE));
        add(new Entry("cloud","advanced",R.string.Settings2Group_maintenance,R.string.Settings2_cloud,R.string.Settings2Desc_cloud,R.drawable.msg_folders,0xFF8B50DE));
        add(new Entry("passcode","advanced",R.string.Settings2Group_privacy,R.string.Settings2_passcode,R.string.Settings2Desc_passcode,R.drawable.msg_settings_old,0xFF8B50DE));
        add(new Entry("appearance_extra_ng","appearance_extra",R.string.Settings2Group_custom,R.string.Settings2_appearance_extra_ng,R.string.Settings2Desc_appearance_extra_ng,R.drawable.msg_settings_old,0xFF8198BE));
        add(new Entry("appearance_extra_nx","appearance_extra",R.string.Settings2Group_custom,R.string.Settings2_appearance_extra_nx,R.string.Settings2Desc_appearance_extra_nx,R.drawable.msg_settings_old,0xFF8198BE));
        add(new Entry("media_extra_ng","media_extra",R.string.Settings2Group_custom,R.string.Settings2_media_extra_ng,R.string.Settings2Desc_media_extra_ng,R.drawable.msg_settings_old,0xFF8198BE));
        add(new Entry("media_extra_nc","media_extra",R.string.Settings2Group_custom,R.string.Settings2_media_extra_nc,R.string.Settings2Desc_media_extra_nc,R.drawable.msg_settings_old,0xFF8198BE));
        add(new Entry("media_extra_nx","media_extra",R.string.Settings2Group_custom,R.string.Settings2_media_extra_nx,R.string.Settings2Desc_media_extra_nx,R.drawable.msg_settings_old,0xFF8198BE));
        add(new Entry("stickers_extra_ng","stickers_extra",R.string.Settings2Group_custom,R.string.Settings2_stickers_extra_ng,R.string.Settings2Desc_stickers_extra_ng,R.drawable.msg_settings_old,0xFF8198BE));
        add(new Entry("stickers_extra_nc","stickers_extra",R.string.Settings2Group_custom,R.string.Settings2_stickers_extra_nc,R.string.Settings2Desc_stickers_extra_nc,R.drawable.msg_settings_old,0xFF8198BE));
        add(new Entry("stickers_extra_nx","stickers_extra",R.string.Settings2Group_custom,R.string.Settings2_stickers_extra_nx,R.string.Settings2Desc_stickers_extra_nx,R.drawable.msg_settings_old,0xFF8198BE));
        add(new Entry("navigation_extra_ng","navigation_extra",R.string.Settings2Group_custom,R.string.Settings2_navigation_extra_ng,R.string.Settings2Desc_navigation_extra_ng,R.drawable.msg_settings_old,0xFF8198BE));
        add(new Entry("navigation_extra_nx","navigation_extra",R.string.Settings2Group_custom,R.string.Settings2_navigation_extra_nx,R.string.Settings2Desc_navigation_extra_nx,R.drawable.msg_settings_old,0xFF8198BE));
        add(new Entry("advanced_extra_ng","advanced_extra",R.string.Settings2Group_custom,R.string.Settings2_advanced_extra_ng,R.string.Settings2Desc_advanced_extra_ng,R.drawable.msg_settings_old,0xFF8198BE));
        add(new Entry("advanced_extra_nx","advanced_extra",R.string.Settings2Group_custom,R.string.Settings2_advanced_extra_nx,R.string.Settings2Desc_advanced_extra_nx,R.drawable.msg_settings_old,0xFF8198BE));
    }
    private static void add(Entry e){if(ENTRIES.put(e.id,e)!=null)throw new IllegalStateException("Duplicate settings route");}
    public static Collection<Entry> all(){return Collections.unmodifiableCollection(ENTRIES.values());}
    public static Entry entry(String id){Entry e=ENTRIES.get(id);if(e==null)throw new IllegalArgumentException("Unknown settings route");return e;}
    public static List<Entry> children(String parent){List<Entry> out=new ArrayList<>();for(Entry e:ENTRIES.values())if(parent.equals(e.parent)&&visible(e.id))out.add(e);return out;}
    public static boolean visible(String id){if(id.endsWith("_extra")&&SignatureLegacyExtras.sources(id).isEmpty())return false;return !"passcode".equals(id)||!tw.nekomimi.nekogram.helpers.PasscodeHelper.isSettingsHidden();}
    private static BaseFragment scope(BaseNekoSettingsActivity f,String source,String route,String title){f.useSignatureSettingsPage(source,route,entry(title).title);return f;}
    private static BaseFragment chats(int screen,String route,String title){return scope(new OpenExteraChatsActivity(screen),"chats",route,title);}
    public static BaseFragment open(String id){if(java.util.Arrays.asList("icon_packs","emoji","translator","ai","pillstack","cloud","passcode").contains(id))return openLegacyEditor(id);return Settings3Registry.open(Settings3Registry.category(id));}
    private static BaseFragment openLegacyEditor(String id){
        switch(id){
            case "advanced_extra_nx":return SignatureLegacyExtras.screen("nx","advanced_extra");
            case "advanced_extra_ng":return SignatureLegacyExtras.screen("ng","advanced_extra");
            case "navigation_extra_nx":return SignatureLegacyExtras.screen("nx","navigation_extra");
            case "navigation_extra_ng":return SignatureLegacyExtras.screen("ng","navigation_extra");
            case "stickers_extra_nx":return SignatureLegacyExtras.screen("nx","stickers_extra");
            case "stickers_extra_nc":return SignatureLegacyExtras.screen("nc","stickers_extra");
            case "stickers_extra_ng":return SignatureLegacyExtras.screen("ng","stickers_extra");
            case "media_extra_nx":return SignatureLegacyExtras.screen("nx","media_extra");
            case "media_extra_nc":return SignatureLegacyExtras.screen("nc","media_extra");
            case "media_extra_ng":return SignatureLegacyExtras.screen("ng","media_extra");
            case "appearance_extra_nx":return SignatureLegacyExtras.screen("nx","appearance_extra");
            case "appearance_extra_ng":return SignatureLegacyExtras.screen("ng","appearance_extra");
            case "layout":return scope(new OpenExteraAppearanceActivity(),"appearance","chat_list",id);
            case "avatars": case "folders": case "fonts":return scope(new OpenExteraAppearanceActivity(),"appearance",id,id);
            case "surfaces":return scope(new OpenExteraAppearanceActivity(),"appearance","effects",id);
            case "visible":return chats(OpenExteraChatsActivity.SCREEN_HIDING,"visible",id);
            case "post_appearance":return chats(OpenExteraChatsActivity.SCREEN_SIGNATURE_MESSAGES,"post_appearance",id);
            case "smart_previews":return chats(OpenExteraChatsActivity.SCREEN_CHATS,"chat_list",id);
            case "messages":case "gestures":return chats(OpenExteraChatsActivity.SCREEN_SIGNATURE_MESSAGES,id,id);
            case "menus":return chats(OpenExteraChatsActivity.SCREEN_MENUS,id,id);
            case "media":return chats(OpenExteraChatsActivity.SCREEN_MEDIA,id,id);
            case "stickers":return chats(OpenExteraChatsActivity.SCREEN_SIGNATURE_STICKERS,id,id);
            case "profile":case "archive":case "translation_options":return scope(new OpenExteraGeneralActivity(),"general",id,id);
            case "general_controls":return scope(new OpenExteraGeneralActivity(),"general","general",id);
            case "advanced_controls":return scope(new OpenExteraOtherActivity(),"other","advanced",id);
            case "files":return new SignatureFilesSettingsActivity();
            case "studio":return new app.flexygram.studio.FlexyStudioActivity();
            case "bubbles":return new app.flexygram.bubbles.BubbleSettingsActivity();
            case "header":return new app.flexygram.header.HeaderSettingsActivity();
            case "composer":return new app.flexygram.composer.FlexyComposerSettingsActivity();
            case "bottom_tabs":return new app.flexygram.navigation.BottomTabsSettingsActivity();
            case "app_navigation":return new OpenExteraAppNavigationActivity();
            case "context":return new app.flexygram.bubbles.interaction.BubbleInteractionSettingsActivity();
            case "plugins":return new app.exteraless.plugins.ui.PluginsActivity();
            case "ai":return new app.exteraless.ai.ui.AiSettingsActivity();
            case "translator":return new tw.nekomimi.nekogram.settings.NekoTranslatorSettingsActivity();
            case "pillstack":return new app.exteraless.pillstack.PillStackSettingsActivity();
            case "emoji":return new tw.nekomimi.nekogram.settings.NekoEmojiSettingsActivity();
            case "icon_packs":return new app.exteraless.icons.IconPacksActivity();
            case "launcher":return new SignatureLauncherSettingsActivity();
            case "animations":return new app.flexygram.bubbles.deletion.MessageAnimationsActivity(false);
            case "cloud":return new OpenExteraCloudActivity();
            case "passcode":return new tw.nekomimi.nekogram.settings.NekoPasscodeSettingsActivity();
            case "general_extra":case "appearance_extra":case "navigation_extra":case "messages_extra":case "stickers_extra":case "media_extra":case "advanced_extra":return SignatureLegacyExtras.open(id);
            default:entry(id);return new SignatureSettingsActivity(id);
        }
    }
    public static BaseFragment legacy(String screen,String key){
        if("ayumoments".equals(screen)||"exteraless_ayumoments".equals(screen)||"ayuMoments".equals(key)||"ClearMessageDatabase".equals(key))return Settings3Registry.open("ayu");
        if(key!=null){
            BaseFragment extra=SignatureLegacyExtras.forKey(key);if(extra!=null)return Settings3Registry.open(Settings3Registry.category(SignatureLegacyExtras.routeForKey(key)));
            switch(key){
                case "iconPacks":return open("icon_packs");case "emojiSets":case "EmojiSets":return open("emoji");
                case "bottomTabs":return open("bottom_tabs");case "appNavigation":return open("app_navigation");
                case "pillStack":return open("pillstack");case "hiding":return open("visible");case "translator":return open("translator");
                case "flexyBubbles":return open("bubbles");case "signatureChatHeader":return open("header");case "flexyComposerSettings":return open("composer");
                case "flexyContextPanel":return open("context");case "flexyMessagesGestures":return open("messages");case "flexyStickersMedia":return open("stickers");
                case "flexySmartPreviews":return open("smart_previews");case "menus":return open("menus");case "media":return open("media");case "aiChat":return open("ai");
                case "flexyThemeWallpaper":case "chatSettings":return new app.flexygram.settings.SignatureChatThemeActivity();
                case "flexyfilesEnabled":case "flexyfilesHelp":return Settings3Registry.open("flexyfiles");
            }
            String source=screen;
            if(screen.equals("menus")||screen.equals("media")||screen.equals("hiding"))source="chats";
            if(source.equals("general")||source.equals("appearance")||source.equals("chats")||source.equals("other")){
                String owner=Settings2Policy.aliasOwner(source,key);
                if(owner.equals("@native"))return new org.telegram.ui.PrivacySettingsActivity();
                if(owner.equals("chat_list"))return open(source.equals("chats")?"smart_previews":"layout");
                if(owner.equals("effects"))return open("surfaces");if(owner.equals("advanced"))return open("advanced_controls");
                if(owner.equals("general"))return open("general_controls");
                if(!owner.startsWith("@")&&ENTRIES.containsKey(owner))return open(owner);
            }
        }
        switch(screen){case "general":return open("general");case "appearance":return open("appearance");case "chats":return open("conversations");case "other":return open("advanced");case "menus":return open("menus");case "media":return open("media");case "hiding":return open("visible");case "settings":return new SignatureSettingsActivity();default:return null;}
    }
    public static int searchGuid(String route){int index=0;for(Entry e:ENTRIES.values()){if(e.id.equals(route))return 10_000_000+1000*index;index++;}return 0;}
    public static List<BaseFragment> searchScreens(){List<BaseFragment> result=new ArrayList<>();for(Entry e:all()){if(!visible(e.id))continue;BaseFragment f=openLegacyEditor(e.id);if(f instanceof BaseNekoSettingsActivity && !(f instanceof SignatureSettingsActivity)||f instanceof tw.nekomimi.nekogram.settings.BaseNekoXSettingsActivity)result.add(f);}return result;}
    private SignatureSettingsRegistry(){}
}
