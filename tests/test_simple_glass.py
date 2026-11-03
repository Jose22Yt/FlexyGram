"""Simple controls retain the pre-preview renderer; JVM and source-boundary regressions."""
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET
import pytest
from test_composer_layout import method
ROOT=Path(__file__).resolve().parents[1]
JAVA=ROOT/'TMessagesProj/src/main/java'

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


def test_simple_settings_ignore_experimental_keys_cache_and_save_once(tmp_path):
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
        'app/exteraless/appearance/FlexyGlassConfig.java': 'package app.exteraless.appearance;public class FlexyGlassConfig{public static boolean value=true;public static boolean enabled(){return value;}}',
        'Probe.java': '''import app.flexygram.effects.GlassSettings;import app.exteraless.appearance.*;import tw.nekomimi.nekogram.NekoConfig;
 public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args)throws Exception{
 var prefs=NekoConfig.prefs;prefs.values.put("FlexyGlassBlurRadius",48);prefs.values.put("FlexyGlassBorderColor",0xffff0000);prefs.values.put("FlexyUniversalGlassOpacity",80);prefs.values.put("FlexyUniversalGlassSurfaces",127);prefs.values.put("FlexyUniversalGlassEdge",100);
 var original=UniversalGlassConfig.snapshot();check(!original.enabled&&original.opacity==42&&original.blur==40&&original.width==8&&original.edge==70);
 int reads=prefs.reads;for(int i=0;i<20000;i++){check(UniversalGlassConfig.snapshot()==original);UniversalGlassConfig.opacity();UniversalGlassConfig.edge();}check(prefs.reads==reads);
 var next=original.with(0,1).with(2,999).with(3,-1).with(4,999);check(next.blur==48&&next.edge==0&&next.width==30&&original.blur==40);check(prefs.edits==0);
 UniversalGlassConfig.save(next);check(prefs.applies==1&&prefs.edits==1&&UniversalGlassConfig.snapshot()==next);
 for(int i=0;i<20000;i++)check(UniversalGlassConfig.blurRadius(40)==48);check(prefs.reads==reads);
 FlexyGlassConfig.value=false;check(UniversalGlassConfig.blurRadius(40)==40);FlexyGlassConfig.value=true;
 var f=UniversalGlassConfig.class.getDeclaredField("cached");f.setAccessible(true);f.set(null,null);var reloaded=UniversalGlassConfig.snapshot();check(reloaded.enabled&&reloaded.blur==48&&reloaded.edge==0&&reloaded.width==30);
 UniversalGlassConfig.setEnabled(false);check(UniversalGlassConfig.blurRadius(40)==40);check(GlassSettings.defaults().opacity==42&&GlassSettings.defaults().blur==40&&GlassSettings.defaults().width==8);
 }}''',
    }, ['app/flexygram/effects/GlassSettings.java', 'app/exteraless/appearance/UniversalGlassConfig.java'])


def test_canceled_surfaces_match_previous_beta_and_editor_has_no_preview():
    paths = ['app/flexygram/header/HeaderSurface.java', 'app/flexygram/header/fusion/SignatureFusionSurface.java',
             'app/flexygram/home/SignatureHomePainter.java', 'org/telegram/ui/ProfileActivity.java',
             'org/telegram/ui/Components/ProfileActionsView.java', 'org/telegram/ui/Components/ProfileGalleryBlurView.java',
             'org/telegram/ui/Components/SharedMediaLayout.java']
    for path in paths:
        relative = 'TMessagesProj/src/main/java/' + path
        assert (ROOT / relative).read_bytes() == subprocess.check_output(['git', 'show', '1c323bf54c:' + relative], cwd=ROOT)
    assert not (JAVA / 'app/flexygram/effects/GlassPreviewView.java').exists()
    assert not (JAVA / 'app/exteraless/appearance/CustomGlassProvider.java').exists()
    screen = (JAVA / 'app/exteraless/settings/UniversalGlassSettingsActivity.java').read_text()
    for obsolete in ['GlassPreviewView', 'chooseZones', 'ColorPicker', 'prepareWallpaper', 'Bitmap', 'preset', 'previewMode']:
        assert obsolete not in screen
    slider = method(screen, 'private View slider(')
    drag = method(slider, 'public void onProgressChanged(')
    assert 'UniversalGlassConfig.save' not in drag and 'savePending' not in drag
    assert 'savePending();' in method(slider, 'public void onStopTrackingTouch(')
    assert 'AppearanceConfig.glassOutlineStyle.setConfigInt(which)' in screen
    resources=[]
    for folder in ['values', 'values-es', 'values-ru']:
        items=list(ET.parse(ROOT/'TMessagesProj/src/main/res'/folder/'flexy_crystal.xml').getroot())
        assert all(item.text for item in items)
        resources.append({item.attrib['name'] for item in items})
    assert resources[0]==resources[1]==resources[2]=={'FlexyCrystalBlur','FlexyCrystalWidth','FlexyCrystalBorderStyle'}
