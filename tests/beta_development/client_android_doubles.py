"""Explicit host doubles: compile/execute beta wrappers, never Android certification."""
from test_frame_endpoint import TREE
STUBS={
'android/annotation/TargetApi.java':'package android.annotation;public @interface TargetApi {int value();}',
'android/os/Build.java':'package android.os;public final class Build {public static final class VERSION {public static int SDK_INT=24;}}',
'android/window/OnBackInvokedCallback.java':'package android.window;public interface OnBackInvokedCallback {void onBackInvoked();}',
'android/window/OnBackInvokedDispatcher.java':'''package android.window;
public class OnBackInvokedDispatcher {
 public static final int PRIORITY_DEFAULT=0;
 public final java.util.List<OnBackInvokedCallback> callbacks=new java.util.ArrayList<>();
 public int registrations,unregistrations;
 private final Runnable fallback;
 public OnBackInvokedDispatcher(Runnable fallback){this.fallback=fallback;}
 public void registerOnBackInvokedCallback(int priority,OnBackInvokedCallback callback){
  if(priority!=PRIORITY_DEFAULT||callbacks.contains(callback))throw new AssertionError("bad registration");
  callbacks.add(callback);registrations++;
 }
 public void unregisterOnBackInvokedCallback(OnBackInvokedCallback callback){
  if(!callbacks.remove(callback))throw new AssertionError("unknown callback");unregistrations++;
 }
 public void dispatch(){if(callbacks.isEmpty())fallback.run();else for(OnBackInvokedCallback cb:new java.util.ArrayList<>(callbacks))cb.onBackInvoked();}
}''',
'android/os/Bundle.java':'''package android.os; public class Bundle {
 public final java.util.Map<String,Object> values=new java.util.HashMap<>();
 public void putInt(String key,int value){values.put(key,value);}public void putBoolean(String key,boolean value){values.put(key,value);}
 public void putString(String key,String value){values.put(key,value);}public Object get(String key){return values.get(key);}
}''',
'android/content/Context.java':'''package android.content; public class Context {public Context getApplicationContext(){return this;}public android.content.res.Resources getResources(){return new android.content.res.Resources();}public java.io.File getFilesDir(){return new java.io.File(System.getProperty("java.io.tmpdir"),"synthetic-beta-files");}}''',
'android/app/Activity.java':'''package android.app;
public class Activity extends android.content.Context {
 public static final java.util.Queue<Runnable> ui=new java.util.concurrent.ConcurrentLinkedQueue<>();
 public static final java.util.concurrent.CountDownLatch posted=new java.util.concurrent.CountDownLatch(1);
 private boolean finishing,destroyed;public boolean changingConfigurations;public android.view.View content;
 protected void onCreate(android.os.Bundle b){}protected void onResume(){}protected void onPause(){}protected void onDestroy(){destroyed=true;}
 protected void onSaveInstanceState(android.os.Bundle b){}public void saveState(android.os.Bundle b){onSaveInstanceState(b);}
 public boolean isChangingConfigurations(){return changingConfigurations;}
 public final android.window.OnBackInvokedDispatcher dispatcher=new android.window.OnBackInvokedDispatcher(this::finish);
 public android.window.OnBackInvokedDispatcher getOnBackInvokedDispatcher(){return dispatcher;}
 public void onBackPressed(){finish();}public void finish(){finishing=true;}
 public boolean isFinishing(){return finishing;}public boolean isDestroyed(){return destroyed;}
 public void setContentView(android.view.View v){content=v;}public void runOnUiThread(Runnable r){ui.add(r);posted.countDown();}
}''',
'android/view/ViewTreeObserver.java':TREE,
'android/view/View.java':'''package android.view;
public class View {
 public interface OnClickListener {void onClick(View v);}
 public static final java.util.List<Runnable> frames=new java.util.ArrayList<>();
 public final ViewTreeObserver tree=new ViewTreeObserver();public final java.util.List<Runnable> timers=new java.util.ArrayList<>();
 public boolean enabled=true;public int backgroundColor;public Object background;public int[] padding=new int[4];OnClickListener click;
 public View(android.content.Context c){}public ViewTreeObserver getViewTreeObserver(){return tree;}
 public void setOnClickListener(OnClickListener l){click=l;}public void performClick(){if(enabled&&click!=null)click.onClick(this);}
 public void setEnabled(boolean b){enabled=b;}public void setBackgroundColor(int c){backgroundColor=c;}public void setBackground(Object b){background=b;}public void setPadding(int l,int t,int r,int b){padding=new int[]{l,t,r,b};}
 public boolean isAttachedToWindow(){return true;}public boolean isShown(){return true;}public boolean hasWindowFocus(){return true;}
 public int getWidth(){return 100;}public int getHeight(){return 100;}
 public boolean postDelayed(Runnable r,long t){timers.add(r);return true;}
 public void postOnAnimation(Runnable r){frames.add(r);}public boolean removeCallbacks(Runnable r){frames.remove(r);timers.remove(r);return true;}
 public void invalidate(){}public static void frame(){if(!frames.isEmpty())frames.remove(0).run();}
}''',
'android/widget/LinearLayout.java':'''package android.widget;public class LinearLayout extends android.view.View {
 public static final int VERTICAL=1,HORIZONTAL=0;public int gravity;public final java.util.List<android.view.View> children=new java.util.ArrayList<>();
 public LinearLayout(android.content.Context c){super(c);}public void setOrientation(int i){}public void setGravity(int i){gravity=i;}public void addView(android.view.View v){children.add(v);}public void addView(android.view.View v,LayoutParams p){children.add(v);}public static class LayoutParams {public static final int MATCH_PARENT=-1,WRAP_CONTENT=-2;public LayoutParams(int w,int h){}}
}''',
'android/widget/TextView.java':'package android.widget;public class TextView extends android.view.View {public String text;public TextView(android.content.Context c){super(c);}public void setText(CharSequence value){text=value.toString();}public void setTextSize(int u,float s){}public void setTextColor(int c){}public void setMaxWidth(int w){}public void setGravity(int g){}}',
'android/widget/ScrollView.java':'''package android.widget;public class ScrollView extends LinearLayout {public ScrollView(android.content.Context c){super(c);}public void setFillViewport(boolean b){}}''',
'org/telegram/messenger/ApplicationLoader.java':'package org.telegram.messenger;public class ApplicationLoader {public static boolean fail;public static void postInitApplication(){if(fail)throw new IllegalStateException("SYNTHETIC_PRIVATE_VALUE");}}',
'org/telegram/messenger/BuildConfig.java':'''package org.telegram.messenger;public class BuildConfig {public static final String APPLICATION_ID="io.github.jose22yt.flexygram.beta.development",APP_HASH="";public static final int APP_ID=0;public static final boolean ISOLATED_DIAGNOSTIC=true;}''',
'org/telegram/messenger/BuildVariantPolicy.java':'''package org.telegram.messenger;public class BuildVariantPolicy {
 public static boolean authenticationAllowed(){return false;}public static boolean telegramTransportAllowed(){return false;}public static boolean pushAllowed(){return false;}
 public static boolean pluginsAllowed(){return false;}public static boolean translationAllowed(){return false;}public static boolean sessionRestoreAllowed(){return false;}}''',
'org/telegram/messenger/NativeLoader.java':'package org.telegram.messenger;public class NativeLoader {public static boolean ready=true;public static boolean loaded(){return ready;}}',
'org/telegram/messenger/R.java':'package org.telegram.messenger;public class R {public static class drawable {public static final int ic_ab_back=1;}}',
'org/telegram/ui/ActionBar/ActionBar.java':'''package org.telegram.ui.ActionBar;public class ActionBar {public static class ActionBarMenuOnItemClick {public void onItemClick(int id){}}
 public boolean occupyStatusBar=true;public void setOccupyStatusBar(boolean value){occupyStatusBar=value;}public void setTitle(String s){}public void setBackButtonImage(int i){}public void setActionBarMenuOnItemClick(ActionBarMenuOnItemClick c){}}''',
'org/telegram/ui/ActionBar/BaseFragment.java':'''package org.telegram.ui.ActionBar;public class BaseFragment {
 protected android.view.View fragmentView;protected ActionBar actionBar=new ActionBar();public ActionBarLayout parent;
 public android.view.View createView(android.content.Context c){return fragmentView=new android.view.View(c);}
 public android.view.View getFragmentView(){return fragmentView;}public ActionBar getActionBar(){return actionBar;}
 public boolean presentFragment(BaseFragment b){return parent.presentFragment(b);}public void finishFragment(){parent.closeLastFragment(true);}
 public void onFragmentDestroy(){}public void onTransitionAnimationStart(boolean open,boolean back){}
}''',
'org/telegram/ui/ActionBar/ActionBarLayout.java':'''package org.telegram.ui.ActionBar;public class ActionBarLayout extends android.view.View {
 public boolean busy;public final android.content.Context context;private java.util.ArrayList<BaseFragment> stack;
 public ActionBarLayout(android.app.Activity a,boolean b){super(a);context=a;}
 public void setFragmentStack(java.util.ArrayList<BaseFragment> s){stack=s;}public java.util.ArrayList<BaseFragment> getFragmentStack(){return stack;}
 public BaseFragment getLastFragment(){return stack.isEmpty()?null:stack.get(stack.size()-1);}
 public void addFragmentToStack(BaseFragment f){f.parent=this;stack.add(f);}public void showLastFragment(){getLastFragment().createView(context);}
 public boolean checkTransitionAnimation(){return busy;}public boolean isTransitionAnimationInProgress(){return busy;}
 public boolean isSwipeInProgress(){return false;}public boolean isPreviewOpenAnimationInProgress(){return false;}
 public boolean presentFragment(BaseFragment f){if(busy)return false;addFragmentToStack(f);f.createView(context);busy=true;return true;}
 // Real ActionBarLayout.closeLastFragment creates the previous view if it was
 // never visible (e.g. home underneath a restored conversation).
 public void closeLastFragment(boolean b){if(busy||stack.size()<2)return;BaseFragment f=getLastFragment();f.onTransitionAnimationStart(false,true);stack.remove(f);f.onFragmentDestroy();if(getLastFragment().getFragmentView()==null)showLastFragment();busy=true;}
 public void onBackPressed(){closeLastFragment(true);}public void onResume(){}public void onPause(){}
 public void removeAllFragments(){for(BaseFragment f:stack)f.onFragmentDestroy();stack.clear();}
 public void rebuildAllFragmentViews(boolean a,boolean b){getLastFragment().createView(context);}
}''',
'org/telegram/ui/ActionBar/Theme.java':'''package org.telegram.ui.ActionBar;public class Theme {public static final int key_windowBackgroundWhite=1;
 public static class ThemeInfo {public boolean dark;ThemeInfo(boolean b){dark=b;}}
 static ThemeInfo current=new ThemeInfo(false);public static ThemeInfo getCurrentTheme(){return current;}
 public static boolean isCurrentThemeDark(){return current.dark;}public static ThemeInfo getTheme(String s){return new ThemeInfo(s.equals("Dark Blue"));}
 public static void applyTheme(ThemeInfo i,boolean a,boolean b){current=i;}public static int getColor(int k){return 0;}}
''',
'org/telegram/ui/Cells/TextSettingsCell.java':'''package org.telegram.ui.Cells;public class TextSettingsCell extends android.view.View {public String text,value;public TextSettingsCell(android.content.Context c){super(c);}public void setTextAndValue(String t,String v,boolean b){text=t;value=v;}}''',
'org/telegram/ui/Cells/DialogCell.java':'''package org.telegram.ui.Cells;public class DialogCell extends android.view.View {public DialogCell(Object o,android.content.Context c,boolean a,boolean b){super(c);}public static class CustomDialog{public long id;public String name,message;public int date;}public void setDialog(CustomDialog d){}}''',
'org/telegram/ui/Cells/ThemePreviewMessagesCell.java':'''package org.telegram.ui.Cells;public class ThemePreviewMessagesCell extends android.view.View {public org.telegram.ui.ActionBar.BaseFragment fragment;public ThemePreviewMessagesCell(android.content.Context c,org.telegram.ui.ActionBar.ActionBarLayout n,int i){super(c);}}''',
'com/chaquo/python/android/AndroidPlatform.java':'package com.chaquo.python.android;public class AndroidPlatform {public AndroidPlatform(android.content.Context c){}}',
'com/chaquo/python/Python.java':'''package com.chaquo.python;public class Python {
 public static final java.util.concurrent.CountDownLatch entered=new java.util.concurrent.CountDownLatch(1),release=new java.util.concurrent.CountDownLatch(1);
 public static boolean failStart,failImport;static boolean started;public static boolean isStarted(){return started;}public static void start(com.chaquo.python.android.AndroidPlatform p){if(failStart)throw new IllegalStateException("SYNTHETIC_PRIVATE_VALUE");started=true;}
 public static Python getInstance(){return new Python();}public Object getModule(String name){if(failImport)throw new IllegalStateException("SYNTHETIC_PRIVATE_VALUE");entered.countDown();try{if(!release.await(5,java.util.concurrent.TimeUnit.SECONDS))throw new RuntimeException();}catch(InterruptedException e){throw new RuntimeException();}return new Object();}}
'''
}

# Framework-only widgets used by the account-free conversation fixture.
STUBS.update({
 'android/util/DisplayMetrics.java': 'package android.util;public class DisplayMetrics {public float density=1;public int widthPixels=360;}',
 'android/util/TypedValue.java': 'package android.util;public class TypedValue {public static final int COMPLEX_UNIT_SP=2;}',
 'android/content/res/Resources.java': 'package android.content.res;public class Resources {public android.util.DisplayMetrics getDisplayMetrics(){return new android.util.DisplayMetrics();}}',
 'android/view/Gravity.java': 'package android.view;public class Gravity {public static final int START=8388611,END=8388613;}',
 'android/graphics/drawable/GradientDrawable.java': 'package android.graphics.drawable;public class GradientDrawable {public int color;public float radius;public void setColor(int c){color=c;}public void setCornerRadius(float r){radius=r;}}',
})

# Insets are explicit host doubles, not a simulation of Android's window manager.
STUBS.update({
 'android/widget/FrameLayout.java': 'package android.widget;public class FrameLayout extends LinearLayout {public FrameLayout(android.content.Context c){super(c);}}',
 'androidx/core/graphics/Insets.java': 'package androidx.core.graphics;public class Insets {public final int left,top,right,bottom;public Insets(int l,int t,int r,int b){left=l;top=t;right=r;bottom=b;}}',
 'androidx/core/view/WindowInsetsCompat.java': '''package androidx.core.view;
 public class WindowInsetsCompat {
  public final androidx.core.graphics.Insets bars;public final int ime;
  public WindowInsetsCompat(int l,int t,int r,int b,int keyboard){bars=new androidx.core.graphics.Insets(l,t,r,b);ime=keyboard;}
  public static class Type {public static int systemBars(){return 1;}public static int displayCutout(){return 2;}}
  public androidx.core.graphics.Insets getInsets(int type){if(type!=3)throw new AssertionError("wrong inset types");return bars;}
  public WindowInsetsCompat inset(int l,int t,int r,int b){return new WindowInsetsCompat(Math.max(0,bars.left-l),Math.max(0,bars.top-t),Math.max(0,bars.right-r),Math.max(0,bars.bottom-b),Math.max(0,ime-b));}
 }''',
 'androidx/core/view/ViewCompat.java': '''package androidx.core.view;
 public class ViewCompat {
  public interface Listener {WindowInsetsCompat apply(android.view.View view,WindowInsetsCompat insets);}
  private static final java.util.Map<android.view.View,Listener> listeners=new java.util.WeakHashMap<>();
  public static void setOnApplyWindowInsetsListener(android.view.View view,Listener listener){listeners.put(view,listener);}
  public static void requestApplyInsets(android.view.View view){}
  public static WindowInsetsCompat dispatch(android.view.View view,WindowInsetsCompat insets){return listeners.get(view).apply(view,insets);}
 }''',
})
