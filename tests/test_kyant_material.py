"""Kyant lab isolation, original effect provenance and production raw-scene cache contracts."""
import hashlib,json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
from test_render_work_reuse import ROOT,JAVA,probe


def test_kyant_provenance_and_explicit_static_dock_patch_are_verified():
    hashes=json.loads((ROOT/'third_party/kyant-backdrop/provenance.json').read_text())
    patches=json.loads((ROOT/'third_party/kyant-backdrop/local-patches.json').read_text())
    for rel,expected in hashes.items():
        if rel in patches['removed']:
            assert not (ROOT/'TMessagesProj/src/main/kotlin/app/flexygram/kyant'/rel).exists()
            continue
        if rel in patches['modified']:
            assert hashlib.sha256((ROOT/'TMessagesProj/src/main/kotlin/app/flexygram/kyant'/rel).read_bytes()).hexdigest()==patches['modified'][rel]
            continue
        text=(ROOT/'TMessagesProj/src/main/kotlin/app/flexygram/kyant'/rel).read_text()
        original=text.split('\n',1)[1].replace('app.flexygram.kyant','com.kyant.backdrop.catalog')
        assert hashlib.sha256(original.encode()).hexdigest()==expected,rel
    host=(JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
    assert 'tabsView.setGlassBackground(' not in host
    bridge=(ROOT/'TMessagesProj/src/main/kotlin/app/flexygram/kyant/KyantDockView.kt').read_text()
    assert 'LiquidBottomTabs(' in bridge and 'rememberLayerBackdrop()' in bridge
    assert 'sourceInvalidated(target)' in host
    assert 'postInvalidateOnAnimation' not in bridge
    assert 'removeCallbacks(frame)' in bridge and 'source.release()' in bridge
    assert 'DisposeOnDetachedFromWindowOrReleasedFromPool' in bridge
    assert 'performLongClick()' in bridge and 'MotionEvent.ACTION_CANCEL' in bridge
    build=(ROOT/'TMessagesProj/build.gradle').read_text()
    assert "implementation 'io.github.kyant0:backdrop:2.0.1'" in build
    assert (ROOT/'TMessagesProj/src/main/res/raw/liquid_glass_shader.agsl').exists()
    assert (JAVA/'org/telegram/ui/Components/blur3/LiquidGlassEffect.java').exists()


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


def test_build_plugins_share_the_kyant_compatible_kotlin_version():
    import re
    root=(ROOT/'build.gradle').read_text()
    helpers=(ROOT/'buildSrc/build.gradle.kts').read_text()
    app=(ROOT/'TMessagesProj/build.gradle').read_text()
    versions=[]
    versions += re.findall(r'kotlin-gradle-plugin:([0-9.]+)',root)
    versions += re.findall(r'kotlin-gradle-plugin:([0-9.]+)',helpers)
    versions += re.findall(r'id\("org.jetbrains.kotlin.jvm"\) version "([0-9.]+)"',helpers)
    versions += re.findall(r"id 'org.jetbrains.kotlin.plugin.compose' version '([0-9.]+)'",app)
    assert len(versions)==4 and set(versions)=={'2.4.10'},versions
    # kotlin-dsl in buildSrc otherwise exports its older compiler to the application.
    assert '`kotlin-dsl`' not in helpers
    assert '`java-gradle-plugin`' in helpers


def test_scroll_frames_refresh_backdrop_without_rebuilding_native_tab_controls(tmp_path):
    from test_composer_layout import method
    source=(ROOT/'TMessagesProj/src/main/kotlin/app/flexygram/kyant/KyantDockView.kt').read_text()
    body=method(source,'private val frame = Runnable')
    # Run the actual callback body in the existing JVM work-count host; only Kotlin's
    # local-val syntax and optional semicolons are lowered. The Android harness also
    # compiles the unchanged production Kotlin against real Compose dependencies.
    body=body[body.index('{'):].replace('val refreshNative = iconsDirty','boolean refreshNative = iconsDirty;')
    body=body.replace('framePending = false\n','framePending = false;\n').replace('++ }','++; }').replace('syncFromNative()\n','syncFromNative();\n')
    probe(tmp_path,{'Probe.java':'''public class Probe{
 boolean framePending,sourceDirty,iconsDirty;long revision,iconsRevision;int syncs;
 void syncFromNative(){syncs++;}
 void frame()BODY
 public static void main(String[]args){Probe p=new Probe();
 for(int i=0;i<10000;i++){p.sourceDirty=true;p.framePending=true;p.frame();}
 if(p.syncs!=0||p.revision!=10000||p.iconsRevision!=0||p.framePending)throw new AssertionError("scroll rebuilt native controls");
 p.iconsDirty=true;p.frame();if(p.syncs!=1||p.iconsRevision!=1||p.iconsDirty)throw new AssertionError("icon update lost");
 p.frame();if(p.syncs!=1)throw new AssertionError("idle native work");
 }}'''.replace('BODY',body)})

def test_native_material_restored_and_kyant_opt_in_only_on_home_dock():
    for rel in ['TMessagesProj/src/main/res/raw/liquid_glass_shader.agsl','TMessagesProj/src/main/java/org/telegram/ui/Components/blur3/LiquidGlassEffect.java']:
        assert (ROOT/rel).read_bytes()==subprocess.check_output(['git','show','d50640dec:'+rel],cwd=ROOT)
    assert not (JAVA/'app/flexygram/kyant/KyantGlassEffect.java').exists()
    assert not (ROOT/'TMessagesProj/src/main/res/raw/kyant_rounded_rect_refraction.agsl').exists()
    for p in JAVA.rglob('*.java'):
        assert '.createKyant(' not in p.read_text(),p
    bridge=(ROOT/'TMessagesProj/src/main/kotlin/app/flexygram/kyant/KyantDockView.kt').read_text()
    assert 'KyantDockConfig.enabled()' in bridge and '!LiteMode.isPowerSaverApplied()' in bridge
    assert 'FLAG_LIQUID_GLASS' not in bridge
    build=(ROOT/'TMessagesProj/build.gradle').read_text()
    assert "buildConfigField 'boolean', 'NATIVE_BASELINE_TEST', 'true'" in build
    assert "id 'app.flexygram.fast-motion'" not in build


def test_physical_dock_geometry_excludes_system_inset_but_preserves_symmetric_margins(tmp_path):
    probe(tmp_path,{'Probe.java':'''import app.flexygram.kyant.KyantDockGeometry;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){
 check(KyantDockGeometry.panelInset(88,0,24,64)==0); // Material3 + gesture navigation
 check(KyantDockGeometry.panelInset(112,0,48,64)==0); // 3-button navigation
 check(KyantDockGeometry.panelInset(72,12,12,64)==4); // upstream floating dock
 check(KyantDockGeometry.panelInset(64,8,8,64)==0); // compact style reserves full touch height
 check(KyantDockGeometry.panelInset(216,0,24,192)==0); // display density 3
}}'''},[JAVA/'app/flexygram/kyant/KyantDockGeometry.java'])


def test_unchanged_native_geometry_does_not_request_recomposition(tmp_path):
    probe(tmp_path,{'Probe.java':'''import app.flexygram.kyant.KyantDockGeometry;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){
 var state=new KyantDockGeometry.State();check(state.update(8,4,344,72,12,12,false,false));
 for(int i=0;i<10000;i++)check(!state.update(8,4,344,72,12,12,false,false));
 check(state.update(8,4,344,72,12,12,true,false)); // RTL change
 check(state.update(8,4,344,72,12,12,true,true)); // theme change
 check(state.update(8,4,344,96,0,24,true,true)); // gesture navigation inset
 check(state.update(12,4,320,96,0,24,true,true)); // native measured position/width
 check(!state.update(12,4,320,96,0,24,true,true));
}}'''},[JAVA/'app/flexygram/kyant/KyantDockGeometry.java'])


def test_disabled_kyant_never_constructs_a_compose_host_and_enable_disable_is_idempotent(tmp_path):
    from test_composer_layout import method
    body=method((JAVA/'org/telegram/ui/MainTabsActivity.java').read_text(),'private void updateKyantDock()')
    probe(tmp_path,{
        'android/os/Build.java':'package android.os;public class Build{public static class VERSION{public static int SDK_INT=33;}}',
        'android/view/ViewGroup.java':'package android.view;public class ViewGroup{public static class LayoutParams{public static int MATCH_PARENT=-1;}}',
        'android/widget/FrameLayout.java':'package android.widget;public class FrameLayout{public static class LayoutParams{public LayoutParams(int x,int y){}}}',
        'app/flexygram/kyant/KyantDockConfig.java':'package app.flexygram.kyant;public class KyantDockConfig{public static boolean on;public static boolean enabled(){return on;}}',
        'app/flexygram/kyant/KyantDockView.java':'package app.flexygram.kyant;public class KyantDockView{public static int creates;public KyantDockView(Object c,Object d,Object s){creates++;}}',
        'Probe.java':'''import android.os.Build;import android.view.ViewGroup;import android.widget.FrameLayout;import app.flexygram.kyant.*;
public class Probe{
 static class Dock{Object host;Object getContext(){return this;}void setKyantHost(Object v){host=v;}}
 static class Host{int adds,removes;void addView(Object v,Object p){adds++;}void removeView(Object v){removes++;}}
 Dock tabsView=new Dock();Host tabsViewWrapper=new Host();Object viewPager=new Object();KyantDockView kyantDockView;
 BODY
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();
 for(int i=0;i<10000;i++)p.updateKyantDock();check(KyantDockView.creates==0&&p.tabsViewWrapper.adds==0);
 KyantDockConfig.on=true;for(int i=0;i<10000;i++)p.updateKyantDock();check(KyantDockView.creates==1&&p.tabsViewWrapper.adds==1&&p.tabsView.host==p.kyantDockView);
 KyantDockConfig.on=false;for(int i=0;i<10000;i++)p.updateKyantDock();check(p.kyantDockView==null&&p.tabsView.host==null&&p.tabsViewWrapper.removes==1);
 KyantDockConfig.on=true;p.updateKyantDock();check(KyantDockView.creates==2);
 Build.VERSION.SDK_INT=32;p=new Probe();p.updateKyantDock();check(p.kyantDockView==null&&KyantDockView.creates==2);
 }}'''.replace('BODY',body)
    })


def test_removed_rebound_has_no_runtime_classes_settings_or_resources():
    assert not (JAVA/'app/flexygram/elastic').exists()
    for root in [ROOT/'TMessagesProj/src/main/java',ROOT/'TMessagesProj/src/main/kotlin']:
        for path in root.rglob('*'):
            if path.suffix in {'.java','.kt'}:
                text=path.read_text()
                for name in ['app.flexygram.elastic.','ElasticInteraction.observe','ElasticControlBackground','FlexyElasticTitle','fg_dm_elastic']:
                    assert name not in text,(path,name)
    tabs=(ROOT/'TMessagesProj/src/main/kotlin/app/flexygram/kyant/components/LiquidBottomTabs.kt').read_text()
    assert 'InteractiveHighlight' not in tabs and 'scaleX' not in tabs and 'scaleY' not in tabs
    selector=(ROOT/'TMessagesProj/src/main/kotlin/app/flexygram/kyant/utils/DockSelectionAnimation.kt').read_text()
    assert 'spring(' not in selector and 'positionJob?.cancel()' in selector
    assert not (ROOT/'TMessagesProj/src/main/res/drawable/fg_dm_elastic.xml').exists()
    for directory in ['values','values-es']:
        assert 'name="FlexyElastic' not in (ROOT/'TMessagesProj/src/main/res'/directory/'strings.xml').read_text()
