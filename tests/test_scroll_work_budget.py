"""Execute scroll scheduling with fake UI queues; no device frame-rate claim."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_translation_scan_waits_for_scroll_and_explicit_requests_still_run(tmp_path):
    source=(JAVA/'org/telegram/ui/ChatActivity.java').read_text()
    active=method(source,'private boolean isTranslationScrollActive()')
    schedule=method(source,'private void checkTranslation(boolean force)')
    prefix=method(source,'if (translationCheckDeferred && isTranslationScrollActive())')
    probe(tmp_path, {'Probe.java': '''
public class Probe {
 static class RecyclerView {static final int SCROLL_STATE_IDLE=0;int state;int getScrollState(){return state;}}
 static class AndroidUtilities {
  static Runnable queued;static long delay;
  static void cancelRunOnUIThread(Runnable r){if(queued==r)queued=null;}
  static void runOnUIThread(Runnable r,long d){if(queued!=null)throw new AssertionError("duplicate queued scan");queued=r;delay=d;}
  static void fire(){Runnable r=queued;queued=null;if(r!=null)r.run();}
 }
 RecyclerView chatListView=new RecyclerView();long lastTranslationCheck;boolean translationCheckDeferred;int scans;
 ACTIVE
 SCHEDULE
 Runnable checkTranslationRunnable=()->{PREFIX translationCheckDeferred=false;lastTranslationCheck=System.currentTimeMillis();scans++;};
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 public static void main(String[] args) {
  Probe p=new Probe();
  for(int state:new int[]{1,2}) {
   p.chatListView.state=state;p.lastTranslationCheck=0;
   for(int i=0;i<5000;i++){p.checkTranslation(false);check(AndroidUtilities.delay==150);}
   for(int i=0;i<10;i++)AndroidUtilities.fire();
   check(p.scans==0&&AndroidUtilities.queued!=null);
  }
  p.chatListView.state=0;AndroidUtilities.fire();check(p.scans==1&&AndroidUtilities.queued==null);
  p.chatListView.state=2;p.checkTranslation(true);check(AndroidUtilities.delay==0);AndroidUtilities.fire();check(p.scans==2);
  p.checkTranslation(false);AndroidUtilities.cancelRunOnUIThread(p.checkTranslationRunnable);AndroidUtilities.fire();check(p.scans==2);
  p.chatListView=null;p.checkTranslation(true);AndroidUtilities.fire();check(p.scans==3);
 }
}'''.replace('ACTIVE',active).replace('SCHEDULE',schedule).replace('PREFIX',prefix)})
    listener=source[source.index('public void onScrollStateChanged(RecyclerView recyclerView, int newState)'):]
    assert 'checkTranslation(false)' in method(listener,'public void onScrollStateChanged(')
    assert 'cancelRunOnUIThread(checkTranslationRunnable)' in method(source,'public void onFragmentDestroy()')


def test_dialog_scroll_requests_do_not_capture_until_root_draw(tmp_path):
    source=(JAVA/'org/telegram/ui/DialogsActivity.java').read_text()
    request=method(source,'private void blur3_InvalidateBlur()')
    assert 'setupRenderNodes' not in request and 'invalidateResultRenderNodes' not in request
    assert 'updateDisplayList' not in request
    draw=method(source,'protected void dispatchDraw(Canvas canvas)')
    assert draw.count('blur3_UpdateBlur();')==1
    assert draw.index('updateStoriesViewAlpha(storiesAlpha)')<draw.index('blur3_UpdateBlur();')<draw.index('super.dispatchDraw(canvas)')
    assert source.count('blur3_UpdateBlur();')==1
    probe(tmp_path, {'Probe.java': '''
public class Probe {
 static class Build {static class VERSION{static int SDK_INT=31;}static class VERSION_CODES{static int S=31;}}
 static class View {int requests;void invalidate(){requests++;}}
 Object scrollableViewNoiseSuppressor=new Object(),actionBar=new Object();View fragmentView=new View();
 REQUEST
 public static void main(String[] args){
  Probe p=new Probe();for(int i=0;i<10000;i++)p.blur3_InvalidateBlur();
  if(p.fragmentView.requests!=10000)throw new AssertionError();
  Build.VERSION.SDK_INT=30;p.blur3_InvalidateBlur();if(p.fragmentView.requests!=10000)throw new AssertionError();
  Build.VERSION.SDK_INT=31;p.scrollableViewNoiseSuppressor=null;p.blur3_InvalidateBlur();
  p.fragmentView=null;p.blur3_InvalidateBlur();
 }
}'''.replace('REQUEST',request)})
