"""Execute the live circle getters with varied native slot sizes and densities."""
from pathlib import Path
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / 'TMessagesProj/src/main/java'


def test_actual_attachment_microphone_and_send_bounds_match(tmp_path):
    if not shutil.which('java'):
        pytest.skip('JDK required')
    ts = pytest.importorskip('tree_sitter')
    java = pytest.importorskip('tree_sitter_java')
    parser = ts.Parser(ts.Language(java.language()))
    source = (JAVA / 'org/telegram/ui/Components/ChatActivityEnterView.java').read_bytes()
    wanted = {'getFlexyVisualInset', 'getFlexyActionDiameter', 'getFlexyVoiceBounds',
              'getFlexySendBounds', 'getFlexyAttachmentBounds'}
    pending = [parser.parse(source).root_node]
    methods = {}
    while pending:
        node = pending.pop()
        if node.type == 'method_declaration':
            name = node.child_by_field_name('name').text.decode()
            if name in wanted:
                methods[name] = node.text.decode()
        pending.extend(node.children)
    assert set(methods) == wanted
    probe = tmp_path / 'ActionSizes.java'
    probe.write_text('''public class ActionSizes {
 static float density;
 static int dp(float value){return (int)Math.ceil(value*density);}
 static final int VISIBLE=0;
 static class V {
  int w,h;float x=11.25f,y=7.5f;
  int getVisibility(){return VISIBLE;}float getAlpha(){return 1;}
  float getScaleX(){return 1;}float getScaleY(){return 1;}
  float getX(){return x;}float getY(){return y;}
  int getWidth(){return w;}int getHeight(){return h;}boolean isOpen(){return false;}
 }
 static class RectF {float l,t,r,b;
  void set(float a,float c,float d,float e){l=a;t=c;r=d;b=e;}
  float width(){return r-l;}float height(){return b-t;}
 }
 V attachButton=new V(),audioVideoButtonContainer=new V(),sendButton=new V(),
   sendButtonContainer=new V(),textFieldContainer=new V(),messageEditTextContainer=new V(),expandStickersButton;
 int flexyInsetDp;
 boolean isFlexyCompactPresentation(){return true;}
''' + '\n'.join(methods.values()) + '''
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 public static void main(String[] args) {
  ActionSizes p=new ActionSizes();
  for(float scale:new float[]{1,1.1f,1.25f,1.5f,2,2.625f,3,3.5f,4}) {
   density=scale;
   for(int inset:new int[]{0,2,4}) for(int slot:new int[]{44,48,60}) {
    p.flexyInsetDp=inset;
    p.attachButton.w=p.attachButton.h=p.audioVideoButtonContainer.w=p.audioVideoButtonContainer.h=
     p.sendButton.w=p.sendButton.h=dp(slot);
    RectF a=new RectF(),v=new RectF(),s=new RectF();
    check(p.getFlexyAttachmentBounds(a)&&p.getFlexyVoiceBounds(v)&&p.getFlexySendBounds(s));
    float expected=p.getFlexyActionDiameter();
    check(expected<=dp(44)&&expected>0);
    for(RectF r:new RectF[]{a,v,s}) {
     check(Math.abs(r.width()-expected)<.001f);
     check(Math.abs(r.height()-expected)<.001f);
    }
   }
  }
 }
}''')
    subprocess.run(['java', '-m', 'jdk.compiler/com.sun.tools.javac.Main', '-d', str(tmp_path),
                    str(JAVA / 'app/flexygram/composer/ComposerGeometry.java'), str(probe)],
                   check=True, capture_output=True)
    subprocess.run(['java', '-cp', str(tmp_path), 'ActionSizes'], check=True, capture_output=True)
