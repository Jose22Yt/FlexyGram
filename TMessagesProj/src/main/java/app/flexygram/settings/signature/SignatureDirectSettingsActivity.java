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

/** One scroll surface with the actual legacy native row adapters and original ConfigItems. */
public final class SignatureDirectSettingsActivity extends SignatureMatteSettingsActivity {
    private String category="chat";
    private final ArrayList<NativeSettingsSection> sections=new ArrayList<>();
    private NativeSectionsAdapter combined;
    private Parcelable scrollState;
    private org.telegram.ui.Components.UndoView sharedTooltip;
    public org.telegram.ui.Components.UndoView settings3Tooltip(){if(sharedTooltip==null)sharedTooltip=new org.telegram.ui.Components.UndoView(fragmentView.getContext());return sharedTooltip;}
    public SignatureDirectSettingsActivity(){}
    public SignatureDirectSettingsActivity(String category){Settings3Registry.entry(category);this.category=category;}
    @Override protected String getActionBarTitle(){return LocaleController.getString(Settings3Registry.entry(category).title);}
    @Override protected BaseListAdapter createAdapter(Context c){return new MatteListAdapter(c){};}
    @Override protected void onItemClick(View v,int p,float x,float y){if(combined!=null)combined.click(v,p,x,y);}
    private <T extends BaseNekoSettingsActivity>T scope(T f,String source,String routes){f.useSignatureSettingsPage(source,routes,Settings3Registry.entry(category).title);return f;}
    private void add(NativeSettingsSection section){sections.add(section);combined.add(section,section.prepareSettings3(this,listView));}
    private void extra(String source,String... routes){
        BaseNekoXSettingsActivity f=source.equals("ng")?new NekoGeneralSettingsActivity():source.equals("nc")?new NekoChatSettingsActivity():new NekoExperimentalSettingsActivity();
        f.useSignatureSettingsPage(Settings3Registry.entry(category).title,cell->{
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
                add(new app.flexygram.header.HeaderSettingsActivity());
                add(new app.flexygram.bubbles.BubbleSettingsActivity());
                add(new app.flexygram.composer.FlexyComposerSettingsActivity());
                add(scope(new OpenExteraChatsActivity(OpenExteraChatsActivity.SCREEN_SIGNATURE_MESSAGES),"chats","messages|post_appearance"));
                add(scope(new OpenExteraChatsActivity(OpenExteraChatsActivity.SCREEN_MENUS),"chats","menus"));
                add(scope(new OpenExteraChatsActivity(OpenExteraChatsActivity.SCREEN_MEDIA),"chats","media"));
                add(scope(new OpenExteraChatsActivity(OpenExteraChatsActivity.SCREEN_SIGNATURE_STICKERS),"chats","stickers"));
                extra("nc","messages_extra","media_extra","stickers_extra");extra("ng","media_extra","stickers_extra");extra("nx","media_extra","stickers_extra");
                add(new app.flexygram.bubbles.interaction.BubbleInteractionSettingsActivity());
                add(new app.flexygram.bubbles.deletion.MessageAnimationsActivity(true));break;
            case "home":
                add(scope(new OpenExteraAppearanceActivity(),"appearance","chat_list|avatars|folders"));
                add(scope(new OpenExteraChatsActivity(OpenExteraChatsActivity.SCREEN_CHATS),"chats","chat_list"));
                add(scope(new OpenExteraChatsActivity(OpenExteraChatsActivity.SCREEN_HIDING),"chats","visible"));
                extra("ng","appearance_extra");extra("nx","appearance_extra");break;
            case "universal":
                add(scope(new OpenExteraGeneralActivity(),"general","general|profile|archive"));
                add(scope(new OpenExteraAppearanceActivity(),"appearance","fonts|effects"));
                add(scope(new OpenExteraOtherActivity(),"other","advanced"));
                add(new SignatureLauncherSettingsActivity());
                extra("ng","general_extra","advanced_extra");extra("nx","advanced_extra");
                links(new String[]{"icon_packs","emoji","cloud","passcode"},new int[]{R.string.Settings2_icon_packs,R.string.Settings2_emoji,R.string.Settings2_cloud,R.string.Settings2_passcode},new int[]{R.drawable.settings3_stack,R.drawable.settings3_chat,R.drawable.settings3_document,R.drawable.settings3_info});break;
            case "ayu":add(new GhostModeActivity());add(new OpenExteraAyuMomentsActivity());break;
            case "navigation":
                add(new app.flexygram.navigation.BottomTabsSettingsActivity());
                add(new OpenExteraAppNavigationActivity.NativeControls());
                add(scope(new OpenExteraChatsActivity(OpenExteraChatsActivity.SCREEN_SIGNATURE_MESSAGES),"chats","gestures"));
                extra("ng","navigation_extra");extra("nx","navigation_extra");
                links(new String[]{"navigationEditor"},new int[]{R.string.Settings2_app_navigation},new int[]{R.drawable.settings3_hand});break;
            case "plugins":
                links(new String[]{"plugins","ai","translator","pillstack"},new int[]{R.string.Settings2_plugins,R.string.Settings2_ai,R.string.Settings2_translator,R.string.Settings2_pillstack},new int[]{R.drawable.settings3_plugins,R.drawable.settings3_sliders,R.drawable.settings3_chat,R.drawable.settings3_stack});
                add(scope(new OpenExteraGeneralActivity(),"general","translation_options"));break;
            default:throw new IllegalArgumentException("Not a direct settings category");
        }
    }
    private void release(){if(sharedTooltip!=null)sharedTooltip.hide(false,0);if(combined!=null){if(listView!=null)listView.setAdapter(null);combined.close();}for(NativeSettingsSection section:sections)section.releaseSettings3();sections.clear();combined=null;sharedTooltip=null;}
    @Override public View createView(Context context){
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
    @Override public void saveSelfArgs(Bundle args){super.saveSelfArgs(args);args.putString("settings3Category",category);if(layoutManager!=null)args.putParcelable("settings3Scroll",layoutManager.onSaveInstanceState());}
    @Override public void restoreSelfArgs(Bundle args){super.restoreSelfArgs(args);String saved=args.getString("settings3Category","chat");Settings3Registry.entry(saved);category=saved;scrollState=args.getParcelable("settings3Scroll");}
    @Override public ArrayList<ThemeDescription> getThemeDescriptions(){ArrayList<ThemeDescription> colors=super.getThemeDescriptions();for(NativeSettingsSection s:sections)colors.addAll(s.settings3Controller().getThemeDescriptions());return colors;}
}
