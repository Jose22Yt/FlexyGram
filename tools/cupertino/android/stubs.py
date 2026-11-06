import json,shutil

def write(dest,root):
 def put(name,s):
  p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
 mapping=json.loads((root/'tools/cupertino/mapping.json').read_text())
 put('org/telegram/messenger/R.java','package org.telegram.messenger;public class R{public static class drawable{'+''.join(f'public static int {name}={i+1};' for i,name in enumerate(sorted(mapping)))+'}}')
 put('app/exteraless/icons/BaseIconPacks.java','package app.exteraless.icons;public class BaseIconPacks{public static final int BASE_DEFAULT=0;public static int selected;public static int getSelected(){return selected;}}')
 put('app/flexygram/animation/FastMotionTiming.java','package app.flexygram.animation;public class FastMotionTiming{public static boolean enabled;public static boolean isEnabled(){return enabled;}}')
 java=root/'TMessagesProj/src/main/java'
 allowed=['CupertinoGlyphDrawable.java','CupertinoIconMap.java','CupertinoIcons.java','CupertinoResources.java','CupertinoSupplement.java','IconPressCurve.java','IconPressFeedback.java']
 for p in (dest/'app/flexygram/icons').glob('*.java'):
  if p.name not in allowed:p.unlink()
 for name in allowed:
  p=root/'tools/cupertino/reference/src/app/flexygram/icons'/name
  target=dest/'app/flexygram/icons'/p.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
 put('androidx/annotation/NonNull.java','package androidx.annotation;public @interface NonNull{}')
 put('org/telegram/messenger/AndroidUtilities.java','package org.telegram.messenger;public class AndroidUtilities{public static float density=1;public static int dp(float v){return Math.round(v*density);}public static float lerp(float a,float b,float t){return a+(b-a)*t;}}')
 put('org/telegram/messenger/Utilities.java','package org.telegram.messenger;public class Utilities{}')
 put('androidx/core/graphics/ColorUtils.java','package androidx.core.graphics;public class ColorUtils{public static int blendARGB(int a,int b,float t){return android.graphics.Color.argb(Math.round(android.graphics.Color.alpha(a)*(1-t)+android.graphics.Color.alpha(b)*t),Math.round(android.graphics.Color.red(a)*(1-t)+android.graphics.Color.red(b)*t),Math.round(android.graphics.Color.green(a)*(1-t)+android.graphics.Color.green(b)*t),Math.round(android.graphics.Color.blue(a)*(1-t)+android.graphics.Color.blue(b)*t));}}')
 put('org/telegram/ui/ActionBar/BackDrawable.java',(java/'org/telegram/ui/ActionBar/BackDrawable.java').read_text())
 # Font is the exact shipped upstream asset; rendering uses Android's native Typeface/Canvas.
 shutil.copyfile(root/'tools/cupertino/reference/assets/cupertino/CupertinoIcons.ttf',dest.parents[2]/'CupertinoIcons.ttf')
