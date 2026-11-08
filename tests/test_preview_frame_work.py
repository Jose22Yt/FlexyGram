"""Work-count probes of production previews and deletion; these are not device FPS."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_classic_header_prepares_text_once_not_every_draw(tmp_path):
    source=(JAVA/'app/flexygram/header/HeaderPreviewView.java').read_text()
    methods='\n'.join(method(source,s) for s in ['private void prepareClassicText(', 'private void drawClassic('])
    assert 'if(previewStyle()==1){prepareClassicText(width);return;}' in method(source,'protected void onMeasure(')
    methods=methods.replace('android.text.TextUtils','TextUtils').replace('android.graphics.PorterDuff','PorterDuff')
    probe(tmp_path, {'Probe.java': '''public class Probe {
 static class AndroidUtilities {static float density=1;static int dp(float f){return Math.round(f*density);}}
 static class LocaleController {static boolean isRTL;}
 static class Theme {static int key_actionBarDefault,key_actionBarDefaultTitle,key_windowBackgroundWhiteBlueText,key_actionBarDefaultSubtitle;static int getColor(int key){return key;}}
 static class PorterDuff {static class Mode{static Object SRC_IN;}}
 static class Paint {float size;void setTextSize(float s){size=s;}void set(Paint p){size=p.size;}void setColor(int c){}void setTextAlign(Object a){}static class Align{static Object RIGHT,LEFT,CENTER;}}
 static class TextUtils {static int calls;static float[] widths=new float[2],sizes=new float[2];static class TruncateAt{static Object END;}
 static CharSequence ellipsize(String s,Paint p,float w,Object t){widths[calls%2]=w;sizes[calls%2]=p.size;calls++;return w<=0?"":s;}}
 static class Canvas {int texts;void drawRect(float a,float b,float c,float d,Paint p){}void drawCircle(float a,float b,float c,Paint p){}int save(){return 0;}void rotate(float a,float b,float c){}void restoreToCount(int i){}void drawText(String t,float a,float b,Paint p){if(!t.isEmpty())texts++;}}
 static class Icon {void setColorFilter(int c,Object m){}void setBounds(int a,int b,int c,int d){}void draw(Canvas c){}}
 Paint text=new Paint(),scratchPaint=new Paint(),avatar=new Paint();Icon back=new Icon(),more=new Icon();
 float titlePx=16,subtitlePx=12;String name="Nombre muy largo",status="en línea",displayName="",displayStatus="";
 int getHeight(){return 100;}int getWidth(){return 360;}
 METHODS
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args){Probe p=new Probe();p.prepareClassicText(360);Canvas c=new Canvas();
 for(int i=0;i<1000;i++){LocaleController.isRTL=i%2==0;p.drawClassic(c);}
 check(TextUtils.calls==2&&c.texts==2000&&TextUtils.widths[0]==238&&TextUtils.sizes[0]==16&&TextUtils.sizes[1]==12);
 AndroidUtilities.density=2;p.titlePx=32;p.subtitlePx=24;p.prepareClassicText(200);
 check(TextUtils.calls==4&&TextUtils.widths[0]==0&&TextUtils.sizes[1]==24);
 }
}'''.replace('METHODS',methods)})


def test_bubble_measure_reuses_layouts_and_invalidates_width_density_theme(tmp_path):
    source=(JAVA/'app/flexygram/bubbles/BubblePreviewView.java').read_text()
    measure=method(source,'protected void onMeasure(')
    assert 'measuredWidth = -1;' in method(source,'private void refreshTheme()')
    assert 'refreshTheme();' in method(source,'protected void onConfigurationChanged(')
    probe(tmp_path,{'Probe.java':'''public class Probe {
 static class AndroidUtilities {static float density=1;static int dp(float n){return Math.round(n*density);}}
 static class MeasureSpec {static int getSize(int n){return n;}}
 static class StaticLayout {int width;StaticLayout(int w){width=w;}int getLineCount(){return 1;}float getLineWidth(int n){return Math.min(100,width);}int getHeight(){return 20;}}
 static class Bubble {int l,t,r,b;void setBounds(int l,int t,int r,int b){this.l=l;this.t=t;this.r=r;this.b=b;}void setTop(int t,int w,int h,boolean a,boolean b){}}
 static class Paint {float getFontSpacing(){return 12;}}
 Bubble[] bubbles={new Bubble(),new Bubble()};StaticLayout[] labels=new StaticLayout[2];String[] samples={"Entrada","Salida"};int[] tops=new int[2];Paint time=new Paint();
 int measuredWidth=-1,measuredHeight,width,height,builds;float measuredDensity=-1;
 StaticLayout layout(String s,int w){builds++;return new StaticLayout(w);}void setMeasuredDimension(int w,int h){width=w;height=h;}
 MEASURE
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args){Probe p=new Probe();p.onMeasure(360,0);int height=p.height;StaticLayout first=p.labels[0];
 for(int i=0;i<1000;i++)p.onMeasure(360,0);
 check(p.builds==4&&p.labels[0]==first&&p.height==height);
 p.onMeasure(240,0);check(p.builds==8&&p.width==240);
 AndroidUtilities.density=2;p.onMeasure(240,0);check(p.builds==12);
 p.measuredWidth=-1;p.onMeasure(240,0);check(p.builds==16);
 Probe fresh=new Probe();fresh.onMeasure(240,0);check(p.height==fresh.height&&p.bubbles[1].l==fresh.bubbles[1].l&&p.labels[0].width==fresh.labels[0].width);
 }
}'''.replace('MEASURE',measure)})


def test_fracture_geometry_is_deterministic_and_preserves_bubble_area(tmp_path):
    base=JAVA/'app/flexygram/bubbles/deletion'
    probe(tmp_path, {'Probe.java': '''import app.flexygram.bubbles.deletion.*;
public class Probe {
 static void check(boolean value){if(!value)throw new AssertionError();}
 public static void main(String[] args){
 for(long seed=0;seed<20;seed++){
 var pieces=FractureMesh.make(220,74,20,seed);var repeated=FractureMesh.make(220,74,20,seed);
 check(pieces.size()==20);double area=0;
 for(int i=0;i<pieces.size();i++){
 var piece=pieces.get(i);float[] xy=piece.xy;check(java.util.Arrays.equals(xy,repeated.get(i).xy));
 double signed=0;for(int j=0;j<xy.length;j+=2){int next=(j+2)%xy.length;
 check(Float.isFinite(xy[j])&&Float.isFinite(xy[j+1]));
 check(xy[j]>=-.001&&xy[j]<=220.001&&xy[j+1]>=-.001&&xy[j+1]<=74.001);
 signed+=xy[j]*xy[next+1]-xy[next]*xy[j+1];}area+=Math.abs(signed)*.5;
 }check(Math.abs(area-220*74)<.1);
 }
 for(int step=0;step<=100;step++){float t=step/100f;
 check(Math.abs(FractureMotionMath.falling(t,100)-t*t)<.00001);
 check(FractureMesh.fade(t)>=0&&FractureMesh.fade(t)<=1);
 check(TntMotion.fade(t)>=0&&TntMotion.fade(t)<=1);
 check(TntMotion.travel(t)>=0&&TntMotion.travel(t)<=1);
 }
 check(FractureMesh.phase(.1f,.2f)==0&&FractureMesh.phase(1,.2f)==1);
 check(TntMotion.flash(0)==0&&TntMotion.flash(1)==0);
 check(TntMotion.fuseDuration(650,2000)==650);
 }
}'''},[base/(name+'.java') for name in ['FractureMesh','FractureMotionMath','TntMotion']])


def test_list_pill_measurement_cache_keeps_content_and_size_invalidation(tmp_path):
    source=(JAVA/'app/flexygram/home/SignatureSmartPillSpan.java').read_text()
    size=method(source,'public int getSize(').replace('@NonNull ','').replace('android.graphics.Typeface','Typeface').replace('android.text.TextUtils','TextUtils')
    probe(tmp_path,{'Probe.java':'''public class Probe {
 static class Typeface{}
 static class Paint {float size=14;Typeface getTypeface(){return new Typeface();}float getTextSize(){return size;}static class FontMetricsInt{int ascent=77;}}
 static class Ink {static int measures;float size;void setTypeface(Typeface t){}void setTextSize(float f){size=f;}float measureText(String s){measures++;return s.length()*size;}}
 static class AndroidUtilities {static float density=1;static int dp(float n){return (int)Math.ceil(n*density);}static Typeface getTypeface(String s){return new Typeface();}}
 static class TextUtils {static int truncates;static class TruncateAt{static Object MIDDLE=new Object(),END=new Object();}static CharSequence ellipsize(String s,Ink p,float w,Object mode){truncates++;int chars=Math.max(0,(int)(w/p.size));return s.substring(0,Math.min(s.length(),chars));}}
 Typeface measuredTypeface;static Typeface cachedTypeface;static Ink sharedInk=new Ink();
 String snippet="un documento largo de prueba",displayText;int maxAvailableWidth=90,measured;boolean isDocument;
 float textSize,measuredDensity=-1,height,iconSize,iconSpacing,paddingH;
 SIZE
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args){
 for(boolean document:new boolean[]{false,true}){
 AndroidUtilities.density=1;
 Probe p=new Probe();p.isDocument=document;Paint ink=new Paint();Paint.FontMetricsInt fm=new Paint.FontMetricsInt();int width=p.getSize(ink,"x",0,1,fm);String text=p.displayText;
 int measures=Ink.measures,truncates=TextUtils.truncates;
 for(int i=0;i<1000;i++)check(p.getSize(ink,"x",0,1,fm)==width);
 check(Ink.measures==measures&&TextUtils.truncates==truncates&&p.displayText.equals(text)&&fm.ascent==77);
 ink.size=22;p.getSize(ink,"x",0,1,null);check(Ink.measures>measures);measures=Ink.measures;
 AndroidUtilities.density+=1;p.getSize(ink,"x",0,1,null);check(Ink.measures>measures);
 measures=Ink.measures;cachedTypeface=new Typeface();p.getSize(ink,"x",0,1,null);check(Ink.measures>measures);
 Probe fresh=new Probe();fresh.isDocument=document;
 check(fresh.getSize(ink,"x",0,1,null)==p.measured&&fresh.displayText.equals(p.displayText));
 }
 }
}'''.replace('SIZE',size)})
