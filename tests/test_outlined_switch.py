"""Execute the real existing switch renderer branch with explicit drawing/theme hosts."""
import re
from test_render_work_reuse import JAVA,probe
from test_composer_layout import method


def test_outline_variant_draws_cross_off_check_on_and_keeps_existing_flexygram_dispatch(tmp_path):
    source=(JAVA/'org/telegram/ui/Components/Switch.java').read_text()
    draw=method(source,'private void drawCustomSwitch(')
    layer=method(source,'private float getLayerColorProgress(')
    mix=method(source,'private int lerpColor(')
    cross=method(source,'private void drawCross(')
    keys=sorted(set(re.findall(r'Theme\.(key_\w+)',draw)))
    theme=''.join('static final int '+k+'='+str(i+10)+';' for i,k in enumerate(keys))
    probe(tmp_path,{'Probe.java':'''public class Probe{
 static final int SWITCH_STYLE_DEFAULT=0,SWITCH_STYLE_MODERN=1,SWITCH_STYLE_MD3=2,SWITCH_STYLE_OUTLINED=3;
 static int dp(float v){return Math.round(v);}static float dpf2(float v){return v;}
 static class Color{static final int TRANSPARENT=0;static int red(int c){return(c>>16)&255;}static int green(int c){return(c>>8)&255;}static int blue(int c){return c&255;}static int alpha(int c){return c>>>24;}}
 static class Build{static class VERSION{static int SDK_INT=35;}static class VERSION_CODES{static final int S=31;}}
 static class MonetHelper{static boolean useMonetMd3Colors(){return false;}static int harmonizeColor(int c){return c;}}
 static class Utilities{static int clamp(int x,int max,int min){return Math.max(min,Math.min(max,x));}}
 static class Theme{KEYS static int getColor(int k,Object r){return k==1?0xff777777:k==2?0xffa0d0e0:k==4?0xff104858:0xff212729;}static int blendOver(int base,int tint){return base;}static int multAlpha(int c,float a){return(c&0xffffff)|((int)((c>>>24)*a)<<24);}static boolean isCurrentThemeDay(){return false;}static Theme getActiveTheme(){return new Theme();}boolean isMonetNight(){return false;}}
 static class Paint{int color,alpha=255;float stroke=1;void setColor(int c){color=c;alpha=c>>>24;}void setAlpha(int a){alpha=a;}int getAlpha(){return alpha;}void setStrokeWidth(float s){stroke=s;}float getStrokeWidth(){return stroke;}}
 static class RectF{void set(float a,float b,float c,float d){}}
 static class Bitmap{int getWidth(){return 37;}int getHeight(){return 20;}void eraseColor(int c){}}
 static class Canvas{int lines,circles,rounds;void drawRoundRect(RectF r,float a,float b,Paint p){rounds++;}void drawCircle(float x,float y,float r,Paint p){circles++;}void drawRect(float a,float b,float c,float d,Paint p){}void drawBitmap(Bitmap b,float x,float y,Paint p){}void save(){}void restore(){}void scale(float x,float y,float a,float b){}void drawLine(float a,float b,float c,float d,Paint p){if(p.alpha>0)lines++;}}
 static class Drawable{int alpha=255,visible;int getIntrinsicWidth(){return 32;}int getIntrinsicHeight(){return 32;}void setColorFilter(Object f){}void setBounds(int l,int t,int r,int b){}void setAlpha(int a){alpha=a;}void draw(Canvas c){if(alpha>0)visible++;}}
 static class PorterDuff{static class Mode{static final int MULTIPLY=1;}}static class PorterDuffColorFilter{PorterDuffColorFilter(int c,int m){}}
 static class Animator{float getFloatValue(){return 1;}}
 final Animator animatorIconVisibility=new Animator();final Paint paint=new Paint(),paint2=new Paint(),googleBorderPaint=new Paint(),overlayMaskPaint=new Paint(),overlayEraserPaint=new Paint();final RectF rectF=new RectF();final Drawable checkDrawable=new Drawable();Drawable iconDrawable,rippleDrawable;
 Bitmap[] overlayBitmap={new Bitmap(),new Bitmap()};Canvas[] overlayCanvas={new Canvas(),new Canvas()};Bitmap overlayMaskBitmap=new Bitmap();Canvas overlayMaskCanvas=new Canvas();
 Object resourcesProvider;float progress,overlayCx,overlayCy,overlayRad;int overrideColorProgress,drawIconType,lastIconColor,lastCheckColor,separateTrackColorKey=-1;int trackColorKey=1,trackCheckedColorKey=2,thumbColorKey=3,thumbCheckedColorKey=4;boolean isChecked;
 int extera;void drawExteraSwitch(Canvas c){extera++;}int getMeasuredWidth(){return 37;}int getMeasuredHeight(){return 20;}float getX(){return 0;}float getY(){return 0;}int processColor(int c){return c;}void drawCenteredDrawable(Canvas c,Drawable d,int x,int y,float s,int a){}
 DRAW LAYER MIX CROSS
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){
 Probe existing=new Probe();existing.drawCustomSwitch(new Canvas(),SWITCH_STYLE_MD3);check(existing.extera==1);
 Probe off=new Probe();Canvas a=new Canvas();off.progress=0;off.drawCustomSwitch(a,SWITCH_STYLE_OUTLINED);check(off.extera==0&&a.lines==2&&off.checkDrawable.visible==0&&a.circles==1&&a.rounds==2);check(off.googleBorderPaint.getStrokeWidth()==2);
 Probe on=new Probe();Canvas b=new Canvas();on.progress=1;on.isChecked=true;on.drawCustomSwitch(b,SWITCH_STYLE_OUTLINED);check(on.extera==0&&b.lines==0&&on.checkDrawable.visible==1&&b.circles==1&&b.rounds==2);
 }}'''.replace('KEYS',theme).replace('DRAW',draw).replace('LAYER',layer).replace('MIX',mix).replace('CROSS',cross)})
