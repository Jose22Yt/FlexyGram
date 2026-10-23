"""Executable production policy + targeted native-path/identity regressions."""
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from test_flexy_composer import method_bodies, ROOT, BASE, ENTER, CONTAINER

class SignatureCustom(unittest.TestCase):
    def test_production_policy_clamps_corrupt_preferences_and_safe_geometry(self):
        source = r"""
import app.flexygram.composer.*;
public class Policy {
 static void ok(boolean b){if(!b)throw new AssertionError("unsafe customization");}
 public static void main(String[] a){
  for(int raw=-1000;raw<=1000;raw++) {
   int y=ComposerStyle.position(raw);ok(y>=-4 && y<=16);
   ok(9+y>=5);ok(ComposerStyle.reserve(y)==Math.max(0,y));
   int level=ComposerStyle.level(raw);ok(level>=0 && level<=2);
   ok(ComposerStyle.diameter(raw)>=36 && ComposerStyle.diameter(raw)<=40);
   for(int g=-20;g<=20;g++) {
    int gap=ComposerStyle.gap(raw,g);ok(gap>=2 && gap<=8);
    ok(ComposerStyle.padding(raw)>=10);
    // 44dp hit slots never scale. Multiline native heights only lose visual inset.
    for(int h:new int[]{44,68,120,300}) {
     ok(h-2*ComposerStyle.inset(raw)>=36);
     ok(ComposerGeometry.TOUCH_SLOT==44);
    }
   }
  }
  ok(ComposerStyle.position(0)==0 && ComposerStyle.inset(0)==2 && ComposerStyle.gap(0,0)==6);
  System.out.print("PASS production geometry policy");
 }
}
"""
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'Policy.java';p.write_text(source)
            package=ROOT/'TMessagesProj/src/main/java/app/flexygram/composer'
            subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(package/'ComposerStyle.java'),str(package/'ComposerGeometry.java'),str(p)],check=True)
            self.assertIn('PASS',subprocess.check_output(['java','-cp',tmp,'Policy'],text=True))

    def test_one_parent_offset_and_native_insets_keyboard_translation_preserved(self):
        old=subprocess.check_output(['git','show',BASE+':'+CONTAINER],cwd=ROOT,text=True)
        now=(ROOT/CONTAINER).read_text()
        actual=method_bodies(now,'checkViewsPositions')[0]
        native=method_bodies(old,'checkViewsPositions')[0]
        self.assertEqual(actual.replace('\n            - (flexyComposer == null ? 0 : flexyComposer.getFlexyVerticalOffset())',''),native)
        for n in ('checkInsets','checkInAppKeyboardChild','checkInAppKeyboardViewHeight','setInputBubbleHeight'):
            self.assertEqual(method_bodies(old,n),method_bodies(now,n))
        enter=(ROOT/ENTER).read_text()
        reserve=method_bodies(enter,'calculateIslandTotalHeight')[0]
        self.assertIn('+ Math.max(0, getFlexyVerticalOffset())',reserve)
        self.assertIn('onChangedIslandTotalHeight(newIslandTotalHeight)',enter)
        for token in ('setScaleX(', 'setScaleY(', 'setTranslationY('):
            self.assertNotIn(token,method_bodies(enter,'applyFlexyComposerPresentation')[0])

    def test_settings_are_live_local_bounded_and_resettable(self):
        base=ROOT/'TMessagesProj/src/main/java/app/flexygram/composer'
        config=(base/'FlexyComposerConfig.java').read_text();ui=(base/'FlexyComposerSettingsActivity.java').read_text()
        for key in ('POSITION','LEVEL','GAP'):
            self.assertIn('ComposerStyle.',config)
            self.assertIn('FlexyComposerConfig.'+key,(ROOT/ENTER).read_text())
            self.assertIn('.remove('+key+')',config)
        for method in ('setPosition(value)','setGap(value)','setLevel(which)','setGlass(','reset()'):
            self.assertIn('FlexyComposerConfig.'+method,ui)
        self.assertIn('if (binding || !user) return',ui)
        self.assertIn('preview.invalidate()',ui)
        for forbidden in ('rebuildFragments','setScaleX','setScaleY','ObjectAnimator','ValueAnimator'):
            self.assertNotIn(forbidden,ui)

    def test_official_art_identity_and_original_launcher_alias(self):
        res=ROOT/'TMessagesProj/src/connectedAlpha/res';a='{http://schemas.android.com/apk/res/android}'
        for name in ('ic_launcher_exteraless','ic_launcher_exteraless_round'):
            x=ET.parse(res/'mipmap-anydpi-v26'/f'{name}.xml').getroot()
            self.assertEqual(x.tag,'adaptive-icon')
            for layer in ('background','foreground','monochrome'):self.assertIsNotNone(x.find(layer).get(a+'drawable'))
            for density in ('mdpi','hdpi','xhdpi','xxhdpi','xxxhdpi'):self.assertTrue((res/f'mipmap-{density}'/f'{name}.png').is_file())
        manifest=(ROOT/'TMessagesProj/src/main/AndroidManifest.xml').read_text()
        self.assertIn('org.telegram.messenger.ExteralessIcon',manifest)
        self.assertIn('def verCode = 1264',(ROOT/'TMessagesProj/build.gradle').read_text())
        self.assertIn('--expected-version-code 1264',(ROOT/'.github/workflows/connected-alpha-arm64.yml').read_text())
        self.assertIn('R.string.FlexyBrandName',(ROOT/'TMessagesProj/src/main/java/tw/nekomimi/nekogram/helpers/TypefaceHelper.java').read_text())

if __name__=='__main__':unittest.main()
