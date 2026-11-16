"""Execute native fragment ownership paths with explicit host APIs, not GPU claims."""
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method


def test_rebuilt_fragment_cannot_reuse_renderer_bound_to_old_dock_or_scene(tmp_path):
    text=(JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
    bodies='\n'.join(method(text,s) for s in [
        'private void updateKyantDock()', 'public void clearViews()', 'public void onPause()'])
    if 'private void releaseKyantDock()' in text:
        bodies+='\n'+method(text,'private void releaseKyantDock()')
    probe(tmp_path,{
      'android/os/Build.java':'package android.os;public class Build{public static class VERSION{public static int SDK_INT=33;}}',
      'android/view/ViewGroup.java':'package android.view;public class ViewGroup{public static class LayoutParams{public static int MATCH_PARENT=-1;}}',
      'android/widget/FrameLayout.java':'package android.widget;public class FrameLayout{public static class LayoutParams{public LayoutParams(int x,int y){}}}',
      'app/flexygram/kyant/KyantDockConfig.java':'package app.flexygram.kyant;public class KyantDockConfig{public static boolean on=true;public static boolean enabled(){return on;}}',
      'app/flexygram/kyant/KyantDockView.java':'''package app.flexygram.kyant;
public class KyantDockView{public static int creates;public final Object dock,scene;public int pauses;
 public KyantDockView(Object c,Object d,Object s){creates++;dock=d;scene=s;}public void onHostPause(){pauses++;}}''',
      'Probe.java':'''import android.os.Build;import android.view.ViewGroup;import android.widget.FrameLayout;import app.flexygram.kyant.*;
class Parent{int clears;public void clearViews(){clears++;}public void onPause(){}}
public class Probe extends Parent{
 static class Dock{Object host;Object getContext(){return this;}void setKyantHost(Object v){host=v;}}
 static class Host{Object child;void addView(Object v,Object p){if(child!=null)throw new AssertionError("duplicate overlay");child=v;}void removeView(Object v){if(child==v)child=null;}}
 static class Pager{void setPosition(int p){}}
 static class Hint{void hide(){}}
 static class MainTabsHelper{static boolean isContactsTabHidden(){return false;}static boolean isCallsTabHidden(){return false;}static boolean isProfileTabHidden(){return false;}}
 boolean lastHideContacts,lastHideCalls,lastHideProfile,dropCallsFragmentAfterPageScroll;
 int getStartPosition(){return 0;}void dropFragmentAtPosition(int p){}
 Dock tabsView=new Dock();Host tabsViewWrapper=new Host();Pager viewPager=new Pager();KyantDockView kyantDockView;Hint accountSwitchHint;
 BODIES
 static void check(boolean b,String message){if(!b)throw new AssertionError(message);}
 public static void main(String[]args){Probe p=new Probe();
  p.updateKyantDock();var first=p.kyantDockView;var oldDock=p.tabsView;var oldWrapper=p.tabsViewWrapper;
  p.clearViews();check(p.kyantDockView==null,"clearViews must drop the obsolete optical host");
  check(oldDock.host==null&&oldWrapper.child==null&&first.pauses==1,"old dock and composition are released");
  p.tabsView=new Dock();p.tabsViewWrapper=new Host();p.viewPager=new Pager();p.updateKyantDock();
  check(p.kyantDockView!=first&&p.kyantDockView.dock==p.tabsView&&p.kyantDockView.scene==p.viewPager,"renderer binds current dock AND scene");
  var current=p.kyantDockView;int creates=KyantDockView.creates;
  for(int i=0;i<10000;i++)p.updateKyantDock();check(p.kyantDockView==current&&KyantDockView.creates==creates,"no per-frame renderer churn");
  p.onPause();check(p.kyantDockView==null&&p.tabsView.host==null&&p.tabsViewWrapper.child==null,"pause releases the entire optical view");
  p.onPause();p.clearViews();check(current.pauses==1,"cleanup is idempotent");
  p.updateKyantDock();check(p.kyantDockView!=current,"return creates a fresh view, not an obsolete composition context");
  KyantDockConfig.on=false;p.updateKyantDock();check(p.kyantDockView==null&&p.tabsView.host==null&&p.tabsViewWrapper.child==null,"OFF retains only native controls");
 }}'''.replace('BODIES',bodies)
    })
