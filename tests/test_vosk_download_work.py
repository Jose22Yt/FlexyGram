"""Run real download cancellation/observer and size-cache methods with explicit queue/HTTP hosts."""
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method

SOURCE=(JAVA/'app/exteraless/speech/VoskManager.java').read_text()


def test_cancel_interrupts_call_and_observers_can_detach_without_skipping_others(tmp_path):
    cancel='public static synchronized void cancelDownload()' if 'public static synchronized void cancelDownload()' in SOURCE else 'public static void cancelDownload()'
    bodies='\n'.join(method(SOURCE,s) for s in [cancel, 'private static void notifyProgress(', 'private static void notifyFinished('])
    probe(tmp_path,{'Probe.java':'''import java.util.*;import java.util.concurrent.atomic.*;
class Call{int cancels;void cancel(){cancels++;}}class VoskModel{}class FileLog{static void e(Throwable t){}}
public class Probe{
 interface DownloadListener{void onProgress(long d,long t);void onFinished(VoskModel m,Throwable e);}
 static final ArrayList<DownloadListener> listeners=new ArrayList<>();static AtomicBoolean cancelled=new AtomicBoolean();static Call activeDownload;
 BODIES
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){activeDownload=new Call();cancelDownload();check(cancelled.get()&&activeDownload.cancels==1);activeDownload=null;cancelDownload();
 int[] got={0,0};DownloadListener first=new DownloadListener(){public void onProgress(long d,long t){listeners.remove(this);}public void onFinished(VoskModel m,Throwable e){listeners.remove(this);}};
 DownloadListener bad=new DownloadListener(){public void onProgress(long d,long t){throw new IllegalStateException();}public void onFinished(VoskModel m,Throwable e){throw new IllegalStateException();}};
 DownloadListener last=new DownloadListener(){public void onProgress(long d,long t){got[0]++;}public void onFinished(VoskModel m,Throwable e){got[1]++;}};
 listeners.add(first);listeners.add(bad);listeners.add(last);notifyProgress(1,2);check(got[0]==1);
 listeners.clear();listeners.add(first);listeners.add(bad);listeners.add(last);notifyFinished(new VoskModel(),null);check(got[1]==1);
 }}'''.replace('BODIES',bodies)})


def test_size_rows_never_walk_files_and_stale_scans_cannot_publish(tmp_path):
    signatures=['public static long installedSize(', 'private static long directorySize(']
    if 'private static void invalidateInstalledSizes()' in SOURCE:signatures+=['private static void invalidateInstalledSizes()']
    bodies='\n'.join(method(SOURCE,s) for s in signatures)
    bodies=bodies.replace('private static long directorySize(File file) {','private static long directorySize(File file) { scans++; scanThread=Thread.currentThread();')
    if 'private static void invalidateInstalledSizes()' not in SOURCE:bodies+='\nprivate static void invalidateInstalledSizes(){}'
    probe(tmp_path,{'Probe.java':'''import java.util.*;import java.io.*;import java.nio.file.*;import java.util.concurrent.*;
class FileLog{static void e(Throwable t){}}
class AndroidUtilities{static final List<Runnable> ui=new ArrayList<>();static void runOnUIThread(Runnable r){synchronized(ui){ui.add(r);}}}
public class Probe{
 static class Queue{boolean reject;final List<Runnable> tasks=new ArrayList<>();void execute(Runnable r){if(reject)throw new RejectedExecutionException();tasks.add(r);}
 void runNext()throws Exception{Runnable r=tasks.remove(0);Throwable[] failed={null};Thread t=new Thread(()->{try{r.run();}catch(Throwable e){failed[0]=e;}});t.start();t.join(2000);check(!t.isAlive()&&failed[0]==null);}}
 static final Queue executor=new Queue();static final Map<String,Long> installedSizes=new HashMap<>();static final Set<String> sizePending=new HashSet<>();static long sizesGeneration;static int scans;static Thread scanThread;static File root;
 static File getModelDir(String code){return new File(root,code);}static void notifySizeChanged(String code){}
 BODIES
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args)throws Exception{root=Files.createTempDirectory("size-probe").toFile();File dir=getModelDir("a");dir.mkdirs();Files.write(new File(dir,"weights").toPath(),new byte[64]);
 try{for(int i=0;i<10000;i++)check(installedSize("a")==-1);
 check(scans==0&&executor.tasks.size()==1);executor.runNext();check(installedSize("a")==64&&scanThread!=Thread.currentThread());int before=scans;
 for(int i=0;i<10000;i++)check(installedSize("a")==64);check(scans==before&&executor.tasks.isEmpty());
 invalidateInstalledSizes();check(installedSize("a")==-1);invalidateInstalledSizes();executor.runNext();check(!installedSizes.containsKey("a")&&!sizePending.contains("a"));
 check(installedSize("a")==-1);executor.runNext();check(installedSize("a")==64);
 invalidateInstalledSizes();executor.reject=true;check(installedSize("a")==-1&&!sizePending.contains("a"));executor.reject=false;check(installedSize("a")==-1);executor.runNext();check(installedSize("a")==64);
 }finally{Files.deleteIfExists(new File(dir,"weights").toPath());Files.deleteIfExists(dir.toPath());Files.deleteIfExists(root.toPath());}
 }}'''.replace('BODIES',bodies)})


def test_download_failures_and_cancellation_remove_staging_and_publish_only_after_release(tmp_path):
    bodies='\n'.join(method(SOURCE,s) for s in ['private static void downloadInternal(', 'private static void unzipStripRoot(', 'private static String stripRoot(', 'private static void deleteRecursive('])
    probe(tmp_path,{'Probe.java':'''import java.io.*;import java.nio.file.*;import java.security.*;import java.util.*;import java.util.concurrent.*;import java.util.concurrent.atomic.*;import java.util.zip.*;
class TextUtils{static boolean isEmpty(String s){return s==null||s.isEmpty();}}
class AndroidUtilities{static void runOnUIThread(Runnable r){r.run();}}
class VoskModel{String code,url="https://example.invalid/model",md5;VoskModel(String c){code=c;}}
class Request{static class Builder{Builder url(String u){return this;}Request build(){return new Request();}}}
class HttpClient{static final HttpClient INSTANCE=new HttpClient();OkHttpClient getInstance(){return new OkHttpClient();}}
class OkHttpClient{static byte[] data;static boolean failRead;static AtomicBoolean cancelOnClose;static int closes;
 Builder newBuilder(){return new Builder();}Call newCall(Request r){return new Call();}static class Builder{Builder callTimeout(long n,TimeUnit u){return this;}Builder readTimeout(long n,TimeUnit u){return this;}OkHttpClient build(){return new OkHttpClient();}}}
class Call{boolean cancelled;void cancel(){cancelled=true;}Response execute()throws IOException{if(cancelled)throw new IOException("cancelled");return new Response();}}
class Response implements AutoCloseable{boolean isSuccessful(){return true;}int code(){return 200;}ResponseBody body(){return new ResponseBody();}public void close(){OkHttpClient.closes++;}}
class ResponseBody{long contentLength(){return OkHttpClient.data.length;}InputStream byteStream(){return new ByteArrayInputStream(OkHttpClient.data){public synchronized int read(byte[] b,int off,int len){if(OkHttpClient.failRead)throw new IllegalStateException("read failed");return super.read(b,off,len);}public void close()throws IOException{super.close();if(OkHttpClient.cancelOnClose!=null)OkHttpClient.cancelOnClose.set(true);}};}}
class VoskTranscriber{static int publications;static <T>Future<T> afterModelRelease(String code,Callable<T> action){publications++;FutureTask<T> t=new FutureTask<>(action);t.run();return t;}}
public class Probe{
 static final int BUFFER_SIZE=64*1024;static final String READY_MARKER=".ready";static File root;static long totalBytes,downloadedBytes;static Call activeDownload;
 static File getModelsDir(){return root;}static void notifyProgress(long d,long t){}
 BODIES
 static void check(boolean b){if(!b)throw new AssertionError();}
 static byte[] zip(String name)throws Exception{var bytes=new ByteArrayOutputStream();try(var zip=new ZipOutputStream(bytes)){zip.putNextEntry(new ZipEntry(name));zip.write(new byte[4096]);zip.closeEntry();}return bytes.toByteArray();}
 static void failed(VoskModel m,AtomicBoolean flag)throws Exception{boolean failed=false;try{downloadInternal(m,flag);}catch(Exception expected){failed=true;}check(failed&&activeDownload==null&&!new File(root,m.code+".zip").exists()&&!new File(root,m.code+".tmp").exists()&&!new File(root,m.code+"/.ready").exists());}
 public static void main(String[]args)throws Exception{root=Files.createTempDirectory("vosk-files").toFile();
 try{
 OkHttpClient.data=zip("model/weights");downloadInternal(new VoskModel("good"),new AtomicBoolean());
 check(VoskTranscriber.publications==1&&new File(root,"good/.ready").isFile()&&new File(root,"good/weights").length()==4096&&!new File(root,"good.zip").exists()&&!new File(root,"good.tmp").exists()&&activeDownload==null);
 VoskModel checksum=new VoskModel("checksum");checksum.md5="wrong";failed(checksum,new AtomicBoolean());
 OkHttpClient.failRead=true;failed(new VoskModel("read"),new AtomicBoolean());OkHttpClient.failRead=false;
 failed(new VoskModel("cancel"),new AtomicBoolean(true));
 AtomicBoolean cancelled=new AtomicBoolean();OkHttpClient.cancelOnClose=cancelled;failed(new VoskModel("extract-cancel"),cancelled);OkHttpClient.cancelOnClose=null;
 String escaped="escaped-"+UUID.randomUUID();OkHttpClient.data=zip("model/../../"+escaped);failed(new VoskModel("badzip"),new AtomicBoolean());check(!new File(root,escaped).exists());
 check(OkHttpClient.closes==5);
 }finally{deleteRecursive(root);}
 }}'''.replace('BODIES',bodies)})


def test_pending_deletion_is_coalesced_and_retains_files_until_owner_runs(tmp_path):
    bodies='\n'.join(method(SOURCE,s) for s in ['public static boolean isDeleting(', 'public static synchronized void delete(String code, Runnable completion)', 'private static void deleteRecursive('])
    probe(tmp_path,{'Probe.java':'''import java.util.*;import java.io.*;import java.nio.file.*;import java.util.concurrent.*;
class AndroidUtilities{static final List<Runnable> ui=new ArrayList<>();static void runOnUIThread(Runnable r){ui.add(r);}}
class FileLog{static void e(Throwable t){}}
class VoskTranscriber{static boolean reject;static final List<FutureTask<?>> jobs=new ArrayList<>();static <T>Future<T> afterModelRelease(String c,Callable<T> action){if(reject)throw new RejectedExecutionException();FutureTask<T> t=new FutureTask<>(action);jobs.add(t);return t;}}
public class Probe{
 static Set<String> deletingCodes=ConcurrentHashMap.newKeySet();static String downloadingCode;static File root;static int invalidations,cancels;
 static void invalidateInstalledSizes(){invalidations++;}static void cancelDownload(){cancels++;}static File getModelDir(String code){return new File(root,code);}
 BODIES
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args)throws Exception{root=Files.createTempDirectory("model-delete").toFile();File model=new File(root,"a");model.mkdirs();Files.write(new File(model,"weights").toPath(),new byte[8]);
 int[] completed={0};
 try{
 delete("a",()->completed[0]++);check(isDeleting("a")&&model.exists()&&VoskTranscriber.jobs.size()==1&&completed[0]==0);
 delete("a",null);check(VoskTranscriber.jobs.size()==1);VoskTranscriber.jobs.remove(0).run();check(!model.exists()&&!isDeleting("a")&&AndroidUtilities.ui.size()==1);
 AndroidUtilities.ui.remove(0).run();check(completed[0]==1);
 VoskTranscriber.reject=true;delete("b",()->completed[0]++);check(!isDeleting("b")&&VoskTranscriber.jobs.isEmpty());AndroidUtilities.ui.remove(0).run();check(completed[0]==2);
 delete("",null);delete(null,null);check(root.exists()&&VoskTranscriber.jobs.isEmpty());
 }finally{deleteRecursive(root);}
 }}'''.replace('BODIES',bodies)})
