"""Production file-loader registration and media refresh ordering, not device timings."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_delegate_registration_keeps_unused_slots_lazy_and_covers_creation_races(tmp_path):
    source=(JAVA/'org/telegram/messenger/FileLoader.java').read_text()
    methods='\n'.join(method(source,s) for s in [
        'static void setDelegateFactory(DelegateFactory factory)',
        'public static FileLoader getInstance(int num)',
        'public FileLoader(int instance)',
        'public void setDelegate(FileLoaderDelegate fileLoaderDelegate)'])
    probe(tmp_path,{'Probe.java':'''import java.util.*;import java.util.concurrent.atomic.*;
class UserConfig{static final int MAX_ACCOUNT_COUNT=10;}
class BaseController{final int account;BaseController(int a){account=a;}}
class FilePathDatabase{static AtomicInteger wrappers=new AtomicInteger();FilePathDatabase(int n){wrappers.incrementAndGet();}}
class FileLoaderPriorityQueue{static final int TYPE_SMALL=0,TYPE_LARGE=1;static AtomicInteger allocations=new AtomicInteger();FileLoaderPriorityQueue(int a,String n,int t,Object q){allocations.incrementAndGet();}}
class FileLoader extends BaseController{
 interface FileLoaderDelegate{int account();}interface DelegateFactory{FileLoaderDelegate create(int n);}
 static FileLoader[]Instance=new FileLoader[10];static DelegateFactory delegateFactory;
 volatile FileLoaderDelegate delegate;FilePathDatabase filePathDatabase;
 FileLoaderPriorityQueue[]smallFilesQueue=new FileLoaderPriorityQueue[5],largeFilesQueue=new FileLoaderPriorityQueue[5];static Object fileLoaderQueue=new Object();void dumpFilesQueue(){}
 METHODS
}
public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 static void reset(){Arrays.fill(FileLoader.Instance,null);FileLoader.delegateFactory=null;FilePathDatabase.wrappers.set(0);FileLoaderPriorityQueue.allocations.set(0);}
 public static void main(String[]a)throws Exception{AtomicInteger binds=new AtomicInteger();FileLoader.DelegateFactory factory=n->{binds.incrementAndGet();return ()->n;};
 FileLoader.setDelegateFactory(factory);check(FilePathDatabase.wrappers.get()==0&&binds.get()==0);
 var used=FileLoader.getInstance(4);for(int i=0;i<10000;i++)check(FileLoader.getInstance(4)==used);
 check(used.delegate.account()==4&&binds.get()==1&&FilePathDatabase.wrappers.get()==1&&FileLoaderPriorityQueue.allocations.get()==10);
 check(FileLoader.getInstance(8).delegate.account()==8&&FileLoaderPriorityQueue.allocations.get()==20);
 reset();binds.set(0);var early=FileLoader.getInstance(7);check(early.delegate==null);FileLoader.setDelegateFactory(factory);check(early.delegate.account()==7&&binds.get()==1&&FilePathDatabase.wrappers.get()==1);
 // Factory installation and calls from push/media threads share the same creation lock.
 reset();binds.set(0);Thread[]threads=new Thread[20];for(int i=0;i<threads.length;i++){final int n=i%10;threads[i]=new Thread(()->FileLoader.getInstance(n));}
 Thread install=new Thread(()->FileLoader.setDelegateFactory(factory));for(Thread t:threads)t.start();install.start();for(Thread t:threads)t.join();install.join();
 check(FilePathDatabase.wrappers.get()==10&&FileLoaderPriorityQueue.allocations.get()==100&&binds.get()==10);
 for(int i=0;i<10;i++)check(FileLoader.getInstance(i).delegate.account()==i);
 // Existing explicit delegates remain supported after the global factory is installed.
 var explicit=FileLoader.getInstance(2);explicit.setDelegate(()->42);check(FileLoader.getInstance(2).delegate.account()==42);
 }}'''.replace('METHODS',methods)})


def test_media_event_bursts_coalesce_but_mid_scan_changes_and_callback_barriers_survive(tmp_path):
    source=(JAVA/'org/telegram/messenger/ImageLoader.java').read_text()
    methods='\n'.join(method(source,s) for s in ['public void checkMediaPaths()',
        'public void checkMediaPaths(Runnable after)','private void refreshMediaPaths(Runnable after)'])
    start=source.index('    private final app.flexygram.performance.CoalescedTask mediaPathRefresh =')
    field=source[start:source.index(';',start)+1]
    probe(tmp_path,{'Probe.java':'''import java.io.File;import java.util.*;
class SparseArray<T>{int generation;SparseArray(int g){generation=g;}}
public class Probe{
 static boolean worker;static List<String>events=new ArrayList<>();
 static class Queue{ArrayDeque<Runnable>jobs=new ArrayDeque<>();boolean background;Queue(boolean b){background=b;}void postRunnable(Runnable r){jobs.add(r);}void one(){boolean old=worker;worker=background;try{jobs.remove().run();}finally{worker=old;}}}
 static class AndroidUtilities{static Queue ui=new Queue(false);static void runOnUIThread(Runnable r){ui.postRunnable(r);}}
 static class FileLoader{static SparseArray<File>current;static void setMediaDirs(SparseArray<File>p){if(worker)throw new AssertionError("publish on worker");current=p;events.add("publish"+p.generation);}}
 Queue cacheOutQueue=new Queue(true);int scans,generation=1;Runnable duringScan;boolean fail;
 SparseArray<File>createMediaPaths(){if(!worker)throw new AssertionError("disk on main");scans++;if(fail){fail=false;throw new IllegalStateException();}SparseArray<File>p=new SparseArray<>(generation);if(duringScan!=null){Runnable r=duringScan;duringScan=null;r.run();}return p;}
 FIELD
 METHODS
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){Probe p=new Probe();for(int i=0;i<10000;i++)p.checkMediaPaths();check(p.cacheOutQueue.jobs.size()==1&&p.scans==0);
 p.duringScan=()->{p.generation=2;for(int i=0;i<10000;i++)p.checkMediaPaths();};p.cacheOutQueue.one();check(p.scans==1&&p.cacheOutQueue.jobs.size()==1);p.cacheOutQueue.one();check(p.scans==2&&p.cacheOutQueue.jobs.isEmpty());
 AndroidUtilities.ui.one();AndroidUtilities.ui.one();check(events.equals(List.of("publish1","publish2"))&&FileLoader.current.generation==2);
 events.clear();p.generation=3;p.checkMediaPaths(()->{check(!worker&&FileLoader.current.generation==3);events.add("callbackA");});p.checkMediaPaths(()->events.add("callbackB"));check(p.cacheOutQueue.jobs.size()==2);
 p.cacheOutQueue.one();p.cacheOutQueue.one();check(events.isEmpty());AndroidUtilities.ui.one();AndroidUtilities.ui.one();check(events.equals(List.of("publish3","callbackA","publish3","callbackB")));
 p.fail=true;p.checkMediaPaths();try{p.cacheOutQueue.one();throw new AssertionError();}catch(IllegalStateException expected){}p.checkMediaPaths();p.cacheOutQueue.one();AndroidUtilities.ui.one();check(p.cacheOutQueue.jobs.isEmpty());
 }}'''.replace('FIELD',field).replace('METHODS',methods)},[JAVA/'app/flexygram/performance/CoalescedTask.java'])


def test_image_startup_installs_callbacks_without_eager_account_construction():
    source=(JAVA/'org/telegram/messenger/ImageLoader.java').read_text()
    ctor=method(source,'public ImageLoader()')
    assert 'FileLoader.getInstance(' not in ctor
    assert ctor.index('FileLoader.setMediaDirs(mediaDirs)') < ctor.index('FileLoader.setDelegateFactory(this::createFileLoaderDelegate)')
    assert 'private volatile FileLoaderDelegate delegate' in (JAVA/'org/telegram/messenger/FileLoader.java').read_text()
    factory=method(source,'private FileLoader.FileLoaderDelegate createFileLoaderDelegate(final int currentAccount)')
    for callback in ['fileUploadProgressChanged','fileDidUploaded','fileDidFailedUpload','fileDidLoaded','fileDidFailedLoad','fileLoadProgressChanged']:
        assert 'void '+callback+'(' in factory


def test_memory_pressure_evicts_existing_images_without_initializing_the_loader(tmp_path):
    source = (JAVA/'org/telegram/messenger/ImageLoader.java').read_text()
    clear = method(source, 'static void clearMemoryIfInitialized()')
    app = (JAVA/'org/telegram/messenger/ApplicationLoader.java').read_text()
    for signature in ('public void onTrimMemory(int level)', 'public void onLowMemory()'):
        assert 'ImageLoader.clearMemoryIfInitialized()' in method(app, signature)
    probe(tmp_path, {'Probe.java': '''
class ImageLoader {
    static ImageLoader Instance;
    int evictions;
    void clearMemory() { evictions++; }
    CLEAR
}
public class Probe {
    public static void main(String[] args) {
        ImageLoader.clearMemoryIfInitialized();
        if (ImageLoader.Instance != null) throw new AssertionError();
        ImageLoader loader = new ImageLoader();
        ImageLoader.Instance = loader;
        ImageLoader.clearMemoryIfInitialized();
        if (ImageLoader.Instance != loader || loader.evictions != 1) throw new AssertionError();
    }
}'''.replace('CLEAR', clear)})
