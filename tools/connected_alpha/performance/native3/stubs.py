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

