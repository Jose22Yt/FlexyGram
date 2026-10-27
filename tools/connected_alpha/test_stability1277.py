"""Execute corrected production decisions; no physical acceptance or latency claims."""
from motion_contract import restore_navigation
from pathlib import Path
import subprocess,tempfile,unittest
from test_flexy_composer import method_bodies
ROOT=Path(__file__).resolve().parents[2]
JAVA=ROOT/'TMessagesProj/src/main/java'
class Stability1277(unittest.TestCase):
 def run_java(self,body):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'Probe.java';p.write_text(body)
   r=subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(p)],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr)
   r=subprocess.run(['java','-cp',tmp,'Probe'],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr)
 def test_actual_night_target_handles_custom_missing_and_wrong_contrast_themes(self):
  s=(JAVA/'org/telegram/ui/DialogsActivity.java').read_text()
  body=s[s.index('                        final boolean toDark = !Theme.isCurrentThemeDark();'):s.index('                        Theme.turnOffAutoNight',s.index('final boolean toDark = !Theme.isCurrentThemeDark();'))]
  self.run_java('''import java.util.*;class Probe{
  static class Theme{static class ThemeInfo{boolean dark;ThemeInfo(boolean d){dark=d;}boolean isDark(){return dark;}}static boolean dark;static Map<String,ThemeInfo> all=new HashMap<>();static boolean isCurrentThemeDark(){return dark;}static ThemeInfo getTheme(String key){return all.get(key);}}
  boolean switchingTheme;Theme.ThemeInfo chosen;boolean target;
  void switchTheme(Theme.ThemeInfo t,boolean d){chosen=t;target=d;}
  void toggle(String dayThemeName,String nightThemeName){'''+body+'''}
  public static void main(String[]a){for(boolean dark:new boolean[]{false,true})for(String day:new String[]{"Blue","CustomDay","Missing","WrongDay"})for(String night:new String[]{"Dark Blue","CustomNight","Missing","WrongNight"}){
  Theme.all.clear();Theme.all.put("Blue",new Theme.ThemeInfo(false));Theme.all.put("Dark Blue",new Theme.ThemeInfo(true));Theme.all.put("CustomDay",new Theme.ThemeInfo(false));Theme.all.put("CustomNight",new Theme.ThemeInfo(true));Theme.all.put("WrongDay",new Theme.ThemeInfo(true));Theme.all.put("WrongNight",new Theme.ThemeInfo(false));Theme.dark=dark;Probe p=new Probe();p.switchingTheme=true;p.toggle(day,night);if(p.chosen==null||p.chosen.isDark()==dark||p.target==dark)throw new AssertionError();}
  Theme.all.clear();Probe p=new Probe();p.switchingTheme=true;p.toggle("missing","missing");if(p.chosen!=null||p.switchingTheme)throw new AssertionError();}}
  ''')
 def test_settings_selector_uses_the_same_global_contrast_and_preserves_preferences(self):
  s=(JAVA/'org/telegram/ui/ThemeActivity.java').read_text()
  a=s.index('} else if (id == day_night_switch)');b=s.index('int[] pos = new int[2];',a);body=s[a:b]
  self.assertIn('final boolean toDark = !Theme.isCurrentThemeDark();',body)
  self.assertNotIn('dayThemeName.equals(themeInfo.getKey())',body)
  self.assertIn('themeInfo.isDark() != toDark',body)
  self.assertNotIn('preferences.edit()',body)
 def test_drawer_selector_uses_global_contrast_and_validates_target_before_latching(self):
  s=(JAVA/'app/exteraless/drawer/DrawerContainer.java').read_text()
  body=method_bodies(s,'toggleTheme')[0]
  self.assertIn('final boolean toDark = !Theme.isCurrentThemeDark();',body)
  self.assertNotIn('dayThemeName.equals(activeTheme.getKey())',body)
  self.assertLess(body.index('themeInfo.isDark() != toDark'),body.index('DialogsActivity.switchingTheme = true;'))
 def test_height_target_guard_executes_actual_measure_code(self):
  s=(JAVA/'org/telegram/ui/Components/ChatActivityEnterView.java').read_text()
  start=s.index('                if (animatorInputFieldHeight.getToFactor() != height)')
  opening=s.index('{',start);depth=1;i=opening+1
  while depth:
   if s[i]=='{':depth+=1
   if s[i]=='}':depth-=1
   i+=1
  block=s[start:i]
  self.run_java('''class Probe{static class A{int factor=44,target=44,starts;int getToFactor(){return target;}int getFactor(){return factor;}void animateTo(int v){target=v;starts++;}void forceFactor(int v){factor=target=v;}}A animatorInputFieldHeight=new A();void measure(int height){'''+block+'''}public static void main(String[]args){Probe p=new Probe();for(int height:new int[]{44,66,88,110,132,154,176,154,132,110,88,66,44}){int n=p.animatorInputFieldHeight.starts;p.measure(height);int next=p.animatorInputFieldHeight.starts;for(int j=0;j<1000;j++)p.measure(height);if(p.animatorInputFieldHeight.starts!=next||next>n+1)throw new AssertionError();}}}''')
 def test_compact_width_is_independent_of_sender_animation(self):
  s=(JAVA/'org/telegram/ui/Components/ChatActivityEnterView.java').read_text()
  method=method_bodies(s,'flexyCompactTextEnd')[0]
  self.run_java('''class Probe{static class app{static class flexygram{static class composer{static class ComposerGeometry{static final int TEXT_END_SLOT=56;}}}}static int dp(int n){return n;}'''+method+'''public static void main(String[]a){Probe p=new Probe();for(int n=0;n<10000;n++)if(p.flexyCompactTextEnd()!=56)throw new AssertionError();}}''')
 def test_theme_engine_system_follow_auth_and_protocol_are_preserved(self):
  for p in ('org/telegram/ui/ActionBar/Theme.java','org/telegram/ui/LaunchActivity.java','org/telegram/ui/LoginActivity.java','org/telegram/ui/ActionBar/ActionBarLayout.java','org/telegram/tgnet/ConnectionsManager.java'):
   path='TMessagesProj/src/main/java/'+p
   self.assertEqual(restore_navigation(path,(ROOT/path).read_bytes()),subprocess.check_output(['git','show','38e677d60847e117ede1c25731f7b6c4fd2970e2:'+path],cwd=ROOT))

 def test_release1277_keeps_package_certificate_and_native_payload_requirements(self):
  from signature1278_contract import restore as restore1278
  gradle=restore1278('TMessagesProj/build.gradle',(ROOT/'TMessagesProj/build.gradle').read_bytes()).decode()
  self.assertIn('def verCode = 1277',gradle)
  before=subprocess.check_output(['git','show','38e677d60847e117ede1c25731f7b6c4fd2970e2:TMessagesProj/build.gradle'],cwd=ROOT,text=True)
  self.assertEqual(gradle.replace('def verCode = 1277','def verCode = 1276'),before)
  workflow=restore1278('.github/workflows/connected-alpha-arm64.yml',(ROOT/'.github/workflows/connected-alpha-arm64.yml').read_bytes()).decode()
  self.assertIn('--expected-version-code 1277',workflow)
  self.assertIn("data['elf_count'] != 96",workflow)
  self.assertIn('c8f04cad685ca5757d35b25ea4b0b4613c7399909948d821e6ada61f9fb12b2c',workflow)
