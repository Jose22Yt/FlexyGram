"""Kyant lab isolation, original effect provenance and production raw-scene cache contracts."""
import hashlib,json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
from test_render_work_reuse import ROOT,JAVA,probe


def test_original_kyant_material_and_animation_sources_are_preserved():
    hashes=json.loads((ROOT/'third_party/kyant-backdrop/provenance.json').read_text())
    for rel,expected in hashes.items():
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
    assert not (ROOT/'TMessagesProj/src/main/res/raw/liquid_glass_shader.agsl').exists()
    assert not (JAVA/'org/telegram/ui/Components/blur3/LiquidGlassEffect.java').exists()


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

def test_native_shader_matches_upstream_program_and_no_original_renderer_remains():
    provenance=json.loads((ROOT/'third_party/kyant-backdrop/native-shader-provenance.json').read_text())
    shader=(ROOT/'TMessagesProj/src/main/res/raw/kyant_rounded_rect_refraction.agsl').read_bytes()
    assert hashlib.sha256(shader).hexdigest()==provenance['sha256']
    assert b'uniform shader content;' in shader and b'refract_index' not in shader
    for p in JAVA.rglob('*.java'):
        source=p.read_text()
        assert 'new LiquidGlassEffect(' not in source, p
        assert 'R.raw.liquid_glass_shader' not in source, p
        assert 'setLiquidGlassEffectAllowed' not in source, p


def test_refraction_is_explicitly_scoped_and_never_restores_retired_features():
    eligible={
      'org/telegram/ui/ActionBar/ActionBar.java',
      'org/telegram/ui/DialogsActivity.java',
      'org/telegram/ui/ChatActivity.java',
      'org/telegram/ui/Components/SharedMediaLayout.java',
      'org/telegram/ui/Components/SearchTagsList.java',
      'org/telegram/ui/Components/ChatActivityEnterView.java',
      'org/telegram/ui/Components/chat/layouts/ChatActivityChannelButtonsLayout.java',
    }
    actual={str(p.relative_to(JAVA)) for p in JAVA.rglob('*.java') if '.createKyant(' in p.read_text()}
    assert actual==eligible
    factory=(JAVA/'org/telegram/ui/Components/blur3/BlurredBackgroundDrawableViewFactory.java').read_text()
    assert 'return createInternal(view, provider, multiwindow, false);' in factory
    assert 'return createInternal(view, provider, false, true);' in factory
    header=(JAVA/'org/telegram/ui/ActionBar/ActionBar.java').read_text()
    assert 'setupGlassInternal(factory, colorProvider, isForum, false)' in header
    assert 'setupGlassInternal(factory, provider, forum, true)' in header
    host=(JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
    assert 'app.exteraless.player.baseline.PlayerMiniView' in host
    assert 'LiquidNavigationConfig' not in host and 'SignatureMusic' not in host
    build=(ROOT/'TMessagesProj/build.gradle').read_text()
    assert "buildConfigField 'boolean', 'NATIVE_BASELINE_TEST', 'true'" in build
    assert "id 'app.flexygram.fast-motion'" not in build


def test_opt_in_policy_never_creates_shaders_for_hidden_or_non_glass_surfaces(tmp_path):
    from test_composer_layout import method
    source=(JAVA/'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawableRenderNode.java').read_text()
    body=method(source,'public void setKyantEffectAllowed(boolean allowed)')
    probe(tmp_path,{'Probe.java':'''public class Probe{
 boolean kyantSurface,kyantEffectAllowed;Object kyantGlassEffect;
 static class Node {int clears;void setRenderEffect(Object e){if(e!=null)throw new AssertionError();clears++;}}
 Node renderNodeFill=new Node();int invalidations;void invalidateDisplayList(){invalidations++;}void invalidateSelf(){}
 BODY
 public static void main(String[]args){Probe p=new Probe();
 for(int i=0;i<10000;i++)p.setKyantEffectAllowed(true);
 if(p.kyantEffectAllowed||p.invalidations!=0||p.kyantGlassEffect!=null)throw new AssertionError("unscoped surface activated");
 p.kyantSurface=true;p.setKyantEffectAllowed(true);
 if(!p.kyantEffectAllowed||p.invalidations!=1||p.kyantGlassEffect!=null)throw new AssertionError("eager shader construction");
 for(int i=0;i<10000;i++)p.setKyantEffectAllowed(true);
 if(p.invalidations!=1)throw new AssertionError("unchanged policy rebuild");
 p.kyantGlassEffect=new Object();p.setKyantEffectAllowed(false);
 if(p.kyantEffectAllowed||p.kyantGlassEffect!=null||p.renderNodeFill.clears!=1||p.invalidations!=2)throw new AssertionError("GPU effect retained on OFF");
 }}'''.replace('BODY',body)})


def test_physical_dock_geometry_excludes_system_inset_but_preserves_symmetric_margins(tmp_path):
    probe(tmp_path,{'Probe.java':'''import app.flexygram.kyant.KyantDockGeometry;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){
 check(KyantDockGeometry.panelInset(88,0,24,64)==0); // Material3 + gesture navigation
 check(KyantDockGeometry.panelInset(112,0,48,64)==0); // 3-button navigation
 check(KyantDockGeometry.panelInset(72,12,12,64)==4); // upstream floating dock
 check(KyantDockGeometry.panelInset(64,8,8,64)==0); // compact style reserves full touch height
 check(KyantDockGeometry.panelInset(216,0,24,192)==0); // display density 3
}}'''},[JAVA/'app/flexygram/kyant/KyantDockGeometry.java'])
