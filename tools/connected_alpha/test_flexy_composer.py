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
        self.assertIn('drawFlexyCompactBackground(canvas)', source)
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
        listener = self.current.split('flexyComposerListener =',1)[1].split('};',1)[0]
        self.assertIn('messageEditTextContainer.requestLayout()', listener)

    def test_native_search_and_action_overlays_keep_their_original_background(self):
        chat = (ROOT/'TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java').read_text()
        # Native priorities fade the composer without changing its visibility.
        self.assertIn('checkBottomViewVisibility(chatActivityEnterView, MESSAGE_INPUT_CONTAINER, false)', chat)
        gate = method_bodies(self.current, 'isFlexyCompactPresentation')[0]
        self.assertIn('getAlpha() == 1f', gate)
        self.assertIn('getVisibility() == VISIBLE', gate)

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

    def test_compact_pill_preserves_separate_native_action_slot(self):
        source = (ROOT/CONTAINER).read_text()
        draw = method_bodies(source, 'drawFlexyCompactBackground')[0]
        self.assertIn('getFlexyTextPillBounds(flexyPill)', draw)
        self.assertIn('flexyPill.offset(offsetX, offsetY)', draw)
        bounds = method_bodies(self.current, 'getFlexyTextPillBounds')[0]
        self.assertIn('messageEditTextContainer.getWidth()', bounds)
        self.assertIn('nativeAttachTranslationX()', bounds)
        # Test actual production geometry in px across multiple screen densities.
        production = ROOT/'TMessagesProj/src/main/java/app/flexygram/composer/ComposerGeometry.java'
        test = '''
import app.flexygram.composer.ComposerGeometry;
public class ActionSlotRegression {
 public static void main(String[] args) {
  if (ComposerGeometry.TRAILING_ACTION_SLOT != 50) throw new AssertionError("native action hit area was reduced");
  for (int density=1;density<=4;density++) for (int dpWidth=280;dpWidth<=500;dpWidth+=20) {
   float width=dpWidth*density, rightInset=7*density, edgeInset=7*density;
   float nativeFieldRight=width-rightInset-edgeInset-44*density;
   float pillRight=ComposerGeometry.pillRight(nativeFieldRight,6*density,0);
   if (pillRight > nativeFieldRight-6*density+0.01f)
    throw new AssertionError("pill covers audio/send action");
   // Native emoji slot is 44dp, right margin 3dp; its 24dp glyph must fit.
   float emojiCenter=nativeFieldRight-25*density;
   if (emojiCenter+12*density > pillRight)
    throw new AssertionError("emoji is outside the text pill");
   if (pillRight <= (7+44+6)*density)
    throw new AssertionError("pill collapses at supported widths");
  }
  System.out.println("PASS: compact pill ends before native audio/send touch slot");
 }
}'''
        with tempfile.TemporaryDirectory() as tmp:
            runner = Path(tmp)/'ActionSlotRegression.java'; runner.write_text(test)
            subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,
                            str(production),str(runner)],check=True)
            self.assertIn('PASS:',subprocess.check_output(
                ['java','-cp',tmp,'ActionSlotRegression'],text=True))

    def test_actual_pill_bounds_keep_emoji_inside_and_both_islands_separate(self):
        method = method_bodies(self.current, 'getFlexyTextPillBounds')[0]
        fixture = '''
public class PillBoundsRegression {
 static float density;
 static int dp(float n){ return (int)Math.ceil(n*density); }
 static class RectF {
  float left,top,right,bottom;
  void set(float a,float b,float c,float d){left=a;top=b;right=c;bottom=d;}
  float width(){return right-left;} float height(){return bottom-top;}
 }
 static class View {
  float x,y; int width,height;
  float getX(){return x;} float getY(){return y;}
  int getWidth(){return width;} int getHeight(){return height;}
 }
 View textFieldContainer=new View(),messageEditTextContainer=new View();
 float actionShift;
 float nativeAttachTranslationX(){return actionShift;}
 static void require(boolean b,String why){if(!b)throw new AssertionError(why);}
 __METHOD__
 public static void main(String[] args){
  PillBoundsRegression p=new PillBoundsRegression();RectF r=new RectF();
  for(float d:new float[]{1,1.25f,1.5f,2,2.75f,3,4}) {
   density=d;
   for(int screen:new int[]{280,335,400,500,800}) for(int h:new int[]{44,68,120}) for(int paid:new int[]{0,56}){
    p.textFieldContainer.x=dp(7);p.textFieldContainer.y=dp(3);
    p.messageEditTextContainer.x=dp(11);p.messageEditTextContainer.y=dp(9);
    p.messageEditTextContainer.width=dp(screen)-dp(44);
    p.messageEditTextContainer.height=dp(h);p.actionShift=-dp(paid);
    require(p.getFlexyTextPillBounds(r),"missing valid surface");
    float x=p.textFieldContainer.x+p.messageEditTextContainer.x;
    float y=p.textFieldContainer.y+p.messageEditTextContainer.y;
    float end=x+p.messageEditTextContainer.width+p.actionShift;
    require(r.left-(x+dp(42))>=dp(6),"attachment merged into pill");
    require(end+dp(2)-r.right>=dp(6),"send merged into pill");
    float emojiCenter=end-dp(3)-dp(22);
    require(emojiCenter+dp(12)<=r.right && emojiCenter-dp(12)>=r.left,"emoji outside pill");
    require(x+dp(62)-r.left>=dp(11),"message text touches pill edge");
    require(r.top==y+dp(2) && r.bottom==y+dp(h)-dp(2),"multiline or native vertical position changed");
   }
  }
  p.messageEditTextContainer.width=0;
  require(!p.getFlexyTextPillBounds(r),"unmeasured field accepted");
  System.out.print("PASS: actual view-coordinate method, translated native field, emoji, paid send and multiline");
 }
}'''.replace('__METHOD__', method)
        with tempfile.TemporaryDirectory() as tmp:
            runner=Path(tmp)/'PillBoundsRegression.java';runner.write_text(fixture)
            production=ROOT/'TMessagesProj/src/main/java/app/flexygram/composer/ComposerGeometry.java'
            subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(production),str(runner)],check=True)
            self.assertIn('PASS:',subprocess.check_output(['java','-cp',tmp,'PillBoundsRegression'],text=True))

    def test_signature_three_islands_and_native_mic_paint(self):
        enter = self.current
        container = (ROOT/CONTAINER).read_text()
        presentation = method_bodies(enter, 'applyFlexyComposerPresentation')[0]
        self.assertIn('R.drawable.msg_add', presentation)
        self.assertIn('R.drawable.msg_input_attach2', presentation)
        self.assertIn('audioVideoButtonContainer.invalidate()', presentation)
        self.assertIn('if (flexyCompactLayout)', enter)
        self.assertIn('ColorUtils.blendARGB(panel, Color.WHITE', enter)
        self.assertIn('ColorUtils.calculateLuminance(panel) < 0.4 ? Color.BLACK : Color.WHITE', container)
        self.assertIn('canvas.drawRoundRect(flexyPill', container)
        self.assertIn('canvas.drawRoundRect(flexyAttach', container)

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
 static class R { static class drawable { static final int msg_add=1, msg_input_attach2=2; } }
 static class AndroidUtilities { static float density=1; }
 static int dp(float n){return Math.round(n);}
 static class MarginLayoutParams { int leftMargin=3,rightMargin=0,gravity; }
 static class FrameLayout { static class LayoutParams extends MarginLayoutParams {} }
 static class V {
  FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(); int visibility=8; Object tag;
  float translation,alpha=1; int width=44, imageResource;
  FrameLayout.LayoutParams getLayoutParams(){return p;}
  int getVisibility(){return visibility;}
  Object getTag(){return tag;}
  void setTranslationX(float x){translation=x;}
  void setImageResource(int icon){imageResource=icon;}
  void invalidate() {}
  int width(){return width;}
  float getAlpha(){return alpha;}
 }
 boolean isChat=true,isStories=false,flexyCompactRequested,flexyCompactLayout;
 Object parentFragment=new Object();
 V senderSelectView=new V(),botCommandsMenuButton=new V(),botWebViewButton=new V(),aiButton=new V();
 V attachButton=new V(),emojiButton=new V(),deleteRichDraftButton=new V(),messageEditText=new V(),sendButton=new V(),audioVideoButtonContainer=new V();
 void updateAudioVideoSendButtonColor() {}
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
   p.require(p.attachButton.imageResource==R.drawable.msg_add);
   p.require(p.emojiButton.p.gravity==(Gravity.BOTTOM|Gravity.RIGHT));
   p.require(p.messageEditText.p.leftMargin==62);
   p.require(p.messageEditText.p.rightMargin>=50+Math.max(0,-p.nativeAttachTranslationX()));
   p.require(p.messageEditText==originalText && p.draft==originalDraft);
   p.nativeMeasure();p.flexyCompactRequested=false;p.applyFlexyComposerPresentation(335);
   p.require(!p.flexyCompactLayout && p.messageEditText.p.rightMargin==end);
   p.require(p.messageEditText.p.leftMargin==50 && p.emojiButton.p.leftMargin==3 && p.emojiButton.p.rightMargin==0);
   p.require(p.attachButton.p.gravity==(Gravity.BOTTOM|Gravity.RIGHT));
   p.require(p.attachButton.imageResource==R.drawable.msg_input_attach2);
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
