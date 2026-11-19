"""Exercise the actual home capture scheduler across effect and viewport changes."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_opaque_home_skips_list_capture_and_reenabling_updates_before_drawing(tmp_path):
    source = (JAVA / 'org/telegram/ui/DialogsActivity.java').read_text()
    update = method(source, 'private void blur3_UpdateBlur()')
    probe(tmp_path, {
        'app/exteraless/appearance/MainTabsUiHelper.java': '''package app.exteraless.appearance;
public class MainTabsUiHelper{public static void setBlurBounds(Object rect,Object view,int height){}}''',
        'Probe.java': '''
public class Probe {
 static class Build{static class VERSION{static int SDK_INT=31;}static class VERSION_CODES{static final int S=31;}}
 static class SharedConfig{static boolean enabled;static boolean chatBlurEnabled(){return enabled;}}
 static class LiteMode{static final int FLAG_LIQUID_GLASS=1;static boolean enabled;static boolean isEnabled(int flag){return enabled;}}
 static class View{static final int VISIBLE=0;int width=1080,height=1920;int getMeasuredWidth(){return width;}int getMeasuredHeight(){return height;}int getVisibility(){return VISIBLE;}int getSumHeightOfAllVisibleChild(){return 10;}}
 static class MainTabsLayout{static boolean visible;static boolean isBottomNavigationVisible(){return visible;}}
 static class DialogStoriesCell{static final int HEIGHT_IN_DP=100;}
 static class Rect{float left,top,right,bottom;void set(float l,float t,float r,float b){left=l;top=t;right=r;bottom=b;}void inset(float x,float y){left+=x;right-=x;top+=y;bottom-=y;}}
 static class Animator{float getFloatValue(){return .5f;}}
 static class Suppressor{int setups,captures,regions,shared;boolean shareResult=true;void setupRenderNodes(Object p,int n){setups++;regions=n;}void invalidateResultRenderNodes(Object c,int w,int h){captures++;}boolean captureDisjointRegions(Object c,int w,int h){shared++;return shareResult;}}
 static class Source{int updates,width,height;void setSize(int w,int h){width=w;height=h;}void updateDisplayListIfNeeded(){updates++;}}
 Suppressor scrollableViewNoiseSuppressor=new Suppressor();View fragmentView=new View(),actionBar=new View(),filterTabsView,topPanelLayout,searchTabsAndFiltersLayout,commentView,chatInputViewsContainer;
 static class Controller{boolean visible=true;boolean hasVisibleTabsSurface(){return visible;}}
 Controller mainTabsActivityController;
 boolean hasStories,hasMainTabs;int navigationBarHeight;float scrollYOffset;Object iBlur3Positions=new Object(),iBlur3Capture=new Object();
 Rect iBlur3PositionActionBar=new Rect(),iBlur3PositionMainTabs=new Rect();Animator animatorSearchVisible=new Animator();
 Object scrollingBlurCapture=new Object();boolean canShare;boolean canShareScrollingBlur(){return canShare;}
 Source iBlur3SourceGlassFrosted=new Source(),iBlur3SourceGlass=new Source();
 static int dp(int n){return n;}static float lerp(float a,float b,float f){return a+(b-a)*f;}
 int getIdleSearchFieldHeight(){return 40;}int calculateListViewPaddingBottom(){return 100;}
 UPDATE
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){
  Probe p=new Probe();for(int i=0;i<1000;i++)p.blur3_UpdateBlur();
  check(p.scrollableViewNoiseSuppressor.captures==0&&p.scrollableViewNoiseSuppressor.setups==0);
  check(p.iBlur3SourceGlass.updates==1000&&p.iBlur3SourceGlassFrosted.updates==1000);
  p.fragmentView.width=720;p.fragmentView.height=1280;p.blur3_UpdateBlur();check(p.iBlur3SourceGlass.width==720&&p.iBlur3SourceGlass.height==1280);
  SharedConfig.enabled=true;p.blur3_UpdateBlur();check(p.scrollableViewNoiseSuppressor.captures==1&&p.scrollableViewNoiseSuppressor.regions==1);
  p.hasMainTabs=true;MainTabsLayout.visible=true;p.blur3_UpdateBlur();check(p.scrollableViewNoiseSuppressor.captures==2&&p.scrollableViewNoiseSuppressor.regions==2);
  SharedConfig.enabled=false;LiteMode.enabled=true;for(int i=0;i<1000;i++)p.blur3_UpdateBlur();check(p.scrollableViewNoiseSuppressor.captures==2);
  SharedConfig.enabled=true;p.hasMainTabs=false;p.commentView=new View();p.chatInputViewsContainer=new View();p.blur3_UpdateBlur();
  check(p.scrollableViewNoiseSuppressor.captures==3&&p.scrollableViewNoiseSuppressor.regions==2&&p.iBlur3PositionMainTabs.top==1180);
  Build.VERSION.SDK_INT=30;p.blur3_UpdateBlur();check(p.scrollableViewNoiseSuppressor.captures==3);
  Build.VERSION.SDK_INT=31;p.fragmentView=null;p.blur3_UpdateBlur();check(p.scrollableViewNoiseSuppressor.captures==3);
  p.fragmentView=new View();p.canShare=true;p.blur3_UpdateBlur();
  check(p.scrollableViewNoiseSuppressor.shared==1&&p.scrollableViewNoiseSuppressor.captures==3);
  p.scrollableViewNoiseSuppressor.shareResult=false;p.blur3_UpdateBlur();
  check(p.scrollableViewNoiseSuppressor.shared==2&&p.scrollableViewNoiseSuppressor.captures==4);
 }
}'''.replace('UPDATE', update)
    })


def test_shared_scrolling_capture_scans_children_once_and_skips_the_gap(tmp_path):
    source = (JAVA / 'org/telegram/ui/Components/RecyclerListView.java').read_text()
    pair = method(source, 'public boolean captureDisjointRegions(Canvas canvas, RectF first, RectF second)')
    views = method(source, 'private void captureChildViews(Canvas canvas, RectF first, RectF second, long drawingTime)')
    probe(tmp_path, {'Probe.java': '''
import java.util.*;
public class Probe {
 record RectF(float top,float bottom) {
  boolean intersects(float l,float t,float r,float b){return t<bottom&&b>top;}
 }
 static class Canvas {int depth;int save(){return depth++;}void restoreToCount(int d){depth=d;}void clipRect(RectF rect){}}
 static class SystemClock {static long uptimeMillis(){return 1;}}
 record View(float y,int height) {
  float getX(){return 0;}float getY(){return y;}int getWidth(){return 200;}int getHeight(){return height;}
 }
 final List<View> children=List.of(new View(-20,50),new View(5,90),new View(60,10),new View(85,30),new View(120,10));
 final List<View> drawn=new ArrayList<>();
 int visits,decorations;boolean edge,ignoreClipChild;
 static final int OVER_SCROLL_NEVER=2;
 boolean hasActiveEdgeEffects(){return edge;}int getOverScrollMode(){return 0;}
 int getChildCount(){return children.size();}
 View getChildAt(int index){visits++;return children.get(index);}
 void captureDecorations(Canvas canvas,RectF region){if(canvas.depth!=1)throw new AssertionError();decorations++;}
 void drawChild(Canvas canvas,View view,long time){if(!ignoreClipChild)throw new AssertionError();drawn.add(view);}
 CAPTURE_PAIR
 CHILD_VIEWS
 public static void main(String[] args){
  Probe p=new Probe();Canvas canvas=new Canvas();RectF top=new RectF(0,20),bottom=new RectF(90,110);
  if(!p.captureDisjointRegions(canvas,top,bottom)||p.visits!=5||p.decorations!=2||canvas.depth!=0
      ||!p.drawn.equals(List.of(p.children.get(0),p.children.get(1),p.children.get(3))))throw new AssertionError();
  p.edge=true;
  if(p.captureDisjointRegions(canvas,top,bottom)||p.visits!=5)throw new AssertionError();
 }
}'''.replace('CAPTURE_PAIR', pair).replace('CHILD_VIEWS', views)})
