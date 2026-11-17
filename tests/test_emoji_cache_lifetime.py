"""Real emoji attach/cleanup/update methods under a deterministic UI clock and sparse-array hosts."""
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method


def _run(tmp_path, scenario):
    src=(JAVA/'org/telegram/ui/Components/AnimatedEmojiDrawable.java').read_text()
    bodies='\n'.join(method(src,s) for s in ['private void updateAttachState()', 'public static void updateAll()'])
    for sig in ['private static void scheduleCleanup()', 'private static void cancelCleanup()', 'private static boolean removeUnused(', 'public static void clearUnused()']:
        if sig in src:bodies+='\n'+method(src,sig)
    start=src.index('    private static final Runnable cleanup =')
    bodies+='\n'+src[start:src.index('    private Boolean canOverrideColorCached',start)]
    probe(tmp_path,{
      'android/os/SystemClock.java':'package android.os;public class SystemClock{public static long now;public static long uptimeMillis(){return now;}}',
      'Probe.java':'''import java.util.*;
class LongSparseArray<T>{final LinkedHashMap<Long,T> values=new LinkedHashMap<>();boolean dirty;int compactions;
 void compact(){if(dirty){compactions++;dirty=false;}}int size(){compact();return values.size();}T get(long k){return values.get(k);}void put(long k,T v){values.put(k,v);}void clear(){values.clear();dirty=false;}
 T valueAt(int n){compact();var it=values.values().iterator();for(int i=0;i<n;i++)it.next();return it.next();}long keyAt(int n){compact();var it=values.keySet().iterator();for(int i=0;i<n;i++)it.next();return it.next();}
 void remove(long k){values.remove(k);dirty=true;}void removeAt(int n){long k=keyAt(n);remove(k);}}
class SparseArray<T> extends LongSparseArray<T>{}
class BuildVars{static boolean DEBUG_PRIVATE_VERSION;}class FileLog{static void e(Throwable t){throw new AssertionError(t);}}class Log{static void d(String t,String s){}}
class AndroidUtilities{
 record Task(Runnable action,long due){}static final ArrayList<Task> queue=new ArrayList<>();static int runs;
 static void cancelRunOnUIThread(Runnable r){queue.removeIf(t->t.action==r);}static void runOnUIThread(Runnable r,long delay){queue.add(new Task(r,android.os.SystemClock.now+delay));}
 static void advance(long target){while(true){Task next=null;for(var t:queue)if(t.due<=target&&(next==null||t.due<next.due))next=t;if(next==null)break;queue.remove(next);android.os.SystemClock.now=next.due;runs++;next.action.run();}android.os.SystemClock.now=target;}
}
class AnimatedEmojiDrawable{
 static SparseArray<LongSparseArray<AnimatedEmojiDrawable>> globalEmojiCache=new SparseArray<>();
 static final long UNUSED_CACHE_DELAY_MS=5000;static boolean LOG_MEMORY_LEAK;static final java.util.concurrent.atomic.AtomicBoolean cleanupScheduled=new java.util.concurrent.atomic.AtomicBoolean();static int attachedCount;static ArrayList<AnimatedEmojiDrawable> attachedDrawable;
 ArrayList<Object> views,holders;boolean attached=true,preloading;long detachedAt=android.os.SystemClock.uptimeMillis();int inits;
 static class Receiver{void onAttachedToWindow(){}void onDetachedFromWindow(){}}
 Receiver imageReceiver=new Receiver();void initDocument(boolean force){inits++;}static void updateLiteModeValues(){}
 BODIES
 static void detach(AnimatedEmojiDrawable d){d.updateAttachState();}
 PRESSURE
}
public class Probe{
 static void check(boolean b,String why){if(!b)throw new AssertionError(why);}
 public static void main(String[]args){SCENARIO}
}'''.replace('BODIES',bodies).replace('PRESSURE','static void pressure(){clearUnused();}' if 'public static void clearUnused()' in src else 'static void pressure(){cleanup.run();}').replace('SCENARIO',scenario)
    })


def test_continuous_detaches_cannot_starve_cleanup_and_recent_entries_keep_warm_window(tmp_path):
    _run(tmp_path,'''var cache=new LongSparseArray<AnimatedEmojiDrawable>();AnimatedEmojiDrawable.globalEmojiCache.put(0,cache);
 var active=new AnimatedEmojiDrawable();cache.put(-1,active);
 for(int i=0;i<100000;i++){
  var d=new AnimatedEmojiDrawable();cache.put(i,d);AnimatedEmojiDrawable.detach(d);
  AndroidUtilities.advance(android.os.SystemClock.now+100);
  if(i%200==0)check(cache.size()<=103,"Continuous scroll must not postpone emoji cleanup forever; retained="+cache.size());
  check(AndroidUtilities.queue.size()<=1,"Only one cleanup callback");
 }
 check(cache.get(-1)==active&&active.attached,"Live emoji must survive");
 AndroidUtilities.advance(android.os.SystemClock.now+20000);check(cache.size()==1&&AndroidUtilities.queue.isEmpty(),"No recurring idle cleaner remains");
 var recent=new AnimatedEmojiDrawable();cache.put(100001,recent);AnimatedEmojiDrawable.detach(recent);
 AndroidUtilities.advance(android.os.SystemClock.now+1000);check(cache.get(100001)==recent,"Recent detached emoji retain native warm window");
 AnimatedEmojiDrawable.pressure();check(cache.size()==1&&cache.get(-1)==active&&AndroidUtilities.queue.isEmpty(),"Pressure clears only unused resources");''')


def test_update_all_removes_adjacent_unused_entries_without_sparse_array_compaction_per_removal(tmp_path):
    _run(tmp_path,'''var cache=new LongSparseArray<AnimatedEmojiDrawable>();AnimatedEmojiDrawable.globalEmojiCache.put(0,cache);
 var active=new AnimatedEmojiDrawable();cache.put(0,active);
 for(int i=1;i<=100;i++){var d=new AnimatedEmojiDrawable();d.attached=false;cache.put(i,d);}
 AnimatedEmojiDrawable.updateAll();
 check(cache.size()==1&&cache.get(0)==active&&active.inits==1,"All adjacent unused entries must go, active material updates once");
 check(cache.compactions<=1,"Batch deletion must not compact sparse arrays after each removal");''')
