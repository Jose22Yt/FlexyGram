"""Exercise production page selection and dock measurement with counted children."""
import sqlite3
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method


def test_archive_initial_page_keeps_pagination_and_end_threshold(tmp_path):
    source = (JAVA/'org/telegram/messenger/MessagesStorage.java').read_text()
    start = source.index('                    if (a == 0) {', source.index('public void getDialogs(int folderId'))
    end = source.index('\n\n', start)
    branch = source[start:end]
    probe(tmp_path, {'Probe.java': '''public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){
 for(int count:new int[]{1,19,20,32,100,150})for(int a=0;a<2;a++){
  int offset=64,off,cnt;
  BRANCH
  check(a==0?off==offset&&cnt==count:off==0&&cnt>=20&&cnt<=100&&cnt==(count<20?20:Math.min(100,count)));
 }
 }}'''.replace('BRANCH', branch)})
    # A bounded first page leaves the remainder available through the normal offset.
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE dialogs(did INTEGER, pinned INTEGER, date INTEGER)')
    db.executemany('INSERT INTO dialogs VALUES (?,0,?)', [(i,i) for i in range(101)])
    pages = [db.execute('SELECT did FROM dialogs ORDER BY pinned DESC,date DESC LIMIT ?,?', (offset,32)).fetchall() for offset in range(0,101,32)]
    assert len(pages[0]) == 32
    assert [row[0] for page in pages for row in page] == list(reversed(range(101)))


def test_hidden_dock_tabs_keep_exit_geometry_without_measurement(tmp_path):
    source = (JAVA/'org/telegram/ui/MainTabsLayout.java').read_text()
    measure = method(source, '@Override protected void onMeasure(int ws,int hs)')
    probe(tmp_path, {
      'app/flexygram/navigation/LiquidNavigationMath.java': '''package app.flexygram.navigation;public class LiquidNavigationMath{public static int dockWidth(int a,int c,int p,int m,float f,boolean b){return a;}}''',
      'Probe.java': '''class View{
 boolean visible=true;int width=75,measures;void measure(int w,int h){width=w;measures++;}
}
class GlassTabView extends View{int styles;void setSkipDrawSelector(boolean b){}void setTextSizeDp(int s){}void setMainTabsAppearance(boolean h,int i){styles++;}}
class LiquidNavigationConfig{static boolean showTitles(){return false;}static float widthFraction(){return 1;}static boolean isFloatingDock(){return true;}static boolean hideLabels(int c,int w){return false;}static int iconDp(){return 24;}}
class Base{protected void onMeasure(int w,int h){}}
public class Probe extends Base{
 interface Tab{float measureTextWidth(int s);}
 static class MeasureSpec{static final int EXACTLY=0;static int getSize(int s){return s;}static int makeMeasureSpec(int s,int m){return s;}}
 static class Metrics{float density=1;}static class Resources{Metrics getDisplayMetrics(){return new Metrics();}}
 View[]children={new GlassTabView(),new GlassTabView(),new GlassTabView()};int maxWidthPx,slotWidth,total;
 int getChildCount(){return children.length;}View getChildAt(int i){return children[i];}boolean isViewVisible(View v){return v.visible;}
 int getPaddingLeft(){return 0;}int getPaddingRight(){return 0;}int getPaddingTop(){return 0;}int getPaddingBottom(){return 0;}int dp(int n){return n;}Resources getResources(){return new Resources();}
 void setMeasuredDimension(int w,int h){total=w;}void calculateTotalSizesAfterMeasure(){}
 MEASURE
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();p.children[1].visible=false;
 p.onMeasure(101,60);check(p.children[0].width==51&&p.children[2].width==50&&p.children[1].width==75);
 for(int i=0;i<100;i++)p.onMeasure(101,60);
 check(p.children[1].measures==0&&((GlassTabView)p.children[1]).styles==0);
 p.children[1].visible=true;p.onMeasure(102,60);for(View v:p.children)check(v.width==34);
 for(View v:p.children)v.visible=false;p.onMeasure(102,60);for(View v:p.children)check(v.width==34);
 }}'''.replace('MEASURE', measure)
    })
