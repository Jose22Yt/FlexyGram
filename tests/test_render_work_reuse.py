"""Execute production render/cache policies; these are work-count checks, not FPS measurements."""
from pathlib import Path
import re
import shutil
import subprocess
import pytest
from test_composer_layout import method

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT/'TMessagesProj/src/main/java'


def probe(tmp_path, files, actual=()):
    if not shutil.which('java'):
        pytest.skip('JDK required')
    files = dict(files)
    build_config = 'org/telegram/messenger/BuildConfig.java'
    if build_config not in files:
        files[build_config] = 'package org.telegram.messenger;public final class BuildConfig{public static final boolean CONNECTED_ALPHA=true,NATIVE_BASELINE_TEST=false;}'
    elif 'NATIVE_BASELINE_TEST' not in files[build_config]:
        files[build_config] = files[build_config].replace('class BuildConfig{', 'class BuildConfig{public static final boolean NATIVE_BASELINE_TEST=false;').replace('class BuildConfig {', 'class BuildConfig {public static final boolean NATIVE_BASELINE_TEST=false;')
    paths=[]
    for name,content in files.items():
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content);paths.append(path)
    r=subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',str(tmp_path),*map(str,paths),*map(str,actual)],capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    r=subprocess.run(['java','-cp',str(tmp_path),'Probe'],capture_output=True,text=True)
    assert r.returncode==0,r.stderr


def test_radius_updates_rebuild_only_when_real_or_shader_geometry_changes(tmp_path):
    source=(JAVA/'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawable.java').read_text()
    functions='\n'.join(method(source,signature) for signature in [
        'public BlurredBackgroundDrawable setRadius(float radius)',
        'public BlurredBackgroundDrawable setRadius(float topLeft, float topRight, float bottomRight, float bottomLeft)',
        'public void setRadius(float topLeft, float topRight, float bottomRight, float bottomLeft, boolean forceBottomZero)',
        'private static boolean sameCorners(', 'public BlurredBackgroundDrawable setThickness(', 'public void setIntensity('])
    probe(tmp_path,{'Probe.java':'''import java.util.Arrays;class BlurredBackgroundDrawable{
 static class Props{float[]radii=new float[8],shaderRadii=new float[8];int builds,liquidThickness;float liquidIntensity=.75f;void build(){builds++;}}
 final Props boundProps=new Props();int changes;void onBoundPropsChanged(){changes++;}
 METHODS
}
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){
 BlurredBackgroundDrawable d=new BlurredBackgroundDrawable();
 for(int i=0;i<20000;i++)d.setRadius(23);check(d.boundProps.builds==1&&d.changes==1);
 d.setRadius(23,23,23,23);check(d.boundProps.builds==1);
 d.setRadius(10,12,14,16,true);check(d.boundProps.builds==2&&d.boundProps.radii[4]==0&&d.boundProps.shaderRadii[4]==14);
 d.setRadius(10,12,14,16,true);check(d.boundProps.builds==2);
 d.setRadius(10,12,0,0);check(d.boundProps.builds==2&&d.boundProps.shaderRadii[4]==14); // Four-corner API preserves native shader radii.
 d.setRadius(10,12,0,0,false);check(d.boundProps.builds==3&&d.boundProps.shaderRadii[4]==0);
 d.setRadius(10,12,14,16);check(d.boundProps.builds==4&&d.boundProps.radii[4]==14);
 int changes=d.changes;for(int i=0;i<20000;i++){d.setThickness(0);d.setIntensity(.75f);}check(d.changes==changes);
 d.setThickness(4);d.setIntensity(.5f);check(d.changes==changes+2);
}}'''.replace('METHODS',functions)})


def test_render_node_reuse_respects_zero_hash_resize_reentry_and_failed_recording(tmp_path):
    files={
        'android/os/Build.java':'package android.os;public class Build{public static class VERSION_CODES{public static final int Q=29;}}',
        'androidx/annotation/RequiresApi.java':'package androidx.annotation;public @interface RequiresApi{int api();}',
        'android/graphics/Canvas.java':'package android.graphics;public class Canvas{}',
        'android/graphics/RecordingCanvas.java':'package android.graphics;public class RecordingCanvas extends Canvas{}',
        'android/graphics/RenderNode.java':'''package android.graphics;public class RenderNode{
 public int width=100,height=60,begins,ends;public boolean display;
 public RenderNode(String n){}public int getWidth(){return width;}public int getHeight(){return height;}
 public boolean hasDisplayList(){return display;}public RecordingCanvas beginRecording(){begins++;display=false;return new RecordingCanvas();}public void endRecording(){ends++;display=true;}}''',
        'org/telegram/ui/Components/blur3/capture/IBlur3Hash.java':'package org.telegram.ui.Components.blur3.capture;public interface IBlur3Hash{void add(long n);void unsupported();}',
        'org/telegram/ui/Components/blur3/Blur3HashImpl.java':'package org.telegram.ui.Components.blur3;public class Blur3HashImpl implements org.telegram.ui.Components.blur3.capture.IBlur3Hash{long hash;public void start(){hash=0;}public long get(){return hash;}public void add(long n){hash=n;}public void unsupported(){hash=-1;}}',
        'Probe.java':'''import org.telegram.ui.Components.blur3.*;import org.telegram.ui.Components.blur3.capture.*;import android.graphics.*;
public class Probe implements RenderNodeWithHash.Renderer{
 RenderNodeWithHash wrapper;long hash;int draws;boolean fail,inside;
 public void renderNodeCalculateHash(IBlur3Hash h){h.add(hash);}
 public void renderNodeUpdateDisplayList(Canvas c){draws++;if(inside){inside=false;wrapper.invalidate();}if(fail){fail=false;throw new RuntimeException();}}
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){Probe p=new Probe();RenderNode node=new RenderNode("test");p.wrapper=new RenderNodeWithHash(node,p);
 p.wrapper.updateDisplayListIfNeeded();for(int i=0;i<1000;i++)p.wrapper.updateDisplayListIfNeeded();check(p.draws==1);
 for(int i=0;i<1000;i++)p.wrapper.invalidate();p.wrapper.updateDisplayListIfNeeded();check(p.draws==2);p.wrapper.updateDisplayListIfNeeded();check(p.draws==2);
 p.hash=1;p.wrapper.updateDisplayListIfNeeded();check(p.draws==3);node.width++;p.wrapper.updateDisplayListIfNeeded();check(p.draws==4);
 node.display=false;p.wrapper.updateDisplayListIfNeeded();check(p.draws==5);
 p.hash=-1;p.wrapper.updateDisplayListIfNeeded();p.wrapper.updateDisplayListIfNeeded();check(p.draws==7);
 p.hash=2;p.fail=true;try{p.wrapper.updateDisplayListIfNeeded();throw new AssertionError();}catch(RuntimeException expected){}check(node.begins==node.ends);
 p.wrapper.updateDisplayListIfNeeded();check(p.draws==9);
 p.inside=true;p.wrapper.invalidate();p.wrapper.updateDisplayListIfNeeded();p.wrapper.updateDisplayListIfNeeded();check(p.draws==11);
 p.wrapper.updateDisplayListIfNeeded();check(p.draws==11);
 node.display=false;p.fail=true;try{p.wrapper.updateDisplayListIfNeeded();throw new AssertionError();}catch(RuntimeException expected){}
 p.wrapper.updateDisplayListIfNeeded();check(p.draws==13&&node.begins==node.ends);
 }}'''}
    probe(tmp_path,files,[JAVA/'org/telegram/ui/Components/blur3/RenderNodeWithHash.java'])


def test_blur_effect_and_shadow_filter_reuse_keeps_real_changes(tmp_path):
    source=(JAVA/'org/telegram/ui/Components/blur3/source/BlurredBackgroundSourceRenderNode.java').read_text()
    setters='\n'.join(method(source,s) for s in ['public void setBlur(float radius)', 'public void setBlur(float radius, RenderEffect effect)'])
    shadow=(JAVA/'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawableRenderNode.java').read_text()
    shadow_state=shadow[shadow.index('    private int appliedShadowColor;'):shadow.index('    private boolean renderNodeInvalidated;')]
    assert 'updateShadowLayer(color)' in method(shadow,'public void draw(')
    probe(tmp_path,{'Probe.java':'''public class Probe{
 static class Shader{enum TileMode{CLAMP}}
 static class RenderEffect{static int blurs,chains;static RenderEffect createBlurEffect(float x,float y,Shader.TileMode m){if(x<=0||y<=0)throw new AssertionError();blurs++;return new RenderEffect();}static RenderEffect createChainEffect(RenderEffect a,RenderEffect b){chains++;return new RenderEffect();}}
 static class Node{int sets;RenderEffect effect;void setRenderEffect(RenderEffect e){sets++;effect=e;}}
 final Node renderNode=new Node();float appliedBlurRadius=Float.NaN;RenderEffect appliedInputEffect;
 SETTERS
 static class Paint{int changes;void setShadowLayer(float r,float x,float y,int c){changes++;}}
 Paint paintShadow=new Paint();float shadowLayerRadius=2,shadowLayerDx,shadowLayerDy=1;
 SHADOW
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();for(int i=0;i<20000;i++)p.setBlur(8);check(RenderEffect.blurs==1&&p.renderNode.sets==1);
 RenderEffect e=new RenderEffect();p.setBlur(8,e);for(int i=0;i<20000;i++)p.setBlur(8,e);check(RenderEffect.blurs==2&&RenderEffect.chains==1);
 p.setBlur(0,e);check(p.renderNode.effect==e&&RenderEffect.blurs==2);p.setBlur(0);check(p.renderNode.effect==null);int sets=p.renderNode.sets;p.setBlur(-1);check(p.renderNode.sets==sets);
 p.setBlur(10);check(RenderEffect.blurs==3);p.setBlur(10,new RenderEffect());check(RenderEffect.blurs==4&&RenderEffect.chains==2);
 for(int i=0;i<20000;i++)p.updateShadowLayer(0x33000000);check(p.paintShadow.changes==1);
 p.shadowLayerDy=3;p.updateShadowLayer(0x33000000);check(p.paintShadow.changes==2);p.updateShadowLayer(0x22000000);check(p.paintShadow.changes==3);
 }}'''.replace('SETTERS',setters).replace('SHADOW',shadow_state)})


def test_settings_resource_cache_is_bounded_and_separates_resource_tables(tmp_path):
    source=(JAVA/'app/exteraless/settings/utils/SettingsIcons.java').read_text()
    names=sorted(set(re.findall(r'R.drawable.(\w+)',source)))
    probe(tmp_path,{
        'android/content/res/Resources.java':'''package android.content.res;public class Resources{public java.util.Map<Integer,String> names=new java.util.HashMap<>();public int reads;public static class NotFoundException extends RuntimeException{}public String getResourceEntryName(int id){reads++;String n=names.get(id);if(n==null)throw new NotFoundException();return n;}}''',
        'android/content/Context.java':'package android.content;public class Context{public android.content.res.Resources resources=new android.content.res.Resources();public android.content.res.Resources getResources(){return resources;}}',
        'android/util/SparseIntArray.java':'package android.util;public class SparseIntArray{public java.util.Map<Integer,Integer> data=new java.util.HashMap<>();public int get(int k,int d){return data.getOrDefault(k,d);}public void put(int k,int v){data.put(k,v);}public void clear(){data.clear();}public int size(){return data.size();}}',
        'org/telegram/messenger/R.java':'package org.telegram.messenger;public class R{public static class drawable{'+''.join(f'public static final int {n}={i+1};' for i,n in enumerate(names))+'}}',
        'Probe.java':'''import app.exteraless.settings.utils.SettingsIcons;import android.content.Context;import org.telegram.messenger.R;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args)throws Exception{
 Context a=new Context();a.resources.names.put(1000,"msg_discussion");for(int i=0;i<20000;i++)check(SettingsIcons.resolve(a,1000)==R.drawable.fg_dm_conversaciones);check(a.resources.reads==1);
 Context b=new Context();b.resources.names.put(1000,"cloud_sync");check(SettingsIcons.resolve(b,1000)==R.drawable.fg_dm_nube);
 check(SettingsIcons.resolve(b,999)==999);b.resources.names.put(999,"msg_discussion");check(SettingsIcons.resolve(b,999)==R.drawable.fg_dm_conversaciones);
 b.resources.names.put(998,"custom_plugin_icon");check(SettingsIcons.resolve(b,998)==998);
 for(int i=2000;i<2500;i++){b.resources.names.put(i,"msg_discussion");SettingsIcons.resolve(b,i);}
 java.lang.reflect.Field f=SettingsIcons.class.getDeclaredField("resolvedIcons");f.setAccessible(true);check(((android.util.SparseIntArray)f.get(null)).size()<=128);
 }}''',
    },[JAVA/'app/exteraless/settings/utils/SettingsIcons.java'])


def test_unread_99_plus_does_not_relayout_but_keeps_real_count(tmp_path):
    source=(JAVA/'app/flexygram/header/SignatureChatHeader.java').read_text()
    setter=method(source,'public void setCount(')
    probe(tmp_path,{
        'android/text/TextPaint.java':'package android.text;public class TextPaint{public void set(TextPaint p){}public float measureText(String s){return s.length()*10;}}',
        'android/text/Layout.java':'package android.text;public class Layout{public enum Alignment{ALIGN_CENTER}}',
        'android/text/StaticLayout.java':'package android.text;public class StaticLayout{public static int builds;public String text;public StaticLayout(String s,TextPaint p,int w,Layout.Alignment a,float x,float y,boolean pad){builds++;text=s;}}',
        'Probe.java':'''public class Probe{static class Theme{static android.text.TextPaint dialogs_countTextPaint=new android.text.TextPaint();}
 int unreadCount,changes;android.text.TextPaint unreadPaint=new android.text.TextPaint();android.text.StaticLayout unreadLayout;
 void changed(){changes++;}SETTER
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();p.setCount(-3);check(p.changes==1&&p.unreadCount==0&&p.unreadLayout.text.equals("0"));
 for(int i=100;i<20000;i++)p.setCount(i);check(p.unreadCount==19999&&p.changes==2&&android.text.StaticLayout.builds==2&&p.unreadLayout.text.equals("99+"));
 p.setCount(99);check(p.changes==3&&p.unreadLayout.text.equals("99"));p.setCount(0);check(p.changes==4&&p.unreadLayout.text.equals("0"));p.setCount(0);check(p.changes==4);
 }}'''.replace('SETTER',setter),
    })


def test_translation_album_dedup_preserves_visibility_and_all_members(tmp_path):
    source=(JAVA/'org/telegram/ui/ChatActivity.java').read_text()
    translate=source[source.index('private Runnable checkTranslationRunnable'):]
    block=method(translate,'if (minId <= maxId)')
    assert 'java.util.HashSet<Long>' in block
    assert 'cancelRunOnUIThread(checkTranslationRunnable)' in method(source,'public void onFragmentDestroy()')
    probe(tmp_path,{'Probe.java':'''import java.util.*;
public class Probe{
 static class MessageObject{int id;long group;MessageObject(int id,long group){this.id=id;this.group=group;}int getId(){return id;}long getGroupId(){return group;}static class GroupedMessages{long groupId;ArrayList<MessageObject>messages=new ArrayList<>();}}
 ArrayList<MessageObject>messages=new ArrayList<>();Map<Long,MessageObject.GroupedMessages>groupedMessagesMap=new HashMap<>();
 List<Integer>seen=new ArrayList<>();List<Boolean>visible=new ArrayList<>();
 class Controller{Controller getTranslateController(){return this;}void checkTranslation(MessageObject m,boolean onScreen){seen.add(m.id);visible.add(onScreen);}}
 Controller getMessagesController(){return new Controller();}
 void run(int minId,int maxId){BLOCK}
 public static void main(String[]args){Probe p=new Probe();MessageObject one=new MessageObject(5,200),two=new MessageObject(200,200);MessageObject.GroupedMessages group=new MessageObject.GroupedMessages();group.groupId=200;group.messages.add(one);group.messages.add(two);p.groupedMessagesMap.put(200L,group);
 for(int i=0;i<1000;i++){p.messages.add(one);p.messages.add(two);}p.messages.add(new MessageObject(100,0));p.run(10,20);
 if(!p.seen.equals(List.of(5,200,100))||!p.visible.equals(List.of(true,false,false)))throw new AssertionError();
 }}'''.replace('BLOCK',block)})


def test_bitmap_blur_reuses_shader_and_releases_unusable_sources(tmp_path):
    source = (JAVA/'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawable.java').read_text()
    draw = method(source, 'private void drawSourceBitmap(')
    probe(tmp_path, {'Probe.java': '''public class Probe {
        static class Bitmap { boolean recycled; boolean isRecycled(){return recycled;} }
        static class Shader { enum TileMode {CLAMP} }
        static class BitmapShader {
            static int created;
            BitmapShader(Bitmap b, Shader.TileMode x, Shader.TileMode y){created++;}
            void setLocalMatrix(Matrix matrix){}
        }
        static class Matrix {void set(Matrix m){} void postTranslate(float x,float y){}}
        static class Paint {void setShader(BitmapShader s){} void setColor(int c){} void setAlpha(int a){}}
        static class Canvas {}
        static class Rect {int left,right,top,bottom;}
        static class Bounds {
            Rect boundsWithPadding=new Rect();
            int draws;
            void draw(Canvas c,Paint p){draws++;}
        }
        static class NinePatchDrawable {void setBounds(int l,int t,int r,int b){} void setAlpha(int a){} void draw(Canvas c){}}
        static class Color {static int alpha(int c){return c>>>24;}}
        static class Theme {static int multAlpha(int c,float a){return c;}}
        static class BlurredBackgroundSourceBitmap {
            Bitmap bitmap;
            Matrix matrix=new Matrix();
            Bitmap getBitmap(){return bitmap;} Matrix getMatrix(){return matrix;}
        }
        BitmapShader bitmapShader;
        Bitmap bitmapInShader;
        int alpha=255, shadowColor, backgroundColor, sourceOffsetX, sourceOffsetY;
        Matrix bitmapShaderMatrix=new Matrix();
        Bounds boundProps=new Bounds();
        Rect ninePatchDrawablePadding=new Rect();
        Paint backgroundBitmapPaint=new Paint(),backgroundBitmapFill=new Paint();
        NinePatchDrawable checkNinePatchDrawable(int c,boolean s){throw new AssertionError();}
        void drawStrokeInternalIfNeeded(Canvas c){}
        DRAW
        public static void main(String[] args){
            Probe p=new Probe(); Canvas c=new Canvas();
            BlurredBackgroundSourceBitmap source=new BlurredBackgroundSourceBitmap();
            source.bitmap=new Bitmap();
            for(int i=0;i<1000;i++){p.sourceOffsetX=i;p.drawSourceBitmap(c,source);}
            if(BitmapShader.created!=1 || p.boundProps.draws!=1000)throw new AssertionError();
            source.bitmap=new Bitmap();p.drawSourceBitmap(c,source);
            source.bitmap.recycled=true;p.drawSourceBitmap(c,source);
            if(p.bitmapShader!=null || p.bitmapInShader!=null)throw new AssertionError();
            source.bitmap=null;p.drawSourceBitmap(c,source);
            if(BitmapShader.created!=2 || p.boundProps.draws!=1001)throw new AssertionError();
        }
    }'''.replace('DRAW',draw)})


def test_downsampled_recording_maps_full_extent_and_reuses_rectangular_target(tmp_path):
    source = (JAVA/'org/telegram/ui/Components/blur3/source/BlurredBackgroundSourceBitmap.java').read_text()
    recording = method(source, 'public Canvas beginRecording(int width, int height, float scale)')
    probe(tmp_path, {'Probe.java': '''public class Probe {
        static class Bitmap {
            enum Config {ARGB_8888}
            int width,height,clears;
            boolean isRecycled(){return false;}
            int getWidth(){return width;} int getHeight(){return height;}
            void eraseColor(int color){clears++;}
            static Bitmap createBitmap(int w,int h, Config config){
                Bitmap b=new Bitmap();b.width=w;b.height=h;return b;
            }
        }
        static class Canvas {
            Canvas(Bitmap b){} float x,y;
            void scale(float sx,float sy){x=sx;y=sy;}
        }
        Bitmap bitmapInternal;
        RECORDING
        public static void main(String[] args){
            Probe p=new Probe();Canvas c=p.beginRecording(100,60,4);
            Bitmap b=p.bitmapInternal;
            if(c.x*100!=25 || c.y*60!=15)throw new AssertionError();
            p.beginRecording(100,60,4);
            if(p.bitmapInternal!=b || b.clears!=1)throw new AssertionError();
            p.beginRecording(160,60,4);
            if(p.bitmapInternal==b || p.bitmapInternal.width!=40)throw new AssertionError();
            p.beginRecording(1,1,8);
            if(p.bitmapInternal.width!=1 || p.bitmapInternal.height!=1)throw new AssertionError();
        }
    }'''.replace('RECORDING', recording)})
