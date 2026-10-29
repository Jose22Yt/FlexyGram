"""Actual panel Android views; theme, strings, icon resources and host are doubles.
No full ChatActivity/navigation, sticker server or visual-acceptance claim.
"""
from pathlib import Path
import importlib.util,sys,re
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('panel_pipeline',HERE.parent/'music_visual/run.py')
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
def write(source,root):
    def put(path,text):
        dest=source/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
    java=root/'TMessagesProj/src/main/java'
    code=''
    for name in ['BubbleActionPanelView','DampedSpringCurve','SelectedBubbleMotion','BubbleInteractionSettings']:
        path='app/flexygram/bubbles/interaction/'+name+'.java';text=(java/path).read_text();put(path,text);code+=text
    strings=sorted(set(re.findall(r'R.string.(\w+)',code)));icons=sorted(set(re.findall(r'R.drawable.(\w+)',code)))
    put('org/telegram/messenger/R.java','package org.telegram.messenger; public class R {public static class string {'+''.join('public static final int '+n+'='+str(i+1)+';' for i,n in enumerate(strings))+'} public static class drawable {'+''.join('public static final int '+n+'=android.R.drawable.ic_menu_edit;' for n in icons)+'}}')
    put('org/telegram/messenger/LocaleController.java','package org.telegram.messenger;public class LocaleController {public static String getString(int id){switch(id){'+''.join('case R.string.'+n+':return "'+n+'";' for n in strings)+'default:return "unknown";}}}')
    colors=['windowBackgroundWhiteBlackText','windowBackgroundWhiteGrayText2','windowBackgroundWhiteBlueText','windowBackgroundWhite','windowBackgroundGray','text_RedRegular']
    put('org/telegram/ui/ActionBar/Theme.java','package org.telegram.ui.ActionBar;public class Theme{public interface ResourcesProvider{int getColor(int key);}'+''.join('public static final int key_'+n+'='+str(i+1)+';' for i,n in enumerate(colors))+'public static int getColor(int key){return 0xff203040;}public static int getColor(int key,ResourcesProvider p){return p==null?getColor(key):p.getColor(key);}}')
    native=(java/'org/telegram/ui/ChatActivity.java').read_text();start=native.index('    private java.util.EnumSet<app.flexygram.bubbles.interaction.BubbleActionPanelView.Action> signatureContextActions(');end=native.index('\n    private boolean createMenu(',start)
    method=native[start:end].replace('private java.util.EnumSet','public java.util.EnumSet')
    put('PanelHostProbe.java','import java.util.ArrayList;public class PanelHostProbe {public static final int OPTION_PIN=13;public static class Status {public boolean allowReply,allowCopy,allowForward,allowEdit,allowDelete;}public Status lastMessageMenuStatus=new Status();'+method+'}')
if __name__=='__main__':
    if '--output-dir' not in sys.argv:sys.argv+=['--output-dir',str(HERE.parents[2]/'build/connected-alpha-context-panel')]
    raise SystemExit(p.main(here=HERE,test_class='ContextPanelTest',stubs_writer=write))
