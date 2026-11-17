"""Actual UserConfig pagination metadata methods with explicit queued preference persistence."""
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method


def test_checkpoint_updates_are_visible_atomic_account_local_and_never_wait_for_disk(tmp_path):
    src=(JAVA/'org/telegram/messenger/UserConfig.java').read_text()
    methods='\n'.join(method(src,s) for s in [
      'public boolean isPinnedDialogsLoaded(', 'public void setPinnedDialogsLoaded(',
      'public int getTotalDialogsCount(', 'public void setTotalDialogsCount(',
      'public long[] getDialogLoadOffsets(', 'public void setDialogsLoadOffset('])
    probe(tmp_path,{'Probe.java':'''import java.util.*;
interface SharedPreferences{
 boolean contains(String k);boolean getBoolean(String k,boolean d);int getInt(String k,int d);long getLong(String k,long d);Editor edit();
 interface Editor{Editor putBoolean(String k,boolean v);Editor putInt(String k,int v);Editor putLong(String k,long v);void apply();boolean commit();}
}
class Prefs implements SharedPreferences{
 final Map<String,Object> memory=new HashMap<>(),disk=new HashMap<>();final List<Map<String,Object>> queued=new ArrayList<>();int edits;
 public boolean contains(String k){return memory.containsKey(k);}public boolean getBoolean(String k,boolean d){return (boolean)memory.getOrDefault(k,d);}public int getInt(String k,int d){return (int)memory.getOrDefault(k,d);}public long getLong(String k,long d){return ((Number)memory.getOrDefault(k,d)).longValue();}
 public Editor edit(){edits++;return new Editor(){Map<String,Object> batch=new HashMap<>();
 public Editor putBoolean(String k,boolean v){batch.put(k,v);return this;}public Editor putInt(String k,int v){batch.put(k,v);return this;}public Editor putLong(String k,long v){batch.put(k,v);return this;}
 public void apply(){memory.putAll(batch);queued.add(new HashMap<>(batch));}
 public boolean commit(){throw new AssertionError("checkpoint must not wait for synchronous disk persistence");}};}
 void flush(){for(var batch:queued)disk.putAll(batch);queued.clear();}
}
class AndroidUtilities{static long getPrefIntOrLong(SharedPreferences p,String k,long d){return p.getLong(k,d);}}
class Config{
 final Prefs prefs=new Prefs();final Object sync=new Object();boolean hasValidDialogLoadIds;
 SharedPreferences getPreferences(){return prefs;}
 METHODS
}
public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args)throws Exception{Config a=new Config(),other=new Config();
 a.setTotalDialogsCount(0,32);check(a.getTotalDialogsCount(0)==32&&a.prefs.disk.isEmpty());
 a.setPinnedDialogsLoaded(1,true);check(a.isPinnedDialogsLoaded(1));
 a.setDialogsLoadOffset(0,123,456,Long.MAX_VALUE,0,0,Long.MIN_VALUE+1);
 long[] expected={123,456,Long.MAX_VALUE,0,0,Long.MIN_VALUE+1};check(Arrays.equals(a.getDialogLoadOffsets(0),expected));
 check(a.prefs.queued.get(2).size()==7); // Six fields + validity flag form one edit.
 int writes=a.prefs.edits;
 for(int i=0;i<10000;i++){a.setTotalDialogsCount(0,32);a.setPinnedDialogsLoaded(1,true);a.setDialogsLoadOffset(0,123,456,Long.MAX_VALUE,0,0,Long.MIN_VALUE+1);}
 check(a.prefs.edits==writes&&other.prefs.memory.isEmpty());
 Thread[] callers=new Thread[4];for(int t=0;t<callers.length;t++){
  callers[t]=new Thread(()->{for(int i=0;i<1000;i++){a.setTotalDialogsCount(0,32);a.setPinnedDialogsLoaded(1,true);a.setDialogsLoadOffset(0,123,456,Long.MAX_VALUE,0,0,Long.MIN_VALUE+1);}});callers[t].start();
 }for(Thread t:callers)t.join();check(a.prefs.edits==writes);
 check(a.getTotalDialogsCount(1)==0&&!a.isPinnedDialogsLoaded(0));
 a.setTotalDialogsCount(1,64);a.setDialogsLoadOffset(1,789,101,0,555,0,Long.MAX_VALUE);
 check(a.getTotalDialogsCount(0)==32&&a.getTotalDialogsCount(1)==64&&a.getDialogLoadOffsets(0)[0]==123&&a.getDialogLoadOffsets(1)[0]==789);
 a.prefs.memory.put("2dialogsLoadOffsetId2",-1); // Simulate a partial/legacy folder checkpoint.
 int partialWrites=a.prefs.edits;a.setDialogsLoadOffset(2,-1,-1,-1,-1,-1,-1);
 check(a.prefs.edits==partialWrites+1&&a.prefs.memory.containsKey("2dialogsLoadOffsetAccess2"));
 // A global validity flag doesn't mean another folder already has all six stored fields.
 a.prefs.flush();Config restarted=new Config();restarted.hasValidDialogLoadIds=true;restarted.prefs.memory.putAll(a.prefs.disk);
 check(Arrays.equals(restarted.getDialogLoadOffsets(2),new long[]{-1,-1,-1,-1,-1,-1}));
 check(Arrays.equals(restarted.getDialogLoadOffsets(0),expected)&&restarted.getTotalDialogsCount(1)==64&&restarted.isPinnedDialogsLoaded(1));
 Config first=new Config();first.setDialogsLoadOffset(0,-1,-1,-1,-1,-1,-1);check(first.prefs.getBoolean("hasValidDialogLoadIds",false));
 Thread[] writers=new Thread[4];for(int t=0;t<4;t++){final int writer=t;writers[t]=new Thread(()->{for(int i=0;i<1000;i++){int n=writer*10000+i;a.setDialogsLoadOffset(2,n,n+1,n+2,n+3,n+4,n+5);}});writers[t].start();}
 for(Thread writer:writers)writer.join();long[] complete=a.getDialogLoadOffsets(2);for(int i=1;i<6;i++)check(complete[i]==complete[0]+i);
 check(Arrays.equals(a.getDialogLoadOffsets(0),expected));
 }}'''.replace('METHODS',methods)})
