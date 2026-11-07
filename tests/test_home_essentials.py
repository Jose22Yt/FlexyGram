"""Home presentation policies and native-folder integration without an APK."""
from test_render_work_reuse import JAVA,ROOT,probe
from test_composer_layout import method
import re,xml.etree.ElementTree as ET


def test_style_default_normalization_and_account_local_folder_pointers(tmp_path):
    probe(tmp_path,{
      'android/content/Context.java':'package android.content;public class Context{public static int MODE_PRIVATE=0;public android.content.SharedPreferences getSharedPreferences(String f,int m){return org.telegram.messenger.ApplicationLoader.preferences;}}',
      'android/content/SharedPreferences.java':'package android.content;public interface SharedPreferences{int getInt(String k,int d);Editor edit();interface Editor{Editor putInt(String k,int v);void apply();}}',
      'org/telegram/messenger/ApplicationLoader.java':'package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext=new android.content.Context();public static android.content.SharedPreferences preferences;}',
      'Probe.java':'''import app.flexygram.home.HomeStyleConfig;import android.content.*;public class Probe{
 static class Prefs implements SharedPreferences,SharedPreferences.Editor{
 java.util.Map<String,Integer> values=new java.util.HashMap<>();public int getInt(String k,int d){return values.getOrDefault(k,d);}public Editor edit(){return this;}public Editor putInt(String k,int v){values.put(k,v);return this;}public void apply(){}}
 public static void main(String[]args){Prefs p=new Prefs();org.telegram.messenger.ApplicationLoader.preferences=p;
 HomeStyleConfig.load();if(HomeStyleConfig.style()!=0||HomeStyleConfig.extraHeaderDp(false)!=0)throw new AssertionError();
 HomeStyleConfig.setStyle(1);HomeStyleConfig.load();if(HomeStyleConfig.style()!=1||HomeStyleConfig.extraHeaderDp(true)!=64)throw new AssertionError();
 HomeStyleConfig.favoriteFolder(0,4);HomeStyleConfig.favoriteFolder(1,9);HomeStyleConfig.setStyle(0);
 if(HomeStyleConfig.favoriteFolder(0)!=4||HomeStyleConfig.favoriteFolder(1)!=9||HomeStyleConfig.favoriteFolder(2)!=0)throw new AssertionError();
 HomeStyleConfig.favoriteFolder(0,1);if(HomeStyleConfig.favoriteFolder(0)!=4)throw new AssertionError();
 for(int n:new int[]{-1,2,Integer.MAX_VALUE}){HomeStyleConfig.setStyle(n);if(HomeStyleConfig.style()!=0)throw new AssertionError();}
 }}'''
    },[JAVA/'app/flexygram/home/HomeStyleConfig.java'])


def test_saved_projection_preserves_controller_order_and_reuses_snapshots(tmp_path):
    probe(tmp_path,{'Probe.java':'''import java.util.*;import app.flexygram.home.HomeDialogProjection;public class Probe{
 public static void main(String[]args){
 HomeDialogProjection<Long> filter=new HomeDialogProjection<>(id->id);
 ArrayList<Long> original=new ArrayList<>(Arrays.asList(9L,1L,8L));
 ArrayList<Long> projected=filter.without(original,1);
 if(!projected.equals(Arrays.asList(9L,8L))||!original.equals(Arrays.asList(9L,1L,8L)))throw new AssertionError();
 for(int i=0;i<20000;i++)if(filter.without(original,1)!=projected)throw new AssertionError();
 original.add(0,7L);filter.invalidate();
 if(!filter.without(original,1).equals(Arrays.asList(7L,9L,8L)))throw new AssertionError();
 if(!filter.without(original,9).equals(Arrays.asList(7L,1L,8L)))throw new AssertionError();
 ArrayList<Long> second=new ArrayList<>(Arrays.asList(1L,2L));
 if(!filter.without(second,9).equals(second))throw new AssertionError();
 if(filter.without(second,9)==second)throw new AssertionError("controller list must not be exposed for mutation");
 }}'''},[JAVA/'app/flexygram/home/HomeDialogProjection.java'])


def test_first_settings_row_has_no_preview_and_favorite_ids_are_not_portable():
    settings=(JAVA/'app/flexygram/settings/signature/SignatureDirectSettingsActivity.java').read_text()
    home=settings[settings.index('case "home":'):settings.index('case "universal":')]
    assert home.index('HomeStyleSettingsActivity')<home.index('SmartPreviewsSettingsActivity')
    selector=(JAVA/'app/flexygram/home/HomeStyleSettingsActivity.java').read_text()
    assert 'TYPE_SETTINGS' in selector and 'setItems(' in selector and 'Preview' not in selector
    catalog=(JAVA/'app/flexygram/studio/StudioClientCatalog.java').read_text()
    assert 'integer("flexygram_home","style",0)' in catalog
    assert 'favorite_folder_' not in catalog


def test_favorites_use_the_native_account_scoped_editor_and_existing_filter_list():
    source=(JAVA/'org/telegram/ui/DialogsActivity.java').read_text()
    click=method(source,'private void openEssentialsFavorites(')
    edit=method(source,'private void editEssentialsFavorites(')
    assert 'scrollToFolder(favorite.id)' in click and 'favorite.locked' in click
    assert 'FilterCreateActivity' not in click
    assert 'FilterCreateActivity.forAccount(account,favorite' in edit
    assert 'dialogFiltersLimitDefault' in edit and 'dialogFiltersLimitPremium' in edit
    native=(JAVA/'org/telegram/ui/FilterCreateActivity.java').read_text()
    ctor=method(native,'private FilterCreateActivity(MessagesController.DialogFilter dialogFilter, ArrayList<Long> alwaysShow,int account)')
    assert ctor.index('setCurrentAccount(account)')<ctor.index('getMessagesController()')
    save=method(native,'private void save(boolean progress, Runnable after)')
    assert save.index('onFilterSaved')>save.index('saveFilterToServer(')
    assert save.index('onFilterSaved')<save.index('postNotificationName(NotificationCenter.dialogFiltersUpdated)')


def test_header_uses_native_shared_glass_with_opaque_fallback_and_no_draw_allocations():
    source=(JAVA/'app/flexygram/home/EssentialsSearchHeader.java').read_text()
    draw=method(source,'protected void onDraw(Canvas canvas)')
    assert 'factory.create(this,BlurredBackgroundProviderImpl.topPanel(provider))' in draw
    assert 'if(glass==null)' in draw and 'checkBlurEnabled(account,provider)' in draw
    assert 'new ' not in draw and 'requestLayout' not in draw
    dialog=(JAVA/'org/telegram/ui/DialogsActivity.java').read_text()
    assert 'child==essentialsSearchHeader)childTop=actionBar.getOccupyStatusBar()' in dialog
    assert 'filterTabsView.setSignatureHome(isSignatureHome() && !isEssentialsHome())' in dialog


def test_new_home_resources_exist_in_all_localizations():
    keys={'FlexyHomeStyle','FlexyHomeEssentials','FlexyHomeFavorites','FlexyHomeFavoritesEmpty','FlexyHomeFavoritesHint'}
    for locale in ['values','values-es','values-ru']:
        names={n.attrib.get('name') for n in ET.parse(ROOT/f'TMessagesProj/src/main/res/{locale}/flexy_home_essentials.xml').getroot()}
        assert keys<=names
    strings=set();drawables={p.stem for p in (ROOT/'TMessagesProj/src/main/res').glob('drawable*/*')}
    for p in (ROOT/'TMessagesProj/src/main/res/values').glob('*.xml'):
        strings.update(n.attrib.get('name') for n in ET.parse(p).getroot())
    for name in ['HomeStyleSettingsActivity','EssentialsShortcuts','EssentialsSearchHeader']:
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
    subprocess.run([sys.executable,str(ROOT/'tools/home_essentials/check_types.py')],check=True,cwd=ROOT,capture_output=True,text=True)
