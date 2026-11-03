"""Execute draft persistence and retained blur refresh policies without packaging an APK."""
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET
import pytest
from test_composer_layout import method

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / 'TMessagesProj/src/main/java'


def run_java(tmp_path, sources, production=()):
    if not shutil.which('java'):
        pytest.skip('JDK required')
    files = []
    for name, content in sources.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        files.append(str(p))
    compile_result = subprocess.run(['java', '-m', 'jdk.compiler/com.sun.tools.javac.Main', '-d', str(tmp_path),
                                    *files, *[str(JAVA / p) for p in production]], capture_output=True, text=True)
    assert compile_result.returncode == 0, compile_result.stderr
    result = subprocess.run(['java', '-cp', str(tmp_path), 'Probe'], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_draft_isolation_atomic_save_clamps_cache_and_reload(tmp_path):
    run_java(tmp_path, {
        'android/content/SharedPreferences.java': '''package android.content;public interface SharedPreferences{
 boolean getBoolean(String k,boolean d);int getInt(String k,int d);Editor edit();
 interface Editor{Editor putBoolean(String k,boolean v);Editor putInt(String k,int v);void apply();}}''',
        'tw/nekomimi/nekogram/NekoConfig.java': '''package tw.nekomimi.nekogram;
 public class NekoConfig{public static Prefs prefs=new Prefs();public static android.content.SharedPreferences getPreferences(){return prefs;}
 public static class Prefs implements android.content.SharedPreferences,android.content.SharedPreferences.Editor{
 public java.util.Map<String,Object> values=new java.util.HashMap<>();public int reads,applies,edits;
 public boolean getBoolean(String k,boolean d){reads++;return (boolean)values.getOrDefault(k,d);}
 public int getInt(String k,int d){reads++;return (int)values.getOrDefault(k,d);}
 public android.content.SharedPreferences.Editor edit(){edits++;return this;}
 public android.content.SharedPreferences.Editor putBoolean(String k,boolean v){values.put(k,v);return this;}
 public android.content.SharedPreferences.Editor putInt(String k,int v){values.put(k,v);return this;}
 public void apply(){applies++;}}}''',
        'app/exteraless/appearance/FlexyGlassConfig.java': '''package app.exteraless.appearance;public class FlexyGlassConfig{public static boolean value=true;public static boolean enabled(){return value;}}''',
        'Probe.java': '''import app.flexygram.effects.GlassSettings;import app.exteraless.appearance.*;import tw.nekomimi.nekogram.NekoConfig;
 public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args)throws Exception{
 var prefs=NekoConfig.prefs;var original=UniversalGlassConfig.snapshot();check(!original.enabled&&original.opacity==42&&original.zones==127);
 int reads=prefs.reads;for(int i=0;i<20000;i++){check(UniversalGlassConfig.snapshot()==original);UniversalGlassConfig.opacity();UniversalGlassConfig.edge();UniversalGlassConfig.surfaces();}check(prefs.reads==reads);
 GlassSettings draft=original.with(0,1).with(1,-10).with(2,999).with(3,-3).with(4,999).with(5,999).with(6,0xffabcdef).with(7,0x7fffffff);
 check(draft.opacity==20&&draft.blur==48&&draft.edge==0&&draft.width==30&&draft.style==2&&draft.zones==127);
 check(UniversalGlassConfig.snapshot()==original&&prefs.applies==0&&prefs.edits==0);
 var p=draft.preset(1);check(p.presetIndex()==1&&p.with(2,25).presetIndex()==-1);check(p.opacity==65&&p.blur==24&&p.edge==40&&p.width==10&&p.style==1&&p.color==draft.color&&p.zones==draft.zones);
 check(UniversalGlassConfig.snapshot()==original);UniversalGlassConfig.save(p);check(prefs.edits==1&&prefs.applies==1&&prefs.values.size()==8&&UniversalGlassConfig.snapshot()==p);
 for(int i=0;i<20000;i++)check(UniversalGlassConfig.blurRadius(40)==24);check(prefs.reads==reads);
 FlexyGlassConfig.value=false;check(UniversalGlassConfig.blurRadius(40)==40);FlexyGlassConfig.value=true;
 var field=UniversalGlassConfig.class.getDeclaredField("cached");field.setAccessible(true);field.set(null,null);
 var restored=UniversalGlassConfig.snapshot();check(restored.enabled&&restored.blur==24&&restored.color==0xffabcdef&&restored.zones==127);
 UniversalGlassConfig.setSurfaces(64);check(UniversalGlassConfig.surfaces()==64);UniversalGlassConfig.setEnabled(false);check(UniversalGlassConfig.blurRadius(40)==40);
 // Preserve old installations' explicit zone selections and opacity when first reading them.
 prefs.values.put("FlexyUniversalGlassSurfaces",63);prefs.values.put("FlexyUniversalGlassOpacity",42);field.set(null,null);
 check(UniversalGlassConfig.surfaces()==63&&UniversalGlassConfig.opacity()==42);
 }}''',
    }, ['app/flexygram/effects/GlassSettings.java', 'app/exteraless/appearance/UniversalGlassConfig.java'])


def test_retained_blur_updates_once_and_zero_does_not_allocate_effect(tmp_path):
    source = (JAVA / 'org/telegram/ui/Components/blur3/DownscaleScrollableNoiseSuppressor.java').read_text()
    one = method(source, 'public void setPrimaryEffectBlur(float radius)')
    two = method(source, 'public void setPrimaryEffectBlur(float radius, RenderEffect secondEffect)')
    refresh = method(source, 'private boolean refreshBlur()')
    run_java(tmp_path, {
        'app/exteraless/appearance/UniversalGlassConfig.java': '''package app.exteraless.appearance;public class UniversalGlassConfig{public static float value=40;public static float blurRadius(float fallback){return value;}}''',
        'Probe.java': '''public class Probe{
 static class Shader{enum TileMode{CLAMP}}
 static class RenderEffect{static int builds;static RenderEffect createBlurEffect(float x,float y,Shader.TileMode m){if(x<=0||y<=0)throw new AssertionError();builds++;return new RenderEffect();}static RenderEffect createChainEffect(RenderEffect a,RenderEffect b){builds++;return new RenderEffect();}}
 static class RenderNodeEffects{static final RenderEffect SAT=new RenderEffect();static RenderEffect getSaturationX3RenderEffect(){return SAT;}}
 float scaleX=8,scaleY=8;RenderEffect effect;int applications;void setPrimaryEffect(RenderEffect e){effect=e;applications++;}
 static float downscaleRadius(float r,float s){return Math.max(1,r/s);}static float dpf2(float r){return r;}
 ONE TWO
 final Probe renderNodesForBlur;boolean isLiquidGlassEnabled=false,simpleMode=true;float configuredRadius=40;
 Probe(){renderNodesForBlur=this;}
 REFRESH
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();for(int i=0;i<20000;i++)check(!p.refreshBlur());check(RenderEffect.builds==0);
 p.setPrimaryEffectBlur(0);check(p.effect==null&&RenderEffect.builds==0);
 p.setPrimaryEffectBlur(0,RenderNodeEffects.SAT);check(p.effect==RenderNodeEffects.SAT&&RenderEffect.builds==0);
 app.exteraless.appearance.UniversalGlassConfig.value=12;check(p.refreshBlur());int n=RenderEffect.builds;for(int i=0;i<20000;i++)check(!p.refreshBlur());check(RenderEffect.builds==n);
 app.exteraless.appearance.UniversalGlassConfig.value=0;check(p.refreshBlur());check(p.effect==RenderNodeEffects.SAT&&RenderEffect.builds==n);
 p.simpleMode=false;app.exteraless.appearance.UniversalGlassConfig.value=20;check(p.refreshBlur());check(p.effect!=null);
 app.exteraless.appearance.UniversalGlassConfig.value=0;check(p.refreshBlur());check(p.effect==null);
 }}'''.replace('ONE', one).replace('TWO', two).replace('REFRESH', refresh),
    })


def test_editor_resources_and_rendering_boundaries():
    resource_sets = []
    for folder in ['values', 'values-es', 'values-ru']:
        items = list(ET.parse(ROOT / 'TMessagesProj/src/main/res' / folder / 'flexy_crystal.xml').getroot())
        assert all(item.text and item.text.strip() for item in items)
        resource_sets.append({item.attrib['name'] for item in items})
    assert resource_sets[0] == resource_sets[1] == resource_sets[2]
    preview = (JAVA / 'app/flexygram/effects/GlassPreviewView.java').read_text()
    draw = method(preview, 'protected void onDraw(Canvas canvas)')
    for forbidden in ['Bitmap.createBitmap', 'stackBlurBitmap', 'new ', 'MessagesController', 'ImageLoader']:
        assert forbidden not in draw
    assert preview.count('Bitmap.createBitmap(180, 100') == 2
    assert 'removeCallbacks(prepareFrame)' in preview
    editor = (JAVA / 'app/exteraless/settings/UniversalGlassSettingsActivity.java').read_text()
    slider = method(editor, 'private void slider(')
    assert 'UniversalGlassConfig.save' not in slider and 'setEnabled(' not in slider
    assert editor.count('UniversalGlassConfig.save(draft)') == 1
    assert 'onBackPressed(boolean invoked)' in editor and 'FlexyCrystalDiscard' in editor
    assert 'fontScale > 1.5f' in editor and 'screenHeightDp < 520' in editor
    profile = (JAVA / 'org/telegram/ui/Components/ProfileActionsView.java').read_text()
    assert 'configureGlass(' in profile
    assert 'createBlurEffect' not in profile and 'Bitmap.createBitmap' not in profile


def test_custom_borders_are_isolated_from_legacy_outline_and_master_wins(tmp_path):
    source = (JAVA / 'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawable.java').read_text()
    outline = method(source, 'private GlassOutlineStyle materialOutlineStyle()')
    run_java(tmp_path, {
        'app/exteraless/appearance/FlexyGlassConfig.java': 'package app.exteraless.appearance;public class FlexyGlassConfig{public static boolean value=true;public static boolean enabled(){return value;}}',
        'org/telegram/ui/Components/blur3/GlassOutlineStyle.java': '''package org.telegram.ui.Components.blur3;public enum GlassOutlineStyle{HIDDEN,SOLID,GLARE;public static GlassOutlineStyle legacy=GLARE;public static GlassOutlineStyle current(){return legacy;}}''',
        'org/telegram/ui/Components/blur3/drawable/color/BlurredBackgroundProvider.java': '''package org.telegram.ui.Components.blur3.drawable.color;
 public interface BlurredBackgroundProvider{default int getBackgroundColor(){return 0;}default int getShadowColor(){return 0;}default int getStrokeColorTop(){return 0;}default int getStrokeColorBottom(){return 0;}default int getStrokeColorFull(){return 0;}default float getStrokeWidthTop(){return 1;}default float getStrokeWidthBottom(){return 1;}default float getShadowRadius(){return 0;}default float getShadowDx(){return 0;}default float getShadowDy(){return 0;}}''',
        'Probe.java': '''import app.flexygram.effects.GlassSettings;import app.exteraless.appearance.*;import org.telegram.ui.Components.blur3.GlassOutlineStyle;import org.telegram.ui.Components.blur3.drawable.color.BlurredBackgroundProvider;
 public class Probe{BlurredBackgroundProvider colorProvider;OUTLINE
 static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){Probe p=new Probe();var colors=new BlurredBackgroundProvider(){};
 for(var legacy:GlassOutlineStyle.values()){GlassOutlineStyle.legacy=legacy;p.colorProvider=colors;check(p.materialOutlineStyle()==legacy);
  for(int style=0;style<3;style++){p.colorProvider=new CustomGlassProvider(colors,GlassSettings.defaults().with(5,style));check(p.materialOutlineStyle()==(style==0?GlassOutlineStyle.SOLID:GlassOutlineStyle.GLARE));}
  p.colorProvider=new CustomGlassProvider(colors,GlassSettings.defaults().with(4,0));check(p.materialOutlineStyle()==GlassOutlineStyle.HIDDEN);
  p.colorProvider=new CustomGlassProvider(colors,GlassSettings.defaults().with(3,0));check(p.materialOutlineStyle()==GlassOutlineStyle.HIDDEN);
  p.colorProvider=new CustomGlassProvider(colors,GlassSettings.defaults());FlexyGlassConfig.value=false;check(p.materialOutlineStyle()==GlassOutlineStyle.HIDDEN);FlexyGlassConfig.value=true;
 }
 }}'''.replace('OUTLINE', outline),
    }, ['app/flexygram/effects/GlassSettings.java', 'app/exteraless/appearance/CustomGlassProvider.java'])


def test_profile_blur_respects_device_budget_and_zero(tmp_path):
    source = (JAVA / 'org/telegram/ui/Components/ProfileGalleryBlurView.java').read_text()
    radius = method(source, 'private float getBlurRadius()')
    run_java(tmp_path, {
        'app/exteraless/appearance/UniversalGlass.java': 'package app.exteraless.appearance;public class UniversalGlass{public static int PROFILE=64;public static boolean active;public static boolean enabled(int scope){return active;}}',
        'app/exteraless/appearance/UniversalGlassConfig.java': 'package app.exteraless.appearance;public class UniversalGlassConfig{public static int blur;public static app.flexygram.effects.GlassSettings snapshot(){return app.flexygram.effects.GlassSettings.defaults().with(2,blur);}}',
        'Probe.java': '''import app.exteraless.appearance.*;public class Probe{
 static class SharedConfig{static final int PERFORMANCE_CLASS_HIGH=2,PERFORMANCE_CLASS_AVERAGE=1,PERFORMANCE_CLASS_LOW=0;static int performance;static int getDevicePerformanceClass(){return performance;}}
 RADIUS public static void main(String[]args){Probe p=new Probe();for(int perf=0;perf<=2;perf++){SharedConfig.performance=perf;int cap=perf==2?20:perf==1?12:8;
  UniversalGlass.active=false;if(p.getBlurRadius()!=cap)throw new AssertionError();UniversalGlass.active=true;
  for(int r=0;r<=48;r++){UniversalGlassConfig.blur=r;float actual=p.getBlurRadius();if(actual<0||actual>cap||actual!=Math.min(cap,r*.5f))throw new AssertionError();}
 }} }'''.replace('RADIUS', radius),
    }, ['app/flexygram/effects/GlassSettings.java'])
