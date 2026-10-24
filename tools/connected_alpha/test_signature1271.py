"""Live1271 scope, native launcher transitions, icon resources and settings preservation."""
import re,subprocess,tempfile,unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from release_1271_contract import BASE,PATHS
ROOT=Path(__file__).resolve().parents[2]
JAVA=ROOT/'TMessagesProj/src/main/java'
A='{http://schemas.android.com/apk/res/android}'
def old(path):return subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT,text=True)
class Signature1271(unittest.TestCase):
 def test_release_scope_and_frozen_working_composer_home_and_native_core(self):
  changed=set(subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines())
  changed.update(p for p in subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines() if not p.startswith("TMessagesProj/jni/"))
  self.assertFalse(changed-PATHS,changed-PATHS)
  for path in ['app/flexygram/composer','app/flexygram/home','org/telegram/ui/Components/ChatActivityEnterView.java','org/telegram/ui/ActionBar/ActionBarLayout.java','org/telegram/ui/LoginActivity.java','org/telegram/tgnet','org/telegram/messenger/MessagesController.java','org/telegram/messenger/SendMessagesHelper.java','org/telegram/messenger/MediaController.java']:
   self.assertEqual(subprocess.check_output(['git','diff',BASE,'--','TMessagesProj/src/main/java/'+path],cwd=ROOT),b'',path)
  self.assertEqual(subprocess.check_output(['git','diff',BASE,'--','TMessagesProj/jni','TMessagesProj/chaquopy'],cwd=ROOT),b'')
  self.assertIn('def verCode = 1271',(ROOT/'TMessagesProj/build.gradle').read_text())
  workflow=(ROOT/'.github/workflows/connected-alpha-arm64.yml').read_text()
  for s in ['--expected-version-code 1271','FlexyGram-Alpha1271-ARM64.tar.age','FlexyGram-Alpha1271-Encrypted',':TMessagesProj:assembleConnectedAlpha']:self.assertIn(s,workflow)
 def test_one_fill_control_no_wallpaper_callback_or_graphics_allocations_in_drawing(self):
  settings=(JAVA/'app/flexygram/bubbles/BubbleSettingsActivity.java').read_text()
  self.assertEqual(re.findall(r'= addRow\("(flexyBubble\w+)"',settings),['flexyBubbleTransparency'])
  self.assertIn('seek.setMax(100)',settings)
  for s in ['setGlass(','setBorder(','setEdges(','recreate(']:self.assertNotIn(s,settings)
  drawable=(JAVA/'org/telegram/ui/ActionBar/MessageDrawable.java').read_text()
  draw=drawable[drawable.index('public void draw(Canvas canvas, Paint paintToUse)'):drawable.index('public Path makePath()')]
  for s in ['flexyGlassSource.draw','new Bitmap','new Paint','new Path','new Shader','saveLayer']:self.assertNotIn(s,draw)
  shared=(JAVA/'org/telegram/messenger/SharedConfig.java').read_text()
  self.assertIn('BubbleStyle.effectiveRadius(BuildConfig.CONNECTED_ALPHA, bubbleRadius)',shared)
  self.assertNotIn('putInt("bubbleRadius", 20)',shared)
  config=(JAVA/'app/flexygram/bubbles/BubbleConfig.java').read_text()
  self.assertEqual(config,old('TMessagesProj/src/main/java/app/flexygram/bubbles/BubbleConfig.java'))
 def test_setting_slider_changes_are_skin_only_and_leave_native_media_sliders_untouched(self):
  for path in ['app/exteraless/appearance/AvatarCornersSeekBar.java','app/exteraless/appearance/AltSeekbar.java','tw/nekomimi/nekogram/settings/NekoChatSettingsActivity.java','tw/nekomimi/nekogram/settings/NekoTranslatorSettingsActivity.java']:
   current=(JAVA/path).read_text().replace('new app.flexygram.settings.FlexySignatureSeekBarView(', 'new SeekBarView(')
   self.assertEqual(current,old('TMessagesProj/src/main/java/'+path),path)
  path='TMessagesProj/src/main/java/org/telegram/ui/Components/SeekBarView.java'
  self.assertEqual((ROOT/path).read_text(),old(path))
  self.assertEqual((JAVA/'org/telegram/ui/ThemeActivity.java').read_text().count('? new app.flexygram.settings.FlexySignatureSeekBarView(context) : new SeekBarView(context)'),2)
  source=(JAVA/'app/exteraless/settings/OpenExteraChatsActivity.java').read_text()
  hub=source.split('private void updateSignatureHubRows()')[1].split('private void updateStickerRows()')[0]
  self.assertEqual(re.findall(r'(\w+Row) = addRow',hub),['flexyBubblesRow','composerSettingsRow','signatureMessagesRow','signatureThemeRow','signatureStickersRow','chatSettingsRow','linksDividerRow'])
  self.assertEqual(source.count('chatSettingsRow = addRow('),1)
  self.assertIn('SignatureChatThemeActivity()',source);self.assertIn('THEME_TYPE_BASIC',source)
  theme=(JAVA/'app/flexygram/settings/SignatureChatThemeActivity.java').read_text()
  self.assertIn('THEME_TYPE_THEMES_BROWSER',theme);self.assertIn('WallpapersListActivity.TYPE_ALL',theme)
  self.assertIn('return 29400',source);self.assertIn('return 29500',source)
 def test_launcher_resource_identity_and_all_legacy_aliases_preserved(self):
  manifest=ET.parse(ROOT/'TMessagesProj/src/main/AndroidManifest.xml').getroot();app=manifest.find('application')
  self.assertEqual(app.get(A+'icon'),'@mipmap/ic_flexy_blue')
  aliases=app.findall('activity-alias');previous=ET.fromstring(old('TMessagesProj/src/main/AndroidManifest.xml')).find('application').findall('activity-alias')
  self.assertTrue({x.get(A+'name') for x in previous}<={x.get(A+'name') for x in aliases})
  launchers=[x for x in aliases if x.find("intent-filter/category[@"+A+"name='android.intent.category.LAUNCHER']") is not None]
  self.assertEqual([x.get(A+'name') for x in launchers if x.get(A+'enabled')=='true'],['org.telegram.messenger.ExteralessIcon'])
  for name in ['blue','green','coral','mono','blueprint','nya','quack','go']:
   for suffix in ['','_round']:
    for density in ['mdpi','hdpi','xhdpi','xxhdpi','xxxhdpi']:self.assertTrue((ROOT/f'TMessagesProj/src/main/res/mipmap-{density}/ic_flexy_{name}{suffix}.png').is_file())
    for version in [26,33]:
     icon=ET.parse(ROOT/f'TMessagesProj/src/main/res/mipmap-anydpi-v{version}/ic_flexy_{name}{suffix}.xml').getroot()
     self.assertEqual(icon.tag,'adaptive-icon')
     if version==33:self.assertIsNotNone(icon.find('monochrome'))
  self.assertEqual('io.github.jose22yt.flexygram.alpha',re.search(r'^APP_PACKAGE=(.+)$',(ROOT/'gradle.properties').read_text(),re.M)[1])
 def test_new_settings_resource_identifiers_exist(self):
  resources=set()
  for file in (ROOT/'TMessagesProj/src/main/res/values').glob('*.xml'):
   for element in ET.parse(file).getroot():
    if element.tag=='string':resources.add(element.get('name'))
  for name in ['app/flexygram/settings/SignatureChatThemeActivity.java','org/telegram/ui/LauncherIconController.java','app/exteraless/appicons/AppIconsActivity.java']:
   for key in re.findall(r'R\.string\.(\w+)',(JAVA/name).read_text()):self.assertIn(key,resources,name+': '+key)
 def test_actual_launcher_batch_and_legacy_update_persistence(self):
  source=(JAVA/'org/telegram/ui/LauncherIconController.java').read_text()
  resources={kind:set(re.findall(r'R\.'+kind+r'\.(\w+)',source)) for kind in ['drawable','mipmap','string']}
  files={
   'org/telegram/ui/LauncherIconController.java':source,
   'org/telegram/messenger/R.java':'package org.telegram.messenger; public class R {'+''.join('public static class '+k+'{'+''.join('public static int '+n+';' for n in v)+'}' for k,v in resources.items())+'}',
   'android/os/Build.java':'package android.os;public class Build {public static class VERSION{public static int SDK_INT=37;}}',
   'android/content/ComponentName.java':'package android.content;public class ComponentName{public final String key;public ComponentName(String p,String k){key=k;}}',
   'android/content/SharedPreferences.java':'package android.content;public class SharedPreferences{String selected="";public String getString(String k,String d){return selected.isEmpty()?d:selected;}public SharedPreferences edit(){return this;}public SharedPreferences putString(String k,String v){selected=v;return this;}public void apply(){}}',
   'android/content/Context.java':'package android.content;public class Context {public static final int MODE_PRIVATE=0;public final android.content.pm.PackageManager pm=new android.content.pm.PackageManager();final SharedPreferences prefs=new SharedPreferences();public String getPackageName(){return "io.github.jose22yt.flexygram.alpha";}public android.content.pm.PackageManager getPackageManager(){return pm;}public SharedPreferences getSharedPreferences(String n,int m){return prefs;}}',
   'android/content/pm/PackageManager.java':'''package android.content.pm;import android.content.ComponentName;import java.util.*;
public class PackageManager{public static final int COMPONENT_ENABLED_STATE_DEFAULT=0,COMPONENT_ENABLED_STATE_ENABLED=1,COMPONENT_ENABLED_STATE_DISABLED=2,DONT_KILL_APP=1;public HashMap<String,Integer> states=new HashMap<>();public boolean fail;public int batches,minEnabled=999;
public int getComponentEnabledSetting(ComponentName c){return states.getOrDefault(c.key,0);}public static class ComponentEnabledSetting{final ComponentName c;final int s;public ComponentEnabledSetting(ComponentName c,int s,int flags){this.c=c;this.s=s;if(flags!=DONT_KILL_APP)throw new AssertionError();}}
public void setComponentEnabledSettings(List<ComponentEnabledSetting> changes){if(fail)throw new SecurityException();batches++;for(ComponentEnabledSetting s:changes)states.put(s.c.key,s.s);}
public void setComponentEnabledSetting(ComponentName c,int s,int flags){states.put(c.key,s);int n=0;for(int x:states.values())if(x==1)n++;minEnabled=Math.min(n,minEnabled);}}
''',
   'org/telegram/messenger/ApplicationLoader.java':'package org.telegram.messenger;public class ApplicationLoader {public static android.content.Context applicationContext=new android.content.Context();}',
   'LauncherRegression.java':'''import org.telegram.ui.LauncherIconController;import org.telegram.ui.LauncherIconController.LauncherIcon;import org.telegram.messenger.ApplicationLoader;
public class LauncherRegression{static void check(boolean v){if(!v)throw new AssertionError();}static int count(){int n=0;for(LauncherIcon i:LauncherIcon.values())if(LauncherIconController.isEnabled(i))n++;return n;}public static void main(String[]args){
check(count()==1);check(LauncherIconController.isEnabled(LauncherIcon.EXTERALESS));
for(int sdk:new int[]{32,37}){android.os.Build.VERSION.SDK_INT=sdk;for(LauncherIcon i:LauncherIcon.values()){LauncherIconController.setIcon(i);check(count()==1);check(LauncherIconController.isEnabled(i));LauncherIconController.tryFixLauncherIconIfNeeded();check(LauncherIconController.isEnabled(i));}}
check(ApplicationLoader.applicationContext.pm.minEnabled>=1);check(ApplicationLoader.applicationContext.pm.batches>0);
android.os.Build.VERSION.SDK_INT=37;LauncherIconController.setIcon(LauncherIcon.FLEX_GREEN);ApplicationLoader.applicationContext.pm.fail=true;try{LauncherIconController.setIcon(LauncherIcon.FLEX_CORAL);throw new AssertionError();}catch(SecurityException expected){}check(count()==1);check(LauncherIconController.isEnabled(LauncherIcon.FLEX_GREEN));ApplicationLoader.applicationContext.pm.fail=false;
for(LauncherIcon i:LauncherIcon.values())ApplicationLoader.applicationContext.pm.states.put(i.getComponentName(ApplicationLoader.applicationContext).key,2);LauncherIconController.tryFixLauncherIconIfNeeded();check(count()==1);check(LauncherIconController.isEnabled(LauncherIcon.FLEX_GREEN));}}
'''}
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   for n,s in files.items():p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
   subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',d,*map(str,root.rglob('*.java'))],check=True)
   subprocess.run(['java','-cp',d,'LauncherRegression'],check=True)
