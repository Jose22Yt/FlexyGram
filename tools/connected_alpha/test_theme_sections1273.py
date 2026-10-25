"""Execute actual native ThemeActivity row allocation; theme/account data are doubles."""
import re,subprocess,tempfile,unittest
from pathlib import Path
from test_preview_input1273 import body
from next_alpha_contract import ROOT,VISUAL_BASE
PATH='TMessagesProj/src/main/java/org/telegram/ui/ThemeActivity.java'

def basic(source):
 s=body(source,'} else if (currentType == THEME_TYPE_BASIC) {')
 return s[s.index('{')+1:-1]

def runner(original,candidate):
 fields=sorted(set(re.findall(r'(\w+)\s*=\s*rowCount\+\+',original+candidate)))
 declarations=';'.join('int '+name+'=-1'for name in fields)+';'
 native='''
 static class Build {static class VERSION {static int SDK_INT=37;}static class VERSION_CODES {static final int S=31;}}
 static class Theme {static class ThemeAccent {int id=101;}static class ThemeInfo {java.util.List<Integer> themeAccents=java.util.List.of(1);ThemeAccent getAccent(boolean b){return new ThemeAccent();}boolean hasAccentColors(){return true;}}static ThemeInfo getCurrentTheme(){return new ThemeInfo();}}
 static class SharedConfig {static boolean raiseToListen;}
 static class TL_account {static class contentSettings {boolean sensitive_can_change;}}
 static class Controller {TL_account.contentSettings settings=new TL_account.contentSettings();TL_account.contentSettings getContentSettings(){return settings;}}
 static class ThemesList {void setDrawDivider(boolean b){}}
 Controller controller=new Controller(); Controller getMessagesController(){return controller;}
 ThemesList themesHorizontalListCell;boolean hasThemeAccents;int rowCount,signatureChatSection;
'''
 return '''import java.util.*;public class ThemeRowsProbe {
 static class Rows {FIELDS NATIVE void old(){ORIGINAL}void next(){CANDIDATE}
 Map<String,Integer> values()throws Exception{Map<String,Integer> out=new TreeMap<>();MAPreturn out;}}
 static void check(boolean b,String why){if(!b)throw new AssertionError(why);}
 public static void main(String[]args)throws Exception{
  for(boolean alpha:new boolean[]{false,true})for(boolean raise:new boolean[]{false,true})for(boolean sensitive:new boolean[]{false,true}){
   org.telegram.messenger.BuildConfig.CONNECTED_ALPHA=alpha;Rows.SharedConfig.raiseToListen=raise;
   Rows old=new Rows(),legacy=new Rows();old.controller.settings.sensitive_can_change=sensitive;legacy.controller.settings.sensitive_can_change=sensitive;old.old();legacy.next();
   check(old.values().equals(legacy.values()),"legacy rows/indices changed");
   if(alpha){Rows classic=new Rows(),theme=new Rows();classic.controller.settings.sensitive_can_change=sensitive;theme.controller.settings.sensitive_can_change=sensitive;classic.signatureChatSection=1;theme.signatureChatSection=2;classic.next();theme.next();
    Set<String> all=new HashSet<>(classic.values().keySet());all.addAll(theme.values().keySet());check(all.containsAll(old.values().keySet()),"native feature row lost");
    for(String name:List.of("backgroundRow","changeUserColor","themeHeaderRow","themeListRow2","nightThemeRow")){check(!classic.values().containsKey(name),"duplicate classic theme control");check(theme.values().containsKey(name),"theme control unreachable");}
    for(String name:List.of("themePreviewRow","themeListRow","createNewThemeRow","editThemeRow","monetStyleRow"))check(theme.values().containsKey(name),"full native themes page incomplete: "+name);
    for(String name:List.of("textSizeRow","chatListRow","swipeGestureRow","browserRow","liteModeRow","stickersRow","sendByEnterRow","distanceRow"))check(classic.values().containsKey(name),"distinct classic function lost: "+name);
   }
  }
 }}'''.replace('MAP',''.join('if('+f+'>=0)out.put("'+f+'",'+f+');' for f in fields)).replace('FIELDS',declarations).replace('NATIVE',native).replace('ORIGINAL',original).replace('CANDIDATE',candidate)

class ThemeSections(unittest.TestCase):
 def test_actual_native_rows_partition_without_losing_preferences_or_legacy_order(self):
  old=subprocess.check_output(['git','show',VISUAL_BASE+':'+PATH],cwd=ROOT,text=True);new=(ROOT/PATH).read_text()
  with tempfile.TemporaryDirectory()as tmp:
   java=Path(tmp)/'ThemeRowsProbe.java';java.write_text(runner(basic(old),basic(new)))
   config=Path(tmp)/'org/telegram/messenger/BuildConfig.java';config.parent.mkdir(parents=True);config.write_text('package org.telegram.messenger;public class BuildConfig {public static boolean CONNECTED_ALPHA=true;}')
   subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(config),str(java)],check=True)
   subprocess.run(['java','-cp',tmp,'ThemeRowsProbe'],check=True)
 def test_native_click_handlers_are_byte_identical_to_checkpoint(self):
  old=subprocess.check_output(['git','show',VISUAL_BASE+':'+PATH],cwd=ROOT,text=True);new=(ROOT/PATH).read_text()
  self.assertEqual(body(old,'listView.setOnItemClickListener('),body(new,'listView.setOnItemClickListener('))
