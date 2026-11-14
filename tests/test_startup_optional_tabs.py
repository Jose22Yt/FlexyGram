"""Run real lazy destination creation, selection and gesture updates with sparse tab slots."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_optional_destinations_are_created_once_on_demand_and_sparse_updates_work(tmp_path):
    source = (JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
    methods = '\n'.join(method(source, anchor) for anchor in ['private void ensureFlexyTab(', 'public void selectTab(', 'public void setGestureSelectedOverride('])
    probe(tmp_path, {
        'org/telegram/ui/Components/glass/GlassTabView.java': '''package org.telegram.ui.Components.glass;
public class GlassTabView{public boolean selected,compact;public float gesture;public void setMainTabsCompact(boolean b){compact=b;}public void setSelected(boolean b,boolean a){selected=b;}public void setGestureSelectedOverride(float v,boolean a){gesture=v;}}''',
        'app/flexygram/navigation/LiquidNavigationTabs.java': '''package app.flexygram.navigation;import org.telegram.ui.Components.glass.GlassTabView;
public class LiquidNavigationTabs{public static int creates;public static GlassTabView create(Object c,Object p,int a,int id){if(c==null)throw new AssertionError();creates++;return new GlassTabView();}}''',
        'app/flexygram/navigation/LiquidNavigationConfig.java': 'package app.flexygram.navigation;public class LiquidNavigationConfig{public static boolean configured(){return true;}}',
        'app/flexygram/navigation/LiquidNavigationDestinations.java': 'package app.flexygram.navigation;public class LiquidNavigationDestinations{public static boolean contains(int[]a,int id){for(int n:a)if(n==id)return true;return false;}}',
        'Probe.java': '''import java.util.*;import org.telegram.ui.Components.glass.GlassTabView;import app.flexygram.navigation.LiquidNavigationTabs;
public class Probe{
 GlassTabView[]tabs=new GlassTabView[11];int currentAccount,currentSelectedTabPosition;Object resourceProvider;int[]flexyShownDestinations={0,1,2,4},flexyConfiguredDestinations={0,1,2,4};
 static class MainTabsHelper{static boolean isMainTabsHideTitleStyle(){return true;}}
 static class Tabs{int added,bound,ignored;Object context=new Object();Object getContext(){return context;}void addView(GlassTabView v){added++;}void addTabToIgnoreClick(GlassTabView v){ignored++;}void setViewVisible(GlassTabView v,boolean visible,boolean animated){if(visible)throw new AssertionError();}void revealSelectedDestination(){}void invalidate(){}}
 Tabs tabsView=new Tabs();void bindTabClicks(GlassTabView view,int id){tabsView.bound++;}int indexToPosition(int id){return id<6?id:-1;}
 METHODS
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 public static void main(String[]args){
  Probe p=new Probe();for(int i=0;i<6;i++)p.tabs[i]=new GlassTabView();
  for(int id:p.flexyShownDestinations)p.ensureFlexyTab(id);check(LiquidNavigationTabs.creates==0&&p.tabsView.added==0);
  p.selectTab(0,false);p.setGestureSelectedOverride(0,true);check(p.tabs[0].selected&&p.tabs[0].gesture==1);
  p.flexyShownDestinations=new int[]{0,6,9};p.flexyConfiguredDestinations=new int[]{0,6,2,4};
  for(int id:p.flexyShownDestinations)p.ensureFlexyTab(id);GlassTabView groups=p.tabs[6];
  check(LiquidNavigationTabs.creates==2&&groups.compact&&p.tabsView.bound==2&&p.tabsView.ignored==2);
  for(int i=0;i<1000;i++)for(int id:p.flexyShownDestinations)p.ensureFlexyTab(id);
  check(LiquidNavigationTabs.creates==2&&p.tabs[6]==groups);
  p.selectTab(2,false);p.setGestureSelectedOverride(2,true);check(p.tabs[9].selected&&p.tabs[9].gesture==1);
  p.ensureFlexyTab(-1);p.ensureFlexyTab(11);check(LiquidNavigationTabs.creates==2);
  p.ensureFlexyTab(10);check(LiquidNavigationTabs.creates==3&&p.tabs[7]==null&&p.tabs[8]==null);
 }
}'''.replace('METHODS',methods)})
    create = method(source, 'public View createView(')
    assert 'for (int id = 6; id < tabs.length; id++)' not in create
    assert 'for (int id : shown) ensureFlexyTab(id);' in method(source, 'private void applyFlexyTabs()')
