"""Actual Vosk ownership/admission methods; native recognition and Android codec are explicit hosts."""
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method


def test_model_close_and_deletion_are_serialized_after_recognition_and_admission_is_bounded(tmp_path):
    src=(JAVA/'app/exteraless/speech/VoskTranscriber.java').read_text()
    release='public static synchronized void releaseModel()' if 'public static synchronized void releaseModel()' in src else 'public static void releaseModel()'
    obtain='private static synchronized Model obtainModel(' if 'private static synchronized Model obtainModel(' in src else 'private static Model obtainModel('
    bodies='\n'.join(method(src,s) for s in [release,obtain,'public static void transcribe('])
    for sig in ['private static void closeCachedModel()', 'private static void complete(', 'static <T> Future<T> afterModelRelease(']:
        if sig in src:bodies+='\n'+method(src,sig)
    probe(tmp_path,{'Probe.java':'''import java.io.*;import java.util.concurrent.*;import java.util.concurrent.atomic.*;import java.util.function.*;
class Model{volatile boolean closed;Thread closer;Model(String path){}void close(){closed=true;closer=Thread.currentThread();}}
class VoskManager{static File getModelDir(String c){return new File(".");}}
class FileLog{static void e(Throwable t){}}
class LibVosk{static void setLogLevel(LogLevel l){}}enum LogLevel{WARNINGS}
public class Probe{
 static final ThreadPoolExecutor executor=new ThreadPoolExecutor(1,1,1,TimeUnit.SECONDS,new LinkedBlockingQueue<>());
 static final AtomicBoolean releaseQueued=new AtomicBoolean();static final AtomicInteger pendingTranscriptions=new AtomicInteger();static final int MAX_PENDING_TRANSCRIPTIONS=4;
 static volatile boolean used;static Model cachedModel;static String cachedCode;static boolean logLevelSet;
 static CountDownLatch entered=new CountDownLatch(1),finish=new CountDownLatch(1);
 static String run(String path)throws Exception{Model model=obtainModel(path);entered.countDown();if(!finish.await(5,TimeUnit.SECONDS))throw new IOException("test timeout");if(model.closed)throw new AssertionError("model closed during recognition");return "ok";}
 BODIES
 static void check(boolean b,String why){if(!b)throw new AssertionError(why);}
 public static void main(String[]args)throws Exception{
 try{
  AtomicInteger calls=new AtomicInteger();transcribe("a",(s,e)->calls.incrementAndGet());check(entered.await(2,TimeUnit.SECONDS),"recognition entered");
  Model active=cachedModel;releaseModel();check(!active.closed,"UI release must not close a model still in use");
  for(int i=0;i<10000;i++)releaseModel();check(executor.getQueue().size()==1,"release requests must coalesce");
  finish.countDown();executor.submit(()->{}).get(3,TimeUnit.SECONDS);check(active.closed&&active.closer!=Thread.currentThread()&&calls.get()==1,"close happens on owner after recognition");
  Model b=executor.submit(()->obtainModel("b")).get();check(!b.closed&&"b".equals(cachedCode),"a new model isn't closed by a stale queued release");
  AFTER_RELEASE
  entered=new CountDownLatch(1);finish=new CountDownLatch(1);AtomicInteger done=new AtomicInteger(),busy=new AtomicInteger();
  transcribe("c",(s,e)->done.incrementAndGet());check(entered.await(2,TimeUnit.SECONDS),"second recognition entered");
  for(int i=0;i<3;i++)transcribe("c",(s,e)->done.incrementAndGet());
  transcribe("c",(s,e)->{busy.incrementAndGet();check(e instanceof RejectedExecutionException,"explicit busy result");throw new IllegalStateException("callback failure");});
  check(busy.get()==1,"overload callback is delivered once");check(executor.getQueue().size()==3,"only four heavy jobs admitted including running job");
  finish.countDown();executor.submit(()->{}).get(3,TimeUnit.SECONDS);check(done.get()==4&&busy.get()==1&&pendingTranscriptions.get()==0,"all admitted completions once and admission released");
 }finally{finish.countDown();executor.shutdownNow();executor.awaitTermination(3,TimeUnit.SECONDS);}
 }}'''.replace('BODIES',bodies).replace('AFTER_RELEASE', '''afterModelRelease("a",()->{check(!b.closed,"deleting another language doesn't close current model");return null;}).get();
 afterModelRelease("b",()->{check(b.closed,"deletion runs only after model release");return null;}).get();''' if 'static <T> Future<T> afterModelRelease(' in src else '')})
