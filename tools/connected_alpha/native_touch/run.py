"""Compile the production hit test against Android; DialogCell is a View double."""
from pathlib import Path
import importlib.util, sys
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('native_touch_pipeline',HERE.parent/'music_visual/run.py')
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
def write(source,root):
    java=root/'TMessagesProj/src/main/java'
    for name in ['NativeInstantTouchTarget','NativeInstantTouchPolicy']:
        path='app/flexygram/navigation/'+name+'.java'
        dest=source/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((java/path).read_bytes())
    dest=source/'org/telegram/ui/Cells/DialogCell.java';dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text('package org.telegram.ui.Cells; public class DialogCell extends android.view.View { public DialogCell(android.content.Context c){super(c);} }')
if __name__=='__main__':
    if '--output-dir' not in sys.argv:sys.argv += ['--output-dir',str(HERE.parents[2]/'build/connected-alpha-native-touch')]
    raise SystemExit(p.main(here=HERE,test_class='NativeTouchTargetTest',stubs_writer=write))
