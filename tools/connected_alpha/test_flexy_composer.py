"""Presentation and native-behaviour regression gates, never physical evidence."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from verify_apk import package_version_code

ROOT = Path(__file__).resolve().parents[2]
BASE = 'c4210911a048d4fde080c03c31aa98741336db2f'
ENTER = 'TMessagesProj/src/main/java/org/telegram/ui/Components/ChatActivityEnterView.java'
CONTAINER = 'TMessagesProj/src/main/java/org/telegram/ui/Components/chat/ChatInputViewsContainer.java'

def method_bodies(source, name):
    # Blank comments and literals while retaining positions for balanced braces.
    masked = re.sub(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
                    lambda m: ''.join('\n' if c == '\n' else ' ' for c in m[0]), source, flags=re.S)
    pattern = r'\b(?:public|private|protected)\s+(?:(?:static|final|synchronized)\s+)*[\w.<>\[\]?]+\s+' + re.escape(name) + r'\s*\([^;{}]*\)\s*\{'
    bodies = []
    for match in re.finditer(pattern, masked):
        pos, depth = match.end(), 1
        while depth:
            if masked[pos] == '{': depth += 1
            elif masked[pos] == '}': depth -= 1
            pos += 1
        bodies.append(source[match.start():pos])
    return bodies

class ComposerRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = subprocess.check_output(['git','show',BASE+':'+ENTER], cwd=ROOT, text=True)
        cls.current = (ROOT/ENTER).read_text()

    def test_native_keyboard_send_record_and_edit_implementations_are_unchanged(self):
        for name in ('onResume','showPopup','hidePopup','onSizeChanged','openKeyboardInternal',
                     'setStickersExpanded','updateRecordInterface','setEditingMessageObject',
                     'sendMessage','sendMessageInternal','processSendingText','checkSendButton',
                     'checkAttachButton','createEmojiView','drawBackground','setDialogId'):
            with self.subTest(method=name):
                before = method_bodies(self.original, name)
                # Names may legitimately not exist in this pinned upstream.
                if before: self.assertEqual(before, method_bodies(self.current, name))

    def test_all_native_measure_and_keyboard_height_bodies_are_preserved(self):
        current = self.current.replace('                applyFlexyComposerPresentation(MeasureSpec.getSize(widthMeasureSpec));\n','')
        for name in ('onMeasure', 'onWindowSizeChanged', 'resizeForTopView', 'checkStickresExpandHeight'):
            self.assertEqual(method_bodies(self.original, name), method_bodies(current, name), name)
        self.assertIn('public static final int DEFAULT_HEIGHT = 44;', self.current)
        self.assertIn('messageEditText.setTextSize(TypedValue.COMPLEX_UNIT_DIP, 18);', self.current)

    def test_native_insets_and_keyboard_container_remain_unchanged(self):
        old = subprocess.check_output(['git','show',BASE+':'+CONTAINER], cwd=ROOT, text=True)
        now = (ROOT/CONTAINER).read_text()
        for name in ('checkInsets','checkViewsPositions','checkInAppKeyboardChild','checkInAppKeyboardViewHeight','setInputBubbleHeight'):
            self.assertEqual(method_bodies(old,name),method_bodies(now,name),name)

    def test_glass_is_paint_only_and_uses_one_existing_backdrop(self):
        source = (ROOT/CONTAINER).read_text()
        draw = method_bodies(source,'drawFlexyCompactBackground')[0]
        self.assertEqual(draw.count('blurredBackgroundDrawable.draw(canvas)'),1)
        for forbidden in ('new ', 'requestLayout(', 'setLayoutParams(', 'setTranslation', 'ValueAnimator', 'ObjectAnimator'):
            self.assertNotIn(forbidden,draw)
        listener = source.split('flexyListener =',1)[1].split('};',1)[0]
        self.assertNotIn('requestLayout(',listener)
        self.assertIn('invalidate()',listener)

    def test_style_change_never_recreates_text_or_rebuilds_fragments(self):
        settings = (ROOT/'TMessagesProj/src/main/java/app/flexygram/composer/FlexyComposerSettingsActivity.java').read_text()
        self.assertNotIn('rebuildFragments',settings)
        self.assertNotIn('triggerRebirth',settings)
        presentation = method_bodies(self.current,'applyFlexyComposerPresentation')[0]
        for forbidden in ('new ', 'removeView(', 'addView(', 'setText(', 'setLayoutParams(', 'requestLayout('):
            self.assertNotIn(forbidden,presentation)
        self.assertIn('unregisterOnSharedPreferenceChangeListener(flexyComposerListener)',self.current)

    def test_geometry_actual_java_preserves_native_reservations_and_touch_slots(self):
        production = ROOT/'TMessagesProj/src/main/java/app/flexygram/composer/ComposerGeometry.java'
        test = '''
import app.flexygram.composer.ComposerGeometry;
public class GeometryRegression {
 public static void main(String[] args) {
  if (ComposerGeometry.TOUCH_SLOT != 44) throw new AssertionError("touch area reduced");
  for (int width=0;width<=1200;width++) {
   if (ComposerGeometry.supportsCompact(width,true)) throw new AssertionError("special controls hidden");
   if (width<280 && ComposerGeometry.supportsCompact(width,false)) throw new AssertionError("narrow overlap");
  }
  for (int nativeEnd=0;nativeEnd<400;nativeEnd++) for (int slot=50;slot<250;slot++) {
   if (ComposerGeometry.textEnd(nativeEnd,slot,false)!=nativeEnd) throw new AssertionError("classic changed");
   int end=ComposerGeometry.textEnd(nativeEnd,slot,true);
   if (end<nativeEnd || end<slot) throw new AssertionError("emoji/paid/bot overlap");
  }
  for (int h=44;h<500;h++) {
   if (ComposerGeometry.visualHeight(h,2)!=h-4) throw new AssertionError("visual height");
  }
  // Rapid style changes must return precisely to every native end reservation.
  for (int i=0;i<100000;i++) {
   int nativeEnd=i%193;
   ComposerGeometry.textEnd(nativeEnd,50,true);
   if (ComposerGeometry.textEnd(nativeEnd,50,false)!=nativeEnd) throw new AssertionError("toggle drift");
  }
  System.out.println("PASS: geometry invariants and 100000 rapid style toggles; not a frame benchmark");
 }
}'''
        with tempfile.TemporaryDirectory() as tmp:
            runner = Path(tmp)/'GeometryRegression.java'; runner.write_text(test)
            subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(production),str(runner)], check=True)
            output = subprocess.check_output(['java','-cp',tmp,'GeometryRegression'],text=True)
            self.assertIn('PASS:',output)

    def test_update_version_parser_rejects_missing_duplicate_and_malformed_versions(self):
        self.assertEqual(package_version_code("package: name='io.github.jose22yt.flexygram.alpha' versionCode='1262' versionName='alpha2'"),1262)
        for text in ("", "package: versionCode='0'", "package: versionCode='x'", "package: versionCode='1262' versionCode='1261'", "package: versionCode='1262'\npackage: versionCode='1261'"):
            with self.subTest(badging=text), self.assertRaises(ValueError): package_version_code(text)

    def test_actual_presentation_method_handles_native_three_dp_margin_and_live_recovery(self):
        methods = '\n'.join(method_bodies(self.current,n)[0] for n in (
            'applyFlexyComposerPresentation','updateAttachButtonTranslationX','nativeAttachTranslationX','flexyCompactTextEnd'))
        fixture = '''
public class PresentationRegression {
 static final int VISIBLE=0;
 static class Gravity { static final int LEFT=3, RIGHT=5, BOTTOM=80; }
 static class AndroidUtilities { static float density=1; }
 static int dp(float n){return Math.round(n);}
 static class MarginLayoutParams { int leftMargin=3,rightMargin=0,gravity; }
 static class FrameLayout { static class LayoutParams extends MarginLayoutParams {} }
 static class V {
  FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(); int visibility=8; Object tag;
  float translation,alpha=1; int width=44;
  FrameLayout.LayoutParams getLayoutParams(){return p;}
  int getVisibility(){return visibility;}
  Object getTag(){return tag;}
  void setTranslationX(float x){translation=x;}
  int width(){return width;}
  float getAlpha(){return alpha;}
 }
 boolean isChat=true,isStories=false,flexyCompactRequested,flexyCompactLayout;
 Object parentFragment=new Object();
 V senderSelectView=new V(),botCommandsMenuButton=new V(),botWebViewButton=new V(),aiButton=new V();
 V attachButton=new V(),emojiButton=new V(),deleteRichDraftButton=new V(),messageEditText=new V(),sendButton=new V();
 float attachLayoutPaddingTranslationX,attachLayoutTranslationX;
 int flexyNativeFieldRight=-1,flexyAppliedFieldRight=-1;
 static final int DEFAULT_HEIGHT=44;
 final String draft="unchanged draft with emoji and multiple lines";
 void nativeMeasure(){emojiButton.p.leftMargin=3;deleteRichDraftButton.p.leftMargin=3;messageEditText.p.leftMargin=50;}
 void nativeEnd(int end){flexyNativeFieldRight=end;messageEditText.p.rightMargin=end;flexyAppliedFieldRight=end;}
 void require(boolean b){if(!b)throw new AssertionError("presentation invariant");}
 __METHODS__
 public static void main(String[] a){
  PresentationRegression p=new PresentationRegression();
  p.attachButton.p.gravity=Gravity.BOTTOM|Gravity.RIGHT;
  p.emojiButton.p.gravity=Gravity.BOTTOM|Gravity.LEFT;
  V originalText=p.messageEditText;
  String originalDraft=p.draft;
  for(int i=0;i<10000;i++){
   int end=new int[]{2,4,50,98,146}[i%5];
   p.nativeEnd(end);p.nativeMeasure();p.flexyCompactRequested=true;
   p.sendButton.width=(i%2==0?44:100);
   p.applyFlexyComposerPresentation(335);
   p.require(p.flexyCompactLayout);
   p.require(p.attachButton.p.gravity==(Gravity.BOTTOM|Gravity.LEFT));
   p.require(p.emojiButton.p.gravity==(Gravity.BOTTOM|Gravity.RIGHT));
   p.require(p.messageEditText.p.leftMargin==54);
   p.require(p.messageEditText.p.rightMargin>=50+Math.max(0,-p.nativeAttachTranslationX()));
   p.require(p.messageEditText==originalText && p.draft==originalDraft);
   p.nativeMeasure();p.flexyCompactRequested=false;p.applyFlexyComposerPresentation(335);
   p.require(!p.flexyCompactLayout && p.messageEditText.p.rightMargin==end);
   p.require(p.messageEditText.p.leftMargin==50 && p.emojiButton.p.leftMargin==3 && p.emojiButton.p.rightMargin==0);
   p.require(p.attachButton.p.gravity==(Gravity.BOTTOM|Gravity.RIGHT));
  }
  p.nativeMeasure();p.flexyCompactRequested=true;p.applyFlexyComposerPresentation(335);
  p.botCommandsMenuButton.tag=new Object();p.emojiButton.p.leftMargin=80;p.messageEditText.p.leftMargin=120;
  p.applyFlexyComposerPresentation(335);
  p.require(!p.flexyCompactLayout && p.emojiButton.p.leftMargin==80 && p.messageEditText.p.leftMargin==120);
  p.botCommandsMenuButton.tag=null;p.nativeMeasure();p.applyFlexyComposerPresentation(200);
  p.require(!p.flexyCompactLayout);
  System.out.print("PASS: actual production presentation method; native margin, paid widths, draft identity, special controls and 10000 recoveries");
 }
}'''.replace('__METHODS__',methods)
        with tempfile.TemporaryDirectory() as tmp:
            runner=Path(tmp)/'PresentationRegression.java';runner.write_text(fixture)
            production=ROOT/'TMessagesProj/src/main/java/app/flexygram/composer/ComposerGeometry.java'
            subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(production),str(runner)],check=True)
            self.assertIn('PASS:',subprocess.check_output(['java','-cp',tmp,'PresentationRegression'],text=True))

if __name__ == '__main__': unittest.main()
