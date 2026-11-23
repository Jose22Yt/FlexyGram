"""Execute Floating's geometry, reveal timing and portable style ID without an APK."""
from test_render_work_reuse import JAVA, probe


def test_floating_style_is_opt_in_and_survives_preference_reload(tmp_path):
    probe(tmp_path, {
        'android/content/SharedPreferences.java': '''package android.content;import java.util.*;
public class SharedPreferences {
 public final Map<String,Object> data=new HashMap<>();
 public Map<String,?> getAll(){return data;}
 public Editor edit(){return new Editor();}
 public class Editor {
  public Editor putInt(String k,int v){data.put(k,v);return this;}
  public Editor putBoolean(String k,boolean v){data.put(k,v);return this;}
  public void apply(){}
 }
}''',
        'android/content/Context.java': '''package android.content;public class Context{
 public static final int MODE_PRIVATE=0;public final SharedPreferences prefs=new SharedPreferences();
 public SharedPreferences getSharedPreferences(String n,int mode){return prefs;}
}''',
        'org/telegram/messenger/ApplicationLoader.java': '''package org.telegram.messenger;
public class ApplicationLoader{public static final android.content.Context applicationContext=new android.content.Context();}''',
        'org/telegram/messenger/BuildConfig.java': '''package org.telegram.messenger;
public class BuildConfig{public static final boolean CONNECTED_ALPHA=true;}''',
        'app/exteraless/appearance/AppearanceConfig.java': '''package app.exteraless.appearance;
public class AppearanceConfig{static final android.content.SharedPreferences p=new android.content.SharedPreferences();public static android.content.SharedPreferences getPreferences(){return p;}}''',
        'Probe.java': '''import app.flexygram.header.HeaderConfig;
public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){
  HeaderConfig.load();check(HeaderConfig.style()==1&&!HeaderConfig.signature()&&!HeaderConfig.floating());
  check(HeaderConfig.counter()&&HeaderConfig.counterMode()==2&&!HeaderConfig.centerTitle()&&!HeaderConfig.adaptiveBubble());
  check(Boolean.TRUE.equals(org.telegram.messenger.ApplicationLoader.applicationContext.prefs.data.get("back_counter_restored_v1")));
  for(int style=0;style<=4;style++){
   HeaderConfig.style(style);HeaderConfig.load();check(HeaderConfig.style()==style);
   check(HeaderConfig.adaptiveBubble()==(style==0));
   check(HeaderConfig.floating()==(style==4));check(HeaderConfig.signature()==(style!=1));
   check(HeaderConfig.fusion()==(style>=2));check(HeaderConfig.portrait()==(style==3));
  }
  HeaderConfig.style(0);HeaderConfig.adaptiveBubble(false);HeaderConfig.load();check(!HeaderConfig.adaptiveBubble());
  HeaderConfig.adaptiveBubble(true);HeaderConfig.load();check(HeaderConfig.adaptiveBubble());
  org.telegram.messenger.ApplicationLoader.applicationContext.prefs.data.put("style",100);
  HeaderConfig.load();check(HeaderConfig.style()==1&&!HeaderConfig.floating());
 }
}'''
    }, [JAVA/'app/flexygram/header/HeaderConfig.java'])


def test_floating_geometry_keeps_both_lines_inside_whole_card(tmp_path):
    probe(tmp_path, {'Probe.java': '''
import app.flexygram.header.fusion.SignatureFusionGeometry;
import app.flexygram.header.fusion.FloatingStatusMotion;
import app.flexygram.animation.FastMotionTiming;
import app.flexygram.studio.core.StudioSchema;
public class Probe {
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 static void equal(float a,float b){check(Math.abs(a-b)<.01f);}
 public static void main(String[]args){
  var g=new SignatureFusionGeometry.Layout();Object photo=g.portrait,status=g.status;
  for(float d:new float[]{1,1.5f,2,3})for(int w:new int[]{240,320,360,412,600,900})
   for(boolean rtl:new boolean[]{false,true})for(boolean call:new boolean[]{false,true})
    for(float unread:new float[]{0,24,40}){
     SignatureFusionGeometry.updateFloating(g,w*d,d,rtl,call,unread*d);
     check(g.floatingStatus&&!g.mattePortrait&&g.portrait==photo&&g.status==status);
     if(!g.fits)continue;
     equal(g.portrait.top,g.center.top);equal(g.portrait.bottom,g.center.bottom);
     equal(rtl?g.portrait.right:g.portrait.left,rtl?g.center.right:g.center.left);
     equal(g.center.height(),48*d);
     equal(g.text.centerX(),g.center.centerX());
     equal(g.text.top,g.center.top);equal(g.text.bottom,g.center.bottom);
     check(g.portrait.width()>.8f*g.center.width()&&g.portrait.width()<.9f*g.center.width());
     check(g.fadeStartX<g.center.centerX()&&g.fadeEndX>g.center.centerX());
     check(g.status.width()==0&&g.status.height()==0);
     for(float text:new float[]{0,20,100,1000}){
      equal(SignatureFusionGeometry.titleCenterX(g,text*d),g.center.centerX());
     }
     check(g.back.width()>=48*d&&g.more.width()==48*d);
     if(call)check(g.call.width()==48*d);
    }
  SignatureFusionGeometry.update(g,412,1,false,true);
  check(!g.floatingStatus&&g.status.width()==0);
  SignatureFusionGeometry.updatePortrait(g,412,1,false,true);
  check(!g.floatingStatus&&g.status.width()==0);
  var motion=new FloatingStatusMotion();
  equal(motion.progress(1000,true),0);
  float last=0;
  for(long t=1000;t<=1220;t++){
   float value=motion.progress(t,true);check(value>=last&&value<=1);last=value;
  }
  equal(last,1);equal(motion.progress(999999,true),1);
  motion.reset();equal(motion.progress(1000000,true),0);
  equal(motion.progress(1000010,false),1);equal(motion.progress(1000011,true),1);
  for(boolean fast:new boolean[]{false,true})for(double scale:new double[]{0,.5,1,2}){
   FastMotionTiming.setEnabled(fast);FastMotionTiming.setSystemScaleProvider(()->scale);
   long duration=FastMotionTiming.duration(FloatingStatusMotion.DURATION_MS);
   motion.reset();equal(motion.progress(1000,true,duration),0);
   equal(motion.progress(1000+duration,true,duration),1);
   equal(motion.progress(1000+duration+100,true,duration),1);
  }
  motion.reset();equal(motion.progress(0,false,220),1);
  motion.reset();equal(motion.progress(0,true,0),1);
  Object style=StudioSchema.key("header","style").validate(4);
  check(Integer.valueOf(4).equals(style));
  try{StudioSchema.key("header","style").validate(5);throw new AssertionError();}
  catch(IllegalArgumentException expected){}
 }
}'''}, [JAVA/'app/flexygram/header/fusion/SignatureFusionGeometry.java',
        JAVA/'app/flexygram/header/fusion/FloatingStatusMotion.java',
        JAVA/'app/flexygram/animation/FastMotionTiming.java',
        JAVA/'app/flexygram/studio/core/StudioSchema.java'])


def test_adaptive_contact_pill_tracks_name_in_both_directions(tmp_path):
    from test_composer_layout import method
    avatar = (JAVA/'org/telegram/ui/Components/ChatAvatarContainer.java').read_text()
    preferred = method(avatar, 'public float signaturePreferredTitleWidth(')
    assert 'getDesiredWidth(title, measure)' in preferred and 'subtitle' not in preferred
    probe(tmp_path, {
        'android/graphics/RectF.java': '''package android.graphics;
        public class RectF {public float left,top,right,bottom;
        public void set(float l,float t,float r,float b){left=l;top=t;right=r;bottom=b;}
        public void offset(float x,float y){set(left+x,top+y,right+x,bottom+y);}
        public float width(){return right-left;}}''',
        'app/flexygram/header/HeaderConfig.java': '''package app.flexygram.header;
        public class HeaderConfig {public static boolean centered;
        public static boolean centerTitle(){return centered;} public static boolean adaptiveBubble(){return true;}}''',
        'Probe.java': '''import app.flexygram.header.*;
        public class Probe {public static void main(String[] args){
          HeaderGeometry g=new HeaderGeometry();
          for(boolean centered:new boolean[]{true,false})for(boolean rtl:new boolean[]{true,false}){
            HeaderConfig.centered=centered;
            for(int name:new int[]{28,143,800,10}){
              g.update(360,24,44,18,1,rtl,1,name+24);
              if(name<200 && g.title.width()!=Math.max(44,name+24))throw new AssertionError();
              if(g.title.left<(rtl?g.avatar:g.back).right+6 || g.title.right>(rtl?g.back:g.avatar).left-6)
                throw new AssertionError();
            }
          }
        }}'''
    }, [JAVA/'app/flexygram/header/HeaderGeometry.java'])


def test_floating_draws_one_fitted_avatar_and_one_local_fade(tmp_path):
    probe(tmp_path, {
        'android/graphics/Canvas.java': '''package android.graphics;public class Canvas{
          public int depth;public float x,y;
          public int save(){return ++depth;} public void translate(float x,float y){this.x=x;this.y=y;}
          public void clipPath(Path p){} public void restoreToCount(int n){depth=n-1;}
        }''',
        'android/graphics/Path.java': '''package android.graphics;public class Path{
          public enum Direction{CW}public void rewind(){}public void addCircle(float x,float y,float r,Direction d){}
        }''',
        'org/telegram/messenger/ImageReceiver.java': '''package org.telegram.messenger;
        public class ImageReceiver{
          public int iw,ih,draws;public float w=12,h=14,x=2,y=3,drawWidth,drawHeight;public boolean fit;
          public int getBitmapWidth(){return iw;}public int getBitmapHeight(){return ih;}
          public float getImageX(){return x;}public float getImageY(){return y;}
          public float getImageWidth(){return w;}public float getImageHeight(){return h;}
          public boolean isAspectFit(){return fit;}public void setAspectFit(boolean f){fit=f;}
          public void setImageCoords(float a,float b,float c,float d){x=a;y=b;w=c;h=d;}
          public void draw(android.graphics.Canvas c){if(!fit)throw new AssertionError();draws++;drawWidth=w;drawHeight=h;}
        }''',
        'app/flexygram/header/fusion/SignatureFusionAvatarMask.java': '''package app.flexygram.header.fusion;
        import android.graphics.Canvas;public class SignatureFusionAvatarMask{
          public static int layers;public static float width,height;
          public int begin(Canvas c,float x,float y,float r,float b){layers++;width=r-x;height=b-y;return c.save();}
          public void finishFloating(Canvas c,int n,float w,float h,boolean rtl){
            if(w!=width||h!=height)throw new AssertionError();c.restoreToCount(n);}
        }''',
        'Probe.java': '''import android.graphics.Canvas;import app.flexygram.header.fusion.*;import org.telegram.messenger.ImageReceiver;
        public class Probe{ public static void main(String[]args){
          SignatureFloatingPhoto renderer=new SignatureFloatingPhoto();
          ImageReceiver r=new ImageReceiver();Canvas c=new Canvas();int frames=0;
          for(boolean rtl:new boolean[]{false,true})for(int w:new int[]{60,120,240,600})
          for(int placeholder:new int[]{38,0,38}){
            r.iw=w;r.ih=120; renderer.draw(c,r,180,48,rtl,placeholder);frames++;
            float expected=placeholder==0?Math.min(180,48f*w/120):38;
            if(r.draws!=frames||SignatureFusionAvatarMask.layers!=frames||r.drawWidth!=expected
              ||r.drawHeight!=(placeholder==0?48:38)||SignatureFusionAvatarMask.width!=expected
              ||c.x!=(rtl?180-expected:0)||c.y!=(placeholder==0?0:5)||c.depth!=0
              ||r.x!=2||r.y!=3||r.w!=12||r.h!=14||r.fit)throw new AssertionError();
          }
        }}'''
    }, [JAVA/'app/flexygram/header/fusion/SignatureFloatingPhoto.java'])
