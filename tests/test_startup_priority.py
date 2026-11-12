"""Startup scheduling and warm-resume layout regressions; no device timing claim."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_local_dialog_request_precedes_plugin_start_and_no_new_frame_gate():
    source = (JAVA/'org/telegram/messenger/ApplicationLoader.java').read_text()
    init = method(source, 'public static void postInitApplication(boolean prepareDialogs)')
    assert init.index('initializeStartupAccount(a, prepareDialogs && a == startupAccount)') < init.index('PluginsController.getInstance().init(applicationContext)')
    core = method(source, 'private static void initializeStartupAccount(int a, boolean prepareDialogs)')
    assert core.index('prepareSelectedDialogs();') < core.index('checkStartupUnsentMessages(a)')
    assert 'postFrameCallback' not in core and 'Thread.sleep' not in core
    sender = method(source, 'private static void checkStartupUnsentMessages(int account)')
    assert sender.index('getCurrentUser() != null') < sender.index('checkUnsentMessages()')


def test_bottom_bar_resume_preserves_geometry_without_repeated_layout(tmp_path):
    source = (JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
    start = source.index('FrameLayout.LayoutParams dockParams =', source.index('private void applyFlexyTabs()'))
    margins = method(source[start:], 'if (dockParams != null)')
    refresh = method((JAVA/'org/telegram/ui/MainTabsLayout.java').read_text(), 'public void refreshBottomBarAppearance()')
    probe(tmp_path, {'Probe.java': '''
public class Probe {
 static class FrameLayout{static class LayoutParams{int leftMargin,rightMargin;}}
 static class LocaleController{static boolean isRTL;}
 static class Theme{static final int key_windowBackgroundWhite=1;static int color=100;static int getColor(int k,Object p){return color;}}
 static class LiquidNavigationConfig{static int radius=20;static int radiusDp(){return radius;}}
 static class Selection{void cancel(){}}
 static class Surface{int color;float radius;void setColor(int c){color=c;}void setCornerRadius(float r){radius=r;}}
 static class GlassTabView{boolean skip;void setSkipDrawSelector(boolean value){skip=value;}}
 static class Background{int updates;void updateColors(){updates++;}}
 static class Tabs{int layouts;void setLayoutParams(FrameLayout.LayoutParams p){layouts++;}}
 Tabs tabsView=new Tabs();Selection selection=new Selection();float selectionX;Surface surface=new Surface();
 Object resourcesProvider;Background glassBackground=new Background();GlassTabView child=new GlassTabView();
 int layouts,invalidations;int dp(int value){return value*2;}void requestLayout(){layouts++;}void invalidate(){invalidations++;}
 int getChildCount(){return 1;}Object getChildAt(int i){return child;}
 REFRESH
 void margins(FrameLayout.LayoutParams dockParams,int reservedSearch){MARGINS}
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 public static void main(String[] args){
  Probe p=new Probe();FrameLayout.LayoutParams params=new FrameLayout.LayoutParams();
  for(int i=0;i<10000;i++){p.margins(params,0);p.refreshBottomBarAppearance();}
  check(p.layouts==0&&p.tabsView.layouts==0&&p.child.skip&&p.surface.color==100&&p.surface.radius==40);
  p.margins(params,48);check(params.leftMargin==0&&params.rightMargin==48&&p.tabsView.layouts==1);
  for(int i=0;i<10000;i++)p.margins(params,48);check(p.tabsView.layouts==1);
  LocaleController.isRTL=true;p.margins(params,48);check(params.leftMargin==48&&params.rightMargin==0&&p.tabsView.layouts==2);
  p.margins(params,0);check(params.leftMargin==0&&params.rightMargin==0&&p.tabsView.layouts==3);
  p.margins(null,48);check(p.tabsView.layouts==3);
  Theme.color=200;LiquidNavigationConfig.radius=30;p.refreshBottomBarAppearance();
  check(p.surface.color==200&&p.surface.radius==60&&p.layouts==0&&p.glassBackground.updates==10001);
 }
}'''.replace('REFRESH',refresh).replace('MARGINS',margins)})
