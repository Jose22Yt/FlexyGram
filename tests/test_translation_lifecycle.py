"""Execute the real scheduler and runnable gates with counted queues and scans."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


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
