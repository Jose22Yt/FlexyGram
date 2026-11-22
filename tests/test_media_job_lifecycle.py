from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_media_store_publishes_only_a_closed_successful_export(tmp_path):
    source = (JAVA / 'org/telegram/messenger/MediaController.java').read_text()
    write_pending = method(source, 'private static Uri writePendingMedia(')
    probe(tmp_path, {'Probe.java': '''import java.io.*;
import java.util.function.BooleanSupplier;
public class Probe {
    interface MediaWriter { void write(OutputStream stream) throws IOException; }
    record Uri(String name) {}
    static class ContentValues {
        int pending=-1;
        ContentValues(int size) {}
        void put(String key,int value) { pending=value; }
    }
    static class MediaStore { static class MediaColumns { static final String IS_PENDING="pending"; } }
    static class FileLog { static void e(RuntimeException e) { throw new AssertionError(e); } }
    static class ContentResolver {
        int inserts, updates, deletes; boolean closed, failClose, noStream, publish=true;
        Uri insert(Uri collection,ContentValues values) {
            check(values.pending==1); inserts++; return new Uri("new-entry");
        }
        OutputStream openOutputStream(Uri entry) {
            if (noStream) return null;
            return new OutputStream() {
                public void write(int value) {}
                public void close() throws IOException { closed=true; if (failClose) throw new IOException("close"); }
            };
        }
        int update(Uri entry,ContentValues values,Object selection,Object args) {
            check(closed && values.pending==0); updates++; return publish ? 1 : 0;
        }
        int delete(Uri entry,Object selection,Object args) { deletes++; return 1; }
    }
    WRITE_PENDING
    static void check(boolean valid) { if (!valid) throw new AssertionError(); }
    public static void main(String[] args) throws IOException {
        Uri collection=new Uri("collection");
        ContentResolver success=new ContentResolver();
        check(writePendingMedia(success,collection,new ContentValues(1),() -> false, out -> out.write(42))!=null);
        check(success.inserts==1 && success.updates==1 && success.deletes==0);
        ContentResolver before=new ContentResolver();
        check(writePendingMedia(before,collection,new ContentValues(1),() -> true, out -> {throw new AssertionError();})==null);
        check(before.inserts==0);
        ContentResolver during=new ContentResolver(); boolean[] cancelled={false};
        check(writePendingMedia(during,collection,new ContentValues(1),() -> cancelled[0], out -> {
            out.write(1); cancelled[0]=true;
        })==null);
        check(during.closed && during.updates==0 && during.deletes==1);
        for (boolean failClose : new boolean[]{false,true}) {
            ContentResolver failing=new ContentResolver(); failing.failClose=failClose;
            try {
                writePendingMedia(failing,collection,new ContentValues(1),() -> false, out -> {
                    if (!failClose) throw new IOException("write");
                });
                throw new AssertionError("expected IOException");
            } catch (IOException expected) {}
            check(failing.closed && failing.updates==0 && failing.deletes==1);
        }
        ContentResolver noStream=new ContentResolver(); noStream.noStream=true;
        check(writePendingMedia(noStream,collection,new ContentValues(1),() -> false, out -> {})==null);
        check(noStream.updates==0 && noStream.deletes==1);
        ContentResolver rejected=new ContentResolver(); rejected.publish=false;
        check(writePendingMedia(rejected,collection,new ContentValues(1),() -> false, out -> {})==null);
        check(rejected.updates==1 && rejected.deletes==1);
    }
}'''.replace('WRITE_PENDING', write_pending)})


def test_playback_queues_one_tick_and_switches_cadence_with_visibility(tmp_path):
    source = (JAVA / 'org/telegram/messenger/MediaController.java').read_text()
    methods = '\n'.join(method(source, signature) for signature in (
        'private void startProgressTimer()', 'private void stopProgressTimer()',
        'public static void onPlaybackUiVisibilityChanged()',
    ))
    probe(tmp_path, {'Probe.java': '''
public class Probe {
    static class ApplicationLoader {
        static boolean mainInterfacePaused, externalInterfacePaused;
    }
    static class AndroidUtilities {
        static Runnable queued; static int delay;
        static void runOnUIThread(Runnable task) { runOnUIThread(task,0); }
        static void runOnUIThread(Runnable task, int ms) {
            if (queued!=null) throw new AssertionError("duplicate tick");
            queued=task; delay=ms;
        }
        static void cancelRunOnUIThread(Runnable task) { if (queued==task) queued=null; }
        static void runTick() { Runnable task=queued; queued=null; task.run(); }
    }
    static Probe Instance;
    Runnable playbackProgressTick;
    boolean runningPlaybackProgressTick, refreshDuringTick;
    Object videoPlayer;
    int updates;
    void updatePlaybackProgress() { updates++; if (refreshDuringTick) onPlaybackUiVisibilityChanged(); }
    METHODS
    static void check(boolean value) { if (!value) throw new AssertionError(); }
    public static void main(String[] args) {
        onPlaybackUiVisibilityChanged(); check(AndroidUtilities.queued==null);
        Probe p=Instance=new Probe(); p.startProgressTimer();
        Runnable old=AndroidUtilities.queued; AndroidUtilities.runTick(); check(AndroidUtilities.delay==17);
        ApplicationLoader.mainInterfacePaused=ApplicationLoader.externalInterfacePaused=true;
        onPlaybackUiVisibilityChanged(); check(AndroidUtilities.delay==0);
        AndroidUtilities.runTick(); check(AndroidUtilities.delay==1000);
        ApplicationLoader.mainInterfacePaused=false;
        onPlaybackUiVisibilityChanged(); check(AndroidUtilities.delay==0);
        p.refreshDuringTick=true; AndroidUtilities.runTick(); check(AndroidUtilities.delay==17);
        p.startProgressTimer(); old.run(); check(p.updates==3);
        ApplicationLoader.mainInterfacePaused=true; p.videoPlayer=new Object();
        AndroidUtilities.runTick(); check(AndroidUtilities.delay==17);
        p.stopProgressTimer(); check(AndroidUtilities.queued==null);
    }
}'''.replace('METHODS', methods).replace('final MediaController controller', 'final Probe controller')})


def test_export_cancellation_releases_both_live_photo_files_and_skips_delayed_loads(tmp_path):
    source = (JAVA / 'org/telegram/messenger/MediaController.java').read_text()
    loader = source[source.index('private static class MediaLoader'):]
    methods = '\n'.join(method(loader, signature) for signature in (
        'private void cancel()', 'private static void releaseWait(', 'private void awaitFiles(',
    ))
    probe(tmp_path, {'Probe.java': '''import java.util.*;
import java.util.concurrent.*;
import java.util.function.Consumer;
public class Probe {
    static class AndroidUtilities {
        static final BlockingQueue<Runnable> ui=new LinkedBlockingQueue<>();
        static void runOnUIThread(Runnable task) { ui.add(task); }
    }
    static class FileLog { static int errors; static void e(Exception e) { errors++; } }
    volatile boolean cancelled;
    volatile CountDownLatch waitingForFile;
    final Map<String,CountDownLatch> pendingFileLoads=new HashMap<>();
    METHODS
    static void check(boolean value) { if (!value) throw new AssertionError(); }
    Thread waitForTwo(Consumer<CountDownLatch> work) {
        Thread worker=new Thread(() -> {
            try { awaitFiles(2,work); } catch (InterruptedException failure) { throw new AssertionError(failure); }
        });
        worker.setDaemon(true); worker.start(); return worker;
    }
    static Runnable nextUi() throws InterruptedException {
        Runnable task=AndroidUtilities.ui.poll(2,TimeUnit.SECONDS); check(task!=null); return task;
    }
    static void finished(Thread worker) throws InterruptedException { worker.join(2000); check(!worker.isAlive()); }
    public static void main(String[] args) throws Exception {
        Probe beforeStart=new Probe(); Thread first=beforeStart.waitForTwo(latch -> { throw new AssertionError(); });
        Runnable delayed=nextUi(); beforeStart.cancel(); finished(first); delayed.run();
        check(beforeStart.waitingForFile==null && beforeStart.pendingFileLoads.isEmpty());
        Probe during=new Probe(); Thread second=during.waitForTwo(latch -> {
            during.pendingFileLoads.put("photo",latch); during.pendingFileLoads.put("video",latch);
        });
        nextUi().run(); during.pendingFileLoads.remove("photo").countDown();
        check(during.waitingForFile.getCount()==1);
        during.cancel(); finished(second); check(during.waitingForFile==null);
        Probe failing=new Probe(); Thread third=failing.waitForTwo(latch -> {
            failing.pendingFileLoads.put("photo",latch); throw new IllegalStateException();
        });
        nextUi().run(); finished(third);
        check(failing.pendingFileLoads.isEmpty() && FileLog.errors==1);
    }
}'''.replace('METHODS', methods)})
