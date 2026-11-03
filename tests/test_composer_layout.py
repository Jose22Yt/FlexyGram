"""Execute composer measurement/scheduling logic with a deterministic Java queue.

This covers restarts and reentrant layout requests, not Android rendering/IME.
"""
import pathlib
import shutil
import subprocess
import tempfile

import pytest


def method(source, signature):
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]


@pytest.mark.skipif(not shutil.which("javac") or not shutil.which("java"), reason="JDK required")
def test_composer_measurement_and_deferred_buttons():
    root = pathlib.Path(__file__).resolve().parents[1]
    source = (root / "TMessagesProj/src/main/java/org/telegram/ui/Components/ChatActivityEnterView.java").read_text()
    container = source[source.index("FrameLayout frameLayout = messageEditTextContainer ="):]
    measure = method(container, "protected void onMeasure(")
    scheduler = method(source, "private void scheduleComposerButtonsUpdate()")
    start = source.index("    private boolean composerButtonsUpdatePending;")
    end = source.index("    private void scheduleComposerButtonsUpdate()", start)
    state = source[start:end]
    harness = """
import java.util.ArrayList;
class MeasuredView {
    int height;
    protected void onMeasure(int width, int height) { this.height=height; }
    int getMeasuredHeight() { return height; }
}
public class ComposerRegression extends MeasuredView {
    static class Animator {
        float current, target; int starts;
        float getFactor() { return current; }
        float getToFactor() { return target; }
        void forceFactor(float value) {current=target=value;}
        void animateTo(float value) {target=value;starts++;}
    }
    static class Editor {
        int lines=1; String text="hello"; boolean layoutRequested;
        boolean isLayoutRequested(){return layoutRequested;}
        int getLineCount(){return lines;} CharSequence getText(){return text;}
    }
    static class TextUtils {
        static boolean isEmpty(CharSequence text){return text==null||text.length()==0;}
    }
    static class AndroidUtilities {
        static CharSequence getTrimmedString(CharSequence text){return text.toString().trim();}
    }
    final Animator animatorInputFieldHeight=new Animator();
    final ArrayList<Runnable> queue=new ArrayList<>();
    final Editor messageEditText=new Editor();
    boolean rich, destroyed, richDraftActive; int updates;
    int dp(int value){return value;}
    static class MeasureSpec {static int getSize(int width){return width;}}
    void applyFlexyComposerPresentation(int width){}
    void checkUi_TopViewVisibility(){}
    void post(Runnable callback){queue.add(callback);}
    void showRichButton(boolean show){rich=show;updates++;}
    void drain(){while(!queue.isEmpty())queue.remove(0).run();}
    static void require(boolean value,String message){if(!value)throw new AssertionError(message);}
    MEASURE
    STATE
    SCHEDULER
    public static void main(String[] args) {
        ComposerRegression c=new ComposerRegression();
        c.onMeasure(300,44); c.onMeasure(300,66);
        for(int i=0;i<100;i++)c.onMeasure(300,66);
        require(c.animatorInputFieldHeight.starts==1,"same height target must not restart");
        c.onMeasure(300,88);c.onMeasure(300,154);c.onMeasure(300,44);
        require(c.animatorInputFieldHeight.starts==4,"growth and deletion must update target");
        c.messageEditText.lines=3;c.scheduleComposerButtonsUpdate();
        c.messageEditText.lines=2;c.scheduleComposerButtonsUpdate();
        require(c.updates==0&&c.queue.size()==1,"defer and coalesce visibility changes");
        c.drain();require(!c.rich,"read latest layout after deletion");
        c.messageEditText.lines=3;c.scheduleComposerButtonsUpdate();c.drain();
        require(!c.rich,"three lines must keep expansion hidden");
        c.messageEditText.lines=4;c.scheduleComposerButtonsUpdate();c.drain();
        require(c.rich,"four lines must offer expansion");
        c.messageEditText.lines=6;c.scheduleComposerButtonsUpdate();c.drain();
        require(c.rich,"long text retains editor controls");
        c.messageEditText.text="   ";c.scheduleComposerButtonsUpdate();c.drain();
        require(!c.rich,"blank text hides editor controls");
        int previousUpdates=c.updates;
        c.messageEditText.layoutRequested=true;c.scheduleComposerButtonsUpdate();c.drain();
        require(c.updates==previousUpdates,"pending text layout must not expose stale line count");
        c.messageEditText.layoutRequested=false;c.scheduleComposerButtonsUpdate();c.drain();
        require(c.updates==previousUpdates+1,"completed measurement must update buttons");
        c.destroyed=true;c.scheduleComposerButtonsUpdate();
        require(c.queue.isEmpty(),"destroyed composer must not schedule updates");
    }
}
""".replace("MEASURE", measure).replace("STATE", state).replace("SCHEDULER", scheduler)
    with tempfile.TemporaryDirectory(prefix="flexygram-composer-") as directory:
        path = pathlib.Path(directory) / "ComposerRegression.java"
        path.write_text(harness)
        result = subprocess.run(["javac", "-d", directory, str(path)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        result = subprocess.run(["java", "-cp", directory, "ComposerRegression"], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
