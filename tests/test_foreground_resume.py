"""Resume work: execute native adapter methods with real DiffUtil and controlled UI/worker queues."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def diff_hosts():
    files = {
        'androidx/annotation/NonNull.java': 'package androidx.annotation;public @interface NonNull{}',
        'androidx/annotation/Nullable.java': 'package androidx.annotation;public @interface Nullable{}',
        'androidx/annotation/VisibleForTesting.java': 'package androidx.annotation;public @interface VisibleForTesting{}',
        'androidx/annotation/IntRange.java': 'package androidx.annotation;public @interface IntRange{long from() default Long.MIN_VALUE;long to() default Long.MAX_VALUE;}',
        'androidx/recyclerview/widget/RecyclerView.java': '''package androidx.recyclerview.widget;public class RecyclerView{
 public static final int NO_POSITION=-1;public static class Adapter{public int events,full;void check(){if(!Thread.currentThread().getName().equals("main"))throw new AssertionError("worker touched adapter");}
 public void notifyDataSetChanged(){check();full++;}public void notifyItemRangeInserted(int p,int n){check();events++;}
 public void notifyItemRangeRemoved(int p,int n){check();events++;}public void notifyItemMoved(int a,int b){check();events++;}
 public void notifyItemRangeChanged(int p,int n,Object payload){check();events++;}}}''',
    }
    source = (JAVA / 'org/telegram/ui/Adapters/DialogsAdapter.java').read_text()
    activity = (JAVA / 'org/telegram/ui/DialogsActivity.java').read_text()
    actual = '\n'.join(method(source, signature) for signature in [
        'private static final class DiffItem', 'private DiffItem[] snapshotDiffItems(', 'private static boolean preservesRowPositions(',
        'public void updateList(Consumer<IntUnaryOperator> saveScrollPosition)', 'private void applyListDiff(',
        'private int mapScrollAnchor(',
        'public void cancelPendingListDiff()', 'public void notifyDataSetChanged()'])
    actual += '\n' + method(activity, 'private void cancelListUpdate()')
    host = '''import java.util.*;import java.util.function.*;import androidx.recyclerview.widget.*;
class Queue{ArrayDeque<Runnable>jobs=new ArrayDeque<>();boolean accept=true;boolean postRunnable(Runnable r){if(!accept)return false;jobs.add(r);return true;}
 void cancelRunnable(Runnable r){jobs.remove(r);}
 void worker()throws Exception{Runnable r=jobs.remove();Throwable[]error={null};Thread t=new Thread(()->{try{r.run();}catch(Throwable e){error[0]=e;}},"diff-worker");t.start();t.join();if(error[0]!=null)throw new AssertionError(error[0]);}}
class DialogDiffQueue{static Queue queue=new Queue();}class AndroidUtilities{static ArrayDeque<Runnable>ui=new ArrayDeque<>();static void runOnUIThread(Runnable r){ui.add(r);}
 static void cancelRunOnUIThread(Runnable r){ui.remove(r);}}
class FileLog{static void e(Throwable e){throw new AssertionError(e);}}
public class Probe extends RecyclerView.Adapter{
 static final int VIEW_TYPE_DIALOG=0,VIEW_TYPE_HEADER_2=1,VIEW_TYPE_ME_URL=2,VIEW_TYPE_USER=3,VIEW_TYPE_EMPTY=4,VIEW_TYPE_LAST_EMPTY=5;
 static class Dialog{long id;boolean isFolder;Dialog(long n){id=n;}}static class Contact{long user_id;}static class Url{String url;}
 static class ItemInternal{int viewType,emptyType;boolean isFolder,isForumCell,pinned;Dialog dialog;Contact contact;Url recentMeUrl;
 ItemInternal(long id){dialog=new Dialog(id);}}
 ArrayList<ItemInternal>itemInternals=new ArrayList<>(),source=new ArrayList<>();boolean isCalculatingDiff,updateListPending;long diffGeneration;Consumer<IntUnaryOperator> pendingScrollPosition;
 Runnable pendingDiffWork;boolean updating,firstDialogsUpdateQueued;final Probe dialogsAdapter=this;final Runnable updateListRunnable=()->{};
 int committedRowsRefreshes;void refreshCommittedRows(){committedRowsRefreshes++;}
 void updateItemList(){itemInternals.clear();itemInternals.addAll(source);}
 ACTUAL
 static void check(boolean value){if(!value)throw new AssertionError();}
 void source(int first,int count){source=new ArrayList<>();for(int i=0;i<count;i++)source.add(new ItemInternal(first+i));}
 void initial(int count){source(0,count);itemInternals=new ArrayList<>(source);}
 static void complete()throws Exception{DialogDiffQueue.queue.worker();check(AndroidUtilities.ui.size()==1);AndroidUtilities.ui.remove().run();}
 public static void main(String[]a)throws Exception{BODY}
}'''.replace('ACTUAL', actual)
    native = [JAVA / f'androidx/recyclerview/widget/{name}.java' for name in ['DiffUtil', 'ListUpdateCallback', 'AdapterListUpdateCallback', 'BatchingListUpdateCallback']]
    return files, host, native


def run_diff(tmp_path, body):
    files, host, native = diff_hosts()
    files['Probe.java'] = host.replace('BODY', body)
    probe(tmp_path, files, native)


def test_large_production_lists_diff_on_worker_and_dispatch_only_on_ui(tmp_path):
    run_diff(tmp_path, '''Probe p=new Probe();p.initial(1000);var visible=p.itemInternals;p.source(20,1200);int[]saved={0};
 p.updateList(mapping->{saved[0]++;check(mapping.applyAsInt(9)==-1);check(mapping.applyAsInt(42)==22);});
 check(p.isCalculatingDiff&&p.events==0&&p.itemInternals==visible&&saved[0]==0);
 check(DialogDiffQueue.queue.jobs.size()==1&&AndroidUtilities.ui.isEmpty());DialogDiffQueue.queue.worker();
 check(p.itemInternals==visible&&p.events==0&&saved[0]==0);AndroidUtilities.ui.remove().run();
 check(!p.isCalculatingDiff&&p.itemInternals.size()==1200&&p.itemInternals.get(0).dialog.id==20&&saved[0]==1&&p.events>0);
 p.source(30,2);p.updateList(null);check(DialogDiffQueue.queue.jobs.size()==1);complete();
 check(p.itemInternals.size()==2&&!p.isCalculatingDiff); // Large removal also stays off UI.
 p.source(40,4);p.updateList(null);check(DialogDiffQueue.queue.jobs.isEmpty()&&!p.isCalculatingDiff&&p.itemInternals.size()==4);
 ''')


def test_scroll_anchor_tracks_chat_id_across_reordering_and_pinning(tmp_path):
    run_diff(tmp_path, """Probe p=new Probe();p.initial(8);p.source(0,8);
 var moved=p.source.remove(6);moved.pinned=true;p.source.add(0,moved);
 var removed=p.source.remove(3);check(removed.dialog.id==2);
 p.updateList(mapping->{
  check(mapping.applyAsInt(6)==0&&mapping.applyAsInt(2)==RecyclerView.NO_POSITION);
  check(mapping.applyAsInt(7)==6&&mapping.applyAsInt(30)==RecyclerView.NO_POSITION);
 });check(p.itemInternals.get(0).dialog.id==6);
 """)


def test_old_worker_cannot_replace_a_full_refresh_or_a_new_inflight_generation(tmp_path):
    run_diff(tmp_path, '''Probe p=new Probe();p.initial(80);p.source(10,90);int[]staleSaved={0};p.updateList(mapping->staleSaved[0]++);
 Runnable stale=DialogDiffQueue.queue.jobs.peek();
 p.source(100,85);p.notifyDataSetChanged();check(p.full==1&&!p.isCalculatingDiff&&p.itemInternals.get(0).dialog.id==100);
 check(DialogDiffQueue.queue.jobs.isEmpty());
 p.source(200,95);p.updateList(null);long current=p.diffGeneration;int events=p.events;
 stale.run();check(AndroidUtilities.ui.isEmpty());
 check(p.diffGeneration==current&&p.isCalculatingDiff&&p.itemInternals.get(0).dialog.id==100&&p.events==events&&staleSaved[0]==0);
 complete();check(!p.isCalculatingDiff&&p.itemInternals.get(0).dialog.id==200&&p.itemInternals.size()==95);
 ''')


def test_leaving_dialogs_cancels_queued_diffs_and_discards_results_already_on_ui(tmp_path):
    run_diff(tmp_path, '''Probe p=new Probe();p.initial(100);int[]saved={0};
 p.source(10,110);p.updateList(mapping->saved[0]++);
 p.source(20,120);p.updateList(mapping->saved[0]++);
 DialogDiffQueue.queue.worker();check(AndroidUtilities.ui.size()==1);
 p.cancelListUpdate();AndroidUtilities.ui.remove().run();
 check(p.events==0&&saved[0]==0&&p.itemInternals.get(0).dialog.id==0);
 check(!p.isCalculatingDiff&&!p.updateListPending&&DialogDiffQueue.queue.jobs.isEmpty());
 p.updateList(null);p.cancelListUpdate();
 check(DialogDiffQueue.queue.jobs.isEmpty()&&p.events==0);
 p.source(30,130);p.updateList(null);complete();
 check(!p.isCalculatingDiff&&p.itemInternals.get(0).dialog.id==30&&p.itemInternals.size()==130);
 ''')


def test_first_dialog_page_publishes_without_worker_and_rejected_diff_recovers(tmp_path):
    run_diff(tmp_path, '''Probe p=new Probe();p.source(40,100);p.updateList(null);
 check(p.itemInternals.size()==100&&p.events==1&&p.committedRowsRefreshes==1);
 check(!p.isCalculatingDiff&&DialogDiffQueue.queue.jobs.isEmpty());
 DialogDiffQueue.queue.accept=false;p.source(50,110);p.updateList(null);
 check(!p.isCalculatingDiff&&p.full==1&&p.itemInternals.get(0).dialog.id==50);
 DialogDiffQueue.queue.accept=true;p.source(60,130);p.updateList(null);
 check(p.committedRowsRefreshes==1);complete();
 check(p.committedRowsRefreshes==2&&p.itemInternals.get(0).dialog.id==60);
 ''')


def test_repeated_refresh_requests_coalesce_and_keep_latest_scroll_callback(tmp_path):
    run_diff(tmp_path, '''Probe p=new Probe();p.initial(100);int[]first={0},discarded={0},latest={0};
 p.source(10,110);p.updateList(mapping->first[0]++);p.source(20,120);p.updateList(mapping->discarded[0]++);
 p.source(30,130);p.updateList(mapping->latest[0]++);check(DialogDiffQueue.queue.jobs.size()==1);
 complete();check(first[0]==1&&discarded[0]==0&&latest[0]==0&&p.isCalculatingDiff&&DialogDiffQueue.queue.jobs.size()==1);
 complete();check(!p.isCalculatingDiff&&p.itemInternals.get(0).dialog.id==30&&p.itemInternals.size()==130&&latest[0]==1&&discarded[0]==0);
 ''')


def test_diff_identity_freezes_mutable_models_and_distinguishes_urls(tmp_path):
    run_diff(tmp_path, '''ItemInternal row=new ItemInternal(5);row.pinned=true;DiffItem frozen=new DiffItem(row);
 row.dialog.id=99;row.pinned=false;check(frozen.id==5&&frozen.pinned&&!frozen.matches(new DiffItem(row)));
 ItemInternal same=new ItemInternal(5);same.pinned=true;check(frozen.matches(new DiffItem(same)));
 ItemInternal url=new ItemInternal(0);url.viewType=VIEW_TYPE_ME_URL;url.recentMeUrl=new Url();url.recentMeUrl.url="before";
 DiffItem before=new DiffItem(url);url.recentMeUrl.url="after";check(before.url.equals("before")&&!before.matches(new DiffItem(url)));
 url.recentMeUrl.url=null;check(!before.matches(new DiffItem(url)));url.recentMeUrl=null;check(!before.matches(new DiffItem(url)));
 ItemInternal header=new ItemInternal(1);header.viewType=VIEW_TYPE_HEADER_2;DiffItem h=new DiffItem(header);header.dialog.isFolder=true;check(!h.matches(new DiffItem(header)));
 ''')


def test_reentrant_full_refresh_and_failed_scroll_save_release_diff_state(tmp_path):
    run_diff(tmp_path, '''Probe p=new Probe();p.initial(80);p.source(10,90);
 p.updateList(mapping->{p.source(200,100);p.notifyDataSetChanged();});complete();
 check(p.itemInternals.size()==100&&p.itemInternals.get(0).dialog.id==200&&!p.isCalculatingDiff&&p.events==0);
 p.source(20,110);p.updateList(mapping->{throw new IllegalStateException("scroll callback");});
 DialogDiffQueue.queue.worker();try{AndroidUtilities.ui.remove().run();throw new AssertionError();}catch(IllegalStateException expected){}
 check(!p.isCalculatingDiff);p.updateList(null);complete();check(p.itemInternals.size()==110&&!p.isCalculatingDiff);
 ''')


def test_resume_visits_visible_lists_once_and_preserves_targeted_chat_return(tmp_path):
    source = (JAVA / 'org/telegram/ui/DialogsActivity.java').read_text()
    actual = method(source, 'private void refreshDialogsOnResume()')
    probe(tmp_path, {'Probe.java': '''class View{static final int VISIBLE=0;}class BaseFragment{}class ChatActivity extends BaseFragment{long getDialogId(){return 42;}}
class Parent{BaseFragment last;BaseFragment getLastFragment(){return last;}}
class ViewPage{int visibility,refreshes;long id;int getVisibility(){return visibility;}void updateListAfterChat(long value){refreshes++;id=value;}}
public class Probe{ViewPage[]viewPages;Parent parentLayout=new Parent();int full;void updateVisibleRows(int mask){full++;}
 ACTUAL
 static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]a){Probe p=new Probe();
 p.refreshDialogsOnResume();check(p.full==0);p.viewPages=new ViewPage[]{new ViewPage(),new ViewPage()};
 p.refreshDialogsOnResume();check(p.full==1&&p.viewPages[0].refreshes==0&&p.viewPages[1].refreshes==0);
 p.parentLayout.last=new ChatActivity();p.viewPages[1].visibility=8;p.refreshDialogsOnResume();
 check(p.full==1&&p.viewPages[0].refreshes==1&&p.viewPages[0].id==42&&p.viewPages[1].refreshes==0);
 p.parentLayout.last=null;p.viewPages[0].visibility=8;p.refreshDialogsOnResume();check(p.full==1);
 }}'''.replace('ACTUAL', actual)})
    resume = method(source, 'public void onResume()')
    assert resume.count('refreshDialogsOnResume()') == 1


def test_unread_folder_batches_reload_and_cancels_it_when_leaving(tmp_path):
    source = (JAVA / 'org/telegram/ui/DialogsActivity.java').read_text()
    signatures = ('private void dispatchUnreadDialogsReload()', 'private void cancelUnreadDialogsReload()',
                  'private void reloadDialogsPages(boolean newMessage)', 'private void onDialogListReload(boolean newMessage)')
    fields = source[source.index('    private boolean unreadDialogsReloadPending,'):
                    source.index('    private void dispatchUnreadDialogsReload()')]
    actual = fields + '\n'.join(method(source, signature) for signature in signatures)
    probe(tmp_path, {'Probe.java': '''import java.util.ArrayDeque;
public class Probe {
 static class AndroidUtilities {
  static ArrayDeque<Runnable> queue=new ArrayDeque<>();
  static void runOnUIThread(Runnable callback,long delay){check(delay==160);queue.add(callback);}
  static void cancelRunOnUIThread(Runnable callback){queue.remove(callback);}
 }
 static final int DIALOGS_TYPE_FOLDER1=7,DIALOGS_TYPE_FOLDER2=8;
 static class ViewPage {int dialogsType=7;}
 static class View {static final int VISIBLE=0;int getVisibility(){return VISIBLE;}}
 static class Tabs extends View {int checks;void checkTabsCounter(){checks++;}}
 static class MessagesController {
  static final int DIALOG_FILTER_FLAG_EXCLUDE_READ=1;
  static class DialogFilter {int flags=1;}
  DialogFilter[] selectedDialogFilter={new DialogFilter(),new DialogFilter()};
 }
 static class Warmup {void request(){}}
 Warmup historyWarmup=new Warmup();
 MessagesController controller=new MessagesController();
 MessagesController getMessagesController(){return controller;}
 ViewPage[] viewPages={new ViewPage(),new ViewPage()};
 Tabs filterTabsView=new Tabs();
 boolean isFinished,isPaused,dialogsListFrozen,slowedReloadAfterDialogClick;
 int reloads;
 boolean sawNewMessage;
 void reloadViewPageDialogs(ViewPage page,boolean newMessage){reloads++;sawNewMessage|=newMessage;}
 ACTUAL
 static void check(boolean valid){if(!valid)throw new AssertionError();}
 public static void main(String[] args){
  Probe p=new Probe();p.slowedReloadAfterDialogClick=true;p.onDialogListReload(false);
  for(int i=0;i<10000;i++)p.onDialogListReload(i==0);
  check(AndroidUtilities.queue.size()==1&&p.reloads==0);
  AndroidUtilities.queue.remove().run();
  check(p.reloads==2&&p.filterTabsView.checks==1&&p.sawNewMessage);
  p.slowedReloadAfterDialogClick=true;p.onDialogListReload(true);p.isPaused=true;
  p.cancelUnreadDialogsReload();check(AndroidUtilities.queue.isEmpty()&&p.reloads==2);
  p.isPaused=false;p.onDialogListReload(false);check(p.reloads==4&&p.filterTabsView.checks==2);
  p.slowedReloadAfterDialogClick=true;p.viewPages[0].dialogsType=0;
  p.onDialogListReload(false);check(p.reloads==6&&AndroidUtilities.queue.isEmpty());
 }
}'''.replace('ACTUAL', actual)})


def test_edit_timer_sleeps_until_visible_countdown_and_rechecks_after_pause(tmp_path):
    source = (JAVA / 'org/telegram/ui/ChatActivity.java').read_text()
    fields = source[source.index('    private static final int EDIT_COUNTDOWN_SECONDS'):
                    source.index('    private void stopEditTimer()')]
    actual = fields + method(source, 'private void stopEditTimer()') + method(source, 'private void checkEditTimer()')
    assert 'cancelRunOnUIThread(editTimerCheck)' in method(source, 'public void onPause()')
    assert 'stopEditTimer()' in method(source, 'public void onFragmentDestroy()')
    probe(tmp_path, {'Probe.java': '''public class Probe {
 static class AndroidUtilities {
  static long delay;static Runnable pending;
  static void runOnUIThread(Runnable callback,long milliseconds){
   check(pending==null);delay=milliseconds;pending=callback;
  }
  static void cancelRunOnUIThread(Runnable callback){if(pending==callback)pending=null;}
  static String formatShortDuration(int seconds){return Integer.toString(seconds);}
  static void fire(){Runnable callback=pending;pending=null;callback.run();}
 }
 static class R {static class string {static int TimeToEdit=1,TimeToEditExpired=2;}}
 static class LocaleController {
  static String formatString(String key,int id,String... values){return values.length==0?key:values[0];}
 }
 static class User {boolean self;}
 static class Owner {int date;}
 static class MessageObject {
  boolean scheduled,unlimited;Owner messageOwner=new Owner();
  boolean canEditMessageAnytime(Object chat){return unlimited;}
 }
 static class Enter {
  MessageObject editing=new MessageObject();int expired;
  MessageObject getEditingMessageObject(){return editing;}
  void onEditTimeExpired(){expired++;}
 }
 static class Manager {int now;int getCurrentTime(){return now;}}
 static class Controller {int maxEditTime=1000;}
 static class SimpleTextView {String text;void setText(String value){text=value;}}
 static class Layout {SimpleTextView obj=new SimpleTextView();Layout current(){return this;}}
 boolean paused,isFinished;User currentUser;Object currentChat;
 Enter chatActivityEnterView=new Enter();Layout replyLayout=new Layout();
 Manager manager=new Manager();Controller controller=new Controller();
 Manager getConnectionsManager(){return manager;}
 Controller getMessagesController(){return controller;}
 ACTUAL
 static void check(boolean valid){if(!valid)throw new AssertionError();}
 public static void main(String[] args){
  Probe p=new Probe();MessageObject edit=p.chatActivityEnterView.editing;
  edit.unlimited=true;p.timedEditMessage=edit;p.checkEditTimer();
  check(AndroidUtilities.pending==null&&p.timedEditMessage==null);
  edit.unlimited=false;p.timedEditMessage=edit;p.checkEditTimer();
  check(AndroidUtilities.delay==1000000&&p.replyLayout.obj.text==null);
  p.manager.now=1000;AndroidUtilities.fire();
  check(AndroidUtilities.delay==1000&&"300".equals(p.replyLayout.obj.text));
  p.paused=true;AndroidUtilities.fire();check(AndroidUtilities.pending==null);
  p.paused=false;p.manager.now=1300;p.checkEditTimer();
  check(p.chatActivityEnterView.expired==1&&"TimeToEditExpired".equals(p.replyLayout.obj.text));
  p.timedEditMessage=edit;p.chatActivityEnterView.editing=new MessageObject();p.checkEditTimer();
  check(p.timedEditMessage==null&&AndroidUtilities.pending==null);
  p.manager.now=0;p.timedEditMessage=p.chatActivityEnterView.editing;p.checkEditTimer();
  p.stopEditTimer();check(p.timedEditMessage==null&&AndroidUtilities.pending==null);
 }
}'''.replace('ACTUAL', actual)})


def test_forwarding_hint_schedules_single_tick_and_stops_when_hidden(tmp_path):
    source = (JAVA / 'org/telegram/ui/ChatActivity.java').read_text()
    fields = source[source.index('    private boolean showTapForForwardingOptionsHit;'):
                    source.index('    private final Runnable forwardingHintTick')].strip()
    fields += '\n' + next(line for line in source.splitlines() if 'private final Runnable forwardingHintTick' in line)
    actual = fields + '\n' + method(source, 'private void scheduleForwardingHint()') + method(source, 'private void animateForwardingHint()')
    for signature in ('public void onPause()', 'public void onFragmentDestroy()'):
        assert 'cancelRunOnUIThread(forwardingHintTick)' in method(source, signature)
    probe(tmp_path, {'Probe.java': '''public class Probe {
 static class AndroidUtilities {
  static Runnable pending;
  static void runOnUIThread(Runnable callback,long delay){check(delay==6000&&pending==null);pending=callback;}
  static void cancelRunOnUIThread(Runnable callback){if(pending==callback)pending=null;}
  static void fire(){Runnable callback=pending;pending=null;callback.run();}
 }
 static class SimpleTextView {
  float alpha;int animations;
  void setPivotX(int value){}
  SimpleTextView animate(){return this;}
  SimpleTextView alpha(float value){alpha=value;return this;}
  SimpleTextView scaleX(float value){return this;}
  SimpleTextView scaleY(float value){return this;}
  SimpleTextView setDuration(int value){return this;}
  void start(){animations++;}
 }
 static class Layout {SimpleTextView obj=new SimpleTextView(),objHint=new SimpleTextView();Layout current(){return this;}}
 Layout replyLayout=new Layout();boolean paused,isFinished;
 ACTUAL
 static void check(boolean valid){if(!valid)throw new AssertionError();}
 public static void main(String[] args){
  Probe p=new Probe();p.forwardingHintEnabled=true;
  for(int i=0;i<10000;i++)p.scheduleForwardingHint();
  AndroidUtilities.fire();check(p.replyLayout.obj.alpha==0&&p.replyLayout.objHint.alpha==1);
  p.paused=true;AndroidUtilities.fire();check(AndroidUtilities.pending==null&&p.replyLayout.obj.animations==1);
  p.paused=false;p.scheduleForwardingHint();AndroidUtilities.fire();
  check(p.replyLayout.obj.alpha==1&&p.replyLayout.objHint.alpha==0);
  p.forwardingHintEnabled=false;AndroidUtilities.fire();check(AndroidUtilities.pending==null&&p.replyLayout.obj.animations==2);
 }
}'''.replace('ACTUAL', actual)})


def test_native_network_resumes_before_list_rebuild_and_fragment_resume():
    source = (JAVA / 'org/telegram/ui/LaunchActivity.java').read_text()
    resume = method(source, 'protected void onResume()')
    assert resume.index('ApplicationLoader.mainInterfacePaused = false') < resume.index('cm.setAppPaused(false, false)')
    assert resume.index('cm.setAppPaused(false, false)') < resume.index('executeOnAppEvent') < resume.index('sortDialogs(null)') < resume.index('actionBarLayout.onResume()')
    assert 'needsDialogsSortOnResume()' in resume
    assert resume.count('cm.setAppPaused(false, false)') == 1
    assert 'cm.resumeNetworkMaybe()' not in resume


def test_chat_pause_saves_a_matching_message_and_offset_and_preserves_unread_entry(tmp_path):
    source = (JAVA / 'org/telegram/ui/ChatActivity.java').read_text()
    save = method(source, 'if (!pausedOnLastMessage && !firstLoading && (!isThreadChat() || isTopic))')
    helpers = '\n'.join(method(source, signature) for signature in (
        'private boolean hasAttachedSponsoredMessage()',
        'private static MessageObject getScrollAnchorMessage(RecyclerView.ViewHolder holder)',
        'private boolean hasUnreadMessagesAfterScrollPosition(int position)',
    ))
    probe(tmp_path, {'Probe.java': '''import java.util.*;
public class Probe {
 static class SharedPreferences {
  final Map<String,Integer> values=new HashMap<>();
  class Editor {
   void putInt(String name,int value){values.put(name,value);}
   void remove(String name){values.remove(name);}
   void apply(){}
  }
  Editor edit(){return new Editor();}
 }
 static class MessagesController {
  static SharedPreferences settings;
  static SharedPreferences getNotificationsSettings(int account){return settings;}
 }
 static class NotificationsController {static String getSharedPrefKey(long dialog,long topic){return "key";}}
 static class BuildVars {static boolean LOGS_ENABLED;}
 static class FileLog {static void d(String value){}}
 static class MessageObject {
  int id;boolean sponsored,unread,out;
  static class Owner {boolean from_scheduled;}
  Owner messageOwner=new Owner();
  MessageObject(int id){this.id=id;}
  int getId(){return id;}
  boolean isSponsored(){return sponsored;}
  boolean isUnread(){return unread;}
  boolean isOut(){return out;}
 }
 static class View {
  int bottom;
  View(int bottom){this.bottom=bottom;}
  int getBottom(){return bottom;}
 }
 interface IMessageCell {MessageObject getMessageObject();}
 static class ChatMessageCell extends View implements IMessageCell {
  MessageObject message;
  ChatMessageCell(int bottom,MessageObject message){super(bottom);this.message=message;}
  public MessageObject getMessageObject(){return message;}
 }
 static class ChatActionCell extends ChatMessageCell {ChatActionCell(int b,MessageObject m){super(b,m);}}
 static class RecyclerView {
  static final int NO_POSITION=-1;
  static class ViewHolder {View itemView;ViewHolder(View view){itemView=view;}}
 }
 static class RecyclerListView extends RecyclerView {
  static class Holder extends ViewHolder {Holder(View item){super(item);}}
  List<View> children=new ArrayList<>();
  Map<Integer,Holder> positions=new HashMap<>();
  int getChildCount(){return children.size();}
  View getChildAt(int index){return children.get(index);}
  Holder findViewHolderForAdapterPosition(int position){return positions.get(position);}
  int getMeasuredHeight(){return 600;}
 }
 static class Layout {int position=2;int findFirstVisibleItemPosition(){return position;}}
 static class Adapter {int messagesStartRow;}
 boolean pausedOnLastMessage,firstLoading,isTopic;
 int currentAccount;long dialog_id;Object currentEncryptedChat;
 Layout chatLayoutManager=new Layout();
 RecyclerListView chatListView=new RecyclerListView();
 Adapter chatAdapter=new Adapter();
 List<MessageObject> messages=new ArrayList<>();
 boolean isThreadChat(){return false;}
 long getTopicId(){return 0;}
 void save(){SAVE}
 HELPERS
 static void check(boolean valid,String scenario){if(!valid)throw new AssertionError(scenario);}
 Probe(){MessagesController.settings=new SharedPreferences();}
 public static void main(String[] args){
  Probe p=new Probe();p.chatListView.positions.put(2,new RecyclerListView.Holder(new View(510)));
  p.chatListView.positions.put(3,new RecyclerListView.Holder(new ChatActionCell(460,new MessageObject(42))));
  p.save();
  check(MessagesController.settings.values.equals(Map.of("diditemkey",42,"diditemokey",-140)),"fallback row must provide both ID and offset");
  p=new Probe();MessageObject unread=new MessageObject(90);unread.unread=true;
  p.messages.add(new MessageObject(91));p.messages.add(unread);
  p.chatListView.positions.put(2,new RecyclerListView.Holder(new ChatMessageCell(480,new MessageObject(42))));
  p.save();check(MessagesController.settings.values.isEmpty(),"prefer the new unread position");
  p=new Probe();p.chatListView.children.add(new ChatMessageCell(100,null));
  p.currentEncryptedChat=new Object();
  p.chatListView.positions.put(2,new RecyclerListView.Holder(new ChatMessageCell(500,new MessageObject(-11))));
  p.save();check(MessagesController.settings.values.get("diditemkey")==-11,"skip an unbound cell and accept secret chat IDs");
  p=new Probe();MessageObject sponsored=new MessageObject(77);sponsored.sponsored=true;
  p.chatListView.children.add(new ChatMessageCell(100,sponsored));
  p.chatListView.positions.put(2,new RecyclerListView.Holder(new ChatMessageCell(480,new MessageObject(42))));
  p.save();check(MessagesController.settings.values.isEmpty(),"sponsored rows must not affect restored position");
  p=new Probe();MessageObject outgoing=new MessageObject(91);outgoing.unread=true;outgoing.out=true;
  p.messages.add(outgoing);
  p.chatListView.positions.put(2,new RecyclerListView.Holder(new ChatMessageCell(480,new MessageObject(42))));
  p.save();check(MessagesController.settings.values.get("diditemkey")==42,"ordinary outgoing unread state does not block restoration");
  outgoing.messageOwner.from_scheduled=true;
  p.save();check(MessagesController.settings.values.isEmpty(),"a sent scheduled message can take unread priority");
 }
}'''.replace('SAVE', save).replace('HELPERS', helpers)})


def test_return_anchor_uses_visible_row_and_keeps_its_pixel_offset(tmp_path):
    source = (JAVA/'org/telegram/ui/DialogsActivity.java').read_text()
    restore = method(source, 'private void restoreScrollAnchor(')
    probe(tmp_path, {'Probe.java': '''import java.util.function.IntUnaryOperator;

    public class Probe {
      static class RecyclerView {static final int NO_POSITION=-1,SCROLL_STATE_IDLE=0;}
      static class View {
        final int position,top,bottom;
        View(int position,int top,int bottom){this.position=position;this.top=top;this.bottom=bottom;}
        int getTop(){return top;}int getBottom(){return bottom;}
      }
      static class ListView {
        final View[] rows={new View(7,-68,12),new View(8,12,92),new View(9,92,172),new View(10,172,252)};
        int state;
        int getScrollState(){return state;}int getChildCount(){return rows.length;}View getChildAt(int i){return rows[i];}
        int getPaddingTop(){return 24;}int getPaddingBottom(){return 24;}int getHeight(){return 200;}
        int getChildAdapterPosition(View child){return child.position;}
      }
      static class Manager {
        int calls,position,offset;boolean pending;
        boolean hasPendingScrollPosition(){return pending;}
        void scrollToPositionWithOffset(int position,int offset){this.position=position;this.offset=offset;calls++;}
      }
      static final int DIALOGS_TYPE_DEFAULT=0,ARCHIVE_ITEM_STATE_HIDDEN=0;
      final ListView listView=new ListView();final Manager layoutManager=new Manager();
      int dialogsType,archivePullViewState;boolean hasStories;float scrollYOffset;
      boolean hasHiddenArchive(){return false;}
      RESTORE
      public static void main(String[]args){
        Probe p=new Probe();
        p.restoreScrollAnchor(position -> position==8 ? 12 : 11,true);
        if(p.layoutManager.position!=12 || p.layoutManager.offset!=-12)throw new AssertionError();
        p.restoreScrollAnchor(position -> position==8 ? RecyclerView.NO_POSITION : 11,true);
        if(p.layoutManager.position!=11 || p.layoutManager.offset!=68)throw new AssertionError();
        p.layoutManager.pending=true;p.restoreScrollAnchor(position -> 0,true);
        p.layoutManager.pending=false;p.listView.state=1;p.restoreScrollAnchor(position -> 0,true);
        if(p.layoutManager.calls!=2)throw new AssertionError();
      }
    }'''.replace('RESTORE', restore)})
