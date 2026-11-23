"""Exercise production page selection and dock measurement with counted children."""
import sqlite3
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method


def test_first_home_dialog_batch_promotes_the_pending_update_once(tmp_path):
    source = (JAVA / 'org/telegram/ui/DialogsActivity.java').read_text()
    methods = '\n'.join(method(source, name) for name in (
        'public void updateList(boolean animated)', 'private boolean shouldPublishFirstHomeDialogs()',
        'private void cancelListUpdate()',
    ))
    start = source.index('        final Runnable updateListRunnable =')
    callback = source[start:source.index('        private void cancelListUpdate()', start)]
    probe(tmp_path, {'Probe.java': '''import java.util.*;
public class Probe {
 static final int DIALOGS_TYPE_DEFAULT=0;
 static class AndroidUtilities {
  static Map<Runnable, Integer> pending=new LinkedHashMap<>();
  static int posts;
  static void runOnUIThread(Runnable callback,int delay){check(!pending.containsKey(callback));pending.put(callback,delay);posts++;}
  static void cancelRunOnUIThread(Runnable callback){pending.remove(callback);}
  static void fire(){Runnable next=pending.keySet().iterator().next();pending.remove(next);next.run();}
 }
 static class Controller {
  List<Integer> dialogs=new ArrayList<>();List<Integer> getDialogs(int folder){return dialogs;}
 }
 static class Adapter {
  final Controller controller;int count,updates,cancelled;
  Adapter(Controller controller){this.controller=controller;}
  int getDialogsCount(){return count;}
  void updateList(Runnable restore){count=controller.dialogs.size();updates++;}
  void cancelPendingListDiff(){cancelled++;}
 }
 static class Animator {boolean isRunning(){return false;}}
 static class ListView {void setItemAnimator(Animator value){}}
 int folderId,communityId,dialogsType;
 boolean isPaused,isFinished,onlySelect,dialogsListFrozen,updating,firstDialogsUpdateQueued,invalidateScrollY;
 Probe[] viewPages={this};
 Controller controller=new Controller();Controller getMessagesController(){return controller;}
 Adapter dialogsAdapter=new Adapter(controller);
 Animator dialogsItemAnimator=new Animator();ListView listView=new ListView();
 Runnable saveScrollPositionRunnable=()->{};
 CALLBACK
 METHODS
 static void check(boolean valid){if(!valid)throw new AssertionError();}
 void delay(int value){check(AndroidUtilities.pending.get(updateListRunnable)==value&&AndroidUtilities.pending.size()==1);}
 public static void main(String[] args){
  Probe p=new Probe();p.updateList(false);p.delay(36);
  p.controller.dialogs.add(1);p.updateList(false);p.delay(0);
  for(int i=0;i<10000;i++)p.updateList(false);
  check(AndroidUtilities.posts==2&&p.firstDialogsUpdateQueued&&p.dialogsAdapter.updates==0);
  AndroidUtilities.fire();
  check(p.dialogsAdapter.updates==1&&p.dialogsAdapter.count==1&&!p.firstDialogsUpdateQueued&&!p.updating);
  p.updateList(false);p.delay(36);p.cancelListUpdate();
  check(AndroidUtilities.pending.isEmpty()&&p.dialogsAdapter.cancelled==1);
  Probe emptyThenPaused=new Probe();emptyThenPaused.controller.dialogs.add(1);
  emptyThenPaused.updateList(false);emptyThenPaused.delay(0);emptyThenPaused.isPaused=true;
  AndroidUtilities.fire();
  check(!emptyThenPaused.firstDialogsUpdateQueued&&!emptyThenPaused.updating&&emptyThenPaused.dialogsAdapter.updates==0);
  Probe picker=new Probe();picker.onlySelect=true;picker.controller.dialogs.add(1);
  picker.updateList(false);picker.delay(36);picker.cancelListUpdate();
 }
}'''.replace('CALLBACK', callback).replace('METHODS', methods)})


def test_archive_initial_page_keeps_pagination_and_end_threshold(tmp_path):
    source = (JAVA/'org/telegram/messenger/MessagesStorage.java').read_text()
    start = source.index('                    if (a == 0) {', source.index('public void getDialogs(int folderId'))
    end = source.index('\n\n', start)
    branch = source[start:end]
    probe(tmp_path, {'Probe.java': '''public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){
 for(int count:new int[]{1,19,20,32,100,150})for(int a=0;a<2;a++){
  int offset=64,off,cnt;
  BRANCH
  check(a==0?off==offset&&cnt==count:off==0&&cnt>=20&&cnt<=100&&cnt==(count<20?20:Math.min(100,count)));
 }
 }}'''.replace('BRANCH', branch)})
    # A bounded first page leaves the remainder available through the normal offset.
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE dialogs(did INTEGER, pinned INTEGER, date INTEGER)')
    db.executemany('INSERT INTO dialogs VALUES (?,0,?)', [(i,i) for i in range(101)])
    pages = [db.execute('SELECT did FROM dialogs ORDER BY pinned DESC,date DESC LIMIT ?,?', (offset,32)).fetchall() for offset in range(0,101,32)]
    assert len(pages[0]) == 32
    assert [row[0] for page in pages for row in page] == list(reversed(range(101)))


def test_native_layout_skips_hidden_tabs_during_measurement():
    source=(JAVA/'org/telegram/ui/MainTabsLayout.java').read_text()
    measure=method(source,'protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec)')
    assert 'isViewVisible(child)' in measure
    assert 'if (!isViewVisible(getChildAt(a))) continue;' in measure
