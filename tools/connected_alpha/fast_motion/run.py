"""Production timing/configuration against Android animators; no APK or global settings changes."""
from pathlib import Path
import importlib.util,sys
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('motion_pipeline',HERE.parent/'music_visual/run.py')
pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)
def write(source,root):
    def put(path,text):
        dest=source/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
    java=root/'TMessagesProj/src/main/java'
    for name in ['FastMotion','FastMotionTiming','FastMotionConfig']:
        path='app/flexygram/animation/'+name+'.java';put(path,(java/path).read_text())
    put('org/telegram/messenger/ApplicationLoader.java','package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext;}')
    # Spring types are explicit compile doubles; this fixture tests framework/legacy timing restoration.
    put('androidx/dynamicanimation/animation/DynamicAnimation.java','package androidx.dynamicanimation.animation;public class DynamicAnimation<T>{public void start(){}}')
    put('androidx/dynamicanimation/animation/SpringAnimation.java','package androidx.dynamicanimation.animation;public class SpringAnimation extends DynamicAnimation<SpringAnimation>{public boolean canSkipToEnd(){return true;}public void skipToEnd(){}}')
if __name__=='__main__':
    if '--output-dir' not in sys.argv:
        sys.argv += ['--output-dir',str(HERE.parents[2]/'build/connected-alpha-fast-motion')]
    raise SystemExit(pipeline.main(here=HERE,test_class='FastMotionRestoreTest',stubs_writer=write))
