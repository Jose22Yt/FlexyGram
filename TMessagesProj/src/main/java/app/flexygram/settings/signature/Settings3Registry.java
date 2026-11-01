/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.settings.signature;
import java.util.*;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.BaseFragment;
/** The approved ten entries. Old route IDs remain aliases, never additional visible hubs. */
public final class Settings3Registry {
    public static final class Entry {
        public final String id;public final int group,title,description,icon;
        Entry(String id,int group,int title,int description,int icon){this.id=id;this.group=group;this.title=title;this.description=description;this.icon=icon;}
    }
    private static final List<Entry> ENTRIES=Collections.unmodifiableList(Arrays.asList(
        new Entry("chat",R.string.Settings3Group_personal,R.string.Settings3_chat,R.string.Settings3Desc_chat,R.drawable.settings3_chat),
        new Entry("home",R.string.Settings3Group_personal,R.string.Settings3_home,R.string.Settings3Desc_home,R.drawable.settings3_stack),
        new Entry("universal",R.string.Settings3Group_personal,R.string.Settings3_universal,R.string.Settings3Desc_universal,R.drawable.settings3_sliders),
        new Entry("ayu",R.string.Settings3Group_functions,R.string.Settings3_ayu,R.string.Settings3Desc_ayu,R.drawable.settings3_ghost),
        new Entry("plugins",R.string.Settings3Group_functions,R.string.Settings3_plugins,R.string.Settings3Desc_plugins,R.drawable.settings3_plugins),
        new Entry("flexyfiles",R.string.Settings3Group_functions,R.string.Settings3_flexyfiles,R.string.Settings3Desc_flexyfiles,R.drawable.settings3_document),
        new Entry("files",R.string.Settings3Group_functions,R.string.Settings3_files,R.string.Settings3Desc_files,R.drawable.settings3_folder),
        new Entry("navigation",R.string.Settings3Group_functions,R.string.Settings3_navigation,R.string.Settings3Desc_navigation,R.drawable.settings3_hand),
        new Entry("studio",R.string.Settings3Group_functions,R.string.Settings3_studio,R.string.Settings3Desc_studio,R.drawable.settings3_stack),
        new Entry("about",R.string.Settings3Group_information,R.string.Settings3_about,R.string.Settings3Desc_about,R.drawable.settings3_info))) ;
    public static List<Entry> all(){return ENTRIES;}
    public static Entry entry(String id){for(Entry e:ENTRIES)if(e.id.equals(id))return e;throw new IllegalArgumentException("Unknown Settings3 category");}
    public static BaseFragment open(String id){
        if("studio".equals(id))return new app.flexygram.studio.FlexyStudioActivity();
        if("flexyfiles".equals(id))return new SignatureFlexyFilesActivity();
        if("files".equals(id)){app.exteraless.settings.OpenExteraGeneralActivity f=new app.exteraless.settings.OpenExteraGeneralActivity();f.useSignatureSettingsPage("general","files",R.string.Settings3_files);return f;}
        return new SignatureDirectSettingsActivity(id);
    }
    public static String category(String route){
        if(route.equals("ayu")||route.equals("ayumoments"))return "ayu";
        if(route.equals("studio"))return "studio";
        if(route.equals("files"))return "files";
        if(route.equals("plugins")||route.equals("extensions")||route.equals("ai")||route.equals("translator")||route.equals("translation")||route.equals("translation_options")||route.equals("pillstack"))return "plugins";
        if(route.equals("navigation")||route.equals("bottom_tabs")||route.equals("app_navigation")||route.equals("gestures")||route.startsWith("navigation_extra"))return "navigation";
        if(route.equals("appearance")||route.equals("chat_list")||route.equals("layout")||route.equals("avatars")||route.equals("folders")||route.equals("visible")||route.equals("smart_previews")||route.startsWith("appearance_extra"))return "home";
        if(route.equals("advanced")||route.equals("advanced_controls")||route.equals("general")||route.equals("general_controls")||route.equals("fonts")||route.equals("effects")||route.equals("surfaces")||route.equals("icons")||route.equals("launcher")||route.equals("profile")||route.equals("archive")||route.startsWith("general_extra")||route.startsWith("advanced_extra"))return "universal";
        return "chat";
    }
    public static BaseFragment searchTarget(BaseFragment original,String key){
        if("flexyfilesEnabled".equals(key)||"flexyfilesHelp".equals(key))return open("flexyfiles");
        String route=null;
        if(original instanceof tw.nekomimi.nekogram.settings.BaseNekoSettingsActivity)route=((tw.nekomimi.nekogram.settings.BaseNekoSettingsActivity)original).getSignatureSettingsRoute();
        if(original instanceof tw.nekomimi.nekogram.settings.BaseNekoXSettingsActivity)route=((tw.nekomimi.nekogram.settings.BaseNekoXSettingsActivity)original).getSignatureSettingsRoute();
        if(route!=null)return open(category(route));
        if(original instanceof app.flexygram.header.HeaderSettingsActivity||original instanceof app.flexygram.bubbles.BubbleSettingsActivity||original instanceof app.flexygram.composer.FlexyComposerSettingsActivity||original instanceof app.flexygram.bubbles.interaction.BubbleInteractionSettingsActivity||original instanceof app.flexygram.bubbles.deletion.MessageAnimationsActivity)return open("chat");
        if(original instanceof app.flexygram.navigation.BottomTabsSettingsActivity)return open("navigation");
        if(original instanceof app.exteraless.settings.OpenExteraAyuMomentsActivity)return open("ayu");
        if(original instanceof SignatureLauncherSettingsActivity)return open("universal");
        return original;
    }
    private Settings3Registry(){}
}
