"""Execute bounded local-history preparation and cache ownership; not device FPS tests."""
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method


def test_warm_history_cache_is_single_use_revision_checked_and_bounded(tmp_path):
    probe(tmp_path, {'Probe.java': '''import app.flexygram.performance.WarmHistoryCache;
public class Probe {
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 public static void main(String[]args){
  WarmHistoryCache<String> c=new WarmHistoryCache<>();Object db=new Object();
  WarmHistoryCache.Revision r=new WarmHistoryCache.Revision(db,4,8);
  c.put(1,25,100,r,100,"one");check(c.take(1,15,101,r)==null);
  check(c.take(1,25,101,r).equals("one"));check(c.take(1,25,101,r)==null);
  c.put(1,25,100,r,100,"one");c.put(2,25,100,r,100,"two");c.put(3,25,100,r,100,"three");
  check(c.take(1,25,101,r)==null);check(c.take(2,25,101,r).equals("two"));check(c.take(3,25,101,r).equals("three"));
  c.put(1,25,100,r,100,"one");c.put(2,25,100,r,100,"two");
  check(c.take(1,25,101,new WarmHistoryCache.Revision(db,5,8))==null&&c.isEmpty());
  c.put(1,25,100,r,100,"one");check(c.take(1,25,101,new WarmHistoryCache.Revision(db,4,9))==null);
  c.put(1,25,100,r,100,"one");check(c.take(1,25,101,new WarmHistoryCache.Revision(new Object(),4,8))==null);
  c.put(1,25,100,r,100,"one");check(c.take(1,25,5100,r)==null&&c.isEmpty());
  c.put(1,25,100,r,100,"one");check(c.take(1,25,99,r)==null);
  c.put(1,25,100,r,300000,"huge");check(c.isEmpty());c.put(1,25,100,null,100,"invalid");check(c.isEmpty());
  c.put(1,25,100,r,262144,"one");c.put(2,25,100,r,262144,"two");c.put(1,25,101,r,262144,"new");
  check(c.take(1,25,102,r).equals("new"));c.clear();check(c.isEmpty());
 }
}'''}, [JAVA/'app/flexygram/performance/WarmHistoryCache.java'])


def warmup_hosts():
    return {
        'android/os/SystemClock.java': 'package android.os;public class SystemClock{public static long now=1000;public static long uptimeMillis(){return now;}}',
        'org/telegram/messenger/AndroidUtilities.java': '''package org.telegram.messenger;import java.util.*;public class AndroidUtilities{
 public static final ArrayList<Runnable> queue=new ArrayList<>();public static long delay;public static int posts;
 public static void runOnUIThread(Runnable r,long ms){if(queue.contains(r))throw new AssertionError("duplicate check");queue.add(r);delay=ms;posts++;}
 public static void cancelRunOnUIThread(Runnable r){queue.remove(r);}
 public static void fire(){Runnable r=queue.remove(0);r.run();}}''',
        'org/telegram/messenger/UserConfig.java': '''package org.telegram.messenger;public class UserConfig{public static UserConfig config=new UserConfig();public long owner=50;public boolean active=true;public static UserConfig getInstance(int n){return config;}public long getClientUserId(){return owner;}public boolean isClientActivated(){return active;}}''',
        'org/telegram/messenger/SharedConfig.java': 'package org.telegram.messenger;public class SharedConfig{public static boolean high=true;public static boolean deviceIsHigh(){return high;}}',
        'org/telegram/messenger/MessagesStorage.java': '''package org.telegram.messenger;import java.util.*;public class MessagesStorage{
 static MessagesStorage instance=new MessagesStorage();public static MessagesStorage getInstance(int a){return instance;}
 public static List<Runnable> completions=new ArrayList<>();public static List<Long> dialogs=new ArrayList<>();public static List<Integer>counts=new ArrayList<>();public static int cancels;
 public Runnable warmChatHistory(long id,int count,Runnable done){dialogs.add(id);counts.add(count);completions.add(done);return ()->cancels++;}
 public static void complete(){completions.remove(0).run();}}''',
    }


def test_idle_preparation_coalesces_events_caps_reads_and_ignores_cancelled_completions(tmp_path):
    files=warmup_hosts()
    files['Probe.java']='''import app.flexygram.performance.ChatHistoryWarmup;import org.telegram.messenger.*;
public class Probe implements ChatHistoryWarmup.Host{
 boolean ready=true;int account;public boolean canWarm(){return ready;}public int account(){return account;}public long[]candidates(){return new long[]{100,200,300};}
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();ChatHistoryWarmup w=new ChatHistoryWarmup(p);
  for(int i=0;i<10000;i++)w.request();check(AndroidUtilities.posts==1&&AndroidUtilities.delay==350);
  AndroidUtilities.fire();check(MessagesStorage.dialogs.size()==1);for(int i=0;i<10000;i++)w.request();check(AndroidUtilities.posts==1);
  MessagesStorage.complete();check(MessagesStorage.dialogs.size()==2);MessagesStorage.complete();check(MessagesStorage.completions.isEmpty());
  w.request();check(AndroidUtilities.delay==3000);w.cancel();check(AndroidUtilities.queue.isEmpty());
  w.request();AndroidUtilities.fire();Runnable old=MessagesStorage.completions.remove(0);w.cancel();check(MessagesStorage.cancels==1);
  w.request();AndroidUtilities.fire();int before=MessagesStorage.dialogs.size();old.run();check(MessagesStorage.dialogs.size()==before);
  p.ready=false;MessagesStorage.complete();check(MessagesStorage.dialogs.size()==before);
  p.ready=true;SharedConfig.high=false;w.request();AndroidUtilities.fire();check(MessagesStorage.counts.get(MessagesStorage.counts.size()-1)==15);
  UserConfig.config.owner++;before=MessagesStorage.dialogs.size();MessagesStorage.complete();check(MessagesStorage.dialogs.size()==before);
  w.request();AndroidUtilities.fire();p.account=1;before=MessagesStorage.dialogs.size();MessagesStorage.complete();check(MessagesStorage.dialogs.size()==before);
  w.cancel();p.ready=false;w.request();check(AndroidUtilities.queue.isEmpty());
  p.ready=true;UserConfig.config.active=false;w.request();AndroidUtilities.fire();check(MessagesStorage.completions.isEmpty());
 }
}'''
    probe(tmp_path,files,[JAVA/'app/flexygram/performance/ChatHistoryWarmup.java'])


def test_visible_candidates_prioritize_unmuted_unread_and_exclude_special_rows(tmp_path):
    source=(JAVA/'org/telegram/ui/DialogsActivity.java').read_text()
    candidates=method(source,'private long[] visibleHistoryCandidates()')
    probe(tmp_path,{'Probe.java':'''import java.util.*;
public class Probe{
 static class View{int getBottom(){return 40;}int getTop(){return 0;}}
 static class DialogCell extends View{long id;DialogCell(long id){this.id=id;}long getDialogId(){return id;}}
 static class RecyclerListView{View[]children;int getChildCount(){return children.length;}View getChildAt(int n){return children[n];}int getPaddingTop(){return 0;}int getHeight(){return 100;}int getPaddingBottom(){return 0;}}
 static class Page{RecyclerListView listView=new RecyclerListView();}Page[]viewPages={new Page()};
 static class TLRPC{static class Dialog{int top_message=5,unread_count;}static class Chat{boolean forum;}}
 static class DialogObject{static boolean isUserDialog(long id){return id>0&&id<1000;}static boolean isChatDialog(long id){return id<0;}}
 static class ChatObject{static boolean isMonoForum(TLRPC.Chat c){return c!=null&&c.forum;}}
 static class Controller{Map<Long,TLRPC.Dialog>dialogs_dict=new HashMap<>();Set<Long>muted=new HashSet<>();TLRPC.Chat getChat(long n){TLRPC.Chat c=new TLRPC.Chat();c.forum=n==4;return c;}boolean isForum(long id){return id==7;}boolean isDialogMuted(long id,int thread){return muted.contains(id);}}
 Controller controller=new Controller();Controller getMessagesController(){return controller;}
 CANDIDATES
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();long[]rows={1,2,3,-4,5,6,7,2000};
  for(long id:rows)p.controller.dialogs_dict.put(id,new TLRPC.Dialog());
  p.controller.muted.add(1L);p.controller.muted.add(3L);p.controller.dialogs_dict.get(3L).unread_count=5;p.controller.dialogs_dict.get(5L).unread_count=1;p.controller.dialogs_dict.get(6L).top_message=0;
  p.viewPages[0].listView.children=new View[]{new View(),new DialogCell(1),new DialogCell(2),new DialogCell(3),new DialogCell(-4),new DialogCell(5),new DialogCell(6),new DialogCell(7),new DialogCell(2000),new DialogCell(5)};
  long[]ids=p.visibleHistoryCandidates();check(Arrays.equals(ids,new long[]{5,2}));
  p.viewPages[0].listView.children=new View[]{new View()};check(p.visibleHistoryCandidates().length==0);
 }
}'''.replace('CANDIDATES',candidates)})
