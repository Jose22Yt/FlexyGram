/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.settings.signature;

import android.content.Context;
import android.content.Intent;
import android.os.Bundle;
import android.os.Parcelable;
import android.view.View;
import androidx.recyclerview.widget.RecyclerView;
import java.util.ArrayList;
import org.telegram.messenger.R;
import org.telegram.messenger.LocaleController;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.ActionBar.ThemeDescription;
import app.flexygram.settings.SignatureMatteSettingsActivity;
import app.exteraless.settings.*;
import tw.nekomimi.nekogram.settings.*;

/** Lazy section overview; editors retain the original native adapters and ConfigItems. */
public final class SignatureDirectSettingsActivity extends SignatureMatteSettingsActivity {
    private String category="chat";
    private String segment="";
    private final ArrayList<NativeSettingsSection> sections=new ArrayList<>();
    private NativeSectionsAdapter combined;
    private Parcelable scrollState;
    private org.telegram.ui.Components.UndoView sharedTooltip;
    public org.telegram.ui.Components.UndoView settings3Tooltip(){if(sharedTooltip==null)sharedTooltip=new org.telegram.ui.Components.UndoView(fragmentView.getContext());return sharedTooltip;}
    public SignatureDirectSettingsActivity(){}
    public SignatureDirectSettingsActivity(String category){Settings3Registry.entry(category);this.category=category;}
    public SignatureDirectSettingsActivity(String category,String segment){this(category);CompactSettingsPlan.page(category,segment);this.segment=segment;}
    private boolean include(String id){return segment.equals(id);}
    private void overview(){
        if(category.equals("chat"))links(new String[]{"composer_style","header_style","bubble_style","context"},new int[]{R.string.FlexyInterfaceLower,R.string.FlexyInterfaceUpper,R.string.FlexyBubblesTitle,R.string.FlexyMenuTitle},new int[]{R.drawable.fg_ios_original_chat_list_composeicon,R.drawable.fg_ios_original_chat_context_menu_user,R.drawable.fg_ios_original_chat_list_tabs_iconchats,R.drawable.fg_ios_original_chat_context_menu_more});
        if(category.equals("universal"))links(new String[]{"icon_packs","emoji","cloud","passcode"},new int[]{R.string.Settings2_icon_packs,R.string.Settings2_emoji,R.string.Settings2_cloud,R.string.Settings2_passcode},new int[]{R.drawable.fg_ios_original_chat_context_menu_palette,R.drawable.fg_ios_original_chat_context_menu_sticker,R.drawable.fg_ios_original_chat_context_menu_cloud,R.drawable.fg_ios_original_chat_context_menu_touchid});
        if(category.equals("navigation"))links(new String[]{"navigationEditor"},new int[]{R.string.Settings2_app_navigation},new int[]{R.drawable.fg_ios_original_chat_context_menu_list});
        if(category.equals("plugins"))links(new String[]{"plugins","ai","translator","pillstack"},new int[]{R.string.Settings2_plugins,R.string.Settings2_ai,R.string.Settings2_translator,R.string.Settings2_pillstack},new int[]{R.drawable.fg_settings_plugins,R.drawable.fg_ios_original_chat_context_menu_bots,R.drawable.fg_ios_original_chat_context_menu_replace,R.drawable.fg_ios_original_chat_context_menu_reorderitems});
        CompactSettingsPlan.Page[] pages=CompactSettingsPlan.pages(category);
        String[] ids=new String[pages.length+1];int[] titles=new int[ids.length],icons=new int[ids.length];
        ids[0]="#sections";titles[0]=R.string.CompactSections;
        for(int i=0;i<pages.length;i++){ids[i+1]="section:"+category+":"+pages[i].id;titles[i+1]=pages[i].title;icons[i+1]=pages[i].icon;}
        links(ids,titles,icons);
    }
    @Override protected String getActionBarTitle(){return LocaleController.getString(segment.isEmpty()?Settings3Registry.entry(category).title:CompactSettingsPlan.page(category,segment).title);}
    @Override protected BaseListAdapter createAdapter(Context c){return new MatteListAdapter(c){};}
    @Override protected void onItemClick(View v,int p,float x,float y){if(combined!=null)combined.click(v,p,x,y);}
    private <T extends BaseNekoSettingsActivity>T scope(T f,String source,String routes){f.useSignatureSettingsPage(source,routes,Settings3Registry.entry(category).title);return f;}
    private void add(NativeSettingsSection section){sections.add(section);combined.add(section,section.prepareSettings3(this,listView));}
    private void extra(String source,String... routes){
        BaseNekoXSettingsActivity f=source.equals("ng")?new NekoGeneralSettingsActivity():source.equals("nc")?new NekoChatSettingsActivity():new NekoExperimentalSettingsActivity();
        f.useSignatureSettingsPage(Settings3Registry.entry(category).title,cell->{
            if(cell instanceof tw.nekomimi.nekogram.config.cell.WithKey&&((tw.nekomimi.nekogram.config.cell.WithKey)cell).getKey()!=null&&!category.equals(SignatureLegacyExtras.categoryForKey(((tw.nekomimi.nekogram.config.cell.WithKey)cell).getKey(),source)))return false;
            if(cell instanceof tw.nekomimi.nekogram.config.cell.WithKey&&"ClearMessageDatabase".equals(((tw.nekomimi.nekogram.config.cell.WithKey)cell).getKey()))return false;
            for(String route:routes)if(SignatureLegacyExtras.accepts(cell,source,route))return true;return false;
        });add(f);
    }
    private void links(String[] ids,int[] titles,int[] icons){
        java.util.ArrayList<String> names=new java.util.ArrayList<>();java.util.ArrayList<Integer> labels=new java.util.ArrayList<>(),glyphs=new java.util.ArrayList<>();
        for(int i=0;i<ids.length;i++){if(ids[i].equals("passcode")&&tw.nekomimi.nekogram.helpers.PasscodeHelper.isSettingsHidden())continue;names.add(ids[i]);labels.add(titles[i]);glyphs.add(icons[i]);}
        int[] t=new int[labels.size()],g=new int[glyphs.size()];for(int i=0;i<t.length;i++){t[i]=labels.get(i);g[i]=glyphs.get(i);}add(new Settings3LinksSection(names.toArray(new String[0]),t,g));
    }
    private void build(){
        switch(category){
            case "chat":
                if(segment.isEmpty()){overview();break;}
                if(include("glare"))add(new app.flexygram.effects.GlareSettingsSection());
                if(include("members"))add(new app.flexygram.memberlens.MemberLensSettingsSection());
                if(include("conversion"))add(new app.flexygram.inlineconverter.InlineConversionSettingsSection());
                if(include("messages")){
                    add(scope(new OpenExteraChatsActivity(OpenExteraChatsActivity.SCREEN_SIGNATURE_MESSAGES),"chats","messages|post_appearance"));
                    extra("nc","messages_extra");
                }
                if(include("menus"))add(scope(new OpenExteraChatsActivity(OpenExteraChatsActivity.SCREEN_MENUS),"chats","menus"));
                if(include("media")){
                    add(scope(new OpenExteraChatsActivity(OpenExteraChatsActivity.SCREEN_MEDIA),"chats","media"));
                    extra("nc","media_extra");extra("ng","media_extra");extra("nx","media_extra");
                }
                if(include("stickers")){
                    add(scope(new OpenExteraChatsActivity(OpenExteraChatsActivity.SCREEN_SIGNATURE_STICKERS),"chats","stickers"));
                    extra("nc","stickers_extra");extra("ng","stickers_extra");extra("nx","stickers_extra");
                }
                if(include("animations"))add(new app.flexygram.bubbles.deletion.MessageAnimationsActivity(true));break;
            case "home":
                if(segment.isEmpty()){overview();break;}
                if(include("list")){
                    add(new app.flexygram.home.HomeListSettingsActivity());
                    add(scope(new OpenExteraAppearanceActivity(),"appearance","chat_list"));
                    add(scope(new OpenExteraChatsActivity(OpenExteraChatsActivity.SCREEN_CHATS),"chats","chat_list"));
                }
                if(include("motion"))add(new app.flexygram.scroll.ScrollEffectsSettingsActivity());
                if(include("pills"))add(new app.flexygram.home.SmartPreviewsSettingsActivity());
                if(include("avatars"))add(scope(new OpenExteraAppearanceActivity(),"appearance","avatars"));
                if(include("folders"))add(scope(new OpenExteraAppearanceActivity(),"appearance","folders"));
                if(include("visible"))add(scope(new OpenExteraChatsActivity(OpenExteraChatsActivity.SCREEN_HIDING),"chats","visible"));
                if(include("extras")){extra("ng","appearance_extra");extra("nx","appearance_extra");}break;
            case "universal":
                if(segment.isEmpty()){overview();break;}
                if(include("general"))add(scope(new OpenExteraGeneralActivity(),"general","general_behavior"));
                if(include("network"))add(scope(new OpenExteraGeneralActivity(),"general","general_network"));
                if(include("notifications"))add(scope(new OpenExteraGeneralActivity(),"general","general_notifications"));
                if(include("maps"))add(scope(new OpenExteraGeneralActivity(),"general","general_maps"));
                if(include("profile")||include("archive"))add(scope(new OpenExteraGeneralActivity(),"general",segment));
                if(include("fonts")||include("effects"))add(scope(new OpenExteraAppearanceActivity(),"appearance",segment));
                if(include("advanced")){
                    add(scope(new OpenExteraOtherActivity(),"other","advanced"));
                    extra("ng","advanced_extra");extra("nx","advanced_extra");
                }
                if(include("extras"))extra("ng","general_extra","appearance_extra");
                if(include("launcher"))add(new SignatureLauncherSettingsActivity());break;
            case "ayu":
                if(segment.isEmpty()){overview();break;}
                if(include("ghost"))add(new GhostModeActivity());
                else add(scope(new OpenExteraAyuMomentsActivity(),"ayu","ayu_"+segment));break;
            case "navigation":
                if(segment.isEmpty()){overview();break;}
                if(include("tabs"))add(new app.flexygram.navigation.BottomTabsSettingsActivity());
                if(include("controls"))add(new OpenExteraAppNavigationActivity.NativeControls());
                if(include("gestures"))add(scope(new OpenExteraChatsActivity(OpenExteraChatsActivity.SCREEN_SIGNATURE_MESSAGES),"chats","gestures"));
                if(include("extras")){extra("ng","navigation_extra");extra("nx","navigation_extra");}break;
            case "plugins":
                if(segment.isEmpty()){overview();break;}
                add(scope(new OpenExteraGeneralActivity(),"general","translation_options"));break;
            default:throw new IllegalArgumentException("Not a direct settings category");
        }
    }
    private void release(){if(sharedTooltip!=null)sharedTooltip.hide(false,0);if(combined!=null){if(listView!=null)listView.setAdapter(null);combined.close();}for(NativeSettingsSection section:sections)section.releaseSettings3();sections.clear();combined=null;sharedTooltip=null;}
    @Override public View createView(Context context){
        if(layoutManager!=null)scrollState=layoutManager.onSaveInstanceState();
        release();View view=super.createView(context);listView.setItemAnimator(null);listView.setSections(org.telegram.messenger.AndroidUtilities.dp(16),org.telegram.messenger.AndroidUtilities.dp(20),true);
        combined=new NativeSectionsAdapter();build();listView.setAdapter(combined);listView.setOnItemClickListener(combined::click);
        // Dispatch native row sharing with its local key and offset.
        listView.setOnItemLongClickListener(combined::longClick);
        if(scrollState!=null)layoutManager.onRestoreInstanceState(scrollState);return view;
    }
    @Override public void scrollToRow(String key,Runnable unknown){
        for(NativeSettingsSection section:sections){BaseFragment f=section.settings3Controller();
            if(f instanceof BaseNekoSettingsActivity&&((BaseNekoSettingsActivity)f).settings3HasRow(key)){((BaseNekoSettingsActivity)f).scrollToRow(key,unknown);return;}
            if(f instanceof BaseNekoXSettingsActivity&&((BaseNekoXSettingsActivity)f).settings3HasRow(key)){((BaseNekoXSettingsActivity)f).scrollToRow(key,unknown);return;}
        }if(unknown!=null)unknown.run();
    }
    public void importToRow(String key,String value,Runnable unknown){for(NativeSettingsSection section:sections){BaseFragment f=section.settings3Controller();if(f instanceof BaseNekoXSettingsActivity&&((BaseNekoXSettingsActivity)f).settings3HasRow(key)){((BaseNekoXSettingsActivity)f).importToRow(key,value,unknown);return;}}scrollToRow(key,unknown);}
    @Override public void onResume(){super.onResume();for(NativeSettingsSection s:sections)s.settings3Controller().onResume();}
    @Override public void onPause(){if(layoutManager!=null)scrollState=layoutManager.onSaveInstanceState();for(NativeSettingsSection s:sections)s.settings3Controller().onPause();super.onPause();}
    @Override public void onFragmentDestroy(){release();super.onFragmentDestroy();}
    @Override public void onActivityResultFragment(int request,int result,Intent data){for(NativeSettingsSection s:sections)s.settings3Controller().onActivityResultFragment(request,result,data);}
    @Override public void onRequestPermissionsResultFragment(int request,String[] permissions,int[] grants){for(NativeSettingsSection s:sections)s.settings3Controller().onRequestPermissionsResultFragment(request,permissions,grants);}
    @Override public void saveSelfArgs(Bundle args){super.saveSelfArgs(args);args.putString("settings3Category",category);args.putString("settings3Segment",segment);if(layoutManager!=null)args.putParcelable("settings3Scroll",layoutManager.onSaveInstanceState());}
    @Override public void restoreSelfArgs(Bundle args){super.restoreSelfArgs(args);String saved=args.getString("settings3Category","chat");Settings3Registry.entry(saved);category=saved;segment=args.getString("settings3Segment","");if(!segment.isEmpty())CompactSettingsPlan.page(category,segment);scrollState=args.getParcelable("settings3Scroll");}
    @Override public ArrayList<ThemeDescription> getThemeDescriptions(){ArrayList<ThemeDescription> colors=super.getThemeDescriptions();for(NativeSettingsSection s:sections)colors.addAll(s.settings3Controller().getThemeDescriptions());return colors;}
}
