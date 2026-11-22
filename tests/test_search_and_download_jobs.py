from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_download_search_retires_work_when_text_repeats_or_view_detaches(tmp_path):
    source = (JAVA / 'org/telegram/ui/Components/SearchDownloadsContainer.java').read_text()
    update = method(source, 'public void update(boolean animated)')
    detach = method(source, 'protected void onDetachedFromWindow()')
    cancel = method(source, 'private long cancelPendingSearch()')
    assert 'final long generation = cancelPendingSearch()' in update
    assert 'if (generation != searchGeneration) return;' in update
    assert 'if (generation == searchGeneration)' in update
    assert 'setQuery(searchQuery)' not in update and update.count('setQuery(query)') == 2
    assert 'cancelPendingSearch()' in detach
    probe(tmp_path, {'Probe.java': '''
public class Probe {
    static class Queue { int cancellations; void cancelRunnable(Runnable task) { cancellations++; } }
    static class Utilities { static final Queue searchQueue=new Queue(); }
    private volatile long searchGeneration;
    Runnable lastSearchRunnable;
    CANCEL_METHOD
    static void check(boolean valid) { if (!valid) throw new AssertionError(); }
    public static void main(String[] args) {
        Probe p=new Probe();
        long first=p.cancelPendingSearch(); p.lastSearchRunnable=() -> {};
        p.cancelPendingSearch(); // Clearing the text.
        long repeated=p.cancelPendingSearch(); p.lastSearchRunnable=() -> {};
        check(repeated!=first && repeated==p.searchGeneration);
        p.cancelPendingSearch(); // Detaching the search view.
        check(repeated!=p.searchGeneration && p.lastSearchRunnable==null && Utilities.searchQueue.cancellations==2);
    }
}'''.replace('CANCEL_METHOD', cancel)})


def test_local_search_ignores_old_disk_jobs_and_filter_callbacks(tmp_path):
    source = (JAVA / 'org/telegram/ui/Adapters/DialogsSearchAdapter.java').read_text()
    search = method(source, 'private void searchDialogsInternal(')
    begin = method(source, 'public void searchDialogs(')
    publish = method(source, 'private void updateSearchResults(')
    assert begin.count('++lastSearchId') == 1 and 'lastSearchId = 0' not in source
    assert publish.index('if (searchId != lastSearchId)') < publish.index('waitingResponseCount--')
    probe(tmp_path, {'Probe.java': '''import java.util.*;
public class Probe {
    static class Queue {
        final ArrayDeque<Runnable> tasks=new ArrayDeque<>(); boolean accept=true;
        boolean postRunnable(Runnable work) { if (accept) tasks.add(work); return accept; }
        void run() { tasks.remove().run(); }
    }
    static class AndroidUtilities {
        static final Queue ui=new Queue();
        static void runOnUIThread(Runnable work) { ui.postRunnable(work); }
    }
    static class TLRPC { static class User {} }
    static class ContactsController { static class Contact {} }
    static class LocaleController { static String getString(int id) { return "Archive"; } }
    static class R { static class string { static final int ArchiveSearchFilter=1; } }
    static class FiltersView {
        record DateData(String query) {}
        static void fillTipDates(String query, List<DateData> dates) { dates.add(new DateData(query)); }
    }
    static class MessagesStorage {
        static final MessagesStorage instance=new MessagesStorage();
        static MessagesStorage getInstance(int account) { return instance; }
        final Queue disk=new Queue(); int reads;
        Queue getStorageQueue() { return disk; }
        void localSearch(int type, String q, Object... results) { reads++; }
    }
    interface FilterDelegate {
        void updateFiltersView(boolean flag, Object unused, ArrayList<FiltersView.DateData> dates, boolean archive);
    }
    int lastSearchId=1, currentAccount, needMessagesSearch, dialogsType;
    Object filterDialogIds;
    ArrayList<FiltersView.DateData> localTipDates=new ArrayList<>();
    boolean localTipArchive;
    final List<String> published=new ArrayList<>();
    FilterDelegate filtersDelegate=(flag, unused, dates, archive) -> published.add(dates.get(0).query());
    int callbacks;
    void updateSearchResults(ArrayList<Object> result, ArrayList<CharSequence> names,
            ArrayList<TLRPC.User> users, ArrayList<ContactsController.Contact> contacts, int id) { callbacks++; }
    SEARCH_METHOD
    static void check(boolean valid) { if (!valid) throw new AssertionError(); }
    public static void main(String[] args) {
        Probe p=new Probe(); MessagesStorage storage=MessagesStorage.instance;
        p.searchDialogsInternal("archive",1); p.lastSearchId=2; storage.disk.run();
        check(storage.reads==0 && p.callbacks==0);
        p.searchDialogsInternal("archive",2); storage.disk.run(); p.lastSearchId=3;
        AndroidUtilities.ui.run(); check(p.published.isEmpty() && !p.localTipArchive);
        p.searchDialogsInternal("today",3); storage.disk.run(); AndroidUtilities.ui.run();
        check(p.published.equals(List.of("today")) && p.localTipDates.get(0).query().equals("today"));
        storage.disk.accept=false; p.searchDialogsInternal("tomorrow",3);
        check(p.callbacks==3 && storage.reads==2);
    }
}'''.replace('SEARCH_METHOD', search)})


def test_file_probe_returns_on_queue_rejection_or_database_failure(tmp_path):
    source = (JAVA / 'org/telegram/messenger/FilePathDatabase.java').read_text()
    check_media = method(source, 'public void checkMediaExistance(')
    probe(tmp_path, {'Probe.java': '''import java.util.*;
import java.util.concurrent.CountDownLatch;
public class Probe {
    static class BuildVars { static final boolean DEBUG_VERSION=false; }
    static class Looper { static Looper getMainLooper() { return new Looper(); } Thread getThread() { return null; } }
    static class FileLog { static int errors; static void e(Throwable e) { errors++; } static void d(String s) {} }
    static class MessageObject { int reads; void checkMediaExistance(boolean unused) { reads++; } }
    boolean accept=true, fail;
    boolean postToFrontRunnable(Runnable runnable) { if (accept) runnable.run(); return accept; }
    void ensureDatabaseCreated() { if (fail) throw new IllegalStateException(); }
    CHECK_MEDIA
    static void check(boolean valid) { if (!valid) throw new AssertionError(); }
    public static void main(String[] args) throws InterruptedException {
        Probe p=new Probe(); MessageObject message=new MessageObject();
        ArrayList<MessageObject> files=new ArrayList<>(List.of(message));
        Thread work=new Thread(() -> {
            p.checkMediaExistance(files);
            p.fail=true; p.checkMediaExistance(files);
            p.accept=false; p.checkMediaExistance(files);
        });
        work.setDaemon(true); work.start(); work.join(2000);
        check(!work.isAlive() && message.reads==1 && FileLog.errors==1);
    }
}'''.replace('CHECK_MEDIA', check_media)})


def test_download_history_batches_file_checks_and_keeps_published_lists_on_read_error(tmp_path):
    source = (JAVA / 'org/telegram/messenger/DownloadController.java').read_text()
    load = method(source, 'public void loadDownloadingFiles()')
    probe(tmp_path, {'Probe.java': '''import java.util.*;
public class Probe {
    static class FileLog { static int errors; static void e(Exception error) { errors++; } }
    static class AndroidUtilities { static void runOnUIThread(Runnable work) { work.run(); } }
    static class Queue { boolean postRunnable(Runnable work) { work.run(); return true; } }
    static class SQLitePreparedStatement {
        int closes; void step() {} void dispose() { closes++; }
    }
    static class NativeByteBuffer {
        int reused; int readInt32(boolean unused) { return 1; } void reuse() { reused++; }
    }
    static class SQLiteCursor {
        int row=-1, closes;
        boolean fail;
        final NativeByteBuffer[] rows={new NativeByteBuffer(),new NativeByteBuffer()};
        boolean next() { return ++row<rows.length; }
        NativeByteBuffer byteBufferValue(int column) { return rows[row]; }
        int intValue(int column) { if (fail && row==1) throw new IllegalStateException(); return row; }
        void dispose() { closes++; }
    }
    static class Database {
        SQLitePreparedStatement trim; SQLiteCursor cursor; boolean fail;
        SQLitePreparedStatement executeFast(String sql) { return trim=new SQLitePreparedStatement(); }
        SQLiteCursor queryFinalized(String sql) { cursor=new SQLiteCursor(); cursor.fail=fail; return cursor; }
    }
    static class Storage {
        final Database db=new Database(); Queue getStorageQueue() { return new Queue(); }
        Database getDatabase() { return db; }
    }
    static class TLRPC { static class Message {
        static Message TLdeserialize(NativeByteBuffer data,int constructor,boolean unused) { return new Message(); }
        void readAttachPath(NativeByteBuffer data,long client) {}
    } }
    static class UserConfig {
        static UserConfig getInstance(int account) { return new UserConfig(); } long clientUserId;
    }
    static class MessageObject { MessageObject(int account,TLRPC.Message owner,boolean a,boolean b) {} }
    static class FileLoader {
        int batches, size;
        void checkMediaExistance(ArrayList<MessageObject> messages) { batches++; size=messages.size(); }
    }
    int currentAccount; final Storage storage=new Storage(); final FileLoader loader=new FileLoader();
    final ArrayList<MessageObject> downloadingFiles=new ArrayList<>(), recentDownloadingFiles=new ArrayList<>();
    Storage getMessagesStorage() { return storage; } FileLoader getFileLoader() { return loader; }
    LOAD_METHOD
    static void check(boolean valid) { if (!valid) throw new AssertionError(); }
    public static void main(String[] args) {
        Probe p=new Probe(); p.loadDownloadingFiles();
        check(p.loader.batches==1 && p.loader.size==2);
        check(p.downloadingFiles.size()==1 && p.recentDownloadingFiles.size()==1);
        MessageObject published=p.downloadingFiles.get(0);
        p.storage.db.fail=true; p.loadDownloadingFiles();
        check(p.loader.batches==1 && p.downloadingFiles.get(0)==published && p.recentDownloadingFiles.size()==1);
        check(FileLog.errors==1 && p.storage.db.cursor.closes==1 && p.storage.db.trim.closes==1);
        for (NativeByteBuffer row:p.storage.db.cursor.rows) check(row.reused==1);
    }
}'''.replace('LOAD_METHOD', load)})
