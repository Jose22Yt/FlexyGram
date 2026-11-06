"""Run the native-material bridge and mode policy, without an APK or device claim."""
from test_render_work_reuse import JAVA, ROOT, probe
from test_composer_layout import method
import xml.etree.ElementTree as ET


def test_native_material_keeps_shader_filter_alpha_and_provider_ownership(tmp_path):
    probe(tmp_path, {
        'app/flexygram/bubbles/SignatureWallpaperBlur.java': '''package app.flexygram.bubbles;import android.graphics.*;public class SignatureWallpaperBlur {public static class Owner {public boolean ready;public int calls,alpha;public Paint material;public float x,y;public boolean draw(Canvas c,Path p,float x,float y,int a,Paint m){calls++;this.x=x;this.y=y;alpha=a;material=m;return ready;}}}''',
        'android/graphics/Path.java': 'package android.graphics;public class Path{}',
        'android/graphics/Paint.java': '''package android.graphics;public class Paint{
 public static final int ANTI_ALIAS_FLAG=1;public static int allocations;public Object shader,filter;public int alpha=255,color;
 public Paint(int flags){allocations++;}public void set(Paint p){shader=p.shader;filter=p.filter;alpha=p.alpha;color=p.color;}
 public Object getColorFilter(){return filter;}public void setColorFilter(Object f){filter=f;}public int getAlpha(){return alpha;}public void setAlpha(int a){alpha=a;}public int getColor(){return color;}}''',
        'android/graphics/Canvas.java': '''package android.graphics;public class Canvas{
 public int draws,alpha,color;public Object shader,filter;public void drawPath(Path p,Paint paint){draws++;alpha=paint.alpha;color=paint.color;shader=paint.shader;filter=paint.filter;}}''',
        'org/telegram/ui/ActionBar/Theme.java': '''package org.telegram.ui.ActionBar;import android.graphics.Paint;public class Theme{
 public static final String key_paint_chatActionBackground="normal",key_paint_chatActionBackgroundSelected="selected",key_paint_chatActionBackgroundDarken="darken",key_paint_chatActionText="ink";
 public static int maps,w,h;public static float x,y;public static boolean gradient;public static final Paint normal=new Paint(1),selected=new Paint(1),darken=new Paint(1),ink=new Paint(1);
 public interface ResourcesProvider{void applyServiceShaderMatrix(int w,int h,float x,float y);boolean hasGradientService();Paint getPaint(String key);}
 public static void applyServiceShaderMatrix(int a,int b,float c,float d){maps++;w=a;h=b;x=c;y=d;}
 public static boolean hasGradientService(){return gradient;}
 public static Paint getThemePaint(String k,ResourcesProvider p){if(p!=null)return p.getPaint(k);return k.equals("normal")?normal:k.equals("selected")?selected:k.equals("darken")?darken:ink;}}''',
        'Probe.java': '''import android.graphics.*;import org.telegram.ui.ActionBar.Theme;import app.flexygram.bubbles.ServiceBubbleSurface;
 public class Probe{static void check(boolean v){if(!v)throw new AssertionError();}
 public static void main(String[]args){ServiceBubbleSurface surface=new ServiceBubbleSurface();Canvas c=new Canvas();Path path=new Path();
 Theme.normal.shader=new Object();Theme.normal.filter=new Object();Theme.normal.alpha=173;Theme.selected.alpha=211;Theme.ink.color=0xffeeeeee;
 int allocations=Paint.allocations;
 for(int alpha:new int[]{0,1,127,255}){
 surface.draw(c,path,null,100,200,3,49,alpha,false);
 check(c.alpha==Math.round(173*alpha/255f)&&c.shader==Theme.normal.shader&&c.filter==Theme.normal.filter);
 check(Theme.normal.alpha==173&&Theme.maps>0&&Theme.w==100&&Theme.h==200&&Theme.x==3&&Theme.y==49);
 surface.draw(c,path,null,100,200,3,49,alpha,true);check(c.alpha==Math.round(211*alpha/255f));
 }
 int draws=c.draws;check(!surface.draw(c,path,null,0,100,0,0,255,false)&&c.draws==draws);
 check(ServiceBubbleSurface.textColor(null)==0xffeeeeee);
 final Paint chatPaint=new Paint(1);chatPaint.alpha=133;chatPaint.color=0xffffffff;chatPaint.shader=new Object();
 Theme.ResourcesProvider provider=new Theme.ResourcesProvider(){public void applyServiceShaderMatrix(int w,int h,float x,float y){check(w==123&&h==456&&x==-10&&y==65);}
 public boolean hasGradientService(){return true;}public Paint getPaint(String k){return chatPaint;}};
 int maps=Theme.maps;draws=c.draws;
 surface.draw(c,path,provider,123,456,-10,65,127,true);check(c.draws==draws+2&&Theme.maps==maps&&c.alpha==Math.round(133*127/255f)&&c.shader==chatPaint.shader&&chatPaint.alpha==133);
 check(ServiceBubbleSurface.textColor(provider)==0xffffffff);
 allocations=Paint.allocations;for(int i=0;i<20000;i++)surface.drawMapped(c,path,provider,255,false);check(Paint.allocations==allocations);
 Theme.gradient=false;Theme.normal.shader=null;Theme.normal.filter=null;surface.drawMapped(c,path,null,255,false);check(c.shader==null&&c.filter==null);
 }}''',
    }, [JAVA/'app/flexygram/bubbles/ServiceBubbleSurface.java'])


def test_mode_default_validation_and_legacy_preferences_survive_switches(tmp_path):
    probe(tmp_path, {
        'android/content/Context.java': '''package android.content;public class Context{public static final int MODE_PRIVATE=0;public SharedPreferences p;public SharedPreferences getSharedPreferences(String f,int m){return p;}}''',
        'android/content/SharedPreferences.java': '''package android.content;public interface SharedPreferences{
 boolean getBoolean(String k,boolean d);int getInt(String k,int d);Editor edit();interface Editor{Editor putBoolean(String k,boolean v);Editor putInt(String k,int v);void apply();}}''',
        'org/telegram/messenger/ApplicationLoader.java': 'package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext=new android.content.Context();}',
        'org/telegram/messenger/BuildConfig.java': 'package org.telegram.messenger;public class BuildConfig{public static final boolean CONNECTED_ALPHA=true;}',
        'Probe.java': '''import android.content.*;import app.flexygram.bubbles.*;import org.telegram.messenger.ApplicationLoader;
 public class Probe{static void check(boolean v){if(!v)throw new AssertionError();}
 static class Prefs implements SharedPreferences,SharedPreferences.Editor{
 java.util.Map<String,Object> values=new java.util.HashMap<>();public boolean getBoolean(String k,boolean d){return (boolean)values.getOrDefault(k,d);}public int getInt(String k,int d){return (int)values.getOrDefault(k,d);}
 public Editor edit(){return this;}public Editor putBoolean(String k,boolean v){values.put(k,v);return this;}public Editor putInt(String k,int v){values.put(k,v);return this;}public void apply(){}
 }
 public static void main(String[]args){Prefs p=new Prefs();ApplicationLoader.applicationContext.p=p;
 BubbleConfig.load();check(BubbleConfig.adaptive()&&BubbleConfig.surfaceEffect()==0&&!BubbleConfig.backgroundBlur());
 BubbleConfig.setBackgroundBlur(true);BubbleConfig.setTransparency(29);BubbleConfig.setBorderTenths(17);BubbleConfig.setOutlineStyle(2);
 check(!BubbleConfig.backgroundBlur());BubbleConfig.setSurfaceEffect(BubbleConfig.LEGACY);BubbleConfig.load();check(!BubbleConfig.adaptive()&&BubbleConfig.backgroundBlur());
 check(BubbleConfig.transparency()==29&&BubbleConfig.borderTenths()==17&&BubbleConfig.outlineStyle()==2&&!BubbleConfig.outlineEnabled());
 BubbleConfig.setSurfaceEffect(BubbleConfig.ADAPTIVE);BubbleConfig.load();check(BubbleConfig.adaptive()&&!BubbleConfig.backgroundBlur()&&BubbleConfig.outlineEnabled());
 BubbleConfig.setSurfaceEffect(BubbleConfig.LEGACY);check(BubbleConfig.backgroundBlur()&&BubbleConfig.transparency()==29);
 for(int value:new int[]{-1,2,Integer.MAX_VALUE}){p.putInt(BubbleConfig.SURFACE_EFFECT,value);BubbleConfig.load();check(BubbleConfig.adaptive());}
 BubbleConfig.setSurfaceEffect(900);check(BubbleConfig.adaptive());
 for(int n=0;n<=20;n++){BubbleConfig.setBorderTenths(n);BubbleConfig.load();check(BubbleConfig.borderTenths()==n&&BubbleConfig.borderDp()==n/10f);}
 BubbleConfig.setBorderTenths(-1);BubbleConfig.load();check(BubbleConfig.borderTenths()==0);
 BubbleConfig.setBorderTenths(21);BubbleConfig.load();check(BubbleConfig.borderTenths()==20);
 check(BubbleConfig.smallTimestamps());BubbleConfig.setSmallTimestamps(false);BubbleConfig.load();check(!BubbleConfig.smallTimestamps());
 BubbleConfig.setSurfaceEffect(BubbleConfig.LEGACY);check(!BubbleConfig.smallTimestamps());
 BubbleConfig.setSmallTimestamps(true);BubbleConfig.load();check(BubbleConfig.smallTimestamps());
 }}''',
    }, [JAVA/'app/flexygram/bubbles/BubbleConfig.java', JAVA/'app/flexygram/bubbles/BubbleStyle.java'])


def test_adaptive_fill_preserves_native_alpha_and_continues_to_shared_border(tmp_path):
    source=(JAVA/'org/telegram/ui/ActionBar/MessageDrawable.java').read_text()
    branch=method(source,'if (adaptiveSurface)').replace('adaptiveSurface', 'adaptive')
    interface=method(source,'public interface GlassSource')
    probe(tmp_path,{'Probe.java': '''public class Probe{
 static class Canvas{int draws;void drawPath(Path p,Paint paint){draws++;}}
 static class Path{}static class Paint{Object shader=new Object();int color,alpha;boolean aa;void reset(){shader=null;}void setAntiAlias(boolean v){aa=v;}void setColor(int c){color=c;}void setAlpha(int a){alpha=a;}}
 static class Theme{static final int key_chat_serviceBackgroundSelected=2,key_chat_serviceBackground=1;}
 static class Color{static int alpha(int c){return c>>>24;}}
 INTERFACE
 static class app{static class flexygram{static class bubbles{
 static class BubbleConfig{static int transparency;static int transparency(){return transparency;}}
 static class BubbleStyle{static int tintAlpha(int t){return Math.round(255*(1-t/100f));}}
 }}}
 boolean adaptive=true,isSelected;int alpha=255,legacy,color;GlassSource flexyGlassSource;Path path=new Path();Paint flexyFillPaint=new Paint();
 int getColor(int key){return key==2?0xcc123456:0xaa654321;}
 void draw(Canvas canvas){BRANCH legacy++;}
 static void check(boolean v){if(!v)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();Canvas c=new Canvas();
 for(int t:new int[]{0,35,100})for(boolean selected:new boolean[]{false,true})for(int a:new int[]{0,1,127,255}){app.flexygram.bubbles.BubbleConfig.transparency=t;p.isSelected=selected;p.alpha=a;p.draw(c);check(p.legacy>0&&p.flexyFillPaint.shader==null&&p.flexyFillPaint.aa&&p.flexyFillPaint.alpha==Math.round((selected?204:170)*a/255f));}
 p.flexyGlassSource=new GlassSource(){public boolean draw(Canvas c,Path path){throw new AssertionError();}public boolean draw(Canvas c,Path path,int alpha,boolean selected){check(alpha==p.alpha&&selected==p.isSelected);return true;}};
 int draws=c.draws,common=p.legacy;p.draw(c);check(c.draws==draws&&p.legacy==common+1);
 p.adaptive=false;p.draw(c);check(p.legacy==common+2);
 }}'''.replace('INTERFACE',interface).replace('BRANCH',branch)})


def test_localized_selector_and_backup_cover_native_mode():
    for locale in ['values','values-es','values-ru']:
        names={e.attrib['name'] for e in ET.parse(ROOT/f'TMessagesProj/src/main/res/{locale}/flexygram_bubbles.xml').getroot()}
        assert {'FlexyBubbleSurfaceEffect','FlexyBubbleAdaptiveSurface','FlexyBubbleLegacySurface'} <= names
    assert '"surface_effect",0' in (JAVA/'app/flexygram/studio/StudioClientCatalog.java').read_text()
    assert '"surfaceEffect","flexygram_bubbles","surface_effect",0,0,1' in (JAVA/'app/flexygram/studio/core/StudioSchema.java').read_text()


def test_service_ink_and_ticks_are_local_cached_and_leave_media_keys_unchanged(tmp_path):
    import re
    source=(JAVA/'org/telegram/ui/Cells/ChatMessageCell.java').read_text()
    functions='\n'.join(method(source,s) for s in ['private boolean hasAdaptiveBubbleSurface()', 'public int getThemedColor(int key)', 'private Drawable getThemedDrawable(String key)', 'private int getTimestampColor(boolean selected)'])
    keys=sorted(set(re.findall(r'Theme\.(key_\w+)',functions)))
    declarations=''.join(f'static final {"String" if k.startswith("key_drawable") else "int"} {k}={chr(34)+k+chr(34) if k.startswith("key_drawable") else str(i+1)};' for i,k in enumerate(keys))
    probe(tmp_path,{'Probe.java': '''import java.util.*;public class Probe{
 static class app{static class flexygram{static class bubbles{
 static class BubbleConfig{static boolean mode=true,tiny=true;static boolean adaptive(){return mode;}static boolean smallTimestamps(){return tiny;}}
 static class BubbleStyle{static boolean signature(){return true;}}
 static class ServiceBubbleSurface{static int ink=0xffffffff;static int textColor(Object p){return ink;}}
 }}}
 static class Drawable{
 static int clones;int tint=7;static class ConstantState{Drawable newDrawable(Object r){clones++;return new Drawable();}}
 ConstantState getConstantState(){return new ConstantState();}Drawable mutate(){return this;}void setTint(int c){tint=c;}}
 static class Provider{Drawable drawable=new Drawable();Drawable getDrawable(String key){return drawable;}}
 static class Theme{KEYS static int getColor(int key,Provider p){return key;}static Drawable getThemeDrawable(String k){return new Drawable();}}
 static class Message{boolean noBackground;boolean out;boolean isOutOwner(){return out;}boolean shouldDrawWithoutBackground(){return noBackground;}}
 static class ArrayMap<K,V>{List<K>keys=new ArrayList<>();List<V>values=new ArrayList<>();int size(){return keys.size();}V valueAt(int i){return values.get(i);}V get(K k){int i=keys.indexOf(k);return i<0?null:values.get(i);}void put(K k,V v){int i=keys.indexOf(k);if(i<0){keys.add(k);values.add(v);}else values.set(i,v);}}
 final ArrayMap<String,Drawable> adaptiveStatusDrawables=new ArrayMap<>(),adaptiveStatusSources=new ArrayMap<>();int adaptiveStatusColor;
 Provider resourcesProvider=new Provider();Message currentMessageObject=new Message();Object getResources(){return null;}
 FUNCTIONS
 static void check(boolean v){if(!v)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();
 for(int key:new int[]{Theme.key_chat_messageTextIn,Theme.key_chat_messageTextOut,Theme.key_chat_inTimeText,Theme.key_chat_outTimeText,Theme.key_chat_messageLinkIn,Theme.key_chat_messageLinkOut,Theme.key_chat_inFileNameText,Theme.key_chat_outAudioDurationText})check(p.getThemedColor(key)==0xffffffff);
 check(p.getThemedColor(-99)==-99);
 for(boolean mode:new boolean[]{true,false}){
  app.flexygram.bubbles.BubbleConfig.mode=mode;
  for(boolean out:new boolean[]{false,true}){
   p.currentMessageObject.out=out;
   int expected=mode?0xffffffff:out?Theme.key_chat_messageTextOut:Theme.key_chat_messageTextIn;
   check(p.getTimestampColor(false)==expected);check(p.getTimestampColor(true)==expected);
   app.flexygram.bubbles.BubbleConfig.tiny=false;
   check(p.getTimestampColor(false)==(out?Theme.key_chat_outTimeText:Theme.key_chat_inTimeText));
   check(p.getTimestampColor(true)==(out?Theme.key_chat_outTimeSelectedText:Theme.key_chat_inTimeSelectedText));
   app.flexygram.bubbles.BubbleConfig.tiny=true;
  }
 }
 app.flexygram.bubbles.BubbleConfig.mode=true;
 String[] keys={Theme.key_drawable_msgOutCheck,Theme.key_drawable_msgOutCheckRead,Theme.key_drawable_msgOutHalfCheck,Theme.key_drawable_msgOutCheckSelected,Theme.key_drawable_msgOutCheckReadSelected,Theme.key_drawable_msgOutHalfCheckSelected};
 for(String key:keys){Drawable d=p.getThemedDrawable(key);check(d!=p.resourcesProvider.drawable&&d.tint==0xffffffff);}
 int clones=Drawable.clones;for(int frame=0;frame<1000;frame++){
 app.flexygram.bubbles.ServiceBubbleSurface.ink=0xff000000|frame;
 for(String key:keys)check(p.getThemedDrawable(key).tint==app.flexygram.bubbles.ServiceBubbleSurface.ink);
 }
 check(Drawable.clones==clones&&p.resourcesProvider.drawable.tint==7&&p.adaptiveStatusDrawables.size()==6);
 p.resourcesProvider.drawable=new Drawable();p.getThemedDrawable(keys[0]);check(Drawable.clones==clones+1);
 p.currentMessageObject.noBackground=true;check(p.getThemedColor(Theme.key_chat_messageTextOut)==Theme.key_chat_messageTextOut&&p.getThemedDrawable(keys[0])==p.resourcesProvider.drawable);
 p.currentMessageObject.noBackground=false;app.flexygram.bubbles.BubbleConfig.mode=false;check(p.getThemedColor(Theme.key_chat_outTimeText)==Theme.key_chat_outTimeText&&p.getThemedDrawable(keys[0])==p.resourcesProvider.drawable);
 }}'''.replace('KEYS',declarations).replace('FUNCTIONS',functions)})
