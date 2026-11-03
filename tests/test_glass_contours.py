"""Execute the actual bubble-derived contour with deterministic Canvas/Paint recording."""
from test_simple_glass import run_java, JAVA
from test_composer_layout import method


def test_round_pill_card_fusion_sides_alpha_and_work_bound(tmp_path):
    run_java(tmp_path, {
        'android/graphics/Path.java':'package android.graphics;public class Path{}',
        'android/graphics/Rect.java':'''package android.graphics;public class Rect{public int left,top,right,bottom;public Rect(int l,int t,int r,int b){left=l;top=t;right=r;bottom=b;}public int width(){return right-left;}public int height(){return bottom-top;}public boolean isEmpty(){return width()<=0||height()<=0;}public float exactCenterX(){return (left+right)*.5f;}public float exactCenterY(){return(top+bottom)*.5f;}}''',
        'android/graphics/Paint.java':'''package android.graphics;public class Paint{public static final int ANTI_ALIAS_FLAG=1;public enum Style{STROKE}public enum Cap{ROUND}public enum Join{ROUND}int color;float width;public Paint(int flags){}public void setStyle(Style s){}public void setStrokeCap(Cap c){}public void setStrokeJoin(Join j){}public void setColor(int c){color=c;}public void setStrokeWidth(float w){width=w;}public int getColor(){return color;}public float getStrokeWidth(){return width;}}''',
        'android/graphics/Canvas.java':'''package android.graphics;public class Canvas{public int depth,draws,sideClips,pathClips,lastColor;public float maxWidth,left,top,right,bottom;public Path path;public void save(){depth++;}public void restore(){depth--;}public void clipPath(Path p){pathClips++;path=p;}public void clipRect(float l,float t,float r,float b){sideClips++;left=l;top=t;right=r;bottom=b;}public void drawPath(Path p,Paint ink){if(p!=path||depth!=1)throw new AssertionError("contour escaped native clip");draws++;lastColor=ink.getColor();maxWidth=Math.max(maxWidth,ink.getStrokeWidth());}}''',
        'Probe.java':'''import app.flexygram.effects.*;import android.graphics.*;
public class Probe{static void check(boolean ok){if(!ok)throw new AssertionError();}public static void main(String[]args){GlassContour contour=new GlassContour();Path path=new Path();
 for(int[] size:new int[][]{{48,48},{300,48},{300,180},{24,24}})for(int position=1;position<=5;position++)for(int mode=0;mode<3;mode++)for(int level:new int[]{0,30,100})for(int alpha:new int[]{32,255}){
  Rect bounds=new Rect(7,9,7+size[0],9+size[1]);GlassSettings settings=GlassSettings.defaults().with(7,mode).with(8,level).with(10,position).with(4,60);Canvas c=new Canvas();
  contour.draw(c,path,bounds,settings,6,0xc0abcdef,0xff445566,alpha);
  check(c.depth==0&&c.pathClips==1&&c.draws>=1&&c.draws<=3&&c.sideClips==(position==5?0:1));
  check((c.lastColor>>>24)==Math.round(192*alpha/255f));check(c.maxWidth<=Math.min(12,Math.min(size[0],size[1])*.25f)*3.6f+.001f);
  if(position==1)check(c.bottom==bounds.exactCenterY());if(position==2)check(c.top==bounds.exactCenterY());if(position==3)check(c.right==bounds.exactCenterX());if(position==4)check(c.left==bounds.exactCenterX());
 }
 for(int field:new int[]{0,3}){Canvas c=new Canvas();contour.draw(c,path,new Rect(0,0,48,48),GlassSettings.defaults().with(field,0),6,0xffffffff,0xff112233,255);check(c.draws==0&&c.depth==0);}
 Canvas zero=new Canvas();contour.draw(zero,path,new Rect(0,0,48,48),GlassSettings.defaults(),0,-1,0,255);check(zero.draws==0);
 GlassSettings strong=new GlassSettings(true,42,999,999,999,999,999,999,999,true,999);check(strong.blur==96&&strong.edge==200&&strong.width==60&&strong.look==3&&strong.fusion==2&&strong.position==5);
 check(!GlassSettings.defaults().personalizedContour());check(GlassSettings.defaults().with(5,1).bubbleStyle()==3);check(GlassSettings.defaults().with(5,2).bubbleStyle()==1);check(GlassSettings.defaults().with(5,3).bubbleStyle()==2);
 }}''',
    }, ['app/flexygram/effects/GlassSettings.java', 'app/flexygram/effects/GlassContour.java', 'app/flexygram/bubbles/BubbleFusion.java'])


def test_opt_in_contour_keeps_canceled_profiles_and_native_geometry():
    source=(JAVA/'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawable.java').read_text()
    gate=method(source,'protected boolean hasPersonalizedContour()')
    assert 'SimpleGlassProvider' in gate and 'personalizedContour()' in gate
    draw=method(source,'protected boolean drawPersonalizedContour(')
    assert 'GlassOutlineStyle.HIDDEN' in draw and 'FlexyGlassConfig.enabled()' in draw
    assert 'boundProps.path' in draw and 'boundProps.boundsWithPadding' in draw
    assert 'new ' not in draw
    hardware=(JAVA/'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawableRenderNode.java').read_text()
    display=method(hardware,'public void updateDisplayList()')
    assert 'drawPersonalizedContour(c, 255)' in display
    for forbidden in ['Bitmap.createBitmap', 'RuntimeShader', 'createBlurEffect']:
        assert forbidden not in display
