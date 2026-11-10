"""Production queue/geometry probes. Work counts are not device FPS measurements."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_cold_chat_open_reads_off_ui_and_keeps_accounts_and_peer_types_separate(tmp_path):
    files = {
        'android/os/Bundle.java': '''package android.os;public class Bundle {
 public long chat,user;public int enc;public long getLong(String k,long d){return k.equals("chat_id")?chat:user;}
 public int getInt(String k,int d){return enc;}}''',
        'org/telegram/tgnet/TLRPC.java': '''package org.telegram.tgnet;public class TLRPC {
 public static class Chat {public long id;}public static class User {public long id;}
 public static class EncryptedChat {public int id;public long user_id;}}''',
        'org/telegram/messenger/AndroidUtilities.java': '''package org.telegram.messenger;public class AndroidUtilities {
 public static Runnable ui;public static void runOnUIThread(Runnable r){ui=r;}}''',
        'org/telegram/messenger/FileLog.java': 'package org.telegram.messenger;public class FileLog {public static void e(Exception e){}}',
        'org/telegram/messenger/MessagesController.java': '''package org.telegram.messenger;import org.telegram.tgnet.TLRPC;import java.util.*;
public class MessagesController {
 static MessagesController[] instances={new MessagesController(),new MessagesController()};
 public static MessagesController getInstance(int a){return instances[a];}
 Map<Long,TLRPC.Chat> chats=new HashMap<>();Map<Long,TLRPC.User>users=new HashMap<>();Map<Integer,TLRPC.EncryptedChat>encs=new HashMap<>();
 public TLRPC.Chat getChat(long id){return chats.get(id);}public TLRPC.User getUser(long id){return users.get(id);}
 public TLRPC.EncryptedChat getEncryptedChat(int id){return encs.get(id);}
 public void putChat(TLRPC.Chat c,boolean cache){chats.put(c.id,c);}public void putUser(TLRPC.User u,boolean cache){users.put(u.id,u);}
 public void putEncryptedChat(TLRPC.EncryptedChat e,boolean cache){encs.put(e.id,e);}}
''',
        'org/telegram/messenger/MessagesStorage.java': '''package org.telegram.messenger;import org.telegram.tgnet.TLRPC;
public class MessagesStorage {
 static MessagesStorage[]instances={new MessagesStorage(),new MessagesStorage()};public static MessagesStorage getInstance(int a){return instances[a];}
 public static boolean onStorage;public static int reads;public static boolean fail,missing;
 public static class Queue {public Runnable work;public void postRunnable(Runnable r){if(work!=null)throw new AssertionError();work=r;}
 public void fire(){Runnable r=work;work=null;onStorage=true;try{r.run();}finally{onStorage=false;}}}
 public Queue queue=new Queue();public Queue getStorageQueue(){return queue;}
 static void reading(){if(!onStorage)throw new AssertionError("disk on UI");reads++;if(fail)throw new IllegalStateException();}
 public TLRPC.Chat getChat(long id){reading();if(missing)return null;TLRPC.Chat c=new TLRPC.Chat();c.id=id;return c;}
 public TLRPC.User getUser(long id){reading();if(missing)return null;TLRPC.User u=new TLRPC.User();u.id=id;return u;}
 public TLRPC.EncryptedChat getEncryptedChat(long id){reading();if(missing)return null;TLRPC.EncryptedChat e=new TLRPC.EncryptedChat();e.id=(int)id;e.user_id=9000000001L;return e;}}
''',
        'Probe.java': '''import app.flexygram.performance.ChatPeerPreloader;import android.os.Bundle;import org.telegram.messenger.*;
public class Probe {
 static int calls;static boolean found;static void done(boolean ok){calls++;found=ok;}
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){
 check(!ChatPeerPreloader.prepare(0,null,Probe::done));
 for(int type=0;type<3;type++){
 Bundle b=new Bundle();if(type==0)b.chat=5000000001L;else if(type==1)b.user=6000000001L;else b.enc=17;
 int before=MessagesStorage.reads;check(ChatPeerPreloader.prepare(1,b,Probe::done));check(MessagesStorage.reads==before&&calls==type);
 MessagesStorage.getInstance(1).queue.fire();check(calls==type);AndroidUtilities.ui.run();check(found&&calls==type+1);
 check(!ChatPeerPreloader.prepare(1,b,Probe::done));
 check(ChatPeerPreloader.prepare(0,b,Probe::done));MessagesStorage.getInstance(0).queue.fire();AndroidUtilities.ui.run();calls--;
 }
 Bundle b=new Bundle();b.user=42;MessagesStorage.missing=true;check(ChatPeerPreloader.prepare(0,b,Probe::done));MessagesStorage.getInstance(0).queue.fire();AndroidUtilities.ui.run();check(!found);
 MessagesStorage.missing=false;MessagesStorage.fail=true;b.user=43;check(ChatPeerPreloader.prepare(0,b,Probe::done));MessagesStorage.getInstance(0).queue.fire();AndroidUtilities.ui.run();check(!found);
 }
}'''
    }
    probe(tmp_path, files, [JAVA/'app/flexygram/performance/ChatPeerPreloader.java'])
    dialogs = (JAVA/'org/telegram/ui/DialogsActivity.java').read_text()
    opening = method(dialogs, 'public boolean presentFragment(BaseFragment fragment)')
    assert opening.index('ChatPeerPreloader.prepare') < opening.index('super.presentFragment')
    assert 'generation != chatOpenGeneration' in opening and 'isPaused()' in opening
    for lifecycle in ['public void onPause()', 'public void onFragmentDestroy()']:
        assert 'chatOpenGeneration++' in method(dialogs, lifecycle)


def test_blur_tiles_cover_negative_coordinates_and_do_not_expand_aligned_edges(tmp_path):
    source = (JAVA/'org/telegram/ui/Components/blur3/DownscaleScrollableNoiseSuppressor.java').read_text()
    rounding = '\n'.join(method(source, s) for s in ['private static int roundDown(', 'public static int roundUp('])
    probe(tmp_path, {'Probe.java': '''public class Probe {
 ROUND
 public static void main(String[]args){
 for(int grid:new int[]{1,8,16})for(int i=-10000;i<=10000;i++){
 float v=i*.125f;int low=roundDown(v,grid),high=roundUp(v,grid);
 if(low>v||high<v||low%grid!=0||high%grid!=0||v-low>=grid||high-v>=grid)throw new AssertionError();
 if(v%grid==0&&(low!=v||high!=v))throw new AssertionError("aligned edge expanded");
 }
 }}'''.replace('ROUND', rounding)})


def test_blur_capture_reuses_static_content_but_refreshes_moved_regions_and_empty_composite(tmp_path):
    source = (JAVA/'org/telegram/ui/Components/blur3/DownscaleScrollableNoiseSuppressor.java').read_text()
    capture = method(source, 'public boolean invalidateResultRenderNodes(IBlur3Capture capture,')
    probe(tmp_path, {'Probe.java': '''import java.util.*;public class Probe {
 static class Rect {int left,top,right=100,bottom=60;}
 static class RectF {void set(Rect r){}}
 static class Canvas {void save(){}void restore(){}void translate(float x,float y){}}
 interface IBlur3Capture {void capture(Canvas c,RectF r);void captureCalculateHash(Hash h,RectF r);}
 static class Hash {long h;void start(){h=0;}void add(long v){h=h*31+v;}long get(){return h;}boolean isUnsupported(){return false;}}
 static class Node {boolean hasDisplayList(){return true;}}
 static class SourcePart {Rect position=new Rect();Node renderNode=new Node();long lastHash;}
 List<SourcePart>rectRenderNodes=new ArrayList<>();int rectRenderNodesCount=1,composites;RectF tmpRectF=new RectF();Hash builder=new Hash();
 Canvas beginRecordingRect(int a){return new Canvas();}void endRecordingRect(){}
 boolean invalidateResultRenderNodes(int w,int h){composites++;return true;}
 CAPTURE
 public static void main(String[]args){Probe p=new Probe();p.rectRenderNodes.add(new SourcePart());int[] draws={0};
 IBlur3Capture c=new IBlur3Capture(){public void capture(Canvas c,RectF r){draws[0]++;}public void captureCalculateHash(Hash h,RectF r){h.add(7);}};
 for(int i=0;i<10000;i++)p.invalidateResultRenderNodes(c,100,60);
 if(draws[0]!=1)throw new AssertionError("static recapture");
 p.rectRenderNodes.get(0).position.top=16;p.invalidateResultRenderNodes(c,100,60);if(draws[0]!=2)throw new AssertionError("stale origin");
 int count=p.composites;p.rectRenderNodesCount=0;p.invalidateResultRenderNodes(c,200,80);if(p.composites!=count+1)throw new AssertionError("stale composite");
 }}'''.replace('CAPTURE', capture)})


def test_hidden_blur_regions_do_not_allocate_or_record_zero_sized_nodes(tmp_path):
    source = (JAVA/'org/telegram/ui/Components/blur3/DownscaleScrollableNoiseSuppressor.java').read_text()
    setup = '\n'.join(method(source, signature) for signature in [
        'public void setupRenderNodes(GlassPositionsArray positions)',
        'public void setupRenderNodes(List<RectF> positions, int count)',
        'private void addCapturePosition('])
    probe(tmp_path, {'Probe.java': '''import java.util.*;public class Probe{
 static class RectF{int l,t,r,b;RectF(int a,int c,int d,int e){l=a;t=c;r=d;b=e;}boolean isEmpty(){return l>=r||t>=b;}}
 static class GlassPositionsArray extends ArrayList<RectF>{}
 static class SourcePart{RectF last;void setPosition(RectF r){last=r;}}
 int rectRenderNodesCount;ArrayList<SourcePart>rectRenderNodes=new ArrayList<>();
 SETUP
 public static void main(String[]args){Probe p=new Probe();GlassPositionsArray positions=new GlassPositionsArray();
 positions.add(new RectF(0,0,0,0));positions.add(new RectF(4,9,2,3));RectF visible=new RectF(0,-16,100,20);positions.add(visible);
 p.setupRenderNodes(positions);if(p.rectRenderNodesCount!=1||p.rectRenderNodes.size()!=1||p.rectRenderNodes.get(0).last!=visible)throw new AssertionError();
 SourcePart first=p.rectRenderNodes.get(0);for(int i=0;i<10000;i++)p.setupRenderNodes(positions,3);
 if(p.rectRenderNodes.size()!=1||p.rectRenderNodes.get(0)!=first)throw new AssertionError();
 p.setupRenderNodes(positions,2);if(p.rectRenderNodesCount!=0)throw new AssertionError();
 }}'''.replace('SETUP', setup)})


def test_badge_clip_matches_scaled_clear_geometry_without_offscreen_layer(tmp_path):
    source = (JAVA/'org/telegram/ui/Components/glass/GlassTabView.java').read_text()
    clip = method(source, 'private void clipCounterGap(')
    draw = method(source, 'protected void dispatchDraw(')
    assert 'saveLayer' not in draw and 'PAINT_CLEAR' not in draw
    probe(tmp_path, {'Probe.java': '''public class Probe {
 static float density=1;static float dpf2(float n){return n*density;}static int dp(float n){return (int)Math.ceil(n*density);}
 static class RectF {float l,t,r,b;void set(float a,float c,float d,float e){l=a;t=c;r=d;b=e;}void set(RectF q){set(q.l,q.t,q.r,q.b);}
 public boolean equals(Object o){RectF q=(RectF)o;return l==q.l&&t==q.t&&r==q.r&&b==q.b;}}
 static class Path {enum Direction{CW}int builds;void rewind(){}void addRoundRect(RectF r,float a,float b,Direction d){builds++;}}
 static class Canvas {int clips;void clipOutPath(Path p){clips++;}void clipPath(Path p,Object op){clips++;}}
 static class Region {static class Op{static Object DIFFERENCE;}}
 static class Counter {float width=25;float getCurrentWidth(){return width;}}
 static class MainTabsUiHelper{static float getMainTabCounterCenterY(boolean m,int h){return 14*density;}}
 static class android {static class os {static class Build {static class VERSION {static int SDK_INT=26;}}}}
 RectF tmpRectF=new RectF(),counterCutoutBounds=new RectF();Path counterCutout=new Path();float counterCutoutRadius=-1;Counter counter=new Counter();boolean mainTabMaterial3;int getHeight(){return 60;}
 CLIP
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){for(float d:new float[]{1,2.75f})for(float factor:new float[]{.1f,.5f,1}){
 density=d;Probe p=new Probe();Canvas c=new Canvas();p.clipCounterGap(c,100,factor);
 float cx=50+dpf2(11),cy=14*d,half=(Math.max(dpf2(16),25+dp(8))*.5f+dpf2(1.33f))*factor;
 check(Math.abs(p.counterCutoutBounds.l-(cx-half))<.0001f&&Math.abs(p.counterCutoutBounds.r-(cx+half))<.0001f);
 check(Math.abs(p.counterCutoutBounds.t-(cy-(dpf2(8)+dpf2(1.33f))*factor))<.0001f);
 for(int i=0;i<10000;i++)p.clipCounterGap(c,100,factor);check(p.counterCutout.builds==1);
 p.counter.width=200;p.clipCounterGap(c,100,factor);check(p.counterCutout.builds==2);
 android.os.Build.VERSION.SDK_INT=25;p.clipCounterGap(c,100,factor);check(c.clips==10003);
 }}
 }'''.replace('CLIP', clip)})


def test_blur_hash_tracks_composition_and_refuses_dirty_content(tmp_path):
    float_fields = ['X', 'Y', 'Alpha', 'ScaleX', 'ScaleY', 'Rotation', 'RotationX', 'RotationY', 'PivotX', 'PivotY']
    int_fields = ['Width', 'Height', 'ScrollX', 'ScrollY', 'Visibility']
    view = 'package android.view;public class View {public boolean dirty,layout;'
    for name in float_fields:
        view += f'public float {name};public float get{name}(){{return {name};}}'
    for name in int_fields:
        view += f'public int {name};public int get{name}(){{return {name};}}'
    view += 'public long getUniqueDrawingId(){return 1;}public boolean isDirty(){return dirty;}public boolean isLayoutRequested(){return layout;}}'
    probe(tmp_path, {
        'android/view/View.java': view,
        'android/os/Build.java': 'package android.os;public class Build{public static class VERSION{public static int SDK_INT=29;}public static class VERSION_CODES{public static final int Q=29;}}',
        'android/graphics/ColorMatrix.java': 'package android.graphics;public class ColorMatrix{public float[]getArray(){return new float[20];}}',
        'Probe.java': '''import org.telegram.ui.Components.blur3.capture.IBlur3Hash;import android.view.View;
public class Probe implements IBlur3Hash {
 long hash;boolean unsupported;public void add(long n){hash=hash*31+n;}public void unsupported(){unsupported=true;}
 static long hash(View v){Probe p=new Probe();p.add(v);if(p.unsupported)throw new AssertionError();return p.hash;}
 public static void main(String[]args)throws Exception{
 View v=new View();long first=hash(v);for(int i=0;i<10000;i++)if(hash(v)!=first)throw new AssertionError();
 for(var f:View.class.getFields()){
 if(f.getType()!=float.class&&f.getType()!=int.class)continue;
 if(f.getType()==float.class)f.setFloat(v,17);else f.setInt(v,17);
 if(hash(v)==first)throw new AssertionError(f.getName());
 if(f.getType()==float.class)f.setFloat(v,0);else f.setInt(v,0);
 }
 v.dirty=true;Probe p=new Probe();p.add(v);if(!p.unsupported)throw new AssertionError();
 v.dirty=false;v.layout=true;p=new Probe();p.add(v);if(!p.unsupported)throw new AssertionError();
 v.layout=false;android.os.Build.VERSION.SDK_INT=28;p=new Probe();p.add(v);if(!p.unsupported)throw new AssertionError();
 }}'''
    }, [JAVA/'org/telegram/ui/Components/blur3/capture/IBlur3Hash.java'])


def test_opaque_native_material_skips_backdrop_recording_and_transparency_restores_it(tmp_path):
    source = (JAVA/'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawableRenderNode.java').read_text()
    update = method(source, 'public void updateDisplayList()')
    probe(tmp_path, {'Probe.java': '''public class Probe {
 static int dp(int n){return n;}static class Color{static int alpha(int c){return c>>>24;}}
 static class Build {static class VERSION{static int SDK_INT=33;}}
 static class Canvas {void save(){}void restore(){}void translate(float x,float y){}void drawColor(int c){}void drawRenderNode(Node n){}void drawPath(Object p,Object ink){}}
 static class Node {int records;Canvas beginRecording(){records++;return new Canvas();}void endRecording(){}}
 static class Rect {int left,top,right=200,bottom=60;int width(){return right-left;}int height(){return bottom-top;}}
 static class Props {Rect boundsWithPadding=new Rect();int liquidThickness;float liquidIntensity,liquidIndex,strokeWidthTop,strokeWidthBottom;float[]radii=new float[8],shaderRadii=new float[8];boolean useFullStroke;Object strokePathTop;}
 static class Source {int draws;void draw(Canvas c,float a,float b,float d,float e){draws++;}}
 static class Liquid {int updates;void update(Object...args){updates++;}}
 float sourceOffsetX,sourceOffsetY;Props boundProps=new Props();Node renderNode=new Node(),renderNodeFill=new Node();Source source=new Source();Liquid liquidGlassEffect=new Liquid();int backgroundColor,strokeColorTop,strokeColorBottom,strokeColorFull;Object paintStrokeTop,paintStrokeBottom,paintStrokeFull;
 void drawStrokeRaw(Object...args){}
 UPDATE
 public static void main(String[]args){Probe p=new Probe();p.backgroundColor=0xff123456;
 for(int i=0;i<1000;i++)p.updateDisplayList();
 if(p.source.draws!=0||p.renderNodeFill.records!=0||p.liquidGlassEffect.updates!=0||p.renderNode.records!=1000)throw new AssertionError();
 p.backgroundColor=0x80123456;p.updateDisplayList();if(p.source.draws!=1||p.liquidGlassEffect.updates!=1)throw new AssertionError();
 p.liquidGlassEffect=null;p.updateDisplayList();if(p.source.draws!=2)throw new AssertionError();
 }}'''.replace('UPDATE', update)})


def test_position_watcher_owns_and_releases_external_window_observers(tmp_path):
    probe(tmp_path, {
        'androidx/annotation/NonNull.java': 'package androidx.annotation;public @interface NonNull{}',
        'android/graphics/PointF.java': 'package android.graphics;public class PointF{public float x,y;}',
        'android/graphics/RectF.java': '''package android.graphics;public class RectF{public float left,top,right,bottom;
 public RectF(){}public RectF(RectF r){set(r);}public void set(RectF r){set(r.left,r.top,r.right,r.bottom);}
 public void set(float l,float t,float r,float b){left=l;top=t;right=r;bottom=b;}public void offset(float x,float y){left+=x;right+=x;top+=y;bottom+=y;}
 public boolean equals(Object o){RectF r=(RectF)o;return left==r.left&&top==r.top&&right==r.right&&bottom==r.bottom;}}''',
        'android/view/ViewParent.java': 'package android.view;public interface ViewParent{}',
        'android/view/ViewTreeObserver.java': '''package android.view;import java.util.*;public class ViewTreeObserver{
 public interface OnPreDrawListener{boolean onPreDraw();}public List<OnPreDrawListener>listeners=new ArrayList<>();public boolean isAlive(){return true;}
 public void addOnPreDrawListener(OnPreDrawListener l){listeners.add(l);}public void removeOnPreDrawListener(OnPreDrawListener l){listeners.remove(l);}}''',
        'android/view/View.java': '''package android.view;import java.util.*;public class View implements ViewParent{
 public interface OnAttachStateChangeListener{void onViewAttachedToWindow(View v);void onViewDetachedFromWindow(View v);}
 public ViewTreeObserver vto=new ViewTreeObserver();public List<OnAttachStateChangeListener>listeners=new ArrayList<>();
 public void addOnAttachStateChangeListener(OnAttachStateChangeListener l){listeners.add(l);}public void removeOnAttachStateChangeListener(OnAttachStateChangeListener l){listeners.remove(l);}
 public ViewTreeObserver getViewTreeObserver(){return vto;}public boolean isAttachedToWindow(){return true;}public ViewParent getParent(){return null;}
 public int getWidth(){return 10;}public int getHeight(){return 20;}public int getScrollX(){return 0;}public int getScrollY(){return 0;}public float getX(){return 0;}public float getY(){return 0;}public void getLocationOnScreen(int[]a){a[0]=0;a[1]=0;}}''',
        'android/view/ViewGroup.java': 'package android.view;public class ViewGroup extends View{}',
        'Probe.java': '''import android.view.*;import org.telegram.ui.Components.chat.ViewPositionWatcher;
public class Probe {static void check(boolean v){if(!v)throw new AssertionError();}public static void main(String[]args){
 ViewGroup anchor=new ViewGroup();View external=new View();ViewPositionWatcher watcher=new ViewPositionWatcher(anchor);
 for(int i=0;i<1000;i++)watcher.subscribe(external,anchor,(v,r)->{},true);
 check(external.vto.listeners.size()==1&&external.listeners.size()==1);
 watcher.unsubscribe(external);check(external.vto.listeners.isEmpty()&&external.listeners.isEmpty());
 View sameWindow=new View();sameWindow.vto=anchor.vto;watcher.subscribe(sameWindow,anchor,(v,r)->{},true);check(anchor.vto.listeners.size()==1);
 watcher.subscribe(external,anchor,(v,r)->{},true);watcher.clear();check(external.listeners.isEmpty()&&external.vto.listeners.isEmpty()&&sameWindow.listeners.isEmpty());
 watcher.subscribe(external,anchor,(v,r)->{},true);watcher.shutdown();check(anchor.vto.listeners.isEmpty()&&anchor.listeners.isEmpty()&&external.listeners.isEmpty());
 }}'''
    }, [JAVA/'org/telegram/ui/Components/chat/ViewPositionWatcher.java'])


def test_glass_reads_program_once_but_never_shares_mutable_shaders(tmp_path):
    probe(tmp_path, {
        'androidx/annotation/RequiresApi.java': 'package androidx.annotation;public @interface RequiresApi{int api();}',
        'android/graphics/Color.java': '''package android.graphics;public class Color {
 public static int alpha(int c){return c>>>24;}public static int red(int c){return c>>>16&255;}
 public static int green(int c){return c>>>8&255;}public static int blue(int c){return c&255;}}''',
        'android/graphics/RuntimeShader.java': '''package android.graphics;public class RuntimeShader {
 public static int instances;public RuntimeShader(String code){if(!code.equals("program"))throw new AssertionError();instances++;}
 public void setFloatUniform(String key,float...v){}}''',
        'android/graphics/RenderEffect.java': '''package android.graphics;public class RenderEffect {
 public static int creates;public RuntimeShader shader;public static RenderEffect createRuntimeShaderEffect(RuntimeShader s,String key){creates++;RenderEffect e=new RenderEffect();e.shader=s;return e;}}''',
        'android/graphics/RenderNode.java': '''package android.graphics;public class RenderNode {
 public RenderEffect effect;public int getWidth(){return 200;}public int getHeight(){return 60;}public void setRenderEffect(RenderEffect e){effect=e;}}''',
        'org/telegram/messenger/AndroidUtilities.java': 'package org.telegram.messenger;public class AndroidUtilities {public static int reads;public static String readRes(int id){reads++;return "program";}}',
        'org/telegram/messenger/R.java': 'package org.telegram.messenger;public class R {public static class raw{public static int liquid_glass_shader;}}',
        'Probe.java': '''import android.graphics.*;import org.telegram.ui.Components.blur3.LiquidGlassEffect;import org.telegram.messenger.AndroidUtilities;
public class Probe {public static void main(String[]args){java.util.Set<RuntimeShader>shaders=new java.util.HashSet<>();
 for(int i=0;i<1000;i++){RenderNode n=new RenderNode();LiquidGlassEffect glass=new LiquidGlassEffect(n);shaders.add(n.effect.shader);
 glass.update(0,0,200,60,20,20,20,20,10,1,1,0x80123456);int effects=RenderEffect.creates;
 for(int j=0;j<100;j++)glass.update(0,0,200,60,20,20,20,20,10,1,1,0x80123456);
 if(RenderEffect.creates!=effects)throw new AssertionError("unchanged uniforms rebuild effect");
 glass.update(0,0,200,60,20,20,20,20,10,1,1,0x80334455);if(RenderEffect.creates!=effects+1)throw new AssertionError();
 }
 if(AndroidUtilities.reads!=1||shaders.size()!=1000||RuntimeShader.instances!=1000)throw new AssertionError();
 }}'''
    }, [JAVA/'org/telegram/ui/Components/blur3/LiquidGlassEffect.java'])
