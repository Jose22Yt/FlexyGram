"""Shrinker compatibility and CI wiring; this is not an APK/device performance measurement."""
import fnmatch
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

import pytest
import yaml
from test_render_work_reuse import ROOT


def test_ci_reduction_preserves_runtime_resource_and_startup_theme_names():
    workflow = yaml.safe_load((ROOT/'.github/workflows/ui-beta-debug.yml').read_text())
    step = next(s for s in workflow['jobs']['build']['steps'] if s['name'] == 'Assemble debug APK with native libraries and Python')
    assert '-PflexyReleaseReduction=true' in step['run']
    assert '-PflexyPerformanceBuild=true' in step['run']
    policy = (ROOT/'gradle/flexygram-performance.gradle').read_text()
    assert 'releaseReduction && !performanceBuild' in policy
    reduction = policy[policy.index('if (releaseReduction) {'):policy.index('if (optimizeExperiment) {')]
    assert 'android.buildTypes.debug' in reduction and 'minifyEnabled = true' in reduction and 'shrinkResources = true' in reduction
    assert 'performance-shrink.pro' in reduction and 'signingConfig' not in reduction
    keep = ET.parse(ROOT/'TMessagesProj/src/main/res/raw/flexy_dynamic_resources_keep.xml').getroot().get('{http://schemas.android.com/tools}keep').split(',')
    assert {'@drawable/*','@raw/*','@string/*'} <= set(keep)
    for style in ET.parse(ROOT/'TMessagesProj/src/main/res/values-v31/flexygram_startup.xml').getroot():
        assert any(fnmatch.fnmatchcase('@style/'+style.get('name'), pattern) for pattern in keep)


@pytest.mark.parametrize('optimize', [False, True])
def test_real_r8_keeps_reflective_client_and_native_entries_while_removing_unused_code(tmp_path, optimize):
    jar = os.environ.get('FLEXY_R8_JAR')
    if not jar or not Path(jar).is_file() or not shutil.which('java'):
        pytest.skip('Set FLEXY_R8_JAR for the host shrinker regression; CI also runs the full Android shrinker')
    files = {
        'app/flexygram/probe/DynamicEntry.java':'package app.flexygram.probe;public class DynamicEntry{public static String label(){return "retained";}}',
        'app/exteraless/probe/PluginSurface.java':'package app.exteraless.probe;public class PluginSurface{public static String pluginEntry(){return "plugin";}}',
        'fixture/NativeOnly.java':'package fixture;public class NativeOnly{public static native int nativeProbe();public static String onNativeEvent(){return "callback";}}',
        'fixture/Work.java':'package fixture;public class Work{public static int plus(int x){return x+2;}}',
        'fixture/Unused.java':'package fixture;public class Unused{public static int discarded(){return 1;}}',
        'fixture/Main.java':'''package fixture;public class Main{public static void main(String[]args)throws Exception{
 if(Work.plus(1)!=3)throw new AssertionError();
 String name=System.getProperty("entry","app.flexygram.probe.DynamicEntry");
 Object result=Class.forName(name).getMethod("label").invoke(null);
 if(!"retained".equals(result))throw new AssertionError();
 Class.forName(System.getProperty("plugin-entry","app.exteraless.probe.PluginSurface")).getMethod("pluginEntry");
 Class<?> nativeType=Class.forName(System.getProperty("native-entry","fixture.NativeOnly"));
 nativeType.getMethod("nativeProbe");
 if(!"callback".equals(nativeType.getMethod(System.getProperty("native-callback","onNativeEvent")).invoke(null)))throw new AssertionError();
}}''',
    }
    sources=[]
    for name, text in files.items():
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text);sources.append(str(path))
    classes=tmp_path/'classes';classes.mkdir()
    result=subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',str(classes),*sources],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    input_jar=tmp_path/'input.jar'
    with zipfile.ZipFile(input_jar,'w')as archive:
        for path in classes.rglob('*.class'):archive.write(path,path.relative_to(classes))
    config=tmp_path/'test.pro'
    base=(ROOT/'TMessagesProj/proguard-rules.pro').read_text().splitlines()
    # Apply the production global timing/name policy and the complete additional compatibility rules.
    config.write_text('\n'.join(line for line in base if line.strip() in (['-dontobfuscate'] if optimize else ['-dontoptimize','-dontobfuscate']))+'\n-keep class fixture.Main { public static void main(java.lang.String[]); }\n')
    settings=subprocess.run(['java','-XshowSettings:properties','-version'],capture_output=True,text=True)
    java_home=next(line.split('=',1)[1].strip()for line in settings.stderr.splitlines()if 'java.home =' in line)
    output=tmp_path/'output.jar'
    result=subprocess.run(['java','-cp',jar,'com.android.tools.r8.R8','--release','--classfile','--lib',java_home,
        '--pg-conf',str(config),'--pg-conf',str(ROOT/'TMessagesProj/performance-shrink.pro'),'--output',str(output),str(input_jar)],capture_output=True,text=True,timeout=90)
    assert result.returncode==0,result.stdout+result.stderr
    with zipfile.ZipFile(output)as archive:
        names=set(archive.namelist())
    assert 'app/flexygram/probe/DynamicEntry.class' in names
    assert 'app/exteraless/probe/PluginSurface.class' in names
    assert 'fixture/NativeOnly.class' in names
    assert 'fixture/Unused.class' not in names
    assert ('fixture/Work.class' not in names) == optimize
    result=subprocess.run(['java','-cp',str(output),'fixture.Main'],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
