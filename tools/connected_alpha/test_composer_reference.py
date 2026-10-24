"""Executable artwork semantics and compact policy; not a device UI acceptance test."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from test_flexy_composer import ROOT, ENTER, method_bodies

BASE = ROOT/'TMessagesProj/src/main/java/app/flexygram/composer'
RES = ROOT/'TMessagesProj/src/main/res'
A = '{http://schemas.android.com/apk/res/android}'

class ReferenceComposer(unittest.TestCase):
    def test_production_artwork_follows_native_action_not_theme(self):
        icons = sorted(p.stem for p in (RES/'drawable').glob('flexy_composer_*.xml'))
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp); r=d/'org/telegram/messenger/R.java';r.parent.mkdir(parents=True)
            r.write_text('package org.telegram.messenger; public class R {public static class drawable {'+
                ''.join('public static final int '+name+'='+str(i+1)+';' for i,name in enumerate(icons))+'}}')
            test=d/'Reference.java';test.write_text('''
import app.flexygram.composer.*;
import org.telegram.messenger.R;
public class Reference {
 static void ok(boolean b) {if(!b) throw new AssertionError("artwork changed action/geometry");}
 // Opaque surfaces must retain WCAG contrast for hint/selector and external controls.
 static double linear(int c) {double s=c/255.;return s<=0.04045?s/12.92:Math.pow((s+0.055)/1.055,2.4);}
 static double lum(int c) {return .2126*linear((c>>16)&255)+.7152*linear((c>>8)&255)+.0722*linear(c&255);}
 static double contrast(int a,int b) {return (Math.max(lum(a),lum(b))+.05)/(Math.min(lum(a),lum(b))+.05);}
 public static void main(String[] args) {
  for(int i=0;i<10000;i++) {
   boolean reference=(i%2)==0;
   ok(ComposerIcons.resource("VOICE",-1,reference)==R.drawable.flexy_composer_voice);
   ok(ComposerIcons.resource("VIDEO",-1,reference)==R.drawable.flexy_composer_video);
   ok(ComposerIcons.resource("KEYBOARD",-1,reference)==R.drawable.flexy_composer_keyboard);
   ok(ComposerIcons.resource("STICKER",-1,reference)==R.drawable.flexy_composer_sticker);
   ok(ComposerIcons.resource("GIF",-10,reference)==-10);
   ok(ComposerIcons.resource("MENU",-20,reference)==-20);
   ok(ComposerIcons.resource("SMILE",-1,reference)==(reference?R.drawable.flexy_composer_folded:R.drawable.flexy_composer_smile));
   for(int level=0;level<3;level++) {
    ok(ComposerStyle.diameter(level)==36-2*level);
    // 24dp vector fits even the smallest surface, with four dp breathing room.
    ok((ComposerStyle.diameter(level)-24)/2>=4);
    ok(ComposerGeometry.TOUCH_SLOT==44);
   }
   for(boolean dark:new boolean[]{false,true}) {
    ok(contrast(ComposerStyle.innerIcon(dark),ComposerStyle.surface(dark,false))>=4.5);
    ok(contrast(ComposerStyle.icon(dark),ComposerStyle.surface(dark,false))>=7);
   }
   ok(ComposerStyle.surface(true,false)!=0xFF000000);
   ok((ComposerStyle.surface(true,true)>>>24)>=232);
   ok((ComposerStyle.surface(false,true)>>>24)>=232);
  }
 }
}''')
            subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(r),str(BASE/'ComposerIcons.java'),str(BASE/'ComposerStyle.java'),str(BASE/'ComposerGeometry.java'),str(test)],check=True)
            subprocess.run(['java','-cp',tmp,'Reference'],check=True)

    def test_vectors_are_original_consistent_and_not_external_font_glyphs(self):
        for p in (RES/'drawable').glob('flexy_composer_*.xml'):
            with self.subTest(icon=p.name):
                s=p.read_text(); x=ET.fromstring(s)
                self.assertIn('SPDX-License-Identifier: GPL-3.0-or-later',s)
                self.assertEqual(x.get(A+'width'),'24dp')
                self.assertEqual(x.get(A+'height'),'24dp')
                self.assertGreater(len(x.findall('path')),0)
                for path in x.findall('path'):
                    self.assertEqual(path.get(A+'strokeWidth'),'1.6')
                    self.assertEqual(path.get(A+'strokeLineCap'),'round')
                    self.assertEqual(path.get(A+'strokeLineJoin'),'round')
                    self.assertEqual(path.get(A+'fillColor'),'@android:color/transparent')

    def test_style_switch_preserves_semantics_and_special_send_resources(self):
        enter=(ROOT/ENTER).read_text()
        for path in ('org/telegram/ui/Components/ChatActivityEnterViewAnimatedIconView.java',
                     'app/exteraless/components/ChatActivityEnterViewStaticIconView.java'):
            text=(ROOT/'TMessagesProj/src/main/java'/path).read_text()
            body=method_bodies(text,'setCompactIcons')[0]
            self.assertIn('setState(currentState, false)',body)
            self.assertNotIn('State.VOICE',body)
            self.assertNotIn('State.VIDEO',body)
        resource=method_bodies(enter,'reloadCompactSendIcon')[0]
        self.assertIn('resId == R.drawable.send_plane_24',resource)
        self.assertIn('? R.drawable.flexy_composer_send : resId',resource)
        self.assertIn('drawableColor = 0',resource)
        config=(BASE/'FlexyComposerConfig.java').read_text()
        self.assertIn('.remove(ICONS)',config)
        self.assertIn('FlexyComposerConfig.ICONS.equals(key)',enter)

    def test_visible_gap_matches_setting_at_all_densities(self):
        # Execute production coordinate method in existing host fixture as well.
        enter=(ROOT/ENTER).read_text()
        self.assertIn('TOUCH_SLOT) - dp(flexyInsetDp), dp(flexyGapDp)',enter)
        self.assertIn('dp(flexyGapDp) - dp(flexyInsetDp), nativeAttachTranslationX()',enter)
        self.assertIn('+ flexyGapDp - flexyInsetDp + flexyTextPaddingDp',enter)
        for scale in (1,1.5,2,2.625,3,4):
            dp=lambda n:int(n*scale+0.5)
            for inset in (4,5,6):
                for gap in range(2,9):
                    attach_right=dp(44)-dp(inset)
                    pill_left=dp(44)-dp(inset)+dp(gap)
                    pill_right=dp(300)-dp(gap)+dp(inset)
                    action_left=dp(300)+dp(inset)
                    self.assertEqual(pill_left-attach_right,dp(gap))
                    self.assertEqual(action_left-pill_right,dp(gap))

if __name__=='__main__':unittest.main()
