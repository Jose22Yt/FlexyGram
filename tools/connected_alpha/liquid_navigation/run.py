"""Actual MainTabsLayout/AnimatedLinearLayout and AndroidX SpringAnimation; app services and tab content are explicit doubles. Not full-app/device acceptance."""
from pathlib import Path
import importlib.util,sys
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('liquid_pipeline',HERE.parent/'music_visual/run.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
def write(source,root):
 def put(path,text):
  dest=source/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
 java=root/'TMessagesProj/src/main/java'
 files=['org/telegram/ui/MainTabsLayout.java','org/telegram/ui/Components/AnimatedLinearLayout.java','org/telegram/ui/Components/CubicBezierInterpolator.java','me/vkryl/android/animator/BoolAnimator.java','me/vkryl/android/animator/FactorAnimator.java','me/vkryl/android/animator/ListAnimator.java','me/vkryl/android/animator/VariableFloat.java','me/vkryl/android/animator/VariableRect.java','me/vkryl/android/animator/Animatable.java','me/vkryl/android/animator/Animated.java','me/vkryl/android/AnimatorUtils.java','me/vkryl/android/util/ClickHelper.java','me/vkryl/core/ArrayUtils.java','me/vkryl/core/BitwiseUtils.java','me/vkryl/core/lambda/Destroyable.java','app/flexygram/navigation/LiquidNavigationConfig.java','app/flexygram/navigation/LiquidNavigationMath.java','app/flexygram/navigation/LiquidNavigationDestinations.java']
 for name in files:put(name,(java/name).read_text())
 for name in ['NonNull','Nullable']:put('androidx/annotation/'+name+'.java','package androidx.annotation;public @interface '+name+'{}')
 put('androidx/annotation/FloatRange.java','package androidx.annotation;public @interface FloatRange{double from() default Double.NEGATIVE_INFINITY;double to() default Double.POSITIVE_INFINITY;}')
 put('org/telegram/messenger/ApplicationLoader.java','package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext=org.robolectric.RuntimeEnvironment.getApplication();}')
 put('org/telegram/messenger/AndroidUtilities.java','''package org.telegram.messenger;public class AndroidUtilities{public static float density=1;static android.os.Handler h=new android.os.Handler(android.os.Looper.getMainLooper());public static int dp(float v){return (int)Math.ceil(v*density);}public static float lerp(float a,float b,float t){return a+(b-a)*t;}public static void runOnUIThread(Runnable r){h.post(r);}public static void runOnUIThread(Runnable r,long delay){h.postDelayed(r,delay);}public static void cancelRunOnUIThread(Runnable r){h.removeCallbacks(r);}}''')
 put('org/telegram/ui/ActionBar/Theme.java','''package org.telegram.ui.ActionBar;public class Theme{public interface ResourcesProvider{}public static int key_glass_tabSelected=1;public static int getColor(int k,ResourcesProvider p){return 0xff2266aa;}public static int multAlpha(int c,float a){return (c&0xffffff)|(Math.round((c>>>24)*a)<<24);}public static int getDividerColor(ResourcesProvider p){return 0xffaaaaaa;}}''')
 put('app/exteraless/appearance/MainTabsUiHelper.java','''package app.exteraless.appearance;public class MainTabsUiHelper{public static boolean isMaterial3NavigationBar(){return false;}public static boolean isIosNavigationBar(){return true;}public static void setMainTabSelectedIndicatorBounds(android.graphics.RectF out,float w,float h){out.set(0,0,w,h);}}''')
 put('tw/nekomimi/nekogram/NekoConfig.java','''package tw.nekomimi.nekogram;public class NekoConfig{public static class Flag{public boolean Bool(){return false;}}public static Flag disableVibration=new Flag();public static android.content.SharedPreferences getPreferences(){return org.telegram.messenger.ApplicationLoader.applicationContext.getSharedPreferences("neko",0);}}''')
 put('xyz/nextalone/nagram/NaConfig.java','''package xyz.nextalone.nagram;public class NaConfig{public static NaConfig INSTANCE=new NaConfig();public static class Flag{boolean value;public boolean Bool(){return value;}public void setConfigBool(boolean v){value=v;}}private final Flag hide=new Flag();public Flag getHideBottomNavigationBar(){return hide;}}''')
 put('me/vkryl/android/ViewUtils.java','''package me.vkryl.android;public class ViewUtils{public static void hapticVibrate(android.view.View v,boolean a,boolean b){}public static void onClick(android.view.View v){}public static void runJustBeforeBeingDrawn(android.view.View v,Runnable r){v.post(r);}}''')
 put('org/telegram/ui/Components/glass/GlassTabView.java','''package org.telegram.ui.Components.glass;public class GlassTabView extends android.widget.FrameLayout implements org.telegram.ui.MainTabsLayout.Tab{private boolean selected,skip;public GlassTabView(android.content.Context c){super(c);setClickable(true);}public boolean isTabSelected(){return selected;}public void setSelected(boolean value,boolean animated){selected=value;}public void setSkipDrawSelector(boolean v){skip=v;}public void setVisualWidth(float w){}public float measureTextWidth(){return 32;}public float measureTextWidth(float v){return 32;}public void setTextSizeDp(float v){}}''')

 # Execute the actual MainTabsActivity visibility method, not a rewritten condition.
 native=(java/'org/telegram/ui/MainTabsActivity.java').read_text()
 anchor=native.index('    private void checkUi_tabsPosition()')
 end=native.index('    private void checkUi_callTabVisible(',anchor)
 method=native[anchor:end]
 put('NativeTabsVisibilityProbe.java','''import android.widget.FrameLayout;import android.view.View;import org.telegram.ui.MainTabsLayout;import xyz.nextalone.nagram.NaConfig;
 public class NativeTabsVisibilityProbe {
 final MainTabsLayout tabsView;final FrameLayout tabsViewWrapper;float factor;
 static int dp(float v){return org.telegram.messenger.AndroidUtilities.dp(v);}static float lerp(float a,float b,float t){return a+(b-a)*t;}
 static class MainTabsHelper{static boolean isMainTabsHideTitleStyle(){return false;}}
 static class UpdateLayoutWrapper{static int HEIGHT=48;boolean isUpdateLayoutVisible(){return false;}}
 final UpdateLayoutWrapper updateLayoutWrapper=new UpdateLayoutWrapper();
 final Factor animatorTabsVisible=new Factor();class Factor{float getFloatValue(){return factor;}}
 void checkUi_miniPlayer(){}
 public NativeTabsVisibilityProbe(MainTabsLayout bar,FrameLayout wrapper){tabsView=bar;tabsViewWrapper=wrapper;}
 public void apply(float value){factor=value;checkUi_tabsPosition();}
 '''+method+'}')

 selection=native[native.index('    public void selectTab('):native.index('    public void setGestureSelectedOverride(')]
 put('NativeTabSelectionProbe.java','''import org.telegram.ui.Components.glass.GlassTabView;
 public class NativeTabSelectionProbe{
 public GlassTabView[] tabs;public int[] flexyShownDestinations,flexyConfiguredDestinations;
 int indexToPosition(int id){return id==0?0:id==1?1:id==2?2:id==4?3:-1;}
 '''+selection+'}')
if __name__=='__main__':
 if '--output-dir' not in sys.argv:sys.argv+=['--output-dir',str(HERE.parents[2]/'build/connected-alpha-liquid-navigation')]
 raise SystemExit(p.main(here=HERE,test_class='LiquidNavigationTest',stubs_writer=write,extra_aars=(('androidx.dynamicanimation','dynamicanimation','1.0.0'),)))
