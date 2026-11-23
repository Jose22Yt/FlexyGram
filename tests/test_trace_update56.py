"""Regression checks for the trace-guided patch. Counts work; no device FPS claims."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe
from test_foreground_resume import run_diff


def test_unchanged_rows_do_not_restore_scroll_but_native_spacer_diff_still_runs(tmp_path):
    run_diff(tmp_path, '''Probe p=new Probe();p.initial(20);int[] restored={0};
 for(int i=0;i<10000;i++){p.source(0,20);p.updateList(mapping->restored[0]++);}
 check(restored[0]==0&&p.events==0&&!p.isCalculatingDiff);
 var footer=new ItemInternal(0);footer.viewType=VIEW_TYPE_LAST_EMPTY;p.itemInternals.add(footer);
 p.source(0,20);var nextFooter=new ItemInternal(0);nextFooter.viewType=VIEW_TYPE_LAST_EMPTY;p.source.add(nextFooter);
 p.updateList(mapping->restored[0]++);check(restored[0]==0&&p.events>0);
 p.source(1,20);p.updateList(mapping->restored[0]++);check(restored[0]==1);
 p.initial(100);p.source(0,100);p.updateList(mapping->restored[0]++);complete();check(restored[0]==1);
 p.source(1,100);p.updateList(mapping->restored[0]++);complete();check(restored[0]==2);
 ''')


def test_global_preferences_do_not_construct_account_controller_and_keep_live_identity(tmp_path):
    source=(JAVA/'org/telegram/messenger/MessagesController.java').read_text()
    get=method(source,'public static SharedPreferences getGlobalMainSettings()')
    probe(tmp_path,{'Probe.java':'''public class Probe {
 static class Activity{static final int MODE_PRIVATE=0;}
 static class SharedPreferences{int value;}
 static class Context{final SharedPreferences main=new SharedPreferences();SharedPreferences getSharedPreferences(String n,int mode){if(!n.equals("mainconfig")||mode!=0)throw new AssertionError();return main;}}
 static class ApplicationLoader{static Context applicationContext=new Context();}
 static class MessagesController{static MessagesController[]Instance=new MessagesController[1];SharedPreferences mainPreferences;GET}
 public static void main(String[]args){
  var p=MessagesController.getGlobalMainSettings();p.value=42;
  if(MessagesController.Instance[0]!=null||MessagesController.getGlobalMainSettings()!=p)throw new AssertionError();
  var controller=new MessagesController();controller.mainPreferences=ApplicationLoader.applicationContext.getSharedPreferences("mainconfig",0);MessagesController.Instance[0]=controller;
  if(MessagesController.getGlobalMainSettings()!=p||controller.mainPreferences.value!=42)throw new AssertionError();
 }
}'''.replace('GET',get)})


def test_dock_capture_visibility_tracks_actual_views_and_partial_fade(tmp_path):
    source=(JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
    visible=method(source,'private boolean hasVisibleTabsSurface()')
    probe(tmp_path,{'Probe.java':'''public class Probe{
 static class View{static final int VISIBLE=0;int visibility;float alpha=1;int getVisibility(){return visibility;}float getAlpha(){return alpha;}}
 View tabsView=new View(),tabsViewWrapper=new View();VISIBLE
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();check(p.hasVisibleTabsSurface());
 for(float alpha:new float[]{.001f,.5f,1}){p.tabsView.alpha=alpha;check(p.hasVisibleTabsSurface());}
 p.tabsView.alpha=0;check(!p.hasVisibleTabsSurface());p.tabsView.alpha=1;p.tabsViewWrapper.alpha=0;check(!p.hasVisibleTabsSurface());
 p.tabsViewWrapper.alpha=1;p.tabsView.visibility=8;check(!p.hasVisibleTabsSurface());p.tabsView.visibility=0;p.tabsViewWrapper.visibility=8;check(!p.hasVisibleTabsSurface());
 p.tabsView=null;check(!p.hasVisibleTabsSurface());
 }
}'''.replace('VISIBLE\n',visible+'\n')})


def test_native_tab_glass_skips_hidden_and_kyant_surfaces(tmp_path):
    source=(JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
    methods='\n'.join(method(source, signature) for signature in (
        'private boolean hasVisibleTabsSurface()', 'private void blur3_invalidateBlur()',
    ))
    position=method(source,'private void checkUi_tabsPosition()')
    assert 'final boolean interactive = factor >= 1f;' in position
    kotlin=(JAVA.parents[0]/'kotlin/app/flexygram/kyant/KyantDockView.kt').read_text()
    assert '!LiteMode.isThermalPressureHigh()' in kotlin
    probe(tmp_path,{'Probe.java':'''public class Probe {
 static class View {
  static final int VISIBLE=0; int visibility,windowVisibility; float alpha=1; boolean shown=true;
  int getVisibility(){return visibility;} float getAlpha(){return alpha;} boolean isShown(){return shown;}
  int getWindowVisibility(){return windowVisibility;}
  int getMeasuredWidth(){return 100;} int getMeasuredHeight(){return 200;}
 }
 static class Build {
  static class VERSION {static int SDK_INT=35;}
  static class VERSION_CODES {static final int S=31;}
 }
 static class SharedConfig {static boolean enabled=true;static boolean chatBlurEnabled(){return enabled;}}
 static class Dock {boolean rendering;boolean isRendering(){return rendering;}}
 static class Source {
  int updates;void setSize(int w,int h){check(w==100&&h==200);}void updateDisplayListIfNeeded(){updates++;}
 }
 Dock kyantDockView=new Dock(); Source iBlur3SourceTabGlass=new Source();
 View tabsView=new View(),tabsViewWrapper=new View(),fragmentView=new View();
 METHODS
 static void check(boolean valid){if(!valid)throw new AssertionError();}
 public static void main(String[] args){
  Probe p=new Probe();p.blur3_invalidateBlur();check(p.iBlur3SourceTabGlass.updates==1);
  p.tabsViewWrapper.alpha=0;p.blur3_invalidateBlur();p.tabsViewWrapper.alpha=1;
  p.tabsView.shown=false;p.blur3_invalidateBlur();p.tabsView.shown=true;
  p.tabsView.windowVisibility=8;p.blur3_invalidateBlur();p.tabsView.windowVisibility=0;
  p.kyantDockView.rendering=true;p.blur3_invalidateBlur();p.kyantDockView.rendering=false;
  SharedConfig.enabled=false;p.blur3_invalidateBlur();SharedConfig.enabled=true;
  check(p.iBlur3SourceTabGlass.updates==1);p.tabsView.alpha=.4f;p.blur3_invalidateBlur();
  check(p.iBlur3SourceTabGlass.updates==2);
 }
}'''.replace('METHODS',methods)})


def test_real_icon_resources_preload_cache_cancel_configuration_and_independent_drawables(tmp_path):
    files={
      'android/annotation/SuppressLint.java':'package android.annotation;public @interface SuppressLint{String[] value();}',
      'androidx/annotation/Nullable.java':'package androidx.annotation;public @interface Nullable{}',
      'android/os/Process.java':'package android.os;public class Process{public static final int THREAD_PRIORITY_BACKGROUND=10;public static void setThreadPriority(int p){}}',
      'android/util/DisplayMetrics.java':'package android.util;public class DisplayMetrics{}',
      'android/content/res/Configuration.java':'''package android.content.res;public class Configuration{public int generation;public Configuration(){}public Configuration(Configuration c){generation=c.generation;}public boolean equals(Object o){return o instanceof Configuration&&((Configuration)o).generation==generation;}}''',
      'android/util/LruCache.java':'''package android.util;public class LruCache<K,V>{private final java.util.LinkedHashMap<K,V>m=new java.util.LinkedHashMap<>(16,.75f,true);int max;public LruCache(int n){max=n;}public synchronized V get(K k){return m.get(k);}public synchronized void put(K k,V v){m.put(k,v);while(m.size()>max)m.remove(m.keySet().iterator().next());}public synchronized void evictAll(){m.clear();}}''',
      'android/graphics/drawable/Drawable.java':'''package android.graphics.drawable;public class Drawable{public int tint;public Drawable mutate(){return this;}public ConstantState getConstantState(){return new ConstantState();}public static class ConstantState{public boolean canApplyTheme(){return false;}public Drawable newDrawable(android.content.res.Resources r){return new Drawable();}}}''',
      'android/content/res/Resources.java':'''package android.content.res;import android.graphics.drawable.Drawable;import java.util.concurrent.*;
public class Resources{public static class Theme{}public static class NotFoundException extends RuntimeException{}public static final java.util.concurrent.atomic.AtomicInteger decodes=new java.util.concurrent.atomic.AtomicInteger();public static volatile int blockId=-1;public static volatile CountDownLatch entered=new CountDownLatch(1),release=new CountDownLatch(1);Configuration config=new Configuration();
 public Resources(){}public Resources(Object a,android.util.DisplayMetrics m,Configuration c){config=new Configuration(c);}public Object getAssets(){return this;}public android.util.DisplayMetrics getDisplayMetrics(){return new android.util.DisplayMetrics();}public Configuration getConfiguration(){return config;}
 public void updateConfiguration(Configuration c,android.util.DisplayMetrics m){config=new Configuration(c);}public Drawable getDrawable(int id){return getDrawableForDensity(id,0,null);}public Drawable getDrawable(int id,Theme t){return getDrawableForDensity(id,0,t);}public Drawable getDrawableForDensity(int id,int d){return getDrawableForDensity(id,d,null);}
 public Drawable getDrawableForDensity(int id,int d,Theme t){decodes.incrementAndGet();if(id==blockId){entered.countDown();try{if(!release.await(3,TimeUnit.SECONDS))throw new AssertionError("blocked decode");}catch(InterruptedException e){throw new AssertionError(e);}}return new Drawable();}}
''',
      'app/exteraless/icons/IconPackManager.java':'''package app.exteraless.icons;public class IconPackManager{static final IconPackManager instance=new IconPackManager();public static IconPackManager getInstance(){return instance;}public android.graphics.drawable.Drawable getDrawable(Object r,int id,int dpi,Object t){if(!Thread.currentThread().getName().equals("main"))throw new AssertionError("worker used icon pack manager");return null;}}''',
      'app/flexygram/icons/ExactIcons.java':'''package app.flexygram.icons;public class ExactIcons{public static android.graphics.drawable.Drawable create(Object r,int id,int dpi,Object t){if(!Thread.currentThread().getName().equals("main"))throw new AssertionError("worker used replacements");return null;}}''',
      'xyz/nextalone/nagram/NaConfig.java':'''package xyz.nextalone.nagram;public class NaConfig{public static final NaConfig INSTANCE=new NaConfig();public Value getIconReplacements(){return new Value();}public static class Value{public int Int(){return 0;}}}''',
      'tw/nekomimi/nekogram/ui/icons/SolarIcons.java':'''package tw.nekomimi.nekogram.ui.icons;public class SolarIcons{public static final SolarIcons Companion=new SolarIcons();public int getConversion(int n){return n;}}''',
      'Probe.java':'''import tw.nekomimi.nekogram.ui.icons.IconsResources;import android.content.res.*;import java.util.concurrent.*;
public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 static void idle(IconsResources r)throws Exception{var f=IconsResources.class.getDeclaredField("warming");f.setAccessible(true);var busy=(java.util.concurrent.atomic.AtomicBoolean)f.get(r);long end=System.nanoTime()+TimeUnit.SECONDS.toNanos(3);while(busy.get()&&System.nanoTime()<end)Thread.sleep(1);check(!busy.get());}
 static void block(int id){Resources.blockId=id;Resources.entered=new CountDownLatch(1);Resources.release=new CountDownLatch(1);}
 public static void main(String[]args)throws Exception{
  IconsResources r=new IconsResources(new Resources());check(r.preloadOriginalIcons(null)==null&&r.preloadOriginalIcons(new int[33])==null);
  check(r.preloadOriginalIcons(new int[]{11,12,13})!=null);idle(r);int decoded=Resources.decodes.get();check(decoded==3);
  var a=r.getDrawable(11);var b=r.getDrawable(11);a.tint=42;check(a!=b&&b.tint==0&&Resources.decodes.get()==decoded);
  check(r.preloadOriginalIcons(new int[]{11,12,13})==null);check(r.preloadOriginalIcons(new int[]{14})!=null);idle(r);check(Resources.decodes.get()==decoded+1);
  block(20);Runnable cancel=r.preloadOriginalIcons(new int[]{20,21});check(Resources.entered.await(3,TimeUnit.SECONDS));
  for(int i=0;i<1000;i++)check(r.preloadOriginalIcons(new int[]{20})==null);
  cancel.run();Resources.release.countDown();idle(r);Resources.blockId=-1;decoded=Resources.decodes.get();r.getDrawable(20);check(Resources.decodes.get()==decoded+1);r.getDrawable(21);check(Resources.decodes.get()==decoded+2);
  block(30);r.preloadOriginalIcons(new int[]{30,31});check(Resources.entered.await(3,TimeUnit.SECONDS));Configuration changed=new Configuration();changed.generation=1;r.updateConfiguration(changed,r.getDisplayMetrics());Resources.release.countDown();idle(r);Resources.blockId=-1;decoded=Resources.decodes.get();r.getDrawable(30);check(Resources.decodes.get()==decoded+1);
  r.preloadOriginalIcons(new int[]{11,12,13});idle(r);decoded=Resources.decodes.get();r.getDrawable(11);check(Resources.decodes.get()==decoded);
 }
}'''
    }
    probe(tmp_path,files,[JAVA/'tw/nekomimi/nekogram/ui/icons/IconsResources.java'])
