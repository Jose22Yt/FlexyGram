"""Home presentation policies and native-folder integration without an APK."""
from test_render_work_reuse import JAVA,ROOT,probe
from test_composer_layout import method
import re,xml.etree.ElementTree as ET


def test_style_migration_and_explicit_option_mapping(tmp_path):
    probe(tmp_path,{
      'android/content/Context.java':'package android.content;public class Context{public static int MODE_PRIVATE=0;public android.content.SharedPreferences getSharedPreferences(String f,int m){return org.telegram.messenger.ApplicationLoader.preferences;}}',
      'android/content/SharedPreferences.java':'package android.content;public interface SharedPreferences{int getInt(String k,int d);Editor edit();interface Editor{Editor putInt(String k,int v);void apply();}}',
      'org/telegram/messenger/ApplicationLoader.java':'package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext=new android.content.Context();public static android.content.SharedPreferences preferences;}',
      'Probe.java':'''import app.flexygram.home.HomeStyleConfig;import android.content.*;public class Probe{
 static class Prefs implements SharedPreferences,SharedPreferences.Editor{
 int reads,writes;java.util.Map<String,Integer> values=new java.util.HashMap<>();public int getInt(String k,int d){reads++;return values.getOrDefault(k,d);}public Editor edit(){writes++;return this;}public Editor putInt(String k,int v){values.put(k,v);return this;}public void apply(){}}
 public static void main(String[]args){Prefs p=new Prefs();org.telegram.messenger.ApplicationLoader.preferences=p;
 if(HomeStyleConfig.style()!=0)throw new AssertionError("fresh install");
 p.values.put("style",1);HomeStyleConfig.load();if(HomeStyleConfig.style()!=0||p.values.get("style")!=0)throw new AssertionError("Essential migration");
 HomeStyleConfig.setStyle(HomeStyleConfig.optionStyle(1));HomeStyleConfig.load();
 if(!HomeStyleConfig.isIos()||HomeStyleConfig.style()!=2||HomeStyleConfig.extraHeaderDp(true)!=54||HomeStyleConfig.headerDp()!=56)throw new AssertionError();
 int reads=p.reads,writes=p.writes;for(int n=0;n<20000;n++)if(!HomeStyleConfig.isIos())throw new AssertionError();
 if(p.reads!=reads||p.writes!=writes)throw new AssertionError("preferences accessed while drawing");
 for(int n:new int[]{-1,1,3,Integer.MAX_VALUE}){HomeStyleConfig.setStyle(n);if(HomeStyleConfig.style()!=0)throw new AssertionError();}
 HomeStyleConfig.setStyle(HomeStyleConfig.optionStyle(0));if(HomeStyleConfig.isIos())throw new AssertionError();
 }}'''
    },[JAVA/'app/flexygram/home/HomeStyleConfig.java'])


def test_first_settings_row_has_no_preview_and_favorite_ids_are_not_portable():
    settings=(JAVA/'app/flexygram/settings/signature/SignatureDirectSettingsActivity.java').read_text()
    home=settings[settings.index('case "home":'):settings.index('case "universal":')]
    assert home.index('HomeStyleSettingsActivity')<home.index('SmartPreviewsSettingsActivity')
    selector=(JAVA/'app/flexygram/home/HomeStyleSettingsActivity.java').read_text()
    assert 'TYPE_SETTINGS' in selector and 'setItems(' in selector and 'Preview' not in selector
    catalog=(JAVA/'app/flexygram/studio/StudioClientCatalog.java').read_text()
    assert 'integer("flexygram_home","style",0)' in catalog
    assert 'favorite_folder_' not in catalog


def test_home_keeps_the_native_dialog_order_and_edit_does_not_select_a_chat():
    source=(JAVA/'org/telegram/ui/DialogsActivity.java').read_text()
    projection=method(source,'public ArrayList<TLRPC.Dialog> getDialogsArray(')
    assert 'return getControllerDialogsArray(' in projection and 'without(' not in projection
    assert '()->showOrUpdateActionMode(0,null)' in source
    selection=method(source,'private void showOrUpdateActionMode(')
    assert 'if(dialogId!=0)addOrRemoveSelectedDialog(dialogId, cell)' in selection
    assert 'createActionMode(null)' in selection and 'selectedDialogs.get(0)' not in selection
    assert 'favoriteFolder' not in source and 'setShortcutOnly(a)' not in source


def test_header_uses_native_shared_glass_with_opaque_fallback_and_no_draw_allocations():
    source=(JAVA/'app/flexygram/home/IosHomeSurface.java').read_text()
    draw=method(source,'protected void onDraw(Canvas canvas)')
    assert 'factory.create(this,BlurredBackgroundProviderImpl.topPanel(provider))' in draw
    assert 'if(glass==null)' in draw and 'checkBlurEnabled(account,provider)' in draw
    assert 'new ' not in draw and 'requestLayout' not in draw
    assert 'SharedConfig.chatBlurEnabled()' in draw
    dialog=(JAVA/'org/telegram/ui/DialogsActivity.java').read_text()
    assert 'child==iosHomeHeader)childTop=actionBar.getOccupyStatusBar()' in dialog
    assert 'filterTabsView.setSignatureHome(isSignatureHome() && !isIosHome())' in dialog


def test_new_home_resources_exist_in_all_localizations():
    keys={'FlexyHomeStyle','FlexyHomeIos','FlexyHomeChatDividers'}
    for locale in ['values','values-es','values-ru']:
        names={n.attrib.get('name') for n in ET.parse(ROOT/f'TMessagesProj/src/main/res/{locale}/flexy_home_style.xml').getroot()}
        assert keys<=names
    strings=set();drawables={p.stem for p in (ROOT/'TMessagesProj/src/main/res').glob('drawable*/*')}
    for p in (ROOT/'TMessagesProj/src/main/res/values').glob('*.xml'):
        strings.update(n.attrib.get('name') for n in ET.parse(p).getroot())
    for name in ['HomeStyleSettingsActivity','IosHomeHeader','IosHomeSearch','IosHomeSurface']:
        source=(JAVA/f'app/flexygram/home/{name}.java').read_text()
        assert set(re.findall(r'R.string.(\w+)',source))<=strings
        assert set(re.findall(r'R.drawable.(\w+)',source))<=drawables


def test_home_views_against_android_sdk_types():
    import os,shutil,subprocess,sys
    from pathlib import Path
    import pytest
    sdk=Path(os.environ.get('ANDROID_HOME',str(ROOT.parent/'.flexygram/android-sdk')))/'platforms/android-37.0/android.jar'
    core=Path(os.environ.get('FLEXY_CORE_JAR','/tmp/flexy-performance-libs/core.jar'))
    if not sdk.is_file() or not core.is_file() or not shutil.which('javac'):
        pytest.skip('Android API37, AndroidX Core and javac required')
    subprocess.run([sys.executable,str(ROOT/'tools/ios_home/check_types.py')],check=True,cwd=ROOT,capture_output=True,text=True)


def test_empty_edit_mode_cannot_dispatch_a_dialog_action(tmp_path):
    source=(JAVA/'org/telegram/ui/DialogsActivity.java').read_text()
    actual=method(source,'private void performSelectedDialogsAction(ArrayList<Long> selectedDialogs, int action, boolean alert, boolean longPress, HashSet<Long> dialogsIdsToRevoke)')
    # Execute the real entry guard with a host whose account/controller is not ready.
    guard=actual[:actual.index('        MessagesController.DialogFilter filter;')]
    probe(tmp_path,{'Probe.java':'''import java.util.*;public class Probe{
 int accesses;Object getParentActivity(){accesses++;return new Object();}
 GUARD accesses+=100;}
 public static void main(String[]a){Probe p=new Probe();p.performSelectedDialogsAction(new ArrayList<>(),1,true,false,null);
 if(p.accesses!=0)throw new AssertionError("empty selection reached native services");
 ArrayList<Long> ids=new ArrayList<>();ids.add(12L);p.performSelectedDialogsAction(ids,1,true,false,null);
 if(p.accesses!=101)throw new AssertionError("valid selection discarded");}
 }'''.replace('GUARD',guard)})
    counters=method(source,'private void updateCounters(boolean hide)')
    assert 'muteItem.setEnabled(count>0)' in counters
    assert 'if (count==0 || canDeleteCount != count' in counters
    assert 'if (count==0 || cantBlockCount != 0)' in counters
    assert 'if (count>0 && forumCount == 0' in counters
    # Select All remains in the enabled overflow; the close control is never disabled.
    assert 'setEnabled' not in method(source,'private void createActionMode(String tag)')
