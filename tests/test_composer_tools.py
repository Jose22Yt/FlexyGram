"""Host checks for relocated composer actions; Android visuals require device testing."""
import pathlib
import shutil
import subprocess
import tempfile

import pytest

from test_composer_layout import method


@pytest.mark.skipif(not shutil.which("javac") or not shutil.which("java"), reason="JDK required")
def test_composer_tool_routes_and_restrictions():
    root = pathlib.Path(__file__).resolve().parents[1]
    source = (root / "TMessagesProj/src/main/java/org/telegram/ui/Components/ChatActivityEnterView.java").read_text()
    methods = "\n".join(method(source, signature) for signature in (
        "private boolean canUseAiEditor()", "private boolean canUseRichEditor()",
        "public boolean showComposerTools(View anchor)",
        "private void addComposerToolsToActionMode(ActionMode mode, Menu menu)",
    ))
    dispatch = method(source, "public boolean performMenuAction(int itemId)")
    dispatch = dispatch.replace("ChatActivityEnterView.this", "ComposerToolsRegression.this")
    harness = """
import java.util.*;
class BaseEditor { public boolean performMenuAction(int id){return id==99;} }
public class ComposerToolsRegression {
    static class View {}
    static class ActionMode {}
    static class Menu {
        static final int NONE=0; Map<Integer,String> entries=new HashMap<>();
        String findItem(int id){return entries.get(id);}
        void add(int group,int id,int order,String text){entries.put(id,text);}
    }
    static class Fragment {boolean secret;boolean isSecretChat(){return secret;}}
    static class MessagesController {
        static final MessagesController instance=new MessagesController(); boolean available=true;
        static MessagesController getInstance(int account){return instance;}
        boolean richEditorAvailable(){return available;}
    }
    static class app {static class exteraless {static class appearance {
        static class AiFeaturesHelper {static boolean hidden;static boolean isAiEditorHidden(){return hidden;}}
    }}}
    static class R {
        static class drawable {static int msg_edit=1,iv_fullscreen=2;}
        static class string {static int AIEditor=3,ArticleEditor=4;}
    }
    static class ItemOptions {
        static ItemOptions last; List<Runnable> actions=new ArrayList<>();boolean shown;
        static ItemOptions makeOptions(Fragment f,View v){return last=new ItemOptions();}
        void add(int icon,String text,Runnable action){actions.add(action);}
        void show(){shown=true;}
    }
    static final int COMPOSER_AI_MENU_ID=1,COMPOSER_RICH_MENU_ID=2;
    Fragment parentFragment=new Fragment();int currentAccount,aiCalls,richCalls;
    boolean destroyed,isLiveComment,business;Object editingMessageObject;
    List<Runnable> pending=new ArrayList<>();
    boolean isEditingBusinessLink(){return business;}
    String getString(int id){return Integer.toString(id);}
    void openAiEditor(){aiCalls++;}void openRichEditor(){richCalls++;}
    void post(Runnable action){pending.add(action);}
    METHODS
    class Editor extends BaseEditor { DISPATCH }
    static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    public static void main(String[] args) {
        ComposerToolsRegression c=new ComposerToolsRegression();
        require(c.showComposerTools(new View()),"attachment long press opens tools");
        require(ItemOptions.last.shown&&ItemOptions.last.actions.size()==2,"both tools available");
        for(Runnable action:ItemOptions.last.actions)action.run();
        require(c.aiCalls==1&&c.richCalls==1,"menu preserves both actions");
        Menu menu=new Menu();menu.add(0,99,0,"Copy");
        c.addComposerToolsToActionMode(new ActionMode(),menu);
        c.addComposerToolsToActionMode(new ActionMode(),menu);
        require(menu.entries.size()==3&&menu.findItem(99)!=null,"preserve selection actions without duplicates");
        Editor editor=c.new Editor();
        require(editor.performMenuAction(99),"standard selection action delegates to parent");
        require(editor.performMenuAction(COMPOSER_AI_MENU_ID),"AI selection action handled");
        require(editor.performMenuAction(COMPOSER_RICH_MENU_ID),"editor selection action handled");
        require(c.aiCalls==1&&c.richCalls==1,"defer opening until selection mode finishes");
        for(Runnable action:c.pending)action.run();
        require(c.aiCalls==2&&c.richCalls==2,"selection actions reach editors");
        c.parentFragment.secret=true;require(!c.showComposerTools(new View()),"secret chat restrictions");
        c.parentFragment.secret=false;c.business=true;require(!c.showComposerTools(new View()),"business link restrictions");
        c.business=false;c.isLiveComment=true;require(!c.showComposerTools(new View()),"live comment restrictions");
        c.isLiveComment=false;app.exteraless.appearance.AiFeaturesHelper.hidden=true;
        require(c.showComposerTools(new View())&&ItemOptions.last.actions.size()==1,"respect hidden AI setting");
        c.editingMessageObject=new Object();require(!c.showComposerTools(new View()),"rich editor unavailable while editing a message");
        c.destroyed=true;require(!c.showComposerTools(new View()),"destroyed composer cannot open tools");
    }
}
""".replace("METHODS", methods).replace("DISPATCH", dispatch)
    with tempfile.TemporaryDirectory(prefix="flexygram-tools-") as directory:
        path = pathlib.Path(directory) / "ComposerToolsRegression.java"
        path.write_text(harness)
        result = subprocess.run(["javac", "-d", directory, str(path)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        result = subprocess.run(["java", "-cp", directory, "ComposerToolsRegression"], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
