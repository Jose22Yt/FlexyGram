"""Explicit host doubles: compile/execute beta wrappers, never Android certification."""
from test_frame_endpoint import TREE
STUBS={
'android/os/Bundle.java':'''package android.os; public class Bundle {
 public final java.util.Map<String,Object> values=new java.util.HashMap<>();
 public void putInt(String key,int value){values.put(key,value);}public void putBoolean(String key,boolean value){values.put(key,value);}
 public void putString(String key,String value){values.put(key,value);}public Object get(String key){return values.get(key);}
}''',
'android/content/Context.java':'''package android.content; public class Context {public Context getApplicationContext(){return this;}public java.io.File getFilesDir(){return new java.io.File(System.getProperty("java.io.tmpdir"),"synthetic-beta-files");}}''',
'android/app/Activity.java':'''package android.app;
public class Activity extends android.content.Context {
 public static final java.util.Queue<Runnable> ui=new java.util.concurrent.ConcurrentLinkedQueue<>();
 public static final java.util.concurrent.CountDownLatch posted=new java.util.concurrent.CountDownLatch(1);
 private boolean finishing,destroyed;public boolean changingConfigurations;public android.view.View content;
 protected void onCreate(android.os.Bundle b){}protected void onResume(){}protected void onPause(){}protected void onDestroy(){destroyed=true;}
 protected void onSaveInstanceState(android.os.Bundle b){}public void saveState(android.os.Bundle b){onSaveInstanceState(b);}
 public boolean isChangingConfigurations(){return changingConfigurations;}
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
 public boolean enabled=true;OnClickListener click;
 public View(android.content.Context c){}public ViewTreeObserver getViewTreeObserver(){return tree;}
 public void setOnClickListener(OnClickListener l){click=l;}public void performClick(){if(enabled&&click!=null)click.onClick(this);}
 public void setEnabled(boolean b){enabled=b;}public void setBackgroundColor(int c){}
 public boolean isAttachedToWindow(){return true;}public boolean isShown(){return true;}public boolean hasWindowFocus(){return true;}
 public int getWidth(){return 100;}public int getHeight(){return 100;}
 public boolean postDelayed(Runnable r,long t){timers.add(r);return true;}
 public void postOnAnimation(Runnable r){frames.add(r);}public boolean removeCallbacks(Runnable r){frames.remove(r);timers.remove(r);return true;}
 public void invalidate(){}public static void frame(){if(!frames.isEmpty())frames.remove(0).run();}
}''',
'android/widget/LinearLayout.java':'''package android.widget;public class LinearLayout extends android.view.View {
 public static final int VERTICAL=1;public final java.util.List<android.view.View> children=new java.util.ArrayList<>();
 public LinearLayout(android.content.Context c){super(c);}public void setOrientation(int i){}public void addView(android.view.View v){children.add(v);}
}''',
'android/widget/TextView.java':'package android.widget;public class TextView extends android.view.View {public String text;public TextView(android.content.Context c){super(c);}public void setText(CharSequence value){text=value.toString();}}',
'android/widget/ScrollView.java':'''package android.widget;public class ScrollView extends LinearLayout {public ScrollView(android.content.Context c){super(c);}public void setFillViewport(boolean b){}}''',
'org/telegram/messenger/ApplicationLoader.java':'package org.telegram.messenger;public class ApplicationLoader {public static boolean fail;public static void postInitApplication(){if(fail)throw new IllegalStateException("SYNTHETIC_PRIVATE_VALUE");}}',
'org/telegram/messenger/BuildConfig.java':'''package org.telegram.messenger;public class BuildConfig {public static final String APPLICATION_ID="io.github.jose22yt.flexygram.beta.development",APP_HASH="";public static final int APP_ID=0;public static final boolean ISOLATED_DIAGNOSTIC=true;}''',
'org/telegram/messenger/BuildVariantPolicy.java':'''package org.telegram.messenger;public class BuildVariantPolicy {
 public static boolean authenticationAllowed(){return false;}public static boolean telegramTransportAllowed(){return false;}public static boolean pushAllowed(){return false;}
 public static boolean pluginsAllowed(){return false;}public static boolean translationAllowed(){return false;}public static boolean sessionRestoreAllowed(){return false;}}''',
'org/telegram/messenger/NativeLoader.java':'package org.telegram.messenger;public class NativeLoader {public static boolean ready=true;public static boolean loaded(){return ready;}}',
'org/telegram/messenger/R.java':'package org.telegram.messenger;public class R {public static class drawable {public static final int ic_ab_back=1;}}',
'org/telegram/ui/ActionBar/ActionBar.java':'''package org.telegram.ui.ActionBar;public class ActionBar {public static class ActionBarMenuOnItemClick {public void onItemClick(int id){}}
 public void setTitle(String s){}public void setBackButtonImage(int i){}public void setActionBarMenuOnItemClick(ActionBarMenuOnItemClick c){}}''',
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
 public void closeLastFragment(boolean b){if(busy||stack.size()<2)return;BaseFragment f=getLastFragment();f.onTransitionAnimationStart(false,true);stack.remove(f);f.onFragmentDestroy();busy=true;}
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
