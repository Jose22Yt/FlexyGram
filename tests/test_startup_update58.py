"""Startup queue ordering and actual SQLite query plans; no device speed claim."""
import re
import sqlite3
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_selected_cache_precedes_auxiliary_work_for_both_database_open_races(tmp_path):
    source = (JAVA/'org/telegram/messenger/MessagesStorage.java').read_text()
    methods = '\n'.join(method(source, signature) for signature in [
        'public static MessagesStorage getInstance(int num)',
        'static MessagesStorage getInstanceForUiStartup(int num)',
        'private static MessagesStorage getInstance(int num, boolean deferStartupTasks)',
        'public MessagesStorage(int instance)',
        'private MessagesStorage(int instance, boolean deferStartupTasks)',
        'void completeUiStartup()', 'private void loadStartupTasks()'])
    opened = method(source, 'public void openDatabase(int openTries)')
    boot = method(opened, 'if (startupTasksDeferred)')
    # Include the actual else branch, not a copy of the scheduling policy.
    start = opened.index(boot)
    end = opened.index('        try {\n            openSync.countDown();', start)
    boot = opened[start:end]
    probe(tmp_path, {'Probe.java': '''import java.util.*;
class BaseController {BaseController(int n){}}
class DispatchQueue {
 ArrayDeque<Runnable> q=new ArrayDeque<>();DispatchQueue(String s){}void setPriority(int n){}
 void postRunnable(Runnable r){q.add(r);}void one(){q.remove().run();}void drain(){while(!q.isEmpty())one();}
}
class MessagesStorage extends BaseController {
 static MessagesStorage[] Instance=new MessagesStorage[4];static Object[]lockObjects={new Object(),new Object(),new Object(),new Object()};
 DispatchQueue storageQueue;boolean startupTasksDeferred,startupTasksPending;boolean opened;List<String>events=new ArrayList<>();
 METHODS
 void openDatabase(int tries){opened=true;BOOT}
 void loadDialogFilters(){storageQueue.postRunnable(()->events.add("filters"));}
 void loadUnreadMessages(){storageQueue.postRunnable(()->events.add("notifications"));}
 void loadPendingTasks(){storageQueue.postRunnable(()->events.add("pending"));}
 void cache(){storageQueue.postRunnable(()->{if(!opened)throw new AssertionError("database not opened");events.add("cache");});}
}
public class Probe {
 static void check(boolean v){if(!v)throw new AssertionError();}
 public static void main(String[]args){
  for(boolean openFirst:new boolean[]{false,true}){
   MessagesStorage.Instance[0]=null;var s=MessagesStorage.getInstanceForUiStartup(0);
   check(s==MessagesStorage.getInstance(0));if(openFirst)s.storageQueue.one();
   s.cache();s.completeUiStartup();s.completeUiStartup();s.storageQueue.drain();
   check(s.events.equals(List.of("cache","filters","notifications","pending")));
   check(!s.startupTasksDeferred&&!s.startupTasksPending);
  }
  // Background/push startup still recovers notifications/tasks without a UI frame.
  var headless=MessagesStorage.getInstance(1);headless.storageQueue.drain();
  check(headless.events.equals(List.of("filters","notifications","pending")));
  check(MessagesStorage.getInstanceForUiStartup(1)==headless);headless.completeUiStartup();headless.storageQueue.drain();check(headless.events.size()==3);
  // Failure / missing session: finally releases bootstrap even with no cache request.
  var cancelled=MessagesStorage.getInstanceForUiStartup(2);cancelled.completeUiStartup();cancelled.storageQueue.drain();
  check(cancelled.events.equals(List.of("filters","notifications","pending")));
  // Public constructor retains background semantics, and no cross-account queue is blocked.
  var direct=new MessagesStorage(3);direct.storageQueue.drain();check(direct.events.size()==3);
 }
}'''.replace('METHODS', methods).replace('BOOT', boot)})
    app = (JAVA/'org/telegram/messenger/ApplicationLoader.java').read_text()
    core = method(app, 'private static void initializeStartupAccount(int a, boolean prepareDialogs, boolean uiStartup)')
    assert core.index('getInstanceForUiStartup(a)') < core.index('MessagesController.getInstance(a)') < core.index('prepareSelectedDialogs()')
    assert 'if (prepareDialogs && uiStartup)' in core
    assert 'finally {\n            if (startupStorage != null) startupStorage.completeUiStartup();' in core


def test_native_initial_page_uses_ordered_index_and_preserves_rows_and_pagination():
    source = (JAVA/'org/telegram/messenger/MessagesStorage.java').read_text()
    migration = (JAVA/'org/telegram/messenger/DatabaseMigrationHelper.java').read_text()
    index = re.search(r'CREATE INDEX IF NOT EXISTS folder_pinned_date_idx_dialogs[^"\n]+', source).group()
    assert index in migration
    assert 'LAST_DB_VERSION = 180' in source
    assert 'if (version == 179)' in migration and 'PRAGMA user_version = 180' in migration
    db = sqlite3.connect(':memory:')
    for table in ('dialogs', 'messages_v2', 'dialog_settings'):
        schema = re.search(r'CREATE TABLE '+table+r'\([^"\n]+', source).group()
        db.execute(schema)
    db.execute('CREATE INDEX folder_id_idx_4_dialogs ON dialogs(folder_id)')
    db.executemany('INSERT INTO dialogs(did, date, pinned, folder_id, last_mid) VALUES(?,?,?,?,?)',
        ((i, i*17, 100000-i if i % 111 == 0 else 0, i % 3, i) for i in range(12000)))
    db.executemany('INSERT INTO messages_v2(mid,uid,data) VALUES(?,?,?)', ((i, i, bytes([i%256])) for i in range(12000)))
    query = re.search(r'"(SELECT d.did, d.last_mid,[^"\n]+)"', method(source, 'public void getDialogs(int folderId')).group(1)
    def sql(folder,offset,count): return query % (folder,offset,count)
    def plan(): return ' '.join(row[3] for row in db.execute('EXPLAIN QUERY PLAN '+sql(0,0,32)))
    before = plan()
    pages = {(folder,offset):db.execute(sql(folder,offset,32)).fetchall() for folder in range(3) for offset in (0,32,64,128)}
    assert 'USE TEMP B-TREE FOR ORDER BY' in before
    db.execute(index)
    after = plan()
    assert 'folder_pinned_date_idx_dialogs' in after and 'TEMP B-TREE' not in after
    for (folder,offset),rows in pages.items(): assert db.execute(sql(folder,offset,32)).fetchall() == rows
    # Future pin/archive/message-date updates retain exactly the native query semantics.
    db.execute('UPDATE dialogs SET pinned=99999,folder_id=0,date=999999 WHERE did=4')
    indexed=db.execute(sql(0,0,32)).fetchall()
    db.execute('DROP INDEX folder_pinned_date_idx_dialogs')
    assert db.execute(sql(0,0,32)).fetchall()==indexed
