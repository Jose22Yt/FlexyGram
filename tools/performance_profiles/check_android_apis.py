#!/usr/bin/env python3
"""Compile performance code against real Android/AndroidX APIs. Never creates an APK."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--sdk',type=Path,default=Path(os.environ.get('ANDROID_HOME',str(ROOT.parent/'.flexygram/android-sdk'))))
parser.add_argument('--libraries',type=Path,required=True,help='Extracted classes.jar files named as documented in docs/FlexyGram-rendimiento-avanzado.md')
args=parser.parse_args()
android=args.sdk/'platforms/android-37.0/android.jar'
names=['metrics','kotlin','annotation','junit','macro','benchmark','benchmarkcommon','testmonitor','uiautomator']
libs=[args.libraries/(name+'.jar') for name in names]
for path in [android,*libs]:
    if not path.is_file():raise SystemExit('Missing API input: '+str(path))
with tempfile.TemporaryDirectory(prefix='flexy-performance-api-') as tmp:
    folder=Path(tmp);source=folder/'src/org/telegram/messenger';source.mkdir(parents=True)
    build=source/'BuildConfig.java';build.write_text('package org.telegram.messenger;public class BuildConfig{public static final boolean PERFORMANCE_TEST_BUILD=true,FLEXY_FRAME_DIAGNOSTICS=true,FLEXY_SYSTEM_TRACE=false;}')
    app=source/'ApplicationLoader.java';app.write_text('package org.telegram.messenger;public class ApplicationLoader{public static ApplicationLoader applicationLoaderInstance;public void onTrimMemory(int level){}}')
    actual=[ROOT/'TMessagesProj/src/main/java/app/flexygram/performance'/(name+'.java') for name in ['FrameDiagnostics','FrameWindowStats','SystemProfiles','MemoryBudgetBridge','TextLayoutPrecompute']]
    tests=list((ROOT/'performance/src/main/java/com/flexygram/performance').glob('*.java'))
    subprocess.run([os.environ.get('JAVAC','javac'),'-proc:none','-cp',os.pathsep.join(map(str,[android,*libs])),'-d',str(folder/'classes'),str(build),str(app),*map(str,actual+tests)],check=True)
print('Five production classes and three device test classes checked against Android API37 and actual AndroidX artifacts. App services are explicit doubles. No APK built.')
