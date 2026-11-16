"""Native trial profile: real feature gates, Android identity and original source routes.
These tests do not establish performance on a physical phone.
"""
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
from test_render_work_reuse import JAVA, ROOT, probe
from test_composer_layout import method

NATIVE = 'package org.telegram.messenger;public final class BuildConfig{public static final boolean CONNECTED_ALPHA=true,NATIVE_BASELINE_TEST=true;}'


def test_native_bubble_and_delete_policy_never_reads_old_preferences(tmp_path):
    interaction=(JAVA/'app/flexygram/bubbles/interaction/BubbleInteractionSettings.java').read_text()
    deletion=(JAVA/'app/flexygram/bubbles/deletion/DeleteMotionSettings.java').read_text()
    style=method(interaction,'public static int style(Context context)')
    get=method(deletion,'public static int get(Context context)')
    allowed=method(deletion,'public static boolean effectsAllowed()')
    probe(tmp_path,{
        'org/telegram/messenger/BuildConfig.java':NATIVE,
        'org/telegram/messenger/SharedConfig.java':'package org.telegram.messenger;public class SharedConfig{public static boolean animationsEnabled(){throw new AssertionError("native delete did custom effect work");}}',
        'org/telegram/messenger/AndroidUtilities.java':'package org.telegram.messenger;public class AndroidUtilities{public static boolean isAccessibilityScreenReaderEnabled(){return false;}}',
        'org/telegram/messenger/LiteMode.java':'package org.telegram.messenger;public class LiteMode{public static boolean isPowerSaverApplied(){return false;}}',
        'Probe.java':'''public class Probe{
 static class Context{static final int MODE_PRIVATE=0;Context getApplicationContext(){return this;}SharedPreferences getSharedPreferences(String f,int m){throw new AssertionError("old preferences read");}}
 static class SharedPreferences{boolean contains(String k){return false;}int getInt(String k,int d){return 4;}boolean getBoolean(String k,boolean d){return true;}}
 static class Interaction{static final int STYLE_DEFAULT=0,STYLE_SIGNATURE=1;static int cachedStyle=1;static final String STYLE_KEY="style";static SharedPreferences prefs(Context c){throw new AssertionError("prefs");}STYLE}
 static class Deletion{static final int DEFAULT=0;static final String FILE="old",KEY="style";static int sanitize(int i){return i;}GET ALLOWED}
 public static void main(String[]args){for(int i=0;i<10000;i++)if(Interaction.style(new Context())!=0||Deletion.get(new Context())!=0||Deletion.effectsAllowed())throw new AssertionError();}
}'''.replace('STYLE}',style+'}').replace('GET ALLOWED',get+'\n'+allowed)})


def test_native_clean_bubbles_cache_only_shape_and_reject_effects(tmp_path):
    probe(tmp_path,{
        'org/telegram/messenger/BuildConfig.java':NATIVE,
        'android/content/Context.java':'''package android.content;public class Context{public static final int MODE_PRIVATE=0;public SharedPreferences getSharedPreferences(String f,int m){return p;}public static int reads,writes,stored;public static final SharedPreferences p=new SharedPreferences(){public int getInt(String k,int d){if(!k.equals("shape"))throw new AssertionError("effect preference read");reads++;return stored;}public boolean getBoolean(String k,boolean d){throw new AssertionError("effect preference read");}public Editor edit(){return new Editor(){public Editor putInt(String k,int v){if(!k.equals("shape"))throw new AssertionError("effect written");stored=v;writes++;return this;}public Editor putBoolean(String k,boolean v){throw new AssertionError("effect written");}public Editor remove(String k){throw new AssertionError();}public void apply(){}};}};}''',
        'android/content/SharedPreferences.java':'''package android.content;public interface SharedPreferences{int getInt(String k,int d);boolean getBoolean(String k,boolean d);Editor edit();interface Editor{Editor putInt(String k,int v);Editor putBoolean(String k,boolean v);Editor remove(String k);void apply();}}''',
        'org/telegram/messenger/ApplicationLoader.java':'package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext=new android.content.Context();}',
        'Probe.java':'''import app.flexygram.bubbles.*;import android.content.Context;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}
static void clean(){check(BubbleConfig.surfaceEffect()==BubbleConfig.DEFAULT&&!BubbleConfig.backgroundBlur()&&!BubbleConfig.outlineEnabled()&&BubbleConfig.transparency()==0&&!BubbleStyle.signature()&&!BubbleConfig.glass()&&!BubbleConfig.border()&&!BubbleConfig.edges()&&!BubbleConfig.smallTimestamps()&&BubbleConfig.fusionMode()==0);}
public static void main(String[]args){
 BubbleConfig.load();check(Context.reads==1&&BubbleConfig.shape()==0);
 for(int shape=0;shape<3;shape++){
  BubbleConfig.setShape(shape);BubbleConfig.reload();check(BubbleConfig.shape()==shape);
  check(BubbleStyle.customShape()==(shape!=0)&&BubbleStyle.flexyShape()==(shape==1));
  int reads=Context.reads,writes=Context.writes;
  for(int i=0;i<10000;i++){BubbleConfig.load();clean();BubbleConfig.shape();BubbleStyle.customShape();}
  check(Context.reads==reads&&Context.writes==writes);
  BubbleConfig.setShape(shape);check(Context.writes==writes);
  BubbleConfig.setSurfaceEffect(0);BubbleConfig.setSmallTimestamps(true);BubbleConfig.setBackgroundBlur(true);BubbleConfig.setOutlineEnabled(true);BubbleConfig.setOutlineStyle(3);BubbleConfig.setBorderPosition(2);BubbleConfig.setBorderTenths(20);BubbleConfig.setPearlIntensity(100);BubbleConfig.setFusionMode(2);BubbleConfig.setFusionIntensity(100);BubbleConfig.setFusionAdapt(false);BubbleConfig.setFuseGlass(true);BubbleConfig.setGlass(true);BubbleConfig.setBorder(true);BubbleConfig.setEdges(true);BubbleConfig.setTransparency(80);
  clean();check(Context.reads==reads&&Context.writes==writes);
 }
 Context.stored=99;BubbleConfig.reload();check(BubbleConfig.shape()==0);clean();
 Context.stored=-1;BubbleConfig.reload();check(BubbleConfig.shape()==0);
}}'''
    },[JAVA/'app/flexygram/bubbles/BubbleConfig.java',JAVA/'app/flexygram/bubbles/BubbleStyle.java'])


def test_files_and_studio_recognition_cannot_activate_in_native_profile(tmp_path):
    files=(JAVA/'app/flexygram/files/FlexyFiles.java').read_text()
    studio=(JAVA/'app/flexygram/studio/FlexyStyleInstallHelper.java').read_text()
    probe(tmp_path,{'org/telegram/messenger/BuildConfig.java':NATIVE,
        'Probe.java':'''import java.util.Locale;public class Probe{
 static class Context{static final int MODE_PRIVATE=0;}
 static class ApplicationLoader{static Context applicationContext=new Context();}
 static class StudioSchema{static boolean filename(String s){throw new AssertionError("studio parser reached");}}
 ENABLED SUPPORTS RECOGNIZED
 public static void main(String[]args){for(String n:new String[]{null,"test.flexyGram","test.zip","test.plugin","a.txt"})if(enabled()||supports(n)||recognized(n))throw new AssertionError();}
}'''.replace('ENABLED',method(files,'public static boolean enabled()')).replace('SUPPORTS',method(files,'public static boolean supports(String name)')).replace('RECOGNIZED',method(studio,'public static boolean recognized(String name)')).replace('static final int MODE_PRIVATE=0;','static final int MODE_PRIVATE=0;Context getSharedPreferences(String s,int m){throw new AssertionError("files prefs");}boolean getBoolean(String k,boolean d){return true;}')})


def test_separate_app_and_no_studio_android_entry_points():
    props=(ROOT/'gradle.properties').read_text()
    assert 'APP_PACKAGE=com.flexygram.messenger.nativebaseline\n' in props
    manifest=ET.parse(ROOT/'TMessagesProj/src/main/AndroidManifest.xml').getroot()
    ns='{http://schemas.android.com/apk/res/android}'
    assert manifest.find('application').get(ns+'label')=='FlexyGram Native Test'
    for node in manifest.iter():
        assert 'app.flexygram.studio.' not in node.get(ns+'name','')
        assert 'application/vnd.flexygram.configuration' not in node.get(ns+'mimeType','')
        assert '.flexystudio' not in node.get(ns+'authorities','')
    assert manifest.find("uses-permission[@"+ns+"name='android.permission.INTERNET']") is not None
    app_id='com.flexygram.messenger.nativebaseline'
    for filename in ['auth.xml','sync_contacts.xml']:
        account=ET.parse(ROOT/'TMessagesProj/src/main/res/xml'/filename).getroot()
        assert account.get(ns+'accountType')==app_id
    for filename in ['auth_menu.xml','shortcuts.xml']:
        root=ET.parse(ROOT/'TMessagesProj/src/main/res/xml'/filename).getroot()
        for intent in root.iter('intent'):
            if intent.get(ns+'targetClass'): assert intent.get(ns+'targetPackage')==app_id



def test_animation_instrumentation_and_manual_shortening_are_removed():
    build=(ROOT/'TMessagesProj/build.gradle').read_text()
    assert "id 'app.flexygram.fast-motion'" not in build
    assert "buildConfigField 'boolean', 'NATIVE_BASELINE_TEST', 'true'" in build
    app=(JAVA/'org/telegram/messenger/ApplicationLoader.java').read_text()
    assert 'FastMotionConfig.load()' not in app
    for file in ['org/telegram/ui/Components/AnimatedFloat.java','org/telegram/ui/ActionBar/ActionBarLayout.java']:
        assert 'app.flexygram.animation.FastMotionTiming' not in (JAVA/file).read_text()
    # Keep the established debug signing method; do not add a keystore generator.
    assert 'signingConfig = signingConfigs.debug' in build
    assert 'keytool' not in (ROOT/'.github/workflows/ui-beta-debug.yml').read_text()


def test_navigation_and_player_use_the_upstream_routes():
    host=(JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
    assert 'LiquidNavigationConfig' not in host and 'SignatureMusic' not in host
    assert 'app.exteraless.player.baseline.PlayerMiniView' in host
    player=JAVA/'app/exteraless/player/baseline'
    assert len(list(player.glob('*.java'))) >= 15
    for p in player.glob('*.java'):
        text=p.read_text()
        assert 'app.flexygram' not in text and 'SignatureMusic' not in text
    context_bar=(JAVA/'org/telegram/ui/Components/FragmentContextView.java').read_text()
    assert 'new app.exteraless.player.PlayerBarView(' not in context_bar
    assert 'new app.exteraless.player.baseline.PlayerBarView(' in context_bar
    service=(JAVA/'org/telegram/messenger/MusicPlayerService.java').read_text()
    assert service.count('app.exteraless.player.baseline.PlayerSheet.onModesChanged();')==2
    native=(player/'Md3Player.java').read_text()
    assert 'return AppearanceConfig.md3Player();' in native
    assert 'return AppearanceConfig.md3MiniPlayer();' in native
    assert 'return new AudioPlayerAlert(context, resourcesProvider);' in native


def test_cached_chats_and_database_are_identical_to_the_backup():
    for path in ['org/telegram/messenger/MessagesStorage.java','org/telegram/messenger/MessagesController.java','org/telegram/messenger/DatabaseMigrationHelper.java']:
        original=subprocess.check_output(['git','show','9b305e3ee7ee16097576d60af07f6ed9f105de9c:TMessagesProj/src/main/java/'+path],cwd=ROOT)
        assert (JAVA/path).read_bytes()==original


def test_retired_navigation_never_loads_saved_preferences(tmp_path):
    source=(JAVA/'app/flexygram/navigation/LiquidNavigationConfig.java').read_text()
    methods='\n'.join(method(source,'public static boolean '+name+'()') for name in ['configured','isEnabled','isVisible'])
    probe(tmp_path, {'org/telegram/messenger/BuildConfig.java':NATIVE,
        'Probe.java':'''public class Probe{
 static boolean enabled=true;static void ensure(){throw new AssertionError("retired navigation preferences reached");}static int[]order(){throw new AssertionError();}
 METHODS
 public static void main(String[]args){if(configured()||isEnabled()||isVisible())throw new AssertionError("custom navigation reactivated");}
}'''.replace('METHODS',methods)})


def test_home_controls_cannot_draw_the_extra_glass_layer():
    source=(JAVA/'org/telegram/ui/DialogsActivity.java').read_text()
    assert 'boolean home = !org.telegram.messenger.BuildConfig.NATIVE_BASELINE_TEST && isSignatureHome()' in source
    assert 'if (!org.telegram.messenger.BuildConfig.NATIVE_BASELINE_TEST && isSignatureHome() && child == menu' in source
    assert 'signatureHomeGlassFactory = org.telegram.messenger.BuildConfig.NATIVE_BASELINE_TEST ? null :' in source


def test_custom_music_queue_actions_do_not_read_playback_state(tmp_path):
    body=method((JAVA/'app/exteraless/player/MusicQueueActions.java').read_text(),'public static boolean eligible(MessageObject item)')
    probe(tmp_path, {'org/telegram/messenger/BuildConfig.java':NATIVE,
        'Probe.java':'''public class Probe{
 static class MessageObject{boolean scheduled;int currentAccount;boolean isMusic(){throw new AssertionError("custom metadata work");}boolean isVoiceOnce(){return false;}boolean isRoundOnce(){return false;}}
 static class MediaController{static MediaController getInstance(){throw new AssertionError("custom playback work");}MessageObject getPlayingMessageObject(){return null;}}
 static class MusicQueueOrder{static boolean same(MessageObject a,MessageObject b){return false;}}
 BODY
 public static void main(String[]args){if(eligible(null)||eligible(new MessageObject()))throw new AssertionError();}
}'''.replace('BODY',body)})


def test_original_player_configuration_exports_cover_all_java_accesses():
    appearance=(ROOT/'TMessagesProj/src/main/kotlin/app/exteraless/appearance/AppearanceConfig.kt').read_text()
    fields=set(re.findall(r'@JvmField\s+val\s+(\w+)',appearance))
    functions=set(re.findall(r'@JvmStatic\s+fun\s+(\w+)',appearance))
    references=set()
    for p in (JAVA/'app/exteraless/player/baseline').glob('*.java'):
        references.update(re.findall(r'AppearanceConfig\.(\w+)',p.read_text()))
    assert not references-fields-functions, sorted(references-fields-functions)
    assert {'playerMiniTop','playerCoverStyle','playerControlsSize'} <= fields
    assert 'playerStyleItems' in functions


def test_original_player_resource_dependencies_have_default_definitions():
    res=ROOT/'TMessagesProj/src/main/res'
    known=set()
    for directory in res.iterdir():
        if not directory.is_dir(): continue
        kind=directory.name.split('-')[0]
        for p in directory.iterdir():
            if not p.is_file(): continue
            if kind!='values': known.add((kind,p.name.split('.')[0]))
            if p.suffix!='.xml': continue
            for node in ET.parse(p).getroot().iter():
                if directory.name=='values' and node.get('name'):
                    tag=node.get('type') if node.tag=='item' else node.tag
                    if tag in ['string-array','integer-array']: tag='array'
                    known.add((tag,node.get('name').replace('.','_')))
                for value in node.attrib.values():
                    for name in re.findall(r'@\+id/(\w+)',value): known.add(('id',name))
    references=set()
    for p in (JAVA/'app/exteraless/player/baseline').glob('*.java'):
        references.update(re.findall(r'(?<!android\.)\bR\.(\w+)\.(\w+)',p.read_text()))
    assert not references-known, sorted(references-known)
    base=ET.parse(res/'values/native_player_original.xml').getroot()
    spanish=ET.parse(res/'values-es/native_player_original.xml').getroot()
    assert {n.get('name') for n in base}=={n.get('name') for n in spanish}
    assert all(n.text and n.text.strip() for n in [*base,*spanish])
