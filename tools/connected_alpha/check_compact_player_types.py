#!/usr/bin/env python3
"""Android API37 + real AndroidX Core type check; playback/navigation are explicit doubles. No APK."""
import importlib.util,os,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('music_stubs',ROOT/'tools/connected_alpha/music_visual/stubs.py')
stubs=importlib.util.module_from_spec(spec);spec.loader.exec_module(stubs)
sdk=Path(os.environ.get('ANDROID_HOME',str(ROOT.parent/'.flexygram/android-sdk')))/'platforms/android-37.0/android.jar'
core=Path(os.environ.get('FLEXY_CORE_JAR','/tmp/flexy-performance-libs/core.jar'))
if not sdk.exists() or not core.exists():raise SystemExit('Android API37 and AndroidX Core classes.jar are required.')
with tempfile.TemporaryDirectory(prefix='compact-player-types-') as tmp:
 src=Path(tmp)/'src';src.mkdir();stubs.write_stubs(src,ROOT)
 subprocess.run(['javac','-encoding','UTF-8','-proc:none','-cp',os.pathsep.join(map(str,[sdk,core,*([core.parent/'annotation.jar'] if (core.parent/'annotation.jar').is_file() else [])])),'-d',tmp+'/classes',*map(str,src.rglob('*.java'))],check=True)
print('Player widgets and actual inner PlayerLayout type checked against API37; playback/theme/navigation services are doubles. No APK built.')
