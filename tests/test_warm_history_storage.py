"""Run the real storage adapter/snapshot delivery with counted storage and stage queues."""
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method


def storage_probe(tmp_path, body):
    source=(JAVA/'org/telegram/messenger/MessagesStorage.java').read_text()
    fields=source[source.index('    private interface WarmHistoryDelivery'):source.index('    public Runnable getMessagesInternal(')]
    fields=fields.replace('    public static void trimWarmHistories() '+method(source,'public static void trimWarmHistories()').split('public static void trimWarmHistories() ',1)[1], '')
    # Keep the real immutable metadata closure and native delivery call; only the SQL reader is a double.
    suffix=source[source.index('        int finalMessagesCount = scheduled ?'):source.index('        //}',source.index('        int finalMessagesCount = scheduled ?'))]
    wrapper=method(source,'public Runnable getMessagesInternal(')
    get=method(source,'public void getMessages(long dialogId, long mergeDialogId, boolean loadInfo, int count,')
    files={
        'android/os/SystemClock.java':'package android.os;public class SystemClock{public static long now=1000;public static long uptimeMillis(){return now;}}',
        'Probe.java':'''import java.util.*;import android.os.SystemClock;
public class Probe {
 static final int LOAD_FROM_UNREAD=2;
 static class Queue {
  List<Runnable> tasks=new ArrayList<>();Map<Runnable,Long> due=new IdentityHashMap<>();boolean reject;
  boolean postRunnable(Runnable r){return postRunnable(r,0);}
  boolean postRunnable(Runnable r,long delay){if(reject)return false;tasks.add(r);due.put(r,SystemClock.now+delay);return true;}
  void cancelRunnable(Runnable r){tasks.removeIf(x->x==r);due.remove(r);}
  void fire(){Runnable first=tasks.get(0);for(Runnable r:tasks)if(due.get(r)<due.get(first))first=r;tasks.remove(first);due.remove(first);first.run();}
 }
 static class AndroidUtilities {static Queue ui=new Queue();static void runOnUIThread(Runnable r){ui.postRunnable(r);}}
 static class Utilities{static Queue stageQueue=new Queue();}
 static class FileLog{static void e(Exception e){}}
 static class Timer{static class Task{}static Task start(Timer t,String name){return new Task();}static void done(Task t){}}
 static class DialogObject{static boolean isUserDialog(long id){return id>0;}static boolean isChatDialog(long id){return id<0;}}
 static class SQLiteCursor{long value;SQLiteCursor(long v){value=v;}boolean next(){return true;}long longValue(int col){return value;}void dispose(){}}
 static class Database{long changes=10,external=1;SQLiteCursor queryFinalized(String sql){return new SQLiteCursor(sql.contains("total_changes")?changes:external);}}
 static class Config{long owner=50;boolean active=true;long getClientUserId(){return owner;}boolean isClientActivated(){return active;}}
 static class Res{List<Integer>messages=new ArrayList<>(List.of(5,6));int getObjectSize(){return 100;}}
 static class Controller{int deliveries;Object[] last;void processLoadedMessages(Object...args){deliveries++;last=args;}}
 Queue storageQueue=new Queue();Database database=new Database();Config config=new Config();Controller controller=new Controller();
 Config getUserConfig(){return config;}Controller getMessagesController(){return controller;}
 int sqlReads;boolean mutateDuringRead,missingHoles;
 FIELDS
 WRAPPER
 private Runnable getMessagesInternal(long dialogId,long mergeDialogId,int count,int max_id,int offset_date,int minDate,int classGuid,int load_type,int mode,long threadMessageId,int loadIndex,boolean processMessages,boolean isTopic,Timer loaderLogger,WarmHistoryReceiver warmReceiver){
  sqlReads++;if(missingHoles&&warmReceiver!=null)return null;if(mutateDuringRead)database.changes++;
  Res res=new Res();boolean scheduled=false;int messagesCount=2,countQueryFinal=count,maxIdOverrideFinal=0,minUnreadIdFinal=5,lastMessageIdFinal=6,countUnreadFinal=2,maxUnreadDateFinal=12,mentionsUnreadFinal=1;boolean isEndFinal=true,queryFromServerFinal=false;
  SUFFIX
 }
 GET
 void open(long did,int count,int max,int mode){getMessages(did,0,false,count,max,0,0,123,2,mode,0,77,true,false,null);while(Utilities.stageQueue.tasks.isEmpty())storageQueue.fire();Utilities.stageQueue.fire();}
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 public static void main(String[]args){BODY}
}'''.replace('FIELDS',fields).replace('WRAPPER',wrapper).replace('SUFFIX',suffix).replace('GET',get).replace('BODY',body)
    }
    probe(tmp_path,files,[JAVA/'app/flexygram/performance/WarmHistoryCache.java'])


def test_prepared_history_uses_native_delivery_once_with_the_opening_guid_and_index(tmp_path):
    storage_probe(tmp_path,'''Probe p=new Probe();int[]done={0};p.warmChatHistory(100,25,()->done[0]++);p.storageQueue.fire();AndroidUtilities.ui.fire();
 check(p.sqlReads==1&&p.controller.deliveries==0&&done[0]==1);
 p.open(100,25,0,0);check(p.sqlReads==1&&p.controller.deliveries==1);
 check(p.controller.last[8].equals(123)&&p.controller.last[17].equals(77)&&p.controller.last[7].equals(true));
 p.open(100,25,0,0);check(p.sqlReads==2&&p.controller.deliveries==2);
 ''')


def test_mutations_account_changes_and_special_loads_use_the_fresh_native_reader(tmp_path):
    storage_probe(tmp_path,'''Probe p=new Probe();
 for(int reason=0;reason<6;reason++){
  p.warmChatHistory(100,25,()->{});p.storageQueue.fire();AndroidUtilities.ui.fire();
  int before=p.sqlReads;
  if(reason==0)p.database.changes++;if(reason==1)p.database.external++;if(reason==2)p.config.owner++;
  if(reason==3)SystemClock.now+=5000;
  p.open(100,reason==4?15:25,reason==5?99:0,0);check(p.sqlReads==before+1);
  p.clearWarmHistoryInternal();
 }
 p.mutateDuringRead=true;p.warmChatHistory(100,25,()->{});p.storageQueue.fire();AndroidUtilities.ui.fire();check(p.warmHistory.isEmpty());
 p.mutateDuringRead=false;p.missingHoles=true;p.warmChatHistory(100,25,()->{});p.storageQueue.fire();AndroidUtilities.ui.fire();check(p.warmHistory.isEmpty());
 ''')


def test_cancellation_rejection_expiry_and_cleanup_leave_no_preparation_work(tmp_path):
    storage_probe(tmp_path,'''Probe p=new Probe();int[]done={0};Runnable cancel=p.warmChatHistory(100,25,()->done[0]++);cancel.run();check(p.storageQueue.tasks.isEmpty()&&p.sqlReads==0);
 p.storageQueue.reject=true;p.warmChatHistory(100,25,()->done[0]++);AndroidUtilities.ui.fire();check(done[0]==1&&p.sqlReads==0);
 p.storageQueue.reject=false;p.warmChatHistory(100,25,()->done[0]++);p.storageQueue.fire();AndroidUtilities.ui.fire();
 check(p.storageQueue.tasks.size()==1);SystemClock.now+=5000;p.storageQueue.fire();check(p.warmHistory.isEmpty()&&p.storageQueue.tasks.isEmpty());
 p.warmChatHistory(100,25,()->{});p.storageQueue.fire();AndroidUtilities.ui.fire();p.clearWarmHistoryInternal();check(p.warmHistory.isEmpty()&&p.storageQueue.tasks.isEmpty());
 p.trimWarmHistoryInternal();int before=p.sqlReads;p.warmChatHistory(100,25,()->{});p.storageQueue.fire();AndroidUtilities.ui.fire();check(p.sqlReads==before&&p.warmHistory.isEmpty());
 ''')


def test_sqlite_stamp_changes_for_local_and_external_writes(tmp_path):
    import sqlite3
    path=tmp_path/'history.db'
    a=sqlite3.connect(path); b=sqlite3.connect(path)
    try:
        a.execute('CREATE TABLE messages(mid INTEGER, data TEXT)');a.commit()
        def stamp():
            return a.execute('SELECT total_changes()').fetchone()[0],a.execute('PRAGMA data_version').fetchone()[0]
        initial=stamp();a.execute('SELECT * FROM messages').fetchall();assert stamp()==initial
        a.execute("INSERT INTO messages VALUES(1,'old')");a.commit();local=stamp();assert local[0]!=initial[0]
        b.execute("UPDATE messages SET data='new'");b.commit();assert stamp()[1]!=local[1]
    finally:
        a.close();b.close()
    source=(JAVA/'org/telegram/messenger/MessagesStorage.java').read_text()
    reader=method(source,'private Runnable getMessagesInternal(')
    hole=reader[reader.index('if (mid != 0) {'):]
    assert hole.index('if (warmReceiver != null) return null;') < hole.index('database.executeFast(')
    assert 'clearWarmHistoryInternal();' in method(source,'private void cleanupInternal(')
