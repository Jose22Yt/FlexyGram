"""Compile the production unread comparison and run its SQL against SQLite histories."""
import json
import re
import sqlite3

from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_unread_comparison_keeps_exact_semantics_and_closes_failed_cursors(tmp_path):
    source = (JAVA/'org/telegram/messenger/MessagesStorage.java').read_text()
    actual = method(source, 'private boolean matchesLocalUnreadCount(')
    output = tmp_path/'queries.txt'
    probe(tmp_path, {'Probe.java': '''import java.util.*;import java.nio.file.*;import org.telegram.SQLite.SQLiteException;
public class Probe {
 static List<String> queries=new ArrayList<>();static String context;
 static class SQLiteCursor{static int closed;static boolean fail;boolean next() throws SQLiteException{if(fail)throw new SQLiteException("step");return true;}long longValue(int n){return 0;}void dispose(){closed++;}}
 static class Database{boolean fail;SQLiteCursor queryFinalized(String sql) throws SQLiteException{if(fail)throw new SQLiteException("prepare");queries.add(context+"|"+sql);return new SQLiteCursor();}}
 Database database=new Database();
 ACTUAL
 public static void main(String[]args)throws Exception{
  Probe p=new Probe();
  for(long did:new long[]{100,200,999})for(long topic:new long[]{0,1,2})for(int expected:new int[]{0,1,3,20,Integer.MAX_VALUE})for(boolean positive:new boolean[]{false,true}){
   context=did+"|"+topic+"|"+expected+"|"+positive;
   p.matchesLocalUnreadCount(did,topic,expected,positive);
  }
  Files.write(Path.of(OUTPUT_PATH),queries);
  int calls=queries.size();if(p.matchesLocalUnreadCount(100,0,-1,true)||queries.size()!=calls)throw new AssertionError("negative expected");
  p.database.fail=true;try{p.matchesLocalUnreadCount(100,0,0,true);throw new AssertionError();}catch(SQLiteException correct){}
  p.database.fail=false;SQLiteCursor.fail=true;int closed=SQLiteCursor.closed;
  try{p.matchesLocalUnreadCount(100,0,0,true);throw new AssertionError();}catch(SQLiteException correct){}
  if(SQLiteCursor.closed!=closed+1)throw new AssertionError("cursor leaked");
 }
}'''.replace('ACTUAL',actual).replace('OUTPUT_PATH',json.dumps(str(output)))}, [JAVA/'org/telegram/SQLite/SQLiteException.java'])
    database = sqlite3.connect(':memory:')
    try:
        for table in ['messages_v2', 'messages_topics']:
            database.execute(f'CREATE TABLE {table}(uid INTEGER,mid INTEGER,out INTEGER,read_state INTEGER,topic_id INTEGER,ttl INTEGER,date INTEGER,send_state INTEGER)')
            for index in [f'task_idx_{table}', f'uid_mid_read_out_idx_{table}']:
                if index.startswith('task'):
                    columns = 'uid,out,read_state,ttl,date,send_state'
                else:
                    columns = 'uid,mid,read_state,out'
                database.execute(f'CREATE INDEX {index} ON {table}({columns})')
            database.executemany(f'INSERT INTO {table} VALUES(?,?,?,?,?,?,?,?)',
                [(did, mid, outgoing, state, topic, 0, abs(mid), 0)
                 for did in [100,200] for mid in range(-8,17)
                 for outgoing in [0,1] for state in [0,1,2,3] for topic in [1,2]])
        for line in output.read_text().splitlines():
            did, topic, expected, positive, sql = line.split('|',4)
            table = 'messages_v2' if topic == '0' else 'messages_topics'
            condition = '>' if positive == 'true' else '!='
            original = f'SELECT COUNT(*) FROM {table} WHERE uid={did} AND out=0 AND read_state IN(0,2) AND mid {condition} 0'
            if topic != '0':
                original += f' AND topic_id={topic}'
            count = database.execute(original).fetchone()[0]
            optimized = database.execute(sql).fetchone()[0]
            assert (optimized == int(expected)) == (count == int(expected)), line
        # A large fully-read history must not be walked to prove there are zero unread messages.
        database.executemany('INSERT INTO messages_v2 VALUES(300,?,0,1,0,0,?,0)', ((i,i) for i in range(1,100001)))
        zero_query = next(line.split('|',4)[4] for line in output.read_text().splitlines() if line.startswith('100|0|0|true|')).replace('uid = 100','uid = 300')
        steps = [0]
        def progress():
            steps[0] += 100
            return 0
        database.set_progress_handler(progress,100)
        assert database.execute(zero_query).fetchone()[0] == 0
        database.set_progress_handler(None,0)
        assert steps[0] < 1000
        assert any('task_idx_messages_v2' in row[3] for row in database.execute('EXPLAIN QUERY PLAN '+zero_query))
    finally:
        database.close()
    reader = method(source, 'private Runnable getMessagesInternal(')
    assert 'matchesLocalUnreadCount(dialogId, threadMessageId, count_unread, true)' in reader
    assert 'matchesLocalUnreadCount(dialogId, threadMessageId, count_unread, false)' in reader


def test_startup_prepares_a_smaller_local_page_and_leaves_loaded_dialogs_alone(tmp_path):
    source = (JAVA/'org/telegram/messenger/ApplicationLoader.java').read_text()
    actual = method(source, 'private static void prepareSelectedDialogs()')
    probe(tmp_path, {'Probe.java': '''import java.util.*;
public class Probe {
 static class Looper{static Looper main=new Looper();static Looper myLooper(){return main;}static Looper getMainLooper(){return main;}}
 static class AndroidUtilities{static void runOnUIThread(Runnable r){r.run();}}
 static class UserConfig{static final int MAX_ACCOUNT_COUNT=10;static int selectedAccount;static boolean active=true;static UserConfig getInstance(int a){return new UserConfig();}boolean isClientActivated(){return active;}Object getCurrentUser(){return active?this:null;}}
 static class MessagesController{static MessagesController instance=new MessagesController();static MessagesController getInstance(int a){return instance;}boolean dialogsLoaded;List<Object>allDialogs=new ArrayList<>();List<Object>getDialogs(int folder){return allDialogs;}int calls,count;boolean local;void loadDialogs(int folder,int offset,int size,boolean cache){if(folder!=0||offset!=0)throw new AssertionError();calls++;count=size;local=cache;}}
 ACTUAL
 public static void main(String[]args){
  prepareSelectedDialogs();MessagesController c=MessagesController.instance;
  if(c.calls!=1||c.count!=32||!c.local)throw new AssertionError("first local page");
  c.dialogsLoaded=true;prepareSelectedDialogs();if(c.calls!=1)throw new AssertionError("resume reload");
  c.dialogsLoaded=false;c.allDialogs.add(new Object());prepareSelectedDialogs();if(c.calls!=1)throw new AssertionError("existing rows reloaded");
  c.allDialogs.clear();UserConfig.active=false;prepareSelectedDialogs();if(c.calls!=1)throw new AssertionError("inactive account");
 }
}'''.replace('ACTUAL', actual.replace('android.os.Looper','Looper').replace('android.os.Trace','Trace').replace('ApplicationLoader::prepareSelectedDialogs','Probe::prepareSelectedDialogs')),
    'Trace.java':'class Trace{static void beginSection(String s){}static void endSection(){}}'})


def test_read_chat_skips_unread_anchor_queries_and_unread_chat_keeps_its_anchor(tmp_path):
    source = (JAVA/'org/telegram/messenger/MessagesStorage.java').read_text()
    branch = method(source, 'else if (max_id_query == 0)')
    helper = method(source, 'private boolean matchesLocalUnreadCount(')
    probe(tmp_path, {'Probe.java': '''import java.util.*;import org.telegram.SQLite.SQLiteException;
public class Probe{
 static class SQLiteCursor{int value;SQLiteCursor(int v){value=v;}boolean next()throws SQLiteException{return true;}int intValue(int n){return value;}long longValue(int n){return value;}void dispose(){}}
 static class Database{int reads;SQLiteCursor queryFinalized(String sql)throws SQLiteException{reads++;return new SQLiteCursor(sql.startsWith("SELECT min")?5:2);}}
 Database database=new Database();long dialogId=100,threadMessageId;int count_unread,min_unread_id,messageMaxId,max_id_query;
 HELPER
 void load()throws SQLiteException{SQLiteCursor cursor=null;if(false){} BRANCH}
 public static void main(String[]args)throws Exception{
  Probe p=new Probe();p.load();if(p.database.reads!=0||p.messageMaxId!=0)throw new AssertionError("read chat scanned");
  p.count_unread=2;p.load();if(p.database.reads!=2||p.messageMaxId!=5||p.min_unread_id!=5)throw new AssertionError("unread anchor lost");
  Probe mismatch=new Probe();mismatch.count_unread=3;mismatch.load();if(mismatch.database.reads!=1||mismatch.messageMaxId!=0)throw new AssertionError("stale count used");
 }
}'''.replace('HELPER',helper).replace('BRANCH',branch)}, [JAVA/'org/telegram/SQLite/SQLiteException.java'])
