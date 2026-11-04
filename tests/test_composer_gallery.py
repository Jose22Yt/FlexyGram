"""Exercise production miniature drawing and row routing without Android/IME or an APK."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_compact_previews_fit_all_existing_position_and_size_values(tmp_path):
    source=(JAVA/'app/flexygram/composer/FlexyComposerSettingsActivity.java').read_text()
    preview=source[source.index('private final class Preview'):]
    draw=method(preview,'private void drawComposer(')
    measure=method(preview,'protected void onMeasure(').replace('@Override ', '')
    probe(tmp_path, {'Probe.java': '''
import app.flexygram.composer.*;
public class Probe {
 static float density=1;
 static int dp(float value){return Math.round(value*density);}
 static void check(boolean b){if(!b)throw new AssertionError();}
 static class R{static class string{static final int TypeMessage=1;}}
 static class Theme{static final int key_chat_messagePanelBackground=1,key_chat_messagePanelSend=2,key_chat_messagePanelIcons=3,key_chat_messagePanelHint=4;}
 static class ColorUtils{static double calculateLuminance(int color){return .8;}}
 static class org{static class telegram{static class messenger{static class AndroidUtilities{static float density=1;}}}}
 static class FlexyComposerConfig{
  static final int CLASSIC=0;static int level,position;static boolean compact;
  static boolean compact(){return compact;}static int level(){return level;}
  static int position(){return position;}static boolean glass(){return false;}
  static int gap(){return ComposerStyle.gap(level,0);}static boolean referenceIcons(){return true;}
 }
 static class Paint{
  static class Align{static final Align LEFT=new Align();}
  void setColor(int c){}void setTextSize(float s){}void setTextAlign(Align a){}
  float ascent(){return -12*density;}float descent(){return 4*density;}
 }
 static class Drawable{}
 static class Canvas{
  final float width,height;int shapes;float firstY=Float.NaN,firstRadius;
  Canvas(float w,float h){width=w;height=h;}
  void bounds(float l,float t,float r,float b){check(l>=-.1&&t>=-.1&&r<=width+.1&&b<=height+.1&&l<=r&&t<=b);shapes++;}
  void drawRoundRect(float l,float t,float r,float b,float rx,float ry,Paint p){bounds(l,t,r,b);}
  void drawCircle(float x,float y,float r,Paint p){if(Float.isNaN(firstY)){firstY=y;firstRadius=r;}bounds(x-r,y-r,x+r,y+r);}
  int save(){return 0;}void restoreToCount(int s){}void clipRect(float l,float t,float r,float b){check(l<=r&&t<=b);}
  void drawText(String text,float x,float y,Paint p){}
 }
 static class Resources{Metrics getDisplayMetrics(){return new Metrics();}}
 static class Metrics{float scaledDensity=density;}
 static class MeasureSpec{static int getSize(int w){return w;}}
 int forcedStyle,measuredHeight;final Paint paint=new Paint();
 final Drawable plus=new Drawable(),clip=new Drawable(),smile=new Drawable(),folded=new Drawable(),voice=new Drawable();
 int getThemedColor(int key){return 0;}String getString(int key){return "Mensaje";}
 Resources getResources(){return new Resources();}
 void icon(Canvas c,Drawable d,float x,float y,int color){check(y-dp(14)>=-.1&&y+dp(14)<=c.height+.1);}
 void setMeasuredDimension(int w,int h){measuredHeight=h;}
 DRAW
 MEASURE
 public static void main(String[]args){
  Probe view=new Probe();
  for(float d:new float[]{1,1.5f,2,3}){
   density=d;org.telegram.messenger.AndroidUtilities.density=d;
   for(int style:new int[]{0,1})for(int width:new int[]{240,320,412,600})
    for(int level=0;level<3;level++)for(int position=-4;position<=16;position++){
     view.forcedStyle=style;FlexyComposerConfig.level=level;FlexyComposerConfig.position=position;
     view.onMeasure(dp(width),0);check(view.measuredHeight==dp(64));
     float height=view.measuredHeight/.8f;Canvas c=new Canvas(dp(width)/.8f,height);
     view.drawComposer(c,c.width,c.height);check(c.shapes==3||style==0&&c.shapes==2);
     if(style==1){check(Math.abs(c.firstY-(height/2-dp(position)))<.01);check(c.firstRadius==dp(ComposerStyle.diameter(level))/2f);}
    }
   view.forcedStyle=-1;view.onMeasure(dp(360),0);check(view.measuredHeight==dp(96));
  }
 }
}'''.replace('DRAW',draw).replace('MEASURE',measure)}, [
        JAVA/'app/flexygram/composer/ComposerStyle.java',
        JAVA/'app/flexygram/composer/ComposerGeometry.java'])


def test_composer_controls_follow_gallery_without_adding_rows_to_header(tmp_path):
    source=(JAVA/'app/flexygram/settings/signature/ConversationStyleSettingsActivity.java').read_text()
    adapter=source[source.index('@Override protected BaseListAdapter createAdapter'):]
    probe(tmp_path, {'Probe.java': '''import java.util.*;
public class Probe {
 static final int GALLERY=310,POSITION=311,TYPE_HEADER=4,TYPE_INFO_PRIVACY=7,TYPE_SETTINGS=2;
 static class HeaderConfig{static void load(){}}
 static class Base{int rowCount;final List<String> keys=new ArrayList<>();
  void updateRows(){rowCount=0;keys.clear();}int addRow(){return addRow("");}
  int addRow(String key){keys.add(key);return rowCount++;}int addHeader(String key){return addRow(key);}}
 static class Page extends Base{
  boolean header;int galleryRow,layoutHeaderRow,levelRow,positionRow,resetPositionRow,infoRow;
  __ROWS__
  class Adapter{__TYPE__}
 }
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){
  Page page=new Page();Page.Adapter a=page.new Adapter();
  page.updateRows();check(page.rowCount==6&&page.galleryRow==0);
  check(a.getItemViewType(0)==GALLERY&&a.getItemViewType(1)==TYPE_HEADER);
  check(page.levelRow==2&&page.positionRow==3&&page.resetPositionRow==4&&page.infoRow==5);
  check(a.getItemViewType(page.positionRow)==POSITION&&a.getItemViewType(page.levelRow)==TYPE_SETTINGS);
  check(page.keys.contains("flexyComposerLevel")&&page.keys.contains("flexyComposerPosition"));
  page.header=true;page.updateRows();check(page.rowCount==1&&a.getItemViewType(0)==GALLERY);
  check(page.positionRow==-1&&page.levelRow==-1&&page.infoRow==-1);
 }
}'''.replace('__ROWS__',method(source,'protected void updateRows()')).replace('__TYPE__',method(adapter,'public int getItemViewType('))})
