"""Kyant lab isolation, original effect provenance and production raw-scene cache contracts."""
import hashlib,json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
from test_render_work_reuse import ROOT,JAVA,probe


def test_lab_is_independent_of_the_main_optimized_app_and_old_backup():
    props=(ROOT/'gradle.properties').read_text()
    assert 'APP_PACKAGE=com.flexygram.messenger.kyantlab\n' in props
    manifest=ET.parse(ROOT/'TMessagesProj/src/main/AndroidManifest.xml').getroot();ns='{http://schemas.android.com/apk/res/android}'
    assert manifest.find('application').get(ns+'label')=='FlexyGram Glass Lab'
    for f in ['auth.xml','sync_contacts.xml']:
        assert ET.parse(ROOT/'TMessagesProj/src/main/res/xml'/f).getroot().get(ns+'accountType')=='com.flexygram.messenger.kyantlab'
    for node in ET.parse(ROOT/'TMessagesProj/src/main/res/xml/contacts.xml').getroot():
        assert node.get(ns+'mimeType').startswith('vnd.android.cursor.item/vnd.com.flexygram.messenger.kyantlab.')
        assert any(x.get(ns+'mimeType')==node.get(ns+'mimeType') for x in manifest.iter('data'))
    for path in ['MessagesController.java','MessagesStorage.java','DatabaseMigrationHelper.java']:
        rel='TMessagesProj/src/main/java/org/telegram/messenger/'+path
        assert (ROOT/rel).read_bytes()==subprocess.check_output(['git','show','9b305e3ee7ee16097576d60af07f6ed9f105de9c:'+rel],cwd=ROOT)


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
    # Existing Telegram optics remain byte-for-byte unchanged outside the lab's dock route.
    for path in ['TMessagesProj/src/main/res/raw/liquid_glass_shader.agsl','TMessagesProj/src/main/java/org/telegram/ui/Components/blur3/LiquidGlassEffect.java']:
        p=ROOT/path
        if p.exists():assert p.read_bytes()==subprocess.check_output(['git','show','9b305e3ee7ee16097576d60af07f6ed9f105de9c:'+path],cwd=ROOT)


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
