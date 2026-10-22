import java.util.*;
import org.telegram.messenger.BuildConfig;

// Compile and execute the inserted production methods, not a reimplementation.
public class SearchHarness {
    static class Queue {
        List<Runnable> tasks = new ArrayList<>();
        void postRunnable(Runnable r, int delay) { tasks.add(r); }
        void postRunnable(Runnable r) { tasks.add(r); }
        void cancelRunnable(Runnable r) { tasks.remove(r); }
        void run() { new ArrayList<>(tasks).forEach(r -> { tasks.remove(r); r.run(); }); }
    }
    static class Utilities { static Queue searchQueue = new Queue(); }
    static class AndroidUtilities { static Queue ui = new Queue(); static void runOnUIThread(Runnable r) { ui.postRunnable(r); } }
    static class FileLog { static String log = ""; static void e(String value) { log += value; } }
    static class TLRPC { static class User {} }
    static class MessagesStorage {
        static MessagesStorage instance = new MessagesStorage();
        static int account;
        Queue queue = new Queue(); boolean fail; int searches;
        static MessagesStorage getInstance(int a) { account = a; return instance; }
        Queue getStorageQueue() { return queue; }
        void localSearch(int type, String query, ArrayList<Object> result, ArrayList<CharSequence> names,
                         ArrayList<TLRPC.User> users, Object ids, int folder) {
            searches++;
            if (fail) throw new IllegalStateException("PRIVATE_QUERY_SENTINEL");
            result.add(query); names.add(query);
        }
    }
    static class Helper { void clear() {} }
    static class Delegate {
        int calls; boolean loading;
        void searchStateChanged(boolean value, boolean animated) { calls++; loading = value; }
    }
    int offlineSearchGeneration;
    boolean offlineSearchDestroyed;
    Runnable searchRunnable;
    String lastSearchText, publicPostsHashtag;
    int folderId, currentAccount = 3, dialogsType, waitingResponseCount, needMessagesSearch;
    int publicPostsTotalCount, publicPostsLastRate, notifications;
    boolean forceLoadingMessages, messagesSearchEndReached, localMessagesSearchEndReached, searchWas;
    Object filterDialogIds, filtersDelegate = new Object();
    Helper searchAdapterHelper = new Helper(); Delegate delegate = new Delegate();
    ArrayList<Object> searchResult = new ArrayList<>(), searchResultMessages = new ArrayList<>(),
            searchForumResultMessages = new ArrayList<>(), searchResultHashtags = new ArrayList<>(),
            searchTopics = new ArrayList<>(), publicPosts = new ArrayList<>();
    ArrayList<CharSequence> searchResultNames = new ArrayList<>();
    void filterRecent(String query) {}
    boolean filter(Object value) { return !value.equals("filtered"); }
    void notifyDataSetChanged() { notifications++; }
    /* METHODS */
    static void expect(boolean condition, String message) { if (!condition) throw new AssertionError(message); }
    static void finish() { Utilities.searchQueue.run(); MessagesStorage.instance.queue.run(); AndroidUtilities.ui.run(); }
    public static void main(String[] args) {
        SearchHarness h = new SearchHarness();
        h.searchOfflineDialogs(" First ", 0);
        expect(h.waitingResponseCount == 1 && h.delegate.loading, "only local callback pending");
        expect(h.messagesSearchEndReached && h.localMessagesSearchEndReached, "remote pagination off");
        finish();
        expect(h.searchResult.equals(List.of("first")) && h.searchResultNames.equals(List.of("first")), "native local results");
        expect(h.waitingResponseCount == 0 && !h.delegate.loading, "loading ends");
        expect(MessagesStorage.account == 3, "account preserved");
        h.searchOfflineDialogs("older", 0); Utilities.searchQueue.run(); MessagesStorage.instance.queue.run();
        h.searchOfflineDialogs("newer", 1); AndroidUtilities.ui.run();
        expect(h.searchResult.isEmpty() && h.waitingResponseCount == 1, "stale callback cannot end newer loading");
        finish(); expect(h.searchResult.equals(List.of("newer")) && h.folderId == 1, "newest query wins");
        h.searchOfflineDialogs("filtered", 0); finish(); expect(h.searchResult.isEmpty(), "native peer filter retained");
        MessagesStorage.instance.fail = true;
        h.searchOfflineDialogs("PRIVATE_QUERY_SENTINEL", 0); finish();
        expect(h.waitingResponseCount == 0 && h.searchResult.isEmpty(), "failure terminates loading");
        expect(FileLog.log.contains("IllegalStateException") && !FileLog.log.contains("PRIVATE_QUERY_SENTINEL"), "safe failure diagnostic");
        MessagesStorage.instance.fail = false;
        h.searchOfflineDialogs("cancelled", 0); Utilities.searchQueue.run(); MessagesStorage.instance.queue.run();
        h.cancelOfflineSearch(); AndroidUtilities.ui.run();
        expect(h.searchResult.isEmpty() && h.delegate == null && h.filtersDelegate == null, "destroy discards callback references");
        int n = h.notifications; h.searchOfflineDialogs("after destruction", 0); finish();
        expect(h.notifications == n && h.waitingResponseCount == 0, "destroyed instance inert");
        SearchHarness recreated = new SearchHarness(); recreated.searchOfflineDialogs("recreated", 0); finish();
        expect(recreated.searchResult.equals(List.of("recreated")), "new view searches independently");
        recreated.searchOfflineDialogs("  ", 0); finish(); expect(recreated.waitingResponseCount == 0 && !recreated.searchWas, "clearing query");
        recreated.needMessagesSearch = 2; int before = MessagesStorage.instance.searches;
        recreated.searchOfflineDialogs("message filter without transport", 0); finish();
        expect(recreated.waitingResponseCount == 0 && before == MessagesStorage.instance.searches, "message only search never waits for disabled provider");
        BuildConfig.FLEXYGRAM_VARIANT = "diagnostic";
        SearchHarness normal = new SearchHarness(); normal.cancelOfflineSearch();
        expect(!normal.offlineSearchDestroyed && normal.delegate != null, "other profile no effect");
        System.out.println("SearchHarness PASS (local queue/storage/UI doubles; no Android or transport)");
    }
}
