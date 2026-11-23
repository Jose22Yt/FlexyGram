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
  static Runnable queued;static long delay;static int posts,cancels;
  static void cancelRunOnUIThread(Runnable r){cancels++;if(queued==r)queued=null;}
  static void runOnUIThread(Runnable r,long d){posts++;if(queued!=null)throw new AssertionError("duplicate queued scan");queued=r;delay=d;}
  static void fire(){Runnable r=queued;queued=null;if(r!=null)r.run();}
 }
 RecyclerView chatListView=new RecyclerView();long lastTranslationCheck;boolean paused,isFinished,translationCheckDeferred;int scans;
 ACTIVE
 SCHEDULE
 Runnable checkTranslationRunnable=()->{PREFIX translationCheckDeferred=false;lastTranslationCheck=System.currentTimeMillis();scans++;};
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 public static void main(String[] args) {
  Probe p=new Probe();
  for(int state:new int[]{1,2}) {
   p.chatListView.state=state;p.lastTranslationCheck=0;
   int before=AndroidUtilities.posts,cancels=AndroidUtilities.cancels;
   for(int i=0;i<5000;i++)p.checkTranslation(false);
   for(int i=0;i<10;i++)AndroidUtilities.fire();
   check(p.scans==0&&AndroidUtilities.queued==null&&AndroidUtilities.posts==before);
   check(AndroidUtilities.cancels-cancels<=1);
  }
  p.chatListView.state=0;p.checkTranslation(false);AndroidUtilities.fire();check(p.scans==1&&AndroidUtilities.queued==null);
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


def test_chat_pagination_only_posts_at_edges_and_keeps_native_loading_rules(tmp_path):
    source = (JAVA/'org/telegram/ui/ChatActivity.java').read_text()
    load = method(source, 'private void checkScrollForLoad(boolean scroll)')
    pending = source[source.index('    private boolean pendingOlderHistoryLoad;'):source.index('    private void processSelectedAttach(')]
    probe(tmp_path, {'Probe.java': '''import java.util.*;
public class Probe {
 static class RecyclerListView {static final int NO_POSITION=-1;}
 static class AndroidUtilities {
  static List<Runnable> queue=new ArrayList<>();static int posts;
  static void runOnUIThread(Runnable r){posts++;queue.add(r);}
  static void cancelRunOnUIThread(Runnable r){queue.remove(r);}
  static void fire(){List<Runnable> copy=new ArrayList<>(queue);queue.clear();for(Runnable r:copy)r.run();}
 }
 static class ListView {int first=40,count=10,positionReads;int getChildCount(){return count;}int getChildAt(int i){return first+i;}int getChildAdapterPosition(int p){positionReads++;return p;}}
 static class Adapter {boolean isFrozen,isFiltered;int loadingUpRow=-1;int getItemCount(){return 100;}}
 static class Controller {List<Object[]> calls=new ArrayList<>();void loadMessages(Object...args){calls.add(args);}}
 static class Media {int calls;void loadMoreSearchMessages(boolean b){calls++;}}
 Object chatLayoutManager=new Object();boolean paused,waitingForGetDifference,isFinished,loading,loadingForward,isTopic;
 ListView chatListView=new ListView();Adapter chatAdapter=new Adapter();Controller controller=new Controller();Media media=new Media();
 static final int MODE_SEARCH=99;int chatMode,lastLoadIndex,classGuid,threadMessageId,replyMaxReadId,searchLoads;
 long dialog_id=100,mergeDialogId;int[] maxMessageId={8,9},minMessageId={3,4},minDate={1,2},maxDate={5,6};
 boolean[] endReached={false,false},forwardEndReached={false,false},cacheEndReached={false,false};
 List<Integer> waitingForLoad=new ArrayList<>(),messagesByDays=new ArrayList<>();
 Controller getMessagesController(){return controller;}Media getMediaDataController(){return media;}
 void loadMoreSearchResults(){searchLoads++;}
 LOAD
 PENDING
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args){
  Probe p=new Probe();
  for(int i=0;i<10000;i++)p.checkScrollForLoad(true);
  check(AndroidUtilities.posts==0&&p.controller.calls.isEmpty());
  p.chatListView.first=70;p.checkScrollForLoad(false);check(AndroidUtilities.queue.isEmpty());
  p.checkScrollForLoad(true);AndroidUtilities.fire();check(p.loading&&p.controller.calls.size()==1);
  for(int i=0;i<10000;i++)p.checkScrollForLoad(true);check(AndroidUtilities.queue.isEmpty());
  p.loading=false;p.endReached[0]=true;p.checkScrollForLoad(true);check(AndroidUtilities.queue.isEmpty());
  p.mergeDialogId=200;p.checkScrollForLoad(true);AndroidUtilities.fire();check(p.controller.calls.size()==2&&p.controller.calls.get(1)[0].equals(200L));
  p.loading=false;p.endReached[1]=true;p.checkScrollForLoad(true);check(AndroidUtilities.queue.isEmpty());
  p.chatListView.first=0;p.checkScrollForLoad(true);AndroidUtilities.fire();check(p.loadingForward&&p.controller.calls.size()==3&&p.controller.calls.get(2)[9].equals(1));
  p.loadingForward=false;p.forwardEndReached[0]=true;p.forwardEndReached[1]=true;p.checkScrollForLoad(true);check(AndroidUtilities.queue.isEmpty());
  p.forwardEndReached[0]=false;
  for(int state=0;state<4;state++){
   p.checkScrollForLoad(true);check(AndroidUtilities.queue.size()==1);
   p.paused=state==0;p.isFinished=state==1;p.chatAdapter.isFrozen=state==2;p.waitingForGetDifference=state==3;
   AndroidUtilities.fire();check(p.controller.calls.size()==3&&!p.loadingForward);
   p.paused=p.isFinished=p.chatAdapter.isFrozen=p.waitingForGetDifference=false;
  }
  p.checkScrollForLoad(true);AndroidUtilities.fire();check(p.controller.calls.size()==4&&p.loadingForward);
  p.chatAdapter.isFiltered=true;p.chatAdapter.loadingUpRow=5;p.checkScrollForLoad(true);check(p.media.calls==1&&AndroidUtilities.queue.isEmpty());
  p.chatAdapter.isFiltered=false;p.chatMode=MODE_SEARCH;p.endReached[0]=false;p.chatListView.first=90;
  p.checkScrollForLoad(true);check(p.searchLoads==1&&p.loading&&AndroidUtilities.queue.isEmpty());
  Probe full=new Probe();full.endReached[0]=full.forwardEndReached[0]=true;
  for(int i=0;i<10000;i++)full.checkScrollForLoad(true);
  check(full.chatListView.positionReads==0&&AndroidUtilities.queue.isEmpty());
  Probe rapid=new Probe();rapid.chatListView.first=80;
  for(int i=0;i<10000;i++)rapid.checkScrollForLoad(true);
  rapid.chatListView.first=0;rapid.checkScrollForLoad(true);
  check(AndroidUtilities.queue.size()==1);
  AndroidUtilities.fire();check(rapid.controller.calls.size()==2&&rapid.loading&&rapid.loadingForward);
  rapid.loadingForward=false;rapid.checkScrollForLoad(true);
  check(AndroidUtilities.queue.size()==1);
  rapid.cancelPendingScrollHistory();
  check(AndroidUtilities.queue.isEmpty());
  rapid.checkScrollForLoad(true);AndroidUtilities.fire();check(rapid.controller.calls.size()==3);
 }
}'''.replace('LOAD',load).replace('PENDING',pending)})


def test_scroll_hints_use_cancellable_identity_and_stop_on_leave(tmp_path):
    source = (JAVA/'org/telegram/ui/ChatActivity.java').read_text()
    start = source.index('private final Runnable checkBotMessageHintRunnable')
    fields = source[start:source.index('private void checkBotMessageHint()', start)]
    scroll = source[source.index('public void onScrolled(RecyclerView recyclerView, int dx, int dy)'):]
    schedule = method(source, 'private void scheduleScrollHintChecks()')
    idle_guard = method(scroll, 'if (recyclerView.getScrollState() == RecyclerView.SCROLL_STATE_IDLE)')
    assert 'scheduleScrollHintChecks();' in idle_guard
    state = method(source[source.index(schedule):], 'public void onScrollStateChanged(')
    assert 'scheduleScrollHintChecks();' in method(state, 'if (newState == RecyclerView.SCROLL_STATE_IDLE)')
    for callback in ('checkSavedMessagesTagHint', 'checkBotMessageHint'):
        assert f'ChatActivity.this::{callback}' not in source
        assert 'paused || chatListView == null || isTranslationScrollActive()' in method(source, f'private void {callback}()')
    for lifecycle in ('public void onPause()', 'public void onFragmentDestroy()'):
        assert 'cancelScrollHintChecks();' in method(source,lifecycle)
    probe(tmp_path, {'Probe.java': '''import java.util.*;
public class Probe {
 static class AndroidUtilities {
  static List<Runnable> queue=new ArrayList<>();
  static int posts;
  static void cancelRunOnUIThread(Runnable r){queue.removeIf(item->item==r);}
  static void runOnUIThread(Runnable r,long delay){posts++;queue.add(r);}
  static void fire(){List<Runnable> copy=new ArrayList<>(queue);queue.clear();for(Runnable r:copy)r.run();}
 }
 static class Hint {boolean shown(){return false;}void hide(){}}
 Hint savedMessagesTagHint=new Hint(),botMessageHint;
 boolean savedMessagesTagHintShown,paused,isFinished;int tagChecks,botChecks;
 static class RecyclerView {
  static final int SCROLL_STATE_IDLE=0;
  int state;int getScrollState(){return state;}
 }
 RecyclerView recyclerView=new RecyclerView();
 void checkSavedMessagesTagHint(){tagChecks++;}void checkBotMessageHint(){botChecks++;}
 FIELDS
 SCHEDULE
 void onScroll(){IDLE_GUARD}
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args){
  Probe p=new Probe();
  for(int state:new int[]{1,2}){
   p.recyclerView.state=state;
   for(int i=0;i<10000;i++)p.onScroll();
   check(AndroidUtilities.posts==0&&AndroidUtilities.queue.isEmpty());
  }
  p.recyclerView.state=0;p.onScroll();
  check(AndroidUtilities.posts==2&&AndroidUtilities.queue.size()==2);AndroidUtilities.fire();check(p.tagChecks==1&&p.botChecks==1);
  p.onScroll();p.cancelScrollHintChecks();AndroidUtilities.fire();check(p.tagChecks==1&&p.botChecks==1);
 }
}'''.replace('FIELDS',fields).replace('SCHEDULE',schedule).replace('IDLE_GUARD',idle_guard)})


def test_dialog_scroll_reuses_range_and_skips_inflight_folder_loads(tmp_path):
    source = (JAVA/'org/telegram/ui/DialogsActivity.java').read_text()
    start = source.index('viewPage.dialogsItemAnimator.onListScroll(-dy);')
    scan = source[source.index('int firstVisiblePosition', start):source.index('invalidateScrollY = true;', start)]
    load = method(source, 'private void checkListLoad(ViewPage viewPage, int firstVisibleItem, int lastVisibleItem, boolean loadAll)')
    probe(tmp_path, {'Probe.java': '''import java.util.*;
public class Probe {
 static class View {final int position;View(int position){this.position=position;}}
 static class RecyclerView {static final int NO_POSITION=-1;int visits;int[] positions={-1,70,71,72,73,74,75,76,77,78,79};int getChildCount(){return positions.length;}View getChildAt(int i){visits++;return new View(positions[i]);}int getChildAdapterPosition(View v){return v.position;}}
 RecyclerView recyclerView=new RecyclerView();Object viewPage=new Object();int first,last,loads;View firstChild;
 void checkListLoad(Object page,int first,int last){this.first=first;this.last=last;}
 void scroll(){SCAN firstChild=firstVisibleChild;}
 void run(boolean load,boolean loadArchived,int folderId){GUARDS if(load)loads++;if(loadArchived)loads++;}
 static class Controller {boolean[] loading={false,false};boolean isLoadingDialogs(int folder){return loading[folder];}}
 Controller controller=new Controller();Controller getMessagesController(){return controller;}
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args){Probe p=new Probe();p.scroll();check(p.first==70&&p.last==79&&p.firstChild.position==70&&p.recyclerView.visits==11);
  p.controller.loading[0]=true;p.controller.loading[1]=true;
  for(int i=0;i<10000;i++)p.run(true,true,0);check(p.loads==0);
  p.controller.loading[1]=false;p.run(true,true,0);check(p.loads==1);
  p.controller.loading[0]=false;p.run(true,false,0);check(p.loads==2);
  p.recyclerView.positions=new int[]{-1,-1};p.scroll();check(p.first==-1&&p.last==-1&&p.firstChild==null);
 }
}'''.replace('SCAN',scan).replace('GUARDS',load[load.index('load &='):load.index('if (load || loadArchived)')])})
def test_empty_dialog_filter_loads_cache_then_server_and_respects_archive_setting(tmp_path):
    source = (JAVA/'org/telegram/ui/DialogsActivity.java').read_text()
    load = method(source, 'private void checkListLoad(ViewPage viewPage, int firstVisibleItem, int lastVisibleItem, boolean loadAll)')
    probe(tmp_path, {'Probe.java': '''import java.util.*;
public class Probe {
 static final int DIALOGS_TYPE_FOLDER1=7,DIALOGS_TYPE_FOLDER2=8;
 static class View {static final int VISIBLE=0;int getVisibility(){return VISIBLE;}}
 static class Tabs extends View {boolean isAnimatingIndicator(){return false;}}
 static class RecyclerView {
  static final int NO_POSITION=-1;
  static class ViewHolder {int getItemViewType(){return 0;}}
  ViewHolder findViewHolderForAdapterPosition(int value){return null;}
 }
 static class ViewPage {int dialogsType=7,selectedType;RecyclerView listView=new RecyclerView();}
 static class AndroidUtilities {static void runOnUIThread(Runnable work){work.run();}}
 static class MessagesController {
  static final int DIALOG_FILTER_FLAG_EXCLUDE_ARCHIVED=1;
  static class DialogFilter {int flags;}
  final ArrayList<DialogFilter> filters=new ArrayList<>(List.of(new DialogFilter()));
  final boolean[] cacheEnd={false,false},serverEnd={false,false},loading={false,false};
  final List<String> loads=new ArrayList<>();int dialogFiltersChatsLimitPremium,dialogFiltersChatsLimitDefault;
  ArrayList<DialogFilter> getDialogFilters(){return filters;}
  boolean isDialogsEndReached(int folder){return cacheEnd[folder];}
  boolean isServerDialogsEndReached(int folder){return serverEnd[folder];}
  boolean isLoadingDialogs(int folder){return loading[folder];}
  void loadDialogs(int folder,int offset,int count,boolean cache){loads.add(folder+":"+cache);}
 }
 static class UserConfig {boolean isPremium(){return false;}}
 final MessagesController controller=new MessagesController();
 MessagesController getMessagesController(){return controller;} UserConfig getUserConfig(){return new UserConfig();}
 boolean tabsAnimationInProgress,startedTracking,floatingForceVisible,dialogsListFrozen; int folderId,currentAccount;
 Tabs filterTabsView;void hideFloatingButton(boolean value){}
 int getPaginationDialogCount(ViewPage page){return 300;}
 List<Integer> getDialogsArray(int a,int type,int folder,boolean frozen){return Collections.nCopies(300,0);}
 LOAD
 static void check(boolean valid){if(!valid)throw new AssertionError();}
 public static void main(String[] args){
  Probe p=new Probe();ViewPage f=new ViewPage();p.checkListLoad(f,-1,-1,false);
  check(p.controller.loads.equals(List.of("0:true","1:true")));p.controller.loads.clear();
  p.controller.filters.get(0).flags=1;p.controller.cacheEnd[0]=true;
  p.checkListLoad(f,-1,-1,false);check(p.controller.loads.equals(List.of("0:false")));p.controller.loads.clear();
  p.controller.serverEnd[0]=true;p.checkListLoad(f,-1,-1,false);check(p.controller.loads.isEmpty());
  f.dialogsType=0;p.controller.cacheEnd[0]=p.controller.serverEnd[0]=false;
  p.checkListLoad(f,-1,-1,false);check(p.controller.loads.isEmpty());
 }
}'''.replace('LOAD', load)})


def test_selector_pagination_uses_the_adapter_snapshot_without_rebuilding_the_list(tmp_path):
    source = (JAVA/'org/telegram/ui/DialogsActivity.java').read_text()
    count = method(source, 'private int getPaginationDialogCount(ViewPage page)')
    probe(tmp_path, {'Probe.java': '''
import java.util.*;
public class Probe {
 static final int DIALOGS_TYPE_ADD_USERS_TO=2,DIALOGS_TYPE_BOT_REQUEST_PEER=15;
 static class Adapter {int getDialogsCount(){return 27;}}
 static class ViewPage {int dialogsType;Adapter dialogsAdapter=new Adapter();}
 int currentAccount,folderId,controllerReads;boolean dialogsListFrozen;
 List<Integer> getDialogsArray(int account,int type,int folder,boolean frozen){controllerReads++;return List.of(1,2,3);}
 COUNT
 public static void main(String[]args){
  Probe p=new Probe();ViewPage page=new ViewPage();
  for(int type:new int[]{DIALOGS_TYPE_ADD_USERS_TO,DIALOGS_TYPE_BOT_REQUEST_PEER}){
   page.dialogsType=type;
   for(int i=0;i<10000;i++)if(p.getPaginationDialogCount(page)!=27)throw new AssertionError();
  }
  if(p.controllerReads!=0)throw new AssertionError();
  page.dialogsType=0;
  if(p.getPaginationDialogCount(page)!=3||p.controllerReads!=1)throw new AssertionError();
 }
}'''.replace('COUNT',count)})
