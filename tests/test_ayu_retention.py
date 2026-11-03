"""Host regressions for deletion ordering and empty channel history.

These exercise extracted production control flow with deterministic queues;
Android UI and the actual Room database still need device validation.
"""
import pathlib
import shutil
import subprocess
import tempfile

import pytest

from test_composer_layout import method


def run_java(harness):
    with tempfile.TemporaryDirectory(prefix="flexygram-ayu-") as directory:
        path = pathlib.Path(directory) / "AyuRegression.java"
        path.write_text(harness)
        result = subprocess.run(["javac", "-d", directory, str(path)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        result = subprocess.run(["java", "-cp", directory, "AyuRegression"], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


@pytest.mark.skipif(not shutil.which("javac") or not shutil.which("java"), reason="JDK required")
def test_remote_deletion_is_saved_before_storage_delete():
    root = pathlib.Path(__file__).resolve().parents[1]
    source = (root / "TMessagesProj/src/main/java/org/telegram/messenger/MessagesController.java").read_text()
    source = source[source.index("// --- AyuGram request hook\n        if (NaConfig.INSTANCE.getEnableSaveDeletedMessages().Bool() && deletedMessages != null)"):]
    hook = method(source, "if (NaConfig.INSTANCE.getEnableSaveDeletedMessages().Bool() && deletedMessages != null)")
    harness = """
import java.util.*;
public class AyuRegression {
    static class LongSparseArray<T> {
        final LinkedHashMap<Long,T> entries=new LinkedHashMap<>();
        int size(){return entries.size();}boolean isEmpty(){return entries.isEmpty();}
        long keyAt(int i){return new ArrayList<>(entries.keySet()).get(i);}
        T valueAt(int i){return new ArrayList<>(entries.values()).get(i);}
        void put(long key,T value){entries.put(key,value);}
        public LongSparseArray<T> clone(){LongSparseArray<T> copy=new LongSparseArray<>();copy.entries.putAll(entries);return copy;}
    }
    static class Message {int id;long sender;Message(int id,long sender){this.id=id;this.sender=sender;}}
    static class Queue {
        final ArrayList<Runnable> tasks=new ArrayList<>();
        void postRunnable(Runnable r){tasks.add(r);}void drain(){while(!tasks.isEmpty())tasks.remove(0).run();}
    }
    static class Storage {
        final Queue queue=new Queue();final Map<Long,ArrayList<Message>> messages=new HashMap<>();
        Queue getStorageQueue(){return queue;}
        ArrayList<Long> getDialogIdsToUpdate(long id,ArrayList<Integer> mids){return new ArrayList<>(List.of(10L));}
    }
    static final Storage storage=new Storage();
    static class Flag {boolean value=true;boolean Bool(){return value;}}
    static class NaConfig {
        static final NaConfig INSTANCE=new NaConfig();Flag enabled=new Flag();
        Flag getEnableSaveDeletedMessages(){return enabled;}
    }
    static class AyuState {static boolean isDeletePermitted(long d,int id){return id==3;}}
    static class AyuSavePreferences {
        final Message message;final long dialogId;
        AyuSavePreferences(Message m,int a,long d,long t,int id,int time){message=m;dialogId=d;}
        long getFromUserId(){return message.sender;}
        static boolean saveDeletedMessageFor(int a,long d,long sender){return d!=-30&&sender!=999;}
    }
    static class MessageObject {static long getTopicId(int a,Message m,boolean forum){return 0;}}
    static class MessageHelper {
        static MessageHelper getInstance(int a){return new MessageHelper();}
        ArrayList<Message> getMessagesStorageMessages(long d,ArrayList<Integer> ids){
            ArrayList<Message> found=new ArrayList<>();
            for(Message m:storage.messages.getOrDefault(d,new ArrayList<>()))if(ids.contains(m.id))found.add(m);
            return found;
        }
    }
    static class AyuMessagesController {
        static final AyuMessagesController INSTANCE=new AyuMessagesController();
        final Set<String> saved=new HashSet<>();final Queue global=new Queue();
        static AyuMessagesController getInstance(){return INSTANCE;}
        void onMessageDeleted(AyuSavePreferences prefs){onMessageDeleted(prefs,true);}
        void onMessageDeleted(AyuSavePreferences prefs,boolean queue){
            Runnable save=()->saved.add(prefs.dialogId+":"+prefs.message.id);
            if(queue)global.postRunnable(save);else save.run();
        }
    }
    static class AndroidUtilities {static final Queue ui=new Queue();static void runOnUIThread(Runnable r){ui.postRunnable(r);}}
    static class AyuConstants {static final int MESSAGES_DELETED_NOTIFICATION=1;}
    static class Notifications {
        final Map<Long,ArrayList<Integer>> deleted=new HashMap<>();
        void postNotificationName(int event,long d,ArrayList<Integer> ids){deleted.put(d,ids);}
    }
    final Notifications notifications=new Notifications();int currentAccount;
    Storage getMessagesStorage(){return storage;}Notifications getNotificationCenter(){return notifications;}
    boolean isForum(long d){return false;}
    void process(LongSparseArray<ArrayList<Integer>> deletedMessages){long currentTime=1000; HOOK }
    static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    public static void main(String[] args){
        AyuRegression c=new AyuRegression();
        storage.messages.put(10L,new ArrayList<>(List.of(new Message(1,12),new Message(3,12),new Message(4,999))));
        storage.messages.put(-20L,new ArrayList<>(List.of(new Message(2,0))));
        storage.messages.put(-30L,new ArrayList<>(List.of(new Message(5,0))));
        LongSparseArray<ArrayList<Integer>> deletes=new LongSparseArray<>();
        deletes.put(0,new ArrayList<>(List.of(1,3,4)));deletes.put(-20,new ArrayList<>(List.of(2)));deletes.put(-30,new ArrayList<>(List.of(5)));
        c.process(deletes);
        storage.queue.postRunnable(()->{
            require(AyuMessagesController.INSTANCE.saved.contains("10:1"),"private copy must exist before delete");
            require(AyuMessagesController.INSTANCE.saved.contains("-20:2"),"channel copy must exist before delete");
            storage.messages.clear();
        });
        storage.queue.drain();AndroidUtilities.ui.drain();
        require(c.notifications.deleted.get(10L).equals(List.of(1)),"exclude manual deletion and excluded sender");
        require(c.notifications.deleted.get(-20L).equals(List.of(2)),"channel notification stays scoped");
        require(!c.notifications.deleted.containsKey(-30L),"excluded chat must not be marked preserved");
    }
}
""".replace("HOOK", hook)
    run_java(harness)


@pytest.mark.skipif(not shutil.which("javac") or not shutil.which("java"), reason="JDK required")
def test_empty_channel_history_and_channel_user_namespace():
    root = pathlib.Path(__file__).resolve().parents[1]
    chat = (root / "TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java").read_text()
    start = chat.index("if (!messages.isEmpty() && load_type != 1)")
    end = chat.index("if (isCache)", start)
    ranges = chat[start:end] + method(chat[end:], "if (isCache)")
    prefs = (root / "TMessagesProj/src/main/java/com/radolyn/ayugram/messages/AyuSavePreferences.java").read_text()
    start = prefs.index("        // Users and channels have separate ID namespaces.")
    end = prefs.index("    private static boolean saveDeletedForDialogKind", start)
    # Exercise the final peer/bot decision after the earlier settings checks.
    peer = prefs[start:end].rstrip()
    harness = """
import java.util.*;
public class AyuRegression {
    static class DialogObject {static boolean isUserDialog(long d){return d>0;}}
    static class AyuUtils {static int getMinRealId(List<Integer> m){return Collections.min(m);}}
    static long[] range(long dialogId,boolean isCache,ArrayList<Integer> messages,int load_type){
        int minVal=0,maxVal=Integer.MAX_VALUE;long startId=minVal,endId=minVal;
        RANGES
        return new long[]{startId,endId};
    }
    static class User {boolean bot=true;}
    static class MessagesController {
        static int lookups;static MessagesController getInstance(int a){return new MessagesController();}
        User getUser(long id){lookups++;return new User();}
    }
    static class Flag {boolean Bool(){return false;}}
    static class NaConfig {static NaConfig INSTANCE=new NaConfig();Flag getSaveDeletedMessageForBot(){return new Flag();}}
    static boolean peerAllowed(int accountId,long dialogId){
        PEER
    static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    public static void main(String[] args){
        require(range(-20,false,new ArrayList<>(),2)[1]==Integer.MAX_VALUE,"empty channel must load preserved history");
        require(range(-30,false,new ArrayList<>(),2)[1]==Integer.MAX_VALUE,"empty group must load preserved history");
        require(range(10,false,new ArrayList<>(),2)[1]==Integer.MAX_VALUE,"private history unchanged");
        require(range(-20,true,new ArrayList<>(),2)[1]==0,"cache response must not race server pagination");
        require(range(-20,false,new ArrayList<>(List.of(8,9)),2)[1]==8,"respect older-history boundary");
        require(peerAllowed(0,-20),"channel must not inherit unrelated bot setting");
        require(MessagesController.lookups==0,"never look up a channel ID as a user");
        require(!peerAllowed(0,20),"private bot setting remains enforced");
    }
}
""".replace("RANGES", ranges).replace("PEER", peer)
    run_java(harness)
