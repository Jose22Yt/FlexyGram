"""Geometry, theme contrast, and ownership checks for the chat edge selector."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_reflection_is_transparent_in_the_middle_and_reuses_gradients(tmp_path):
    probe(tmp_path, {
        'android/graphics/Canvas.java': '''package android.graphics;
public class Canvas {
 public int draws, depth, bands, clips, paths; public float top, radius, left, thickness;
 public Paint paint, edge;
 public boolean hardware;
 public boolean isHardwareAccelerated(){return hardware;}
 public int save(){ return ++depth; }
 public void translate(float x, float y){ top=y; }
 public void restoreToCount(int id){ depth=id-1; }
 public void clipPath(Path p){clips++;}
 public void drawPath(Path p,Paint paint){
  if(paint.getShader() instanceof BitmapShader){paths++;return;}
  if(p.offsetY!=-top || paint.getStyle()!=Paint.Style.STROKE)throw new AssertionError();
  paths++;
 }
 public void drawRoundRect(float l,float t,float r,float b,float rx,float ry,Paint p){
  if(b<=t || r<=l || rx!=ry)throw new AssertionError();
  if(p.getStyle()==Paint.Style.STROKE){
   if(t!=p.getStrokeWidth()*.5f)throw new AssertionError();
   thickness=p.getStrokeWidth();left=l;edge=p;bands++;
  }else{
   if(t!=0 && !(p.getShader() instanceof BitmapShader))throw new AssertionError();
   draws++;radius=rx;paint=p;
  }
 }
}''',
        'android/graphics/Paint.java': '''package android.graphics;
public class Paint {
 public static final int ANTI_ALIAS_FLAG=1, FILTER_BITMAP_FLAG=2;
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
        'android/graphics/Bitmap.java': 'package android.graphics; public class Bitmap {public int getWidth(){return 80;}public int getHeight(){return 80;}}',
        'android/graphics/BitmapFactory.java': 'package android.graphics; public class BitmapFactory {public static int count; public static Bitmap decodeResource(Object resources,int id){count++;return new Bitmap();}}',
        'android/graphics/BitmapShader.java': 'package android.graphics; public class BitmapShader extends Shader {public static int count, updates;public BitmapShader(Bitmap b,TileMode x,TileMode y){count++;}public void setLocalMatrix(Matrix m){updates++;}}',
        'android/graphics/Matrix.java': 'package android.graphics; public class Matrix {public void setScale(float x,float y){}public void postTranslate(float x,float y){}}',
        'org/telegram/messenger/ApplicationLoader.java': 'package org.telegram.messenger; public class ApplicationLoader {public static ApplicationLoader applicationContext=new ApplicationLoader(); public Object getResources(){return null;}}',
        'org/telegram/messenger/R.java': 'package org.telegram.messenger; public class R {public static class drawable {public static final int flexy_satin_pill_dark=1,flexy_satin_circle_dark=2,flexy_satin_pill_light=3,flexy_satin_circle_light=4;}}',
        'android/graphics/Path.java': '''package android.graphics;
public class Path {
 public float offsetY;
 public void offset(float x,float y,Path destination){destination.offsetY=y;}
}''',
        'android/os/Build.java': 'package android.os; public class Build { public static class VERSION { public static int SDK_INT=33; } }',
        'androidx/annotation/RequiresApi.java': 'package androidx.annotation; public @interface RequiresApi { int value(); }',
        'android/graphics/RuntimeShader.java': '''package android.graphics;
public class RuntimeShader extends Shader {
 public static int creations; public int updates; public float width,height,radius;
 public RuntimeShader(String source){creations++;}
 public void setFloatUniform(String name,float value){updates++;if(name.equals("radius"))radius=value;}
 public void setFloatUniform(String name,float first,float second){updates++;width=first;height=second;}
 public void setFloatUniform(String name,float a,float b,float c,float d){updates++;}
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
public class AndroidUtilities { public static float density=2f; public static float dpf2(float dp){return dp*density;} }''',
        'org/telegram/messenger/LiteMode.java': '''package org.telegram.messenger;
public class LiteMode { public static boolean thermalHigh; public static boolean isThermalPressureHigh(){return thermalHigh;} }''',
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
  int topCrest=subtle.colors[0]>>>24, bottomCrest=subtle.colors[5]>>>24;
  check(topCrest==36 && bottomCrest==32);
  check((subtle.colors[1]>>>24)==25 && (subtle.colors[4]>>>24)==22);
  check((subtle.colors[2]>>>24)==0 && (subtle.colors[3]>>>24)==0);
  check(Math.abs(subtle.stops[2]*subtle.height-8.5f)<.02f);
  check(Math.abs((1-subtle.stops[3])*subtle.height-6.8f)<.02f);
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
  org.telegram.messenger.AndroidUtilities.density=3f;
  reflection.draw(canvas,0,20,200,320,40,false,255);
  LinearGradient scaled=(LinearGradient)canvas.paint.getShader();
  check(scaled!=subtleLight && Math.abs(scaled.stops[2]*scaled.height-6f)<.02f);
  org.telegram.messenger.AndroidUtilities.density=2f;
  canvas.hardware=true;
  reflection.draw(canvas,10,20,410,100,40,true,150);
  RuntimeShader curved=(RuntimeShader)canvas.paint.getShader();
  check(curved.width==400 && curved.height==80 && curved.radius==40 && canvas.paint.getAlpha()==150);
  int updates=curved.updates;
  reflection.draw(canvas,11,21,411,101,40,true,150);
  check(curved==canvas.paint.getShader() && curved.updates==updates && RuntimeShader.creations==1);
  reflection.draw(canvas,0,0,45,45,40,false,255);
  check(curved.radius==22.5f && curved.width==45 && canvas.depth==0);
  android.os.Build.VERSION.SDK_INT=32;
  reflection.draw(canvas,0,0,45,45,22.5f,true,255);
  check(canvas.paint.getShader() instanceof LinearGradient && RuntimeShader.creations==1);
  reflection.setSubtle(false);
  reflection.draw(canvas,0,20,420,100,40,true,255);
  check(canvas.bands==6006 && java.util.Arrays.equals(((LinearGradient)canvas.paint.getShader()).colors,dark.colors));
  reflection.setSatin(true);
  reflection.draw(canvas,0,20,420,100,40,true,255);
  check(canvas.paint.getShader() instanceof BitmapShader && canvas.bands==6006);
  int materialUpdates=BitmapShader.updates;
  for(int i=0;i<200;i++){
   reflection.draw(canvas,0,20+i,420,100+i,40,true,255);
   check(canvas.top==20+i && canvas.depth==0);
  }
  check(BitmapShader.updates==materialUpdates);

  int paths=canvas.paths;
  android.os.Build.VERSION.SDK_INT=33;
  for(int i=0;i<100;i++){
   reflection.draw(canvas,0,20+i,420,100+i,40,true,200);
   reflection.draw(canvas,10,0,50,40,20,true,255);
   reflection.drawClipped(canvas,0,20,420,100,new Path(),true,255);
  }
  check(canvas.paths==paths+100 && BitmapFactory.count==2 && BitmapShader.count==2);
  reflection.draw(canvas,10,0,50,40,20,false,255);
  check(BitmapFactory.count==3 && BitmapShader.count==3 && RuntimeShader.creations==1);

  reflection.setSatin(false);
  reflection.setColorOsGlass(true);
  android.os.Build.VERSION.SDK_INT=33;
  canvas.hardware=true;
  reflection.draw(canvas,10,20,410,100,40,true,220);
  RuntimeShader colorOs=(RuntimeShader)canvas.paint.getShader();
  check(colorOs!=curved && RuntimeShader.creations==2 && colorOs.width==400 && colorOs.height==80 && colorOs.radius==40 && canvas.paint.getAlpha()==220);
  int colorOsUpdates=colorOs.updates;
  reflection.draw(canvas,15,25,415,105,40,true,220);
  check(colorOs==canvas.paint.getShader() && colorOs.updates==colorOsUpdates && RuntimeShader.creations==2);
  reflection.draw(canvas,0,0,48,48,48,false,255);
  check(colorOs.radius==24f && colorOs.width==48 && canvas.depth==0);
  int beforeFallbackBands=canvas.bands;
  android.os.Build.VERSION.SDK_INT=32;
  reflection.draw(canvas,0,20,200,120,24,true,255);
  check(canvas.paint.getShader() instanceof LinearGradient && canvas.bands==beforeFallbackBands+1);
  int beforeClippedPaths=canvas.paths;
  reflection.drawClipped(canvas,0,20,200,120,new Path(),false,200);
  check(canvas.paths==beforeClippedPaths+1 && canvas.depth==0);
  android.os.Build.VERSION.SDK_INT=33;
  org.telegram.messenger.LiteMode.thermalHigh=true;
  reflection.draw(canvas,0,20,200,120,24,true,255);
  check(canvas.paint.getShader() instanceof LinearGradient);
  org.telegram.messenger.LiteMode.thermalHigh=false;
 }
}''',
    }, [JAVA/'app/flexygram/effects/ChatEdgeReflection.java', JAVA/'app/flexygram/effects/SatinEdgeMaterial.java'])


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
 public boolean subtle,satin,colorOsGlass;
 public void setSubtle(boolean value){subtle=value;}
 public void setSatin(boolean value){satin=value;}
 public void setColorOsGlass(boolean value){colorOsGlass=value;}
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
  check(ChatEdgeStyle.hasCustomEdge() && !reflection.subtle && !reflection.colorOsGlass);
  ChatEdgeStyle.setSelected(ChatEdgeStyle.SUBTLE);
  check(NekoConfig.prefs.stored==2 && ChatEdgeStyle.isSubtle() && !ChatEdgeStyle.isGlobalSurfaceEdge());
  check(ChatEdgeStyle.updateReflection(reflection)==reflection && reflection.subtle);
  ChatEdgeStyle.setSelected(ChatEdgeStyle.SATIN);
  check(NekoConfig.prefs.stored==3 && ChatEdgeStyle.isSatin() && ChatEdgeStyle.isGlobalSurfaceEdge() && !ChatEdgeStyle.isSubtle());
  check(ChatEdgeStyle.updateReflection(reflection)==reflection && reflection.satin && !reflection.subtle && !reflection.colorOsGlass);
  ChatEdgeStyle.setSelected(ChatEdgeStyle.COLOROS_GLASS);
  check(NekoConfig.prefs.stored==4 && ChatEdgeStyle.isColorOsGlass() && ChatEdgeStyle.isGlobalSurfaceEdge() && !ChatEdgeStyle.isSatin());
  check(ChatEdgeStyle.updateReflection(reflection)==reflection && reflection.colorOsGlass && !reflection.satin && !reflection.subtle);
  ChatEdgeStyle.setSelected(ChatEdgeStyle.CURRENT);
  check(NekoConfig.prefs.stored==0 && !ChatEdgeStyle.hasCustomEdge() && !ChatEdgeStyle.isGlobalSurfaceEdge());
 }
}''',
    }, [JAVA/'app/flexygram/effects/ChatEdgeStyle.java'])
