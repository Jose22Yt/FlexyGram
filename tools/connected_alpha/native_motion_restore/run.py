"""Compile real restored native controls; execute API35 isolated Android tests."""
from pathlib import Path
import importlib.util,sys
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location("native_restore_pipeline",HERE.parent/"music_visual/run.py")
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
def write(source,root):
    java=root/"TMessagesProj/src/main/java"
    for name in ["ButtonBounce","ScaleStateListAnimator","CubicBezierInterpolator"]:
        path="org/telegram/ui/Components/"+name+".java"
        dest=source/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((java/path).read_bytes())
    dest=source/"org/telegram/messenger/AndroidUtilities.java";dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text("package org.telegram.messenger;public class AndroidUtilities{public static float lerp(float a,float b,float t){return a+(b-a)*t;}}")
if __name__=="__main__":
    if "--output-dir" not in sys.argv:sys.argv += ["--output-dir",str(HERE.parents[2]/"build/connected-alpha-native-motion-restore")]
    raise SystemExit(p.main(here=HERE,test_class="NativeMotionRestoreTest",stubs_writer=write))
