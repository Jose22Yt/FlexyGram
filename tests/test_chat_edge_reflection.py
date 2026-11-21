"""Geometry, theme contrast, and ownership checks for the chat edge selector."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_reflection_is_transparent_in_the_middle_and_reuses_gradients(tmp_path):
    probe(tmp_path, {
        'android/graphics/Canvas.java': '''package android.graphics;
public class Canvas {
 public int draws, depth, bands, clips, paths; public float top, radius, left, thickness;
 public Paint paint, edge;
 public int save(){ return ++depth; }
 public void translate(float x, float y){ top=y; }
 public void restoreToCount(int id){ depth=id-1; }
 public void clipPath(Path p){clips++;}
 public void drawPath(Path p,Paint paint){
  if(p.offsetY!=-top || paint.getStyle()!=Paint.Style.STROKE)throw new AssertionError();
  paths++;
 }
 public void drawRoundRect(float l,float t,float r,float b,float rx,float ry,Paint p){
  if(b<=t || r<=l || rx!=ry)throw new AssertionError();
  if(p.getStyle()==Paint.Style.STROKE){
   if(t!=p.getStrokeWidth()*.5f)throw new AssertionError();
   thickness=p.getStrokeWidth();left=l;edge=p;bands++;
  }else{
   if(t!=0)throw new AssertionError();
   draws++;radius=rx;paint=p;
  }
 }
}''',
        'android/graphics/Paint.java': '''package android.graphics;
public class Paint {
 public static final int ANTI_ALIAS_FLAG=1;
 public enum Style{FILL,STROKE}
 private Shader shader; private int alpha=255;
 private Style style=Style.FILL; private float width;
 public Paint(int flags){}
 public Style getStyle(){return style;}
 public void setStyle(Style style){this.style=style;}
 public float getStrokeWidth(){return width;}
 public void setStrokeWidth(float width){this.width=width;}
 public Shader getShader(){ return shader; }
 public void setShader(Shader s){ shader=s; }
 public int getAlpha(){ return alpha; }
 public void setAlpha(int a){ alpha=a; }
}''',
        'android/graphics/Path.java': '''package android.graphics;
public class Path {
 public float offsetY;
 public void offset(float x,float y,Path destination){destination.offsetY=y;}
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
  check(LinearGradient.creations==4 && canvas.draws==2000 && canvas.bands==6000 && canvas.depth==0);
  check(canvas.top==250 && canvas.radius==22.5f && canvas.paint.getAlpha()==255);
  check(canvas.thickness>0 && canvas.thickness<3f && canvas.left==canvas.thickness*.5f);
  LinearGradient dark=(LinearGradient)canvas.paint.getShader();
  LinearGradient darkSide=(LinearGradient)canvas.edge.getShader();
  check((dark.colors[0]>>>24)>0 && (dark.colors[5]>>>24)>(dark.colors[0]>>>24));
  check((dark.colors[2]>>>24)==0 && (dark.colors[3]>>>24)==0);
  check((darkSide.colors[0]>>>24)==0 && (darkSide.colors[3]>>>24)==0);
  check((darkSide.colors[1]>>>24)>0 && darkSide.stops[1]<.5f && darkSide.stops[2]>.5f);
  reflection.draw(canvas,0,20,200,320,40,false,150);
  LinearGradient light=(LinearGradient)canvas.paint.getShader();
  LinearGradient lightSide=(LinearGradient)canvas.edge.getShader();
  check(light!=dark && light.colors[5]!=dark.colors[5] && canvas.paint.getAlpha()==150);
  check((lightSide.colors[1]&0xffffff)<(darkSide.colors[1]&0xffffff));
  check(light.stops[2]*light.height<=10.01f && (1-light.stops[3])*light.height<=10.01f);
  reflection.drawClipped(canvas,0,20,200,320,new Path(),false,150);
  check(canvas.clips==1 && canvas.paths==3 && canvas.depth==0);
  reflection.draw(canvas,0,0,10,10,5,true,0);
  check(LinearGradient.creations==6 && canvas.draws==2002);
  reflection.setSubtle(true);
  for(int i=0;i<100;i++)reflection.draw(canvas,0,20+i,420,100+i,40,true,255);
  LinearGradient subtle=(LinearGradient)canvas.paint.getShader();
  check(LinearGradient.creations==7 && canvas.bands==6003);
  check((subtle.colors[5]>>>24)<(dark.colors[5]>>>24)/3);
  check(subtle.stops[2]*subtle.height<3f && (subtle.colors[2]>>>24)==0);
  reflection.drawClipped(canvas,0,20,200,320,new Path(),false,255);
  check(canvas.clips==2 && canvas.paths==3 && canvas.depth==0);
  LinearGradient subtleLight=(LinearGradient)canvas.paint.getShader();
  check((subtleLight.colors[0]&0xffffff)==0xffffff);
  check((subtleLight.colors[5]&0xffffff)==0x474747);
  check((subtleLight.colors[2]>>>24)==0 && (subtleLight.colors[3]>>>24)==0);
  check(subtleLight.stops[2]*subtleLight.height>3.9f && subtleLight.stops[2]*subtleLight.height<4.1f);
  check((1-subtleLight.stops[3])*subtleLight.height>1.9f && (1-subtleLight.stops[3])*subtleLight.height<2.1f);
  reflection.draw(canvas,0,20,200,320,40,false,255);
  check(canvas.paint.getShader()==subtleLight);
  reflection.setSubtle(false);
  reflection.draw(canvas,0,20,420,100,40,true,255);
  check(canvas.bands==6006 && java.util.Arrays.equals(((LinearGradient)canvas.paint.getShader()).colors,dark.colors));
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



def test_style_preserves_legacy_choice_and_persists_subtle(tmp_path):
    probe(tmp_path, {
        'tw/nekomimi/nekogram/NekoConfig.java': '''package tw.nekomimi.nekogram;
public class NekoConfig {
 public static final Preferences prefs = new Preferences();
 public static Preferences getPreferences(){return prefs;}
 public static class Preferences {
  public int stored = -1;
  public boolean getBoolean(String key, boolean fallback){return true;}
  public int getInt(String key, int fallback){return stored == -1 ? fallback : stored;}
  public Preferences edit(){return this;}
  public Preferences putInt(String key, int value){stored=value; return this;}
  public void apply(){}
 }
}''',
        'app/flexygram/effects/ChatEdgeReflection.java': '''package app.flexygram.effects;
public class ChatEdgeReflection {
 public boolean subtle;
 public void setSubtle(boolean value){subtle=value;}
}''',
        'Probe.java': '''public class Probe {
 public static void main(String[] args){app.flexygram.effects.StyleProbe.run();}
}''',
        'app/flexygram/effects/StyleProbe.java': '''package app.flexygram.effects;
import tw.nekomimi.nekogram.NekoConfig;
public class StyleProbe {
 static void check(boolean value){if(!value)throw new AssertionError();}
 public static void run(){
  check(ChatEdgeStyle.getSelected()==ChatEdgeStyle.REFLECTION);
  ChatEdgeReflection reflection=ChatEdgeStyle.updateReflection(null);
  check(ChatEdgeStyle.hasCustomEdge() && !reflection.subtle);
  ChatEdgeStyle.setSelected(ChatEdgeStyle.SUBTLE);
  check(NekoConfig.prefs.stored==2 && ChatEdgeStyle.isSubtle());
  check(ChatEdgeStyle.updateReflection(reflection)==reflection && reflection.subtle);
  ChatEdgeStyle.setSelected(ChatEdgeStyle.CURRENT);
  check(NekoConfig.prefs.stored==0 && !ChatEdgeStyle.hasCustomEdge());
 }
}''',
    }, [JAVA/'app/flexygram/effects/ChatEdgeStyle.java'])
