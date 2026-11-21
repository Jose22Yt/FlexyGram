"""Scoped Kyant integration: real production caches executed with counted Android doubles."""
import hashlib,json
from test_render_work_reuse import ROOT,JAVA,probe
from test_composer_layout import method


def test_raw_scene_cache_records_only_on_change_and_never_captures_the_bar(tmp_path):
    probe(tmp_path,{
        'androidx/annotation/RequiresApi.java':'package androidx.annotation;public @interface RequiresApi{int value();}',
        'android/graphics/Matrix.java':'''package android.graphics;public class Matrix{public float x,y;public void reset(){x=y=0;}public void getValues(float[] a){a[0]=a[4]=a[8]=1;a[2]=x;a[5]=y;}}''',
        'android/view/ViewParent.java':'package android.view;public interface ViewParent{}',
        'android/view/View.java':'''package android.view;public class View implements ViewParent{public int draws;public float x,y;public boolean attached=true,fail;public ViewParent parent;public ViewParent getParent(){return parent;}public boolean isAttachedToWindow(){return attached;}public void transformMatrixToGlobal(android.graphics.Matrix m){m.x+=x;m.y+=y;}public void transformMatrixToLocal(android.graphics.Matrix m){m.x-=x;m.y-=y;}public Resources getResources(){return new Resources();}public void draw(android.graphics.Canvas c){draws++;if(fail)throw new IllegalStateException();}public static class Resources{public Metrics getDisplayMetrics(){return new Metrics();}}public static class Metrics{public float density=2;}}''',
        'android/graphics/Canvas.java':'''package android.graphics;public class Canvas{public boolean hardware=true;public int nodes;public boolean isHardwareAccelerated(){return hardware;}public int save(){return 1;}public void restoreToCount(int n){}public void translate(float x,float y){}public void concat(Matrix m){}public void clipRect(int l,int t,int r,int b){}public void drawRenderNode(RenderNode n){nodes++;}}''',
        'android/graphics/RecordingCanvas.java':'package android.graphics;public class RecordingCanvas extends Canvas{}',
        'android/graphics/RenderNode.java':'''package android.graphics;public class RenderNode{public static int records,discards,lastWidth,lastHeight;boolean valid;int w,h;public RenderNode(String n){}public void setPosition(int l,int t,int r,int b){w=r-l;h=b-t;lastWidth=w;lastHeight=h;}public boolean hasDisplayList(){return valid;}public int getWidth(){return w;}public int getHeight(){return h;}public RecordingCanvas beginRecording(){records++;return new RecordingCanvas();}public void endRecording(){valid=true;}public void discardDisplayList(){discards++;valid=false;}}''',
        'Probe.java':'''import android.graphics.*;import android.view.*;import app.flexygram.kyant.KyantBackdropSource;public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){
 View scene=new View(),bar=new View(),cell=new View();cell.parent=scene;KyantBackdropSource source=new KyantBackdropSource(scene,bar);Canvas canvas=new Canvas();
 check(source.contains(scene)&&source.contains(cell)&&!source.contains(bar));
 for(int i=0;i<10000;i++)source.draw(canvas,320,128,1,0);check(scene.draws==1&&RenderNode.records==1&&canvas.nodes==10000);
 check(RenderNode.lastWidth==448&&RenderNode.lastHeight==256);
 source.draw(canvas,320,128,2,0);check(scene.draws==2);
 bar.x=12;source.draw(canvas,320,128,2,0);check(scene.draws==3);
 source.draw(canvas,320,128,2,-2);check(scene.draws==4);
 source.draw(canvas,400,128,2,-2);check(scene.draws==5);
 canvas.hardware=false;source.draw(canvas,400,128,3,-2);check(scene.draws==5);canvas.hardware=true;
 scene.attached=false;source.draw(canvas,400,128,3,-2);check(scene.draws==5);scene.attached=true;
 source.release();check(RenderNode.discards==1);source.draw(canvas,400,128,3,-2);check(scene.draws==6);
 scene.fail=true;try{source.draw(canvas,400,128,4,0);throw new AssertionError();}catch(IllegalStateException expected){}
 scene.fail=false;source.draw(canvas,400,128,4,0);check(scene.draws==8);
}}'''
    },[JAVA/'app/flexygram/kyant/KyantBackdropSource.java'])


def test_two_compose_layers_replay_one_native_icon_recording_per_revision(tmp_path):
    probe(tmp_path,{
        'androidx/annotation/RequiresApi.java':'package androidx.annotation;public @interface RequiresApi{int value();}',
        'android/view/View.java':'package android.view;public class View{public int draws,w=40,h=32;public boolean fail;public int getWidth(){return w;}public int getHeight(){return h;}public void draw(android.graphics.Canvas c){draws++;if(fail)throw new IllegalStateException();}}',
        'android/graphics/Canvas.java':'package android.graphics;public class Canvas{public boolean hardware=true;public int nodes;public boolean isHardwareAccelerated(){return hardware;}public void drawRenderNode(RenderNode n){nodes++;}}',
        'android/graphics/RecordingCanvas.java':'package android.graphics;public class RecordingCanvas extends Canvas{}',
        'android/graphics/RenderNode.java':'''package android.graphics;public class RenderNode{public static int records;boolean valid;public RenderNode(String n){}public void setPosition(int a,int b,int c,int d){}public boolean hasDisplayList(){return valid;}public RecordingCanvas beginRecording(){records++;return new RecordingCanvas();}public void endRecording(){valid=true;}public void discardDisplayList(){valid=false;}}''',
        'Probe.java':'''import android.graphics.*;import android.view.View;import app.flexygram.kyant.KyantIconSnapshot;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]a){View v=new View();Canvas c=new Canvas();KyantIconSnapshot icon=new KyantIconSnapshot(v);
 for(int i=0;i<10000;i++)icon.draw(c,1);check(v.draws==1&&RenderNode.records==1&&c.nodes==10000);
 icon.draw(c,2);icon.draw(c,2);check(v.draws==2);v.w=50;icon.draw(c,2);check(v.draws==3);
 v.fail=true;try{icon.draw(c,3);throw new AssertionError();}catch(IllegalStateException expected){}v.fail=false;icon.draw(c,3);check(v.draws==5);
 icon.release();icon.draw(c,3);check(v.draws==6);v.h=0;icon.draw(c,4);check(v.draws==6);v.h=32;c.hardware=false;icon.draw(c,4);check(v.draws==7);
}}'''
    },[JAVA/'app/flexygram/kyant/KyantIconSnapshot.java'])


def test_preference_is_independent_persistent_and_listener_lifetime_is_bounded(tmp_path):
    probe(tmp_path,{
        'android/content/Context.java':'''package android.content;public class Context{public static final int MODE_PRIVATE=0;public static boolean saved;public static int reads,writes;public Context getSharedPreferences(String name,int mode){if(!name.equals("mainconfig"))throw new AssertionError();return this;}public boolean getBoolean(String name,boolean d){reads++;return saved;}public Context edit(){return this;}public Context putBoolean(String name,boolean v){if(!name.equals("flexy_kyant_home_dock"))throw new AssertionError();saved=v;return this;}public void apply(){writes++;}}''',
        'org/telegram/messenger/ApplicationLoader.java':'package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext=new android.content.Context();}',
        'Probe.java':'''import app.flexygram.kyant.KyantDockConfig;import android.content.Context;public class Probe{public static void main(String[]a)throws Exception{int[]events={0};Runnable listener=()->events[0]++;KyantDockConfig.addListener(listener);KyantDockConfig.addListener(listener);for(int i=0;i<10000;i++)if(KyantDockConfig.isEnabled())throw new AssertionError();if(Context.reads!=1)throw new AssertionError();KyantDockConfig.setEnabled(true);KyantDockConfig.setEnabled(true);if(!Context.saved||events[0]!=1||Context.writes!=1)throw new AssertionError();KyantDockConfig.removeListener(listener);KyantDockConfig.setEnabled(false);if(Context.saved||events[0]!=1)throw new AssertionError();var loaded=KyantDockConfig.class.getDeclaredField("loaded");loaded.setAccessible(true);loaded.setBoolean(null,false);if(KyantDockConfig.isEnabled()||Context.reads!=2)throw new AssertionError();}}'''
    },[JAVA/'app/flexygram/kyant/KyantDockConfig.java'])


def test_scope_preserves_telegram_engine_and_disables_it_only_for_home_bar():
    host=(JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
    assert 'iBlur3FactoryGlass.setLiquidGlassEffectAllowed(false)' in host
    assert 'setKyantEffectAllowed' not in host
    lazy=method(host,'private void ensureKyantDock(Context context)')
    assert 'KyantDockConfig.isEnabled()' in lazy and 'Build.VERSION.SDK_INT >= 33' in lazy
    bridge=(ROOT/'TMessagesProj/src/main/kotlin/app/flexygram/kyant/KyantDockView.kt').read_text()
    assert 'iconSnapshots.getOrPut(tab)' in bridge and 'tab.draw(target)' not in bridge
    assert 'LiteMode.isPowerSaverApplied()' in bridge and 'FLAG_LIQUID_GLASS' not in bridge
    assert 'visibleScratch' in bridge and 'visible.toList()' in bridge
    assert 'KyantDockConfig.removeListener(configListener)' in bridge
    assert 'removeCallbacks(frame)' in bridge and '!sourceDirty' in bridge
    assert (JAVA/'org/telegram/ui/Components/blur3/LiquidGlassEffect.java').exists()
    assert (ROOT/'TMessagesProj/src/main/res/raw/liquid_glass_shader.agsl').exists()
    original=json.loads((ROOT/'third_party/kyant-backdrop/provenance.json').read_text())
    # The upstream provenance stays intact. Pin the locally adapted component separately.
    original['components/LiquidBottomTabs.kt'] = 'c3620ba747f13d93bf141fc01ab0a4106232820ab83439edd2ed012e7fd63491'
    for path,sha in original.items():
        source=(ROOT/'TMessagesProj/src/main/kotlin/app/flexygram/kyant'/path).read_text()
        normalized=source.split('\n',1)[1].replace('app.flexygram.kyant','com.kyant.backdrop.catalog')
        assert hashlib.sha256(normalized.encode()).hexdigest()==sha


def test_real_content_container_compiles_and_draws_once_before_optional_initialization(tmp_path):
    # Compile the complete production anonymous class, not just one selected method:
    # duplicate overrides are valid syntax but must be rejected by the Java compiler.
    host=(JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
    create=method(host,'protected FrameLayout createContentView(Context context)')
    probe(tmp_path,{'Probe.java':'''import java.util.*;
@interface NonNull{}class Context{}class View{}class Canvas{
 void drawRect(int l,int t,int r,int b,Object paint){Probe.events.add(l==0?"left":"right");}}
class FrameLayout extends View{
 FrameLayout(Context c){}protected void dispatchDraw(Canvas c){Probe.events.add("children");}
 public void onDescendantInvalidated(View child,View target){}
 protected void onLayout(boolean c,int l,int t,int r,int b){}
 int getWidth(){return 200;}int getHeight(){return 100;}}
class Base{protected FrameLayout createContentView(Context c){return null;}}
class Theme{static Object fillingPaint(int color){return color;}}
public class Probe extends Base{
 static List<String>events=new ArrayList<>();int insetLeft=5,insetRight=6;
 static class Dock{void sourceInvalidated(View v){}void syncFromNative(){}}
 static class Work{void afterDraw(){events.add("kyant");}}
 Dock kyantDockView=new Dock();Work kyantInitWork=new Work();
 int getEstBackgroundColor(){return 0;}void checkUi_tabsPosition(){}void checkUi_fadeView(){}
 void blur3_invalidateBlur(){events.add("blur");}void blur3_updateFadeColors(){events.add("fade");}
 CREATE
 public static void main(String[]args){Probe p=new Probe();FrameLayout view=p.createContentView(new Context());
 view.dispatchDraw(new Canvas());if(!events.equals(List.of("left","right","children","blur","fade","kyant")))throw new AssertionError(events.toString());
 events.clear();p.kyantInitWork=null;view.dispatchDraw(new Canvas());if(!events.equals(List.of("left","right","children","blur","fade")))throw new AssertionError(events.toString());}
}'''.replace('CREATE',create)})


def test_optical_headroom_keeps_native_height_and_touch_boundary(tmp_path):
    probe(tmp_path, {
        'android/content/Context.java': 'package android.content; public class Context {}',
        'android/view/MotionEvent.java': '''package android.view; public class MotionEvent {
            public static final int ACTION_DOWN = 0;
            final int action; final float y;
            public MotionEvent(int action, float y) { this.action = action; this.y = y; }
            public int getActionMasked() { return action; }
            public float getY() { return y; }
        }''',
        'android/view/View.java': '''package android.view; public class View {
            public static final int VISIBLE = 0, GONE = 8;
            public int visibility = VISIBLE;
            public Object params;
            public int getVisibility() { return visibility; }
            public Object getLayoutParams() { return params; }
            public int getMeasuredHeight() { return 72; }
        }''',
        'android/widget/FrameLayout.java': '''package android.widget;
        import android.content.Context;
        import android.view.*;
        public class FrameLayout extends View {
            public static class LayoutParams { public int height = 72, topMargin, bottomMargin; }
            public static class MeasureSpec {
                public static final int EXACTLY = 1;
                public static int makeMeasureSpec(int size, int mode) { return size; }
            }
            public int measured, layoutRequests, touches;
            public FrameLayout(Context c) {}
            protected void onMeasure(int w, int h) { measured = h; }
            public void measure(int w, int h) { onMeasure(w, h); }
            protected void measureChildWithMargins(View v, int w, int x, int h, int y) {}
            public static int resolveSize(int size, int spec) { return Math.min(size, spec); }
            public int getSuggestedMinimumHeight() { return 0; }
            public int getPaddingTop() { return 0; }
            public int getPaddingBottom() { return 24; }
            public void requestLayout() { layoutRequests++; }
            public boolean dispatchTouchEvent(MotionEvent event) { touches++; return true; }
        }''',
        'Probe.java': '''import android.content.Context;
        import android.view.*;
        import android.widget.FrameLayout;
        import app.flexygram.kyant.KyantDockContainer;
        public class Probe {
            public static void main(String[] args) {
                View dock = new View();
                dock.params = new FrameLayout.LayoutParams();
                KyantDockContainer p = new KyantDockContainer(new Context(), dock);
                p.measure(360, 800);
                if (p.measured != 96) throw new AssertionError("native height");
                p.setOpticalTopInset(24);
                p.setOpticalTopInset(24);
                p.measure(360, 800);
                if (p.measured != 120 || p.layoutRequests != 1) throw new AssertionError("bounded headroom");
                if (p.dispatchTouchEvent(new MotionEvent(0, 23))) throw new AssertionError("intercepted list");
                if (!p.dispatchTouchEvent(new MotionEvent(0, 24))) throw new AssertionError("lost bar input");
                if (!p.dispatchTouchEvent(new MotionEvent(2, 10))) throw new AssertionError("lost active drag");
                dock.visibility = View.GONE;
                p.measure(360, 800);
                if (p.measured != 24 || p.dispatchTouchEvent(new MotionEvent(0, 0)))
                    throw new AssertionError("hidden dock owns space or touch");
            }
        }'''
    }, [JAVA / 'app/flexygram/kyant/KyantDockContainer.java'])
