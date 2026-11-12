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
 public static class Adapter{public int events,full;void check(){if(!Thread.currentThread().getName().equals("main"))throw new AssertionError("worker touched adapter");}
 public void notifyDataSetChanged(){check();full++;}public void notifyItemRangeInserted(int p,int n){check();events++;}
 public void notifyItemRangeRemoved(int p,int n){check();events++;}public void notifyItemMoved(int a,int b){check();events++;}
 public void notifyItemRangeChanged(int p,int n,Object payload){check();events++;}}}''',
    }
    source = (JAVA / 'org/telegram/ui/Adapters/DialogsAdapter.java').read_text()
    actual = '\n'.join(method(source, signature) for signature in [
        'private static final class DiffItem', 'private DiffItem[] snapshotDiffItems(',
        'public void updateList(Runnable saveScrollPosition)', 'private void applyListDiff(', 'public void notifyDataSetChanged()'])
    host = '''import java.util.*;import androidx.recyclerview.widget.*;
class Queue{ArrayDeque<Runnable>jobs=new ArrayDeque<>();void postRunnable(Runnable r){jobs.add(r);}
 void worker()throws Exception{Runnable r=jobs.remove();Throwable[]error={null};Thread t=new Thread(()->{try{r.run();}catch(Throwable e){error[0]=e;}},"diff-worker");t.start();t.join();if(error[0]!=null)throw new AssertionError(error[0]);}}
class Utilities{static Queue searchQueue=new Queue();}class AndroidUtilities{static ArrayDeque<Runnable>ui=new ArrayDeque<>();static void runOnUIThread(Runnable r){ui.add(r);}}
class FileLog{static void e(Throwable e){throw new AssertionError(e);}}
public class Probe extends RecyclerView.Adapter{
 static final int VIEW_TYPE_DIALOG=0,VIEW_TYPE_HEADER_2=1,VIEW_TYPE_ME_URL=2,VIEW_TYPE_USER=3,VIEW_TYPE_EMPTY=4,VIEW_TYPE_LAST_EMPTY=5;
 static class Dialog{long id;boolean isFolder;Dialog(long n){id=n;}}static class Contact{long user_id;}static class Url{String url;}
 static class ItemInternal{int viewType,emptyType;boolean isFolder,isForumCell,pinned;Dialog dialog;Contact contact;Url recentMeUrl;
 ItemInternal(long id){dialog=new Dialog(id);}}
 ArrayList<ItemInternal>itemInternals=new ArrayList<>(),source=new ArrayList<>();boolean isCalculatingDiff,updateListPending;long diffGeneration;Runnable pendingScrollPosition;
 void updateItemList(){itemInternals.clear();itemInternals.addAll(source);}
 ACTUAL
 static void check(boolean value){if(!value)throw new AssertionError();}
 void source(int first,int count){source=new ArrayList<>();for(int i=0;i<count;i++)source.add(new ItemInternal(first+i));}
 void initial(int count){source(0,count);itemInternals=new ArrayList<>(source);}
 static void complete()throws Exception{Utilities.searchQueue.worker();check(AndroidUtilities.ui.size()==1);AndroidUtilities.ui.remove().run();}
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
 p.updateList(()->saved[0]++);check(p.isCalculatingDiff&&p.events==0&&p.itemInternals==visible&&saved[0]==0);
 check(Utilities.searchQueue.jobs.size()==1&&AndroidUtilities.ui.isEmpty());Utilities.searchQueue.worker();
 check(p.itemInternals==visible&&p.events==0&&saved[0]==0);AndroidUtilities.ui.remove().run();
 check(!p.isCalculatingDiff&&p.itemInternals.size()==1200&&p.itemInternals.get(0).dialog.id==20&&saved[0]==1&&p.events>0);
 p.source(30,2);p.updateList(null);check(Utilities.searchQueue.jobs.size()==1);complete();
 check(p.itemInternals.size()==2&&!p.isCalculatingDiff); // Large removal also stays off UI.
 p.source(40,4);p.updateList(null);check(Utilities.searchQueue.jobs.isEmpty()&&!p.isCalculatingDiff&&p.itemInternals.size()==4);
 ''')


def test_old_worker_cannot_replace_a_full_refresh_or_a_new_inflight_generation(tmp_path):
    run_diff(tmp_path, '''Probe p=new Probe();p.initial(80);p.source(10,90);int[]staleSaved={0};p.updateList(()->staleSaved[0]++);
 p.source(100,85);p.notifyDataSetChanged();check(p.full==1&&!p.isCalculatingDiff&&p.itemInternals.get(0).dialog.id==100);
 p.source(200,95);p.updateList(null);long current=p.diffGeneration;int events=p.events;
 complete();check(p.diffGeneration==current&&p.isCalculatingDiff&&p.itemInternals.get(0).dialog.id==100&&p.events==events&&staleSaved[0]==0);
 complete();check(!p.isCalculatingDiff&&p.itemInternals.get(0).dialog.id==200&&p.itemInternals.size()==95);
 ''')


def test_repeated_refresh_requests_coalesce_and_keep_latest_scroll_callback(tmp_path):
    run_diff(tmp_path, '''Probe p=new Probe();p.initial(100);int[]first={0},discarded={0},latest={0};
 p.source(10,110);p.updateList(()->first[0]++);p.source(20,120);p.updateList(()->discarded[0]++);
 p.source(30,130);p.updateList(()->latest[0]++);check(Utilities.searchQueue.jobs.size()==1);
 complete();check(first[0]==1&&discarded[0]==0&&latest[0]==0&&p.isCalculatingDiff&&Utilities.searchQueue.jobs.size()==1);
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
 p.updateList(()->{p.source(200,100);p.notifyDataSetChanged();});complete();
 check(p.itemInternals.size()==100&&p.itemInternals.get(0).dialog.id==200&&!p.isCalculatingDiff&&p.events==0);
 p.source(20,110);p.updateList(()->{throw new IllegalStateException("scroll callback");});
 Utilities.searchQueue.worker();try{AndroidUtilities.ui.remove().run();throw new AssertionError();}catch(IllegalStateException expected){}
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


def test_native_network_resumes_before_list_rebuild_and_fragment_resume():
    source = (JAVA / 'org/telegram/ui/LaunchActivity.java').read_text()
    resume = method(source, 'protected void onResume()')
    assert resume.index('ApplicationLoader.mainInterfacePaused = false') < resume.index('cm.setAppPaused(false, false)')
    assert resume.index('cm.resumeNetworkMaybe()') < resume.index('sortDialogs(null)') < resume.index('actionBarLayout.onResume()')
    assert resume.count('cm.setAppPaused(false, false)') == resume.count('cm.resumeNetworkMaybe()') == 1
