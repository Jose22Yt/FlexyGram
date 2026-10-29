"""Destination persistence/layout policies and integration checks; Android touch is separate."""
from pathlib import Path
import subprocess, tempfile, unittest, xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2]
JAVA=ROOT/'TMessagesProj/src/main/java'
class LiquidNavigation(unittest.TestCase):
 def test_order_sanitization_and_narrow_window_overflow_keep_safe_destinations(self):
  code='''import app.flexygram.navigation.*;import java.util.*;public class DestinationProbe{static void ok(boolean x){if(!x)throw new AssertionError();}public static void main(String[]a){Random r=new Random(17);for(int n=0;n<20000;n++){int[] raw=new int[r.nextInt(18)];for(int i=0;i<raw.length;i++)raw[i]=r.nextInt(15)-3;int[] ids=LiquidNavigationDestinations.sanitize(raw);ok(ids.length>=2&&ids.length<=LiquidNavigationDestinations.COUNT);ok(LiquidNavigationDestinations.contains(ids,0));Set<Integer>s=new HashSet<>();for(int id:ids)ok(id>=0&&id<9&&s.add(id));ok(Arrays.equals(ids,LiquidNavigationDestinations.sanitize(ids)));for(int slots=2;slots<=LiquidNavigationDestinations.COUNT;slots++){int[] fit=LiquidNavigationDestinations.fit(ids,slots);ok(fit.length<=slots&&LiquidNavigationDestinations.contains(fit,0));for(int id:fit)ok(id==9||LiquidNavigationDestinations.contains(ids,id));if(ids.length>slots)ok(fit[fit.length-1]==9);}}}}'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'DestinationProbe.java';p.write_text(code)
   subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',d,str(JAVA/'app/flexygram/navigation/LiquidNavigationDestinations.java'),str(p)],check=True,capture_output=True)
   subprocess.run(['java','-cp',d,'DestinationProbe'],check=True,capture_output=True)
 def test_real_destinations_never_become_fictional_pager_positions(self):
  source=(JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
  self.assertIn('TABS_COUNT = 4',source)
  for token in ['DialogsActivity.DIALOGS_TYPE_GROUPS_ONLY','DialogsActivity.DIALOGS_TYPE_CHANNELS_ONLY','target=new ChatActivity(args)','new CallLogActivity(args)','new ContactsActivity(args)','new SettingsActivity(args)','new FeedActivity(args)','target.setCurrentAccount(currentAccount)','tabs[shown[i]].bringToFront()']:
   self.assertIn(token,source)
  start=source.index('private void applyFlexyTabs()');end=source.index('private void openFlexySettings()',start)
  self.assertNotIn('removeAllViews',source[start:end]);self.assertNotIn('dropFragment',source[start:end])
  self.assertIn('MainTabsUiHelper.applyTabsBottomInset(',source[start:end])
  self.assertIn('ViewCompat.requestApplyInsets(fragmentView)',source[start:end])
 def test_fully_visible_bar_is_enabled_at_the_native_terminal_factor(self):
  source=(JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
  self.assertIn('tabsView.setEnabled(factor >= .999f)',source)
  self.assertNotIn('tabsView.setEnabled(factor > 1)',source)
 def test_settings_preview_uses_the_actual_bar_and_native_reorder_list(self):
  preview=(JAVA/'app/flexygram/navigation/LiquidNavigationPreviewView.java').read_text()
  self.assertIn('new MainTabsLayout(',preview);self.assertIn('LiquidNavigationTabs.create(',preview)
  self.assertNotIn('onTouchEvent(',preview)
  editor=(JAVA/'app/flexygram/navigation/LiquidNavigationTabsActivity.java').read_text()
  for token in ['allowReorder(true)','listenReorder','LiquidNavigationConfig.order(ids)','preview.settingsChanged()']:
   self.assertIn(token,editor)
 def test_localized_configuration_labels_match(self):
  labels=[]
  for locale in ['values','values-es','values-ru']:
   root=ET.parse(ROOT/'TMessagesProj/src/main/res'/locale/'flexy_liquid_navigation.xml').getroot()
   keys=[x.get('name') for x in root];self.assertEqual(len(keys),len(set(keys)));labels.append(set(keys))
  self.assertEqual(labels[0],labels[1]);self.assertEqual(labels[0],labels[2])
