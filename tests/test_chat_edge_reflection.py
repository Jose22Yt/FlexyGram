"""Geometry, theme contrast, and ownership checks for the chat edge selector."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_reflection_is_transparent_in_the_middle_and_reuses_gradients(tmp_path):
    probe(tmp_path, {
        'android/graphics/Canvas.java': '''package android.graphics;
public class Canvas {
 public int draws, depth; public float top, radius; public Paint paint;
 public int save(){ return ++depth; }
 public void translate(float x, float y){ top=y; }
 public void restoreToCount(int id){ depth=id-1; }
 public void drawRoundRect(float l,float t,float r,float b,float rx,float ry,Paint p){
  if(t!=0 || b<=t || r<=l || rx!=ry)throw new AssertionError();
  draws++;radius=rx;paint=p;
 }
}''',
        'android/graphics/Paint.java': '''package android.graphics;
public class Paint {
 public static final int ANTI_ALIAS_FLAG=1;
 private Shader shader; private int alpha=255;
 public Paint(int flags){}
 public Shader getShader(){ return shader; }
 public void setShader(Shader s){ shader=s; }
 public int getAlpha(){ return alpha; }
 public void setAlpha(int a){ alpha=a; }
}''',
        'android/graphics/Shader.java': 'package android.graphics; public class Shader { public enum TileMode { CLAMP } }',
        'android/graphics/LinearGradient.java': '''package android.graphics;
public class LinearGradient extends Shader {
 public static int creations; public final int[] colors; public final float[] stops; public final float height;
 public LinearGradient(float x1,float y1,float x2,float y2,int[] rgb,float[] pos,TileMode mode){
  creations++;colors=rgb.clone();stops=pos.clone();height=y2-y1;
 }
}''',
        'android/graphics/RectF.java': 'package android.graphics; public class RectF { public float left,top,right,bottom; }',
        'org/telegram/messenger/AndroidUtilities.java': '''package org.telegram.messenger;
public class AndroidUtilities { public static float dpf2(float dp){return dp*2;} }''',
        'Probe.java': '''import android.graphics.*;
import app.flexygram.effects.ChatEdgeReflection;
public class Probe {
 static void check(boolean value){if(!value)throw new AssertionError();}
 public static void main(String[] args){
  Canvas canvas=new Canvas(); ChatEdgeReflection reflection=new ChatEdgeReflection();
  for(int i=0;i<1000;i++){
   reflection.draw(canvas,0,20+i,420,100+i+(i%2)*.001f,40,true,128);
   reflection.draw(canvas,0,250,45,295,25,true,255);
  }
  check(LinearGradient.creations==2 && canvas.draws==2000 && canvas.depth==0);
  check(canvas.top==250 && canvas.radius==22.5f && canvas.paint.getAlpha()==255);
  LinearGradient dark=(LinearGradient)canvas.paint.getShader();
  check((dark.colors[0]>>>24)>0 && (dark.colors[5]>>>24)>(dark.colors[0]>>>24));
  check((dark.colors[2]>>>24)==0 && (dark.colors[3]>>>24)==0);
  reflection.draw(canvas,0,20,200,320,40,false,150);
  LinearGradient light=(LinearGradient)canvas.paint.getShader();
  check(light!=dark && light.colors[5]!=dark.colors[5] && canvas.paint.getAlpha()==150);
  check(light.stops[2]*light.height<=10.01f && (1-light.stops[3])*light.height<=10.01f);
  reflection.draw(canvas,0,0,10,10,5,true,0);
  check(LinearGradient.creations==3 && canvas.draws==2001);
 }
}''',
    }, [JAVA/'app/flexygram/effects/ChatEdgeReflection.java'])


def test_existing_outline_and_reflection_are_mutually_exclusive():
    drawable = (JAVA/'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawable.java').read_text()
    draw = method(drawable, 'public final void drawWithChatEdge(')
    assert draw.index('setStrokeVisible(reflection == null)') < draw.index('draw(canvas)')
    colors = method(drawable, 'public void updateColors()')
    assert 'strokeColorTop = strokeVisible && glare' in colors
    assert 'strokeColorBottom = strokeVisible && glare' in colors
    assert 'strokeColorFull = !strokeVisible ? 0' in colors
    assert 'shadowColor = glare ?' in colors
    composer = (JAVA/'org/telegram/ui/Components/chat/ChatInputViewsContainer.java').read_text()
    edge = method(composer, 'private void drawSurfaceEdge(')
    assert 'if (reflection == null)' in edge and 'else' in edge
    selector = (JAVA/'app/flexygram/effects/ChatEdgeSettingsSection.java').read_text()
    assert selector.count('addRow(') == 1 and 'createSingleChoiceDialog' in selector
