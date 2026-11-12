"""Run the actual legacy ownership filter; equivalent native dialogs have one entry."""
from pathlib import Path
from test_render_work_reuse import probe,JAVA
from test_composer_layout import method

S=JAVA/'app/flexygram/settings/signature'


def test_duplicate_legacy_controls_are_suppressed_and_native_destinations_survive(tmp_path):
    files={
        'app/flexygram/settings/signature/SignatureLegacyExtras.java':(S/'SignatureLegacyExtras.java').read_text(),
        'app/flexygram/settings/signature/Settings2Policy.java':(S/'Settings2Policy.java').read_text(),
        'org/telegram/messenger/R.java':'package org.telegram.messenger;public class R{}',
        'org/telegram/ui/ActionBar/BaseFragment.java':'package org.telegram.ui.ActionBar;public class BaseFragment{}',
        'tw/nekomimi/nekogram/config/cell/AbstractConfigCell.java':'package tw.nekomimi.nekogram.config.cell;public class AbstractConfigCell{}',
        'tw/nekomimi/nekogram/config/cell/WithKey.java':'package tw.nekomimi.nekogram.config.cell;public interface WithKey{String getKey();}',
        'tw/nekomimi/nekogram/settings/BaseNekoXSettingsActivity.java':'package tw.nekomimi.nekogram.settings;public class BaseNekoXSettingsActivity extends org.telegram.ui.ActionBar.BaseFragment{public void useSignatureSettingsPage(String source,String route,int title){}}',
        'app/flexygram/settings/signature/Settings3Registry.java':'package app.flexygram.settings.signature;public class Settings3Registry{public static String category(String route){return route;}}',
        'app/flexygram/settings/signature/SignatureSettingsRegistry.java':'package app.flexygram.settings.signature;public class SignatureSettingsRegistry{public static class Entry{public int title;}public static Entry entry(String id){return new Entry();}}',
        'app/flexygram/settings/signature/SignatureSettingsActivity.java':'package app.flexygram.settings.signature;public class SignatureSettingsActivity extends org.telegram.ui.ActionBar.BaseFragment{public SignatureSettingsActivity(String route){}}',
    }
    for name in ['NekoGeneralSettingsActivity','NekoChatSettingsActivity','NekoExperimentalSettingsActivity']:
        files['tw/nekomimi/nekogram/settings/'+name+'.java']='package tw.nekomimi.nekogram.settings;public class '+name+' extends BaseNekoXSettingsActivity{}'
    files['Probe.java']='''import app.flexygram.settings.signature.*;import tw.nekomimi.nekogram.config.cell.*;
public class Probe{
 static class Cell extends AbstractConfigCell implements WithKey{String key;Cell(String k){key=k;}public String getKey(){return key;}}
 public static void main(String[]args){
 String[][] duplicates={{"CloudflareCredentials","media"},{"LlmProviderGeminiKey","media"},{"TranscribeProviderOpenAI","media"},{"TextStyle","menus"},{"SensitiveDisableFiltering","advanced_controls"},{"EmojiSets","emoji"},{"HideReactions","visible"}};
 for(String[] d:duplicates){
  if(!d[1].equals(SignatureLegacyExtras.canonicalRouteForKey(d[0])))throw new AssertionError("missing destination: "+d[0]);
  for(String source:new String[]{"ng","nc","nx"})for(String route:new String[]{"messages_extra","media_extra","stickers_extra","appearance_extra","general_extra","navigation_extra","advanced_extra"})if(SignatureLegacyExtras.accepts(new Cell(d[0]),source,route))throw new AssertionError("repeated entry: "+d[0]);
  if(SignatureLegacyExtras.forKey(d[0])!=null)throw new AssertionError("legacy factory bypasses canonical editor");
 }
 for(String[] c:new String[][]{{"CloudflareCredentials","media"},{"LlmProviderGeminiKey","media"},{"TranscribeProviderOpenAI","media"},{"TextStyle","menus"}})if(!Settings2Policy.matches("chats",c[1],c[0]))throw new AssertionError("lost native control: "+c[0]);
 if(!Settings2Policy.matches("other","advanced","SensitiveDisableFiltering"))throw new AssertionError("lost sensitive control");
 var media=new Settings2Policy.Rows("chats","media");if(!media.named("transcribeProviderOpenAI")||!media.named("voskModels"))throw new AssertionError("conditional transcription options filtered out");
 if(!Settings2Policy.matches("chats","visible","HideReactions"))throw new AssertionError("native reaction group lost");
 if(!SignatureLegacyExtras.accepts(new Cell("CustomEditedMessage"),"nc","messages_extra"))throw new AssertionError("unrelated option lost");
 }}'''
    probe(tmp_path,files,[])


def test_old_links_and_search_redirect_before_selecting_legacy_extra():
    old=method((S/'SignatureSettingsRegistry.java').read_text(),'public static BaseFragment legacy(')
    assert old.index('canonicalRouteForKey(key)')<old.index('SignatureLegacyExtras.forKey(key)')
    search=method((S/'Settings3Registry.java').read_text(),'public static BaseFragment searchTarget(')
    assert search.index('canonicalRouteForKey(key)')<search.index('getSignatureSettingsRoute()')


def test_reaction_preferences_keep_the_existing_migration_and_three_native_options():
    root=JAVA.parents[3]
    config=(root/'TMessagesProj/src/main/kotlin/app/exteraless/chats/ChatsConfig.kt').read_text()
    migration=method(config,'private fun migrateLegacyKeys()')
    for text in ['if (NaConfig.hideReactions.Bool())','hideReactionsInChannels.setConfigBool(true)','hideReactionsInGroups.setConfigBool(true)','hideReactionsInPrivate.setConfigBool(true)','NaConfig.hideReactions.setConfigBool(false)']:
        assert text in migration
    native=(JAVA/'app/exteraless/settings/OpenExteraChatsActivity.java').read_text()
    for name in ['hideReactionsInChannels','hideReactionsInGroups','hideReactionsInPrivate']:
        assert 'ChatsConfig.'+name in native


def test_known_native_aliases_cannot_reappear_as_legacy_extras():
    import re
    extras=(S/'SignatureLegacyExtras.java').read_text()
    aliases=(S/'Settings2Policy.java').read_text()
    suppressed=set(re.findall(r'owned.add\("([^"]+)"',extras))|set(re.findall(r'canonical\("([^"]+)"',extras))
    legacy_keys=re.findall(r'own\("([^"]+)","(?:ng|nc|nx)","[^"]+"',extras)
    for key in legacy_keys:
        native_routes=re.findall(r'ALIASES.put\("[^:]+:'+re.escape(key)+r'","([^"]+)"',aliases)
        if any(not route.startswith('@') for route in native_routes):
            assert key in suppressed,'Legacy control duplicates an existing native alias: '+key
