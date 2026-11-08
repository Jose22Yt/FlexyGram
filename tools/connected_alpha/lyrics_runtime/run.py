#!/usr/bin/env python3
"""Exercise actual lyrics providers/parser/cache with fixture HTTPS responses on Android. No live service or APK."""
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('lyrics_pipeline',HERE.parent/'music_visual/run.py')
pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)
def write_stubs(source,root):
 def put(path,text):
  p=source/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
 for name in ('OnlineLyrics','Lyrics'):
  put('app/exteraless/player/'+name+'.java',(root/'TMessagesProj/src/main/java/app/exteraless/player'/f'{name}.java').read_text())
 put('org/telegram/messenger/AndroidUtilities.java','''package org.telegram.messenger;public class AndroidUtilities{
 public static void runOnUIThread(Runnable r){new android.os.Handler(android.os.Looper.getMainLooper()).post(r);}}''')
 put('org/telegram/messenger/ApplicationLoader.java','package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext;}')
 put('org/telegram/messenger/BuildVars.java','package org.telegram.messenger;public class BuildVars{public static final String BUILD_VERSION_STRING="test";}')
 put('org/telegram/messenger/DispatchQueue.java','''package org.telegram.messenger;public class DispatchQueue{
 public static final java.util.ArrayDeque<Runnable> tasks=new java.util.ArrayDeque<>();public DispatchQueue(String name){}public void postRunnable(Runnable r){tasks.add(r);}
 public static void drain(){while(!tasks.isEmpty())tasks.remove().run();}}''')
 put('org/telegram/messenger/FileLog.java','package org.telegram.messenger;public class FileLog{public static void e(Throwable e){}}')
 put('org/telegram/messenger/Utilities.java','''package org.telegram.messenger;public class Utilities{
 public static String MD5(String s){try{return java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("MD5").digest(s.getBytes(java.nio.charset.StandardCharsets.UTF_8)));}catch(Exception e){throw new AssertionError(e);}}}''')
if __name__=='__main__':raise SystemExit(pipeline.main(here=HERE,test_class='LyricsRuntimeTest',stubs_writer=write_stubs))
