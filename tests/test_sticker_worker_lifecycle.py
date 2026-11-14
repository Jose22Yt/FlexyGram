"""Execute the real sheet encoding/cancellation methods with deterministic bitmap ownership."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_sticker_cancellation_recycles_queued_bitmaps_and_ignores_closed_sheet_callbacks(tmp_path):
    source = (JAVA/'app/flexygram/stickers/FlexyStickerSheet.java').read_text()
    functions = method(source, 'private void startEncoding()') + '\n' + method(source, 'public void dismiss()')
    start = source.index('    private static final ThreadPoolExecutor ENCODER')
    executor = source[start:source.index('    private FutureTask<Void>', start)]
    probe(tmp_path, {'Probe.java': '''import java.io.File;import java.util.concurrent.*;import java.util.concurrent.atomic.AtomicReference;
class BottomSheet{public void dismiss(){}}
public class Probe extends BottomSheet{
 EXECUTOR
 FutureTask<Void>encodingTask;boolean dismissed;Bitmap capturedBitmap=new Bitmap();FlexyStickerEncoder.StickerBytes stickerBytes;File stickerFile;TLRPC.TL_document stickerDoc;
 Button sendButton=new Button(),favoriteButton=new Button(),exportButton=new Button();
 static class Button{boolean enabled;void setEnabled(boolean b){enabled=b;}void setAlpha(float f){}}
 static class Bitmap{enum Config{ARGB_8888}boolean recycled;int recycles;Bitmap copied;
 Bitmap copy(Config c,boolean b){return copied=new Bitmap();}boolean isRecycled(){return recycled;}void recycle(){recycled=true;if(++recycles!=1)throw new AssertionError("double recycle");}}
 static class Context{File getCacheDir(){return new File(".");}}Context getContext(){return new Context();}
 static class TLRPC{static class TL_document{}}
 static class FileLog{static void e(Throwable t){}}
 static class FlexyStickerMetadata{static TLRPC.TL_document create(int w,int h,int size,String label){return new TLRPC.TL_document();}}
 static class AndroidUtilities{static ConcurrentLinkedQueue<Runnable>ui=new ConcurrentLinkedQueue<>();static void runOnUIThread(Runnable r){ui.add(r);}}
 static class FlexyStickerEncoder{
  static boolean block;static CountDownLatch entered=new CountDownLatch(1),release=new CountDownLatch(1);
  static class StickerBytes{int width=512,height=512;byte[]bytes={1};}
  static StickerBytes encodeAndRecycle(Bitmap b){try{entered.countDown();if(block)try{release.await();}catch(InterruptedException e){Thread.currentThread().interrupt();}return new StickerBytes();}finally{b.recycle();}}
  static File writeToCache(File f,StickerBytes b){return new File(f,"sticker.webp");}}
 FUNCTIONS
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 static void waitForUi()throws Exception{long end=System.nanoTime()+TimeUnit.SECONDS.toNanos(3);while(AndroidUtilities.ui.isEmpty()&&System.nanoTime()<end)Thread.sleep(1);check(!AndroidUtilities.ui.isEmpty());}
 public static void main(String[]args)throws Exception{
  try{
   Probe success=new Probe();success.startEncoding();waitForUi();AndroidUtilities.ui.remove().run();
   check(success.stickerBytes!=null&&success.sendButton.enabled);success.dismiss();
   Probe closed=new Probe();closed.startEncoding();waitForUi();Bitmap original=closed.capturedBitmap,copy=original.copied;
   closed.dismiss();AndroidUtilities.ui.remove().run();check(closed.stickerBytes==null&&!closed.sendButton.enabled&&original.recycles==1&&copy.recycles==1);
   FlexyStickerEncoder.block=true;FlexyStickerEncoder.entered=new CountDownLatch(1);
   Probe active=new Probe();active.startEncoding();check(FlexyStickerEncoder.entered.await(3,TimeUnit.SECONDS));
   Probe queued=new Probe();queued.startEncoding();Bitmap queuedCopy=queued.capturedBitmap.copied;
   queued.dismiss();check(queuedCopy.recycles==1&&ENCODER.getQueue().isEmpty());
   Bitmap activeCopy=active.capturedBitmap.copied;active.dismiss();FlexyStickerEncoder.release.countDown();
   ENCODER.shutdown();check(ENCODER.awaitTermination(3,TimeUnit.SECONDS));check(activeCopy.recycles==1&&AndroidUtilities.ui.isEmpty());
  }finally{FlexyStickerEncoder.release.countDown();ENCODER.shutdownNow();}
 }
}'''.replace('EXECUTOR', executor).replace('FUNCTIONS', functions)})
