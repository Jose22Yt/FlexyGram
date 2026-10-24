"""Explicit test doubles for out-of-scope Telegram services/animations, never shipped.

Real Android TextViews, FrameLayouts, measurements, RTL, accessibility and the three
upstream native cell sources are exercised. Animated values/switch artwork are not
certified by this isolated probe; the APK keeps their untouched production engines.
"""
import re

def sources(native_sources):
    keys=sorted(set(re.findall(r'Theme\.(key_\w+)',native_sources)))
    return {
'org/telegram/messenger/AndroidUtilities.java':'''package org.telegram.messenger; import android.graphics.*; public class AndroidUtilities {
 public static float density=1; public static RectF rectTmp=new RectF();
 public static int dp(float v){return (int)Math.ceil(v*density);} public static float dpf2(float v){return v*density;}
 public static Typeface regular(){return Typeface.DEFAULT;} public static Typeface bold(){return Typeface.DEFAULT_BOLD;}
}''',
'org/telegram/messenger/LocaleController.java':'package org.telegram.messenger; public class LocaleController {public static boolean isRTL;}',
'org/telegram/messenger/BuildVars.java':'package org.telegram.messenger; public class BuildVars {public static boolean DEBUG_PRIVATE_VERSION=false;}',
'org/telegram/messenger/BuildConfig.java':'package org.telegram.messenger; public class BuildConfig {public static boolean CONNECTED_ALPHA=true;}',
'org/telegram/messenger/ApplicationLoader.java':'package org.telegram.messenger; public class ApplicationLoader {public static android.content.Context applicationContext;}',
'org/telegram/messenger/R.java':'package org.telegram.messenger; public class R { public static class drawable {public static int arrow_more=android.R.drawable.arrow_down_float;}}',
'org/telegram/ui/ActionBar/Theme.java':'''package org.telegram.ui.ActionBar; import android.graphics.*; import android.graphics.drawable.*; public class Theme {
 public interface ResourcesProvider{} public static boolean dark; public static Paint dividerPaint=new Paint();
 _KEYS_
 public static int getColor(int k){return getColor(k,null);} public static int getColor(int k,ResourcesProvider p){
 if(k==key_windowBackgroundWhiteBlackText)return dark?0xffeeeeee:0xff16181c;
 return dark?0xffa3a5aa:0xff72757c;}
 public static Drawable createRoundRectDrawable(int r,int c){return new ColorDrawable(c);}
 public static Drawable createSelectorDrawable(int c,int m){return new ColorDrawable(c);}
}'''.replace('_KEYS_','\n'.join(f'public static int {key}={i};' for i,key in enumerate(keys,1))),
'org/telegram/ui/Components/AnimatedTextView.java':'''package org.telegram.ui.Components; import android.content.*; import android.util.*; import android.widget.*;
public class AnimatedTextView extends TextView {
 public static class AnimatedTextDrawable {public void setAllowCancel(boolean v){} }
 private AnimatedTextDrawable drawable=new AnimatedTextDrawable();
 public AnimatedTextView(Context c,boolean... flags){super(c);} public AnimatedTextDrawable getDrawable(){return drawable;}
 public void setText(CharSequence t,boolean animated){super.setText(t);}
 public void setAnimationProperties(float a,long b,long c,Object d){}
 @Override public void setTextSize(float px){super.setTextSize(TypedValue.COMPLEX_UNIT_PX,px);}
}''',
'org/telegram/ui/Components/AnimatedEmojiDrawable.java':'''package org.telegram.ui.Components; public class AnimatedEmojiDrawable extends android.graphics.drawable.ColorDrawable {public void addView(android.view.View v){} public void removeView(android.view.View v){} }''',
'org/telegram/ui/Components/BackupImageView.java':'''package org.telegram.ui.Components; import android.content.*; import android.widget.*; public class BackupImageView extends ImageView { public BackupImageView(Context c){super(c);} public Receiver getImageReceiver(){return new Receiver();} public static class Receiver {public android.graphics.drawable.Drawable getDrawable(){return null;}} }''',
'org/telegram/ui/Components/RLottieImageView.java':'package org.telegram.ui.Components; public class RLottieImageView extends android.widget.ImageView {public RLottieImageView(android.content.Context c){super(c);}}',
'org/telegram/ui/Components/EmojiTextView.java':'package org.telegram.ui.Components; public class EmojiTextView extends android.widget.TextView {public EmojiTextView(android.content.Context c){super(c);}}',
'org/telegram/ui/Components/CubicBezierInterpolator.java':'package org.telegram.ui.Components; public class CubicBezierInterpolator implements android.animation.TimeInterpolator {public static CubicBezierInterpolator EASE_OUT_QUINT=new CubicBezierInterpolator(); public float getInterpolation(float v){return v;}}',
'org/telegram/ui/Components/Switch.java':'''package org.telegram.ui.Components; public class Switch extends android.view.View {
 boolean checked; public Switch(android.content.Context c){super(c);} public void setDrawIconType(int v){} public void setColors(int...v){}
 public void setChecked(boolean v,boolean a){checked=v;}public boolean isChecked(){return checked;} public void setIcon(int v){}public boolean hasIcon(){return false;}
}''',
'app/exteraless/appearance/M3ListItems.java':'package app.exteraless.appearance; public class M3ListItems {public static boolean enabled(){return false;}public static int rowHeight(int b){return b;} public static int detailRowHeight(int b){return b;}}',
'org/telegram/ui/Components/LayoutHelper.java':'''package org.telegram.ui.Components;
import android.widget.*; import org.telegram.messenger.AndroidUtilities;
public class LayoutHelper {public static int MATCH_PARENT=-1,WRAP_CONTENT=-2;
 static int size(float x){return x<0?(int)x:AndroidUtilities.dp(x);}
 public static FrameLayout.LayoutParams createFrame(float w,float h){return createFrame(w,h,0);}
 public static FrameLayout.LayoutParams createFrame(float w,float h,int g){return createFrame(w,h,g,0,0,0,0);}
 public static FrameLayout.LayoutParams createFrame(float w,float h,int g,float l,float t,float r,float b){FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(size(w),size(h),g);p.setMargins(size(l),size(t),size(r),size(b));return p;}
 public static LinearLayout.LayoutParams createLinear(float w,float h,int g){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(size(w),size(h));p.gravity=g;return p;}
}'''
    }
