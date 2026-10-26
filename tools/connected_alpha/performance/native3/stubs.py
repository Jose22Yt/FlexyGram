"""Full candidate/baseline drawable source; Android graphics native, Telegram helpers explicit doubles."""
from pathlib import Path
import subprocess
BASE='8c47e5532a600f9a8b4ccbfdac5090d09a1075a0'

def write_stubs(source,root):
 def put(path,text):
  target=source/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
 for name in ['NonNull','Nullable','DrawableRes']:put('androidx/annotation/'+name+'.java','package androidx.annotation;public @interface '+name+' {}')
 path='TMessagesProj/src/main/java/org/telegram/ui/Components/voip/CellFlickerDrawable.java'
 candidate=(root/path).read_text();baseline=subprocess.check_output(['git','show',BASE+':'+path],cwd=root,text=True)
 put('org/telegram/ui/Components/voip/CellFlickerDrawable.java',candidate)
 put('org/telegram/ui/Components/voip/BaselineCellFlickerDrawable.java',baseline.replace('CellFlickerDrawable','BaselineCellFlickerDrawable'))
 put('org/telegram/messenger/AndroidUtilities.java','''package org.telegram.messenger;public class AndroidUtilities {public static float density=1;public static final android.graphics.RectF rectTmp=new android.graphics.RectF();public static int dp(float value){return (int)Math.ceil(value*density);}}''')
 put('org/telegram/messenger/SvgHelper.java','''package org.telegram.messenger;public class SvgHelper {public static class SvgDrawable extends android.graphics.drawable.ColorDrawable {public void setPaint(android.graphics.Paint p){}public float getScale(int w,int h){return 1;}}}''')
 put('org/telegram/ui/Components/voip/GroupCallMiniTextureView.java','''package org.telegram.ui.Components.voip;public class GroupCallMiniTextureView extends android.view.View {public Texture textureView;public GroupCallMiniTextureView(android.content.Context c){super(c);textureView=new Texture(c);}public static class Texture extends android.view.View {public float currentClipHorizontal,currentClipVertical,roundRadius;public Texture(android.content.Context c){super(c);}}}''')

 path='TMessagesProj/src/main/java/org/telegram/ui/Components/ClipRoundedDrawable.java'
 candidate=(root/path).read_text();baseline=subprocess.check_output(['git','show',BASE+':'+path],cwd=root,text=True)
 put('org/telegram/ui/Components/ClipRoundedDrawable.java',candidate)
 put('org/telegram/ui/Components/BaselineClipRoundedDrawable.java',baseline.replace('ClipRoundedDrawable','BaselineClipRoundedDrawable'))
 fixture=Path(__file__).with_name('ClipNativeTest.java.in')
 if fixture.is_file():put('org/telegram/ui/Components/ClipNativeTest.java',fixture.read_text())

 path='TMessagesProj/src/main/java/org/telegram/ui/Components/ReplaceableIconDrawable.java'
 baseline=subprocess.check_output(['git','show',BASE+':'+path],cwd=root,text=True)
 candidate=baseline
 patch=Path(__file__).parents[1]/'motion3.patch'
 if patch.is_file():
  import tempfile
  with tempfile.TemporaryDirectory()as d:
   target=Path(d)/path;target.parent.mkdir(parents=True);target.write_text(baseline)
   subprocess.run(['git','apply','--check',str(patch.resolve())],cwd=d,check=True,capture_output=True)
   subprocess.run(['git','apply',str(patch.resolve())],cwd=d,check=True,capture_output=True)
   candidate=target.read_text()
 put('org/telegram/ui/Components/BaselineReplaceableIconDrawable.java',baseline.replace('ReplaceableIconDrawable','BaselineReplaceableIconDrawable'))
 put('org/telegram/ui/Components/CandidateReplaceableIconDrawable.java',candidate.replace('ReplaceableIconDrawable','CandidateReplaceableIconDrawable'))
 fixture=Path(__file__).with_name('MotionNativeTest.java.in')
 if fixture.is_file():put('org/telegram/ui/Components/MotionNativeTest.java',fixture.read_text())
