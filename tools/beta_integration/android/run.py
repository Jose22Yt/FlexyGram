"""Compile production Beta views against API37 and exercise native Android graphics in isolation."""
from pathlib import Path
import importlib.util,sys,re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
s=importlib.util.spec_from_file_location('beta_android_pipeline',ROOT/'tools/connected_alpha/music_visual/run.py')
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
def write(source,root):
    def put(name,text):
        path=source/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    put('androidx/annotation/NonNull.java','package androidx.annotation;public @interface NonNull {}')
    java=root/'TMessagesProj/src/main/java'
    files=['app/flexygram/bubbles/deletion/'+n+'.java' for n in ['DeleteMotionMath','DeleteMotionOverlay','DeleteMotionSettings']]
    files+=['app/flexygram/bubbles/interaction/ContextPreviewViewport.java','app/flexygram/bubbles/interaction/ContextPreviewPlacement.java',
        'app/flexygram/home/SignatureSmartPillSpan.java','app/flexygram/home/SignatureSmartPreviewPalette.java']
    for name in files:put(name,(java/name).read_text())
    put('org/telegram/messenger/SharedConfig.java','package org.telegram.messenger;public class SharedConfig{public static boolean enabled=true;public static boolean animationsEnabled(){return enabled;}}')
    put('org/telegram/messenger/AndroidUtilities.java','package org.telegram.messenger;public class AndroidUtilities{public static boolean isAccessibilityScreenReaderEnabled(){return false;}public static int dp(float n){return Math.round(n);}}')
    put('org/telegram/messenger/LocaleController.java','package org.telegram.messenger;public class LocaleController{public static String getString(int n){return "Classic";}}')
    put('org/telegram/messenger/R.java','package org.telegram.messenger;public class R{public static class string{public static int FlexyContextNativeStyle=1;}}')
    put('org/telegram/ui/Cells/ChatMessageCell.java','package org.telegram.ui.Cells;public class ChatMessageCell extends android.view.View{public ChatMessageCell(android.content.Context c){super(c);}public boolean drawBackgroundInParent(){return false;}public void drawBackgroundInternal(android.graphics.Canvas c,boolean b){}}')
    put('org/telegram/ui/ActionBar/Theme.java','package org.telegram.ui.ActionBar;public class Theme{public interface ResourcesProvider{}public static int key_actionBarTabLine=1,key_windowBackgroundWhite=2;public static int getColor(int k,ResourcesProvider p){return k==1?0xff2487bd:0xfff8f8f8;}}')
    put('app/flexygram/home/SignatureSmartPreviews.java','package app.flexygram.home;public class SignatureSmartPreviews{public static int mode(){return 0;}}')
if __name__=='__main__':
    sys.argv+=['--output-dir',str(ROOT/'build/beta-android')]
    raise SystemExit(p.main(here=HERE,test_class='BetaAndroidTest',stubs_writer=write))
