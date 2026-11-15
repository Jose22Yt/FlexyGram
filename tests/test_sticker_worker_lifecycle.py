"""Execute the real sheet encoding/cancellation methods with deterministic bitmap ownership."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_sticker_cancellation_recycles_queued_bitmaps_and_ignores_closed_sheet_callbacks(tmp_path):
    source = (JAVA/'app/flexygram/stickers/FlexyStickerSheet.java').read_text()
    functions = method(source, 'private void startEncoding()') + '\n' + method(source, 'public void dismiss()')
    start = source.index('    private static final ThreadPoolExecutor ENCODER')
    executor = source[start:source.index('    private FutureTask<Void>', start)]
    probe(tmp_path, {'Probe.java': '''import java.io.File;import java.io.InterruptedIOException;import java.util.concurrent.*;import java.util.concurrent.atomic.AtomicReference;
class BottomSheet{public void dismiss(){}}
public class Probe extends BottomSheet{
 static File cache;
 EXECUTOR
 FutureTask<Void>encodingTask;boolean dismissed;Bitmap capturedBitmap=new Bitmap();FlexyStickerEncoder.StickerBytes stickerBytes;File stickerFile;TLRPC.TL_document stickerDoc;
 Button sendButton=new Button(),favoriteButton=new Button(),exportButton=new Button();
 static class Button{boolean enabled;void setEnabled(boolean b){enabled=b;}void setAlpha(float f){}}
 static class Bitmap{enum Config{ARGB_8888}boolean recycled;int recycles;Bitmap copied;
 Bitmap copy(Config c,boolean b){return copied=new Bitmap();}boolean isRecycled(){return recycled;}void recycle(){recycled=true;if(++recycles!=1)throw new AssertionError("double recycle");}}
 static class Context{File getCacheDir(){return cache;}}Context getContext(){return new Context();}
 static class TLRPC{static class TL_document{}}
 static class FileLog{static void e(Throwable t){}}
 static class FlexyStickerMetadata{static TLRPC.TL_document create(int w,int h,int size,String label){return new TLRPC.TL_document();}}
 static class AndroidUtilities{static ConcurrentLinkedQueue<Runnable>ui=new ConcurrentLinkedQueue<>();static void runOnUIThread(Runnable r){ui.add(r);}}
 static class FlexyStickerEncoder{
  static boolean block;static CountDownLatch entered=new CountDownLatch(1),release=new CountDownLatch(1);
  static class StickerBytes{int width=512,height=512;byte[]bytes={1};}
  static StickerBytes encodeAndRecycle(Bitmap b){try{entered.countDown();if(block)try{release.await();}catch(InterruptedException e){Thread.currentThread().interrupt();}return new StickerBytes();}finally{b.recycle();}}
  static File writeToCache(File f,StickerBytes b){try{File file=File.createTempFile("sticker-",".webp",f);java.nio.file.Files.write(file.toPath(),b.bytes);return file;}catch(java.io.IOException e){throw new RuntimeException(e);}}}
 FUNCTIONS
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 static void waitForUi()throws Exception{long end=System.nanoTime()+TimeUnit.SECONDS.toNanos(3);while(AndroidUtilities.ui.isEmpty()&&System.nanoTime()<end)Thread.sleep(1);check(!AndroidUtilities.ui.isEmpty());}
 public static void main(String[]args)throws Exception{
  cache=java.nio.file.Files.createTempDirectory("sticker-preview-").toFile();
  try{
   Probe success=new Probe();success.startEncoding();waitForUi();AndroidUtilities.ui.remove().run();
   check(success.stickerBytes!=null&&success.sendButton.enabled&&success.stickerFile.isFile());success.dismiss();check(cache.list().length==0);
   Probe closed=new Probe();closed.startEncoding();waitForUi();Bitmap original=closed.capturedBitmap,copy=original.copied;
   closed.dismiss();AndroidUtilities.ui.remove().run();check(closed.stickerBytes==null&&!closed.sendButton.enabled&&original.recycles==1&&copy.recycles==1&&cache.list().length==0);
   FlexyStickerEncoder.block=true;FlexyStickerEncoder.entered=new CountDownLatch(1);
   Probe active=new Probe();active.startEncoding();check(FlexyStickerEncoder.entered.await(3,TimeUnit.SECONDS));
   Probe queued=new Probe();queued.startEncoding();Bitmap queuedCopy=queued.capturedBitmap.copied;
   queued.dismiss();check(queuedCopy.recycles==1&&ENCODER.getQueue().isEmpty());
   Bitmap activeCopy=active.capturedBitmap.copied;active.dismiss();FlexyStickerEncoder.release.countDown();
   ENCODER.shutdown();check(ENCODER.awaitTermination(3,TimeUnit.SECONDS));check(activeCopy.recycles==1&&AndroidUtilities.ui.isEmpty()&&cache.list().length==0);
  }finally{FlexyStickerEncoder.release.countDown();ENCODER.shutdownNow();for(File file:cache.listFiles())file.delete();cache.delete();}
 }
}'''.replace('EXECUTOR', executor).replace('FUNCTIONS', functions)})


def test_preview_hands_off_files_before_dismiss_and_failed_picker_keeps_preview(tmp_path):
    source = (JAVA/'app/flexygram/stickers/FlexyStickerSheet.java').read_text()
    functions = '\n'.join(method(source, signature) for signature in (
        'private void onSendClicked(', 'private void onExportClicked()', 'public void dismiss()'))
    probe(tmp_path, {'Probe.java': '''import java.io.*;import java.util.concurrent.*;
class BottomSheet{public void dismiss(){}}
public class Probe extends BottomSheet{
 static ThreadPoolExecutor ENCODER=new ThreadPoolExecutor(0,1,1,TimeUnit.SECONDS,new ArrayBlockingQueue<>(1));
 FutureTask<Void>encodingTask;boolean dismissed;Bitmap capturedBitmap;File stickerFile;TLRPC.TL_document stickerDoc=new TLRPC.TL_document();
 Object sendButton=new Object(),exportButton=new Object();Fragment fragment=new Fragment();
 static class Bitmap{boolean isRecycled(){return false;}void recycle(){}}
 static class TLRPC{static class Document{}static class TL_document extends Document{}}
 static class Fragment{boolean accepts;File exported;boolean exportFlexySticker(File f){if(accepts)exported=f;return accepts;}}
 static class AndroidUtilities{static void vibrateCursor(Object v){}}
 static class FileLog{static void e(Throwable t){}}
 static class LocaleController{static String getString(int r){return "result";}}
 static class R{static class string{static final int FlexyStickerSavedFavorite=1,FlexyStickerSent=2,ErrorOccurred=3;}static class drawable{static final int stickers_favorites_remix=1,msg_send_remix=2;}}
 static class BulletinFactory{static boolean canShowBulletin(Object f){return false;}static BulletinFactory of(Object f){return new BulletinFactory();}BulletinFactory createSimpleBulletin(int id,String text){return this;}BulletinFactory createErrorBulletin(String text){return this;}void show(){}}
 static class FlexyStickerSender{interface Callback{void onSuccess(TLRPC.Document d);void onError(Throwable error);}static File source;
  static void send(Fragment f,File file,TLRPC.TL_document doc,boolean favorites,Callback cb){if(!file.isFile())throw new AssertionError("dismiss deleted the transport source");source=file;}}
 FUNCTIONS
 static void check(boolean b){if(!b)throw new AssertionError();}
 static File file()throws Exception{return File.createTempFile("preview-handoff-",".webp");}
 public static void main(String[]args)throws Exception{
  Probe p=new Probe();p.stickerFile=file();File send=p.stickerFile;p.onSendClicked(false);check(p.dismissed&&p.stickerFile==null&&send.isFile()&&FlexyStickerSender.source==send);send.delete();
  p=new Probe();p.stickerFile=file();File export=p.stickerFile;p.onExportClicked();check(!p.dismissed&&p.stickerFile==export&&export.isFile());
  p.fragment.accepts=true;p.onExportClicked();check(p.dismissed&&p.stickerFile==null&&p.fragment.exported==export&&export.isFile());export.delete();
  p=new Probe();p.stickerFile=file();File discard=p.stickerFile;p.dismiss();p.dismiss();check(!discard.exists()&&p.stickerFile==null);
  ENCODER.shutdownNow();
 }
}'''.replace('FUNCTIONS', functions)})
