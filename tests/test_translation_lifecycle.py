"""Execute the real scheduler and runnable gates with counted queues and scans."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_language_detection_deduplicates_by_chat_and_can_retry_a_rejected_request(tmp_path):
    source = (JAVA / 'org/telegram/messenger/TranslateController.java').read_text()
    start = source.index('    private record LanguageCheckKey(')
    fields = source[start:source.index('    private void checkLanguage(', start)]
    check_language = method(source, 'private void checkLanguage(')
    probe(tmp_path, {'Probe.java': '''import java.util.*;
import java.util.function.Consumer;
public class Probe {
    static final String UNKNOWN_LANGUAGE="unknown";
    static class Owner { String originalLanguage; }
    record MessageObject(long dialog,int id,Owner messageOwner) {
        long getDialogId() { return dialog; }
        int getId() { return id; }
    }
    static class Queue {
        final ArrayDeque<Runnable> work=new ArrayDeque<>();
        boolean accept=true;
        boolean postRunnable(Runnable runnable) { if (!accept) return false; work.add(runnable); return true; }
    }
    static class Utilities { static final Queue stageQueue=new Queue(); }
    static class AndroidUtilities { static void runOnUIThread(Runnable runnable) { runnable.run(); } }
    static class TextUtils { static boolean isEmpty(String value) { return value==null || value.isEmpty(); } }
    static class LanguageDetector {
        static boolean fail;
        static boolean hasSupport() { return true; }
        static void detectLanguage(String text, Consumer<String> success, Consumer<Exception> failure) {
            if (fail) failure.accept(new IllegalStateException()); else success.accept("es");
        }
    }
    static class Storage { void updateMessageCustomParams(long dialog, Owner owner) {} }
    final Storage storage=new Storage();
    int textReads, decisions;
    Storage getMessagesStorage() { return storage; }
    boolean isDialogTranslatable(long dialog) { return dialog==200; }
    String getDetectLanguageText(MessageObject message) { textReads++; return "texto"; }
    void checkDialogTranslatable(MessageObject message) { decisions++; }
    FIELDS
    METHOD
    static void require(boolean condition) { if (!condition) throw new AssertionError(); }
    public static void main(String[] args) {
        Probe p=new Probe();
        Queue queue=Utilities.stageQueue;
        MessageObject first=new MessageObject(100,32,new Owner()), second=new MessageObject(101,1,new Owner());
        require(Objects.hash(first.dialog,first.id)==Objects.hash(second.dialog,second.id));
        p.checkLanguage(first);
        for (int i=0;i<10000;i++) p.checkLanguage(first);
        p.checkLanguage(second);
        p.checkLanguage(new MessageObject(200,1,new Owner()));
        require(queue.work.size()==2 && p.textReads==2);
        queue.work.remove().run();
        LanguageDetector.fail=true; queue.work.remove().run();
        require(p.pendingLanguageChecks.isEmpty() && p.decisions==1);
        require("es".equals(first.messageOwner.originalLanguage) && UNKNOWN_LANGUAGE.equals(second.messageOwner.originalLanguage));
        p.checkLanguage(first); require(p.decisions==2 && queue.work.isEmpty());
        queue.accept=false;
        MessageObject retry=new MessageObject(101,32,new Owner());
        p.checkLanguage(retry); require(p.pendingLanguageChecks.isEmpty());
        queue.accept=true; p.checkLanguage(retry); require(queue.work.size()==1);
        LanguageDetector.fail=false; queue.work.remove().run();
        require(p.pendingLanguageChecks.isEmpty() && "es".equals(retry.messageOwner.originalLanguage));
    }
}'''.replace('FIELDS', fields).replace('METHOD', check_language)})


def test_paused_translation_does_no_work_and_resumes_one_pending_scan(tmp_path):
    source = (JAVA/'org/telegram/ui/ChatActivity.java').read_text()
    schedule = method(source, 'private void checkTranslation(boolean force)')
    active = method(source, 'private boolean isTranslationScrollActive()')
    callback = source.split('private Runnable checkTranslationRunnable = () -> {', 1)[1]
    gates = callback.split('translationCheckDeferred = false;', 1)[0]
    probe(tmp_path, {'Probe.java': '''
public class Probe {
 static class RecyclerView {static final int SCROLL_STATE_IDLE=0;int state;int getScrollState(){return state;}}
 static class AndroidUtilities {
  static Runnable queued;static int posts;
  static void cancelRunOnUIThread(Runnable r){if(queued==r)queued=null;}
  static void runOnUIThread(Runnable r,long delay){posts++;if(queued!=null)throw new AssertionError("duplicate task");queued=r;}
  static void fire(){Runnable r=queued;queued=null;if(r!=null)r.run();}
 }
 RecyclerView chatListView=new RecyclerView();long lastTranslationCheck;
 boolean paused,isFinished,translationCheckDeferred;int scans;
 ACTIVE SCHEDULE
 Runnable checkTranslationRunnable=()->{GATES translationCheckDeferred=false;lastTranslationCheck=System.currentTimeMillis();scans++;};
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 public static void main(String[]args){
  Probe p=new Probe();p.paused=true;
  for(int i=0;i<10000;i++)p.checkTranslation(i%2==0);
  check(AndroidUtilities.posts==0&&p.scans==0&&p.translationCheckDeferred);
  p.paused=false;if(p.translationCheckDeferred)p.checkTranslation(false);
  check(AndroidUtilities.posts==1);AndroidUtilities.fire();check(p.scans==1&&!p.translationCheckDeferred);
  p.checkTranslation(false);p.paused=true;AndroidUtilities.fire();
  check(p.scans==1&&p.translationCheckDeferred&&AndroidUtilities.queued==null);
  p.paused=false;if(p.translationCheckDeferred)p.checkTranslation(false);
  AndroidUtilities.fire();check(p.scans==2&&!p.translationCheckDeferred);
  p.isFinished=true;for(int i=0;i<10000;i++)p.checkTranslation(true);
  check(AndroidUtilities.queued==null&&p.scans==2);
 }
}'''.replace('ACTIVE',active).replace('SCHEDULE',schedule).replace('GATES',gates)})
    pause = method(source, 'public void onPause()')
    resume = method(source, 'public void onResume()')
    assert 'cancelRunOnUIThread(checkTranslationRunnable)' in pause
    assert 'translationCheckDeferred = true;' in pause
    assert resume.index('paused = false;') < resume.index('if (translationCheckDeferred) checkTranslation(false);')
