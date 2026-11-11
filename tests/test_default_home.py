"""Default home restoration and backward compatibility after removing iPhone home."""
from test_render_work_reuse import JAVA,ROOT,probe
from test_composer_layout import method
import xml.etree.ElementTree as ET


def test_retired_layout_preferences_migrate_without_touching_other_settings(tmp_path):
    probe(tmp_path,{
      'android/content/Context.java':'package android.content;public class Context{public static int MODE_PRIVATE=0;public android.content.SharedPreferences getSharedPreferences(String f,int m){return org.telegram.messenger.ApplicationLoader.preferences;}}',
      'android/content/SharedPreferences.java':'package android.content;public interface SharedPreferences{int getInt(String k,int d);Editor edit();interface Editor{Editor putInt(String k,int v);void apply();}}',
      'org/telegram/messenger/ApplicationLoader.java':'package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext=new android.content.Context();public static android.content.SharedPreferences preferences;}',
      'Probe.java':'''import app.flexygram.home.HomeStyleConfig;import android.content.*;public class Probe{
 static class Prefs implements SharedPreferences,SharedPreferences.Editor{
 int writes;java.util.Map<String,Integer> values=new java.util.HashMap<>();public int getInt(String k,int d){return values.getOrDefault(k,d);}public Editor edit(){writes++;return this;}public Editor putInt(String k,int v){values.put(k,v);return this;}public void apply(){}}
 public static void main(String[]args){Prefs p=new Prefs();org.telegram.messenger.ApplicationLoader.preferences=p;
 HomeStyleConfig.load();if(p.writes!=0)throw new AssertionError("fresh install wrote preferences");
 p.values.put("unrelated",77);
 for(int retired:new int[]{1,2,-1,Integer.MAX_VALUE}){
 p.values.put("style",retired);HomeStyleConfig.load();if(p.values.get("style")!=0||p.values.get("unrelated")!=77)throw new AssertionError();
 int writes=p.writes;HomeStyleConfig.load();if(p.writes!=writes)throw new AssertionError("migration repeated");
 }
 }}'''
    },[JAVA/'app/flexygram/home/HomeStyleConfig.java'])


def test_no_style_selector_or_iphone_home_routes_remain():
    native=(JAVA/'org/telegram/ui/DialogsActivity.java').read_text()
    assert 'isIosHome' not in native and 'iosHomeHeader' not in native
    assert 'filterTabsView.setSignatureHome(isSignatureHome())' in native
    assert 'return getControllerDialogsArray(' in method(native,'public ArrayList<TLRPC.Dialog> getDialogsArray(')
    settings=(JAVA/'app/flexygram/home/HomeListSettingsActivity.java').read_text()
    assert 'styleRow' not in settings and 'setItems(' not in settings and 'TYPE_SETTINGS' not in settings
    assert 'FlexyHomeChatDividers' in settings
    assert not (JAVA/'app/flexygram/home/IosHomeHeader.java').exists()
    registry=(JAVA/'app/flexygram/settings/signature/Settings3Registry.java').read_text()
    assert 'flexyHomeStyle' not in registry and 'HomeListSettingsActivity' in registry
    for locale in ['values','values-es','values-ru']:
        names={n.attrib.get('name') for n in ET.parse(ROOT/f'TMessagesProj/src/main/res/{locale}/flexy_home_list.xml').getroot()}
        assert names=={'FlexyHomeChatDividers'}
    rows=(JAVA/'org/telegram/ui/Cells/DialogCell.java').read_text()
    assert 'isIosHome' not in rows and 'useForceThreeLines = forceThreeLines;' in rows
    nav=(JAVA/'app/flexygram/navigation/LiquidNavigationConfig.java').read_text()
    assert 'HomeStyleConfig' not in nav and 'IOS_ORDER' not in nav
    # Original artwork and the pre-existing default home controls are retained.
    assert 'IosOriginalAssets.TAB_CHATS' in (JAVA/'org/telegram/ui/Components/glass/GlassTabView.java').read_text()
    assert 'drawSignatureHomeControl(canvas, searchItem)' in native


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


def test_home_list_settings_against_android_types():
    import os,shutil,subprocess,sys
    from pathlib import Path
    import pytest
    sdk=Path(os.environ.get('ANDROID_HOME',str(ROOT.parent/'.flexygram/android-sdk')))/'platforms/android-37.0/android.jar'
    core=Path(os.environ.get('FLEXY_CORE_JAR','/tmp/flexy-performance-libs/core.jar'))
    if not sdk.is_file() or not core.is_file() or not shutil.which('javac'):
        pytest.skip('Android API37, AndroidX Core and javac required')
    subprocess.run([sys.executable,str(ROOT/'tools/home_list/check_types.py')],check=True,cwd=ROOT,capture_output=True,text=True)
