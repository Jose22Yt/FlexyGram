#!/usr/bin/env python3
"""Compile changed icon classes against real Android + AndroidX APIs. Never builds an APK.
Dependencies on Telegram application services are explicit doubles, not Android classes.
"""
import argparse,os,re,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
JAVA=ROOT/'TMessagesProj/src/main/java'

def check(android,core):
    paths=['app/flexygram/icons/'+n+'.java' for n in ['OriginalIconDrawable','ExactIcons','ExactIconMap','IosOriginalAssets','CupertinoIcons','ConversationControlIcons']]
    paths+=['app/exteraless/player/PlayerIcon.java','org/telegram/ui/ActionBar/BackDrawable.java',
            'app/flexygram/bubbles/interaction/BubbleMenuIcon.java','app/flexygram/home/SignaturePreviewIcon.java']
    code='\n'.join((JAVA/p).read_text()for p in paths)
    names=sorted(set(re.findall(r'R\.drawable\.(\w+)',code)))
    stubs={
        'org/telegram/messenger/R.java':'package org.telegram.messenger;public class R{public static class drawable{'+''.join(f'public static int {n}={i+1};'for i,n in enumerate(names))+'}}',
        'org/telegram/messenger/AndroidUtilities.java':'package org.telegram.messenger;public class AndroidUtilities{public static float density=1;public static int dp(float v){return (int)Math.ceil(v*density);}public static float lerp(float a,float b,float t){return a+(b-a)*t;}}',
        'org/telegram/messenger/Utilities.java':'package org.telegram.messenger;public class Utilities{public static float clamp(float v,float max,float min){return Math.max(min,Math.min(max,v));}}',
        'org/telegram/messenger/ApplicationLoader.java':'package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext;}',
        'app/exteraless/icons/BaseIconPacks.java':'package app.exteraless.icons;public class BaseIconPacks{public static int BASE_DEFAULT=0,BASE_CUPERTINO=3;public static int getSelected(){return 0;}}',
        'app/flexygram/bubbles/interaction/BubbleActionPanelView.java':'package app.flexygram.bubbles.interaction;public class BubbleActionPanelView{public enum Action{REPLY,COPY,STICKER,FORWARD,EDIT,PIN,DELETE,SELECT,SAVE,SHARE,LINK,MORE}}',
    }
    for annotation in ['NonNull','Nullable']:
        stubs['androidx/annotation/'+annotation+'.java']='package androidx.annotation;public @interface '+annotation+'{}'
    with tempfile.TemporaryDirectory(prefix='ios-original-types-')as tmp:
        src=Path(tmp);files=[]
        for name,text in stubs.items():
            p=src/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);files.append(p)
        subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-proc:none','-encoding','UTF-8','-cp',os.pathsep.join([str(android),str(core)]),'-d',str(src/'classes'),*map(str,files),*map(str,(JAVA/p for p in paths))],check=True)
    print('10 production icon classes checked against real Android and AndroidX APIs; application services are doubles. No APK.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--android-jar',type=Path,required=True);parser.add_argument('--core-jar',type=Path,required=True)
    args=parser.parse_args();check(args.android_jar,args.core_jar)
