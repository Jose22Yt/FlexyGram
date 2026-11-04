#!/usr/bin/env python3
"""Compile Studio Java against Android SDK + explicit native API doubles. Never packages an APK."""
import os, subprocess, tempfile, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'studio_native'))
from stubs import write_stubs
ROOT=Path(__file__).resolve().parents[2]
SDK=Path(os.environ.get('ANDROID_HOME',str(ROOT.parent/'.flexygram/android-sdk')))
with tempfile.TemporaryDirectory(prefix='studio-types-') as tmp:
 src=Path(tmp)/'src';src.mkdir();write_stubs(src,ROOT)
 provider=src/'androidx/core/content/FileProvider.java';provider.parent.mkdir(parents=True,exist_ok=True)
 provider.write_text('package androidx.core.content;public class FileProvider{public String getType(android.net.Uri u){return null;}public static android.net.Uri getUriForFile(android.content.Context c,String a,java.io.File f){return null;}}')
 javac=os.environ.get('JAVAC','javac')
 subprocess.run([javac,'-encoding','UTF-8','-proc:none','-cp',str(SDK/'platforms/android-37.0/android.jar'),'-d',tmp+'/classes',*map(str,src.rglob('*.java'))],check=True)
 print('Studio Java type check passed against Android API37; native app classes are explicit doubles; no APK built.')
