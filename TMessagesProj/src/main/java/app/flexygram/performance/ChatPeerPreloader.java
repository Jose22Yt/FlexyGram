/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.performance;

import android.os.Bundle;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.FileLog;
import org.telegram.messenger.MessagesController;
import org.telegram.messenger.MessagesStorage;
import org.telegram.messenger.NotificationCenter;
import org.telegram.messenger.UserConfig;
import org.telegram.tgnet.TLRPC;

/** UI-owned, coalesced cold-peer lookups. Disk reads stay on Telegram's storage queue. */
public final class ChatPeerPreloader {
    public interface Completion { void done(boolean found); }
    private static final Map<String,ArrayList<Completion>> pending=new HashMap<>();
    private static final Map<Integer,NotificationCenter.NotificationCenterDelegate> logoutObservers=new HashMap<>();
    private ChatPeerPreloader() { }

    public static boolean prepare(int account, Bundle args, Completion completion) {
        if (args == null) return false;
        long chatId = args.getLong("chat_id", 0), userId = args.getLong("user_id", 0);
        int encryptedId = args.getInt("enc_id", 0);
        if(chatId==0 && userId==0 && encryptedId==0)return false;
        long owner = UserConfig.getInstance(account).getClientUserId();
        if (!owns(account, owner)) {
            // Returning false would invite the caller's synchronous cold-open fallback.
            AndroidUtilities.runOnUIThread(()->completion.done(false));return true;
        }
        MessagesController controller = MessagesController.getInstance(account);
        TLRPC.EncryptedChat cachedEncrypted = encryptedId == 0 ? null : controller.getEncryptedChat(encryptedId);
        if (chatId != 0) {
            if (controller.getChat(chatId) != null) return false;
        } else if (userId != 0) {
            if (controller.getUser(userId) != null) return false;
        } else if (encryptedId != 0) {
            if (cachedEncrypted != null && controller.getUser(cachedEncrypted.user_id) != null) return false;
        } else return false;

        String key = account + ":" + owner + ":" + System.identityHashCode(controller) + ":"
                + (chatId != 0 ? "c" + chatId : userId != 0 ? "u" + userId : "e" + encryptedId);
        ArrayList<Completion> waiting=pending.get(key);
        if(waiting!=null) {waiting.add(completion);return true;}
        ArrayList<Completion> callbacks=new ArrayList<>();callbacks.add(completion);pending.put(key,callbacks);
        if(!logoutObservers.containsKey(account)) {
            NotificationCenter.NotificationCenterDelegate observer=(event,id,arguments)->cancelAccount(id);
            logoutObservers.put(account,observer);
            NotificationCenter.getInstance(account).addObserver(observer,NotificationCenter.appDidLogout);
        }
        MessagesStorage storage = MessagesStorage.getInstance(account);
        try {
            storage.getStorageQueue().postRunnable(() -> {
                TLRPC.Chat chat = null;
                TLRPC.User user = null;
                TLRPC.EncryptedChat encrypted = null;
                try {
                    // A queued read that belongs to a logged-out owner does no further disk work.
                    if (owns(account, owner)) {
                        if (chatId != 0) chat = storage.getChat(chatId);
                        else if (userId != 0) user = storage.getUser(userId);
                        else {
                            encrypted = cachedEncrypted != null ? cachedEncrypted : storage.getEncryptedChat(encryptedId);
                            if (encrypted != null) user = storage.getUser(encrypted.user_id);
                        }
                    }
                } catch (Exception failed) { FileLog.e(failed); }
                TLRPC.Chat loadedChat = chat;
                TLRPC.User loadedUser = user;
                TLRPC.EncryptedChat loadedEncrypted = encrypted;
                AndroidUtilities.runOnUIThread(() -> {
                    if (!owns(account, owner) || MessagesController.getInstance(account)!=controller) {finish(account,key, false);return;}
                    // Live updates received during IO take precedence over an older storage snapshot.
                    if (loadedChat != null && controller.getChat(chatId) == null) controller.putChat(loadedChat, true);
                    if (loadedUser != null && controller.getUser(loadedUser.id) == null) controller.putUser(loadedUser, true);
                    if (loadedEncrypted != null && controller.getEncryptedChat(encryptedId) == null) controller.putEncryptedChat(loadedEncrypted, true);
                    boolean found = chatId != 0 ? controller.getChat(chatId) != null
                            : userId != 0 ? controller.getUser(userId) != null
                            : controller.getEncryptedChat(encryptedId) != null
                              && controller.getUser(controller.getEncryptedChat(encryptedId).user_id) != null;
                    finish(account,key, found);
                });
            });
        } catch (RuntimeException unavailable) {
            FileLog.e(unavailable);finish(account,key,false);
        }
        return true;
    }
    private static boolean owns(int account,long owner) {
        return owner!=0 && UserConfig.getInstance(account).isClientActivated()
                && UserConfig.getInstance(account).getClientUserId()==owner;
    }
    private static void releaseObserver(int account) {
        String prefix=account+":";
        for(String key:pending.keySet())if(key.startsWith(prefix))return;
        NotificationCenter.NotificationCenterDelegate observer=logoutObservers.remove(account);
        if(observer!=null)NotificationCenter.getInstance(account).removeObserver(observer,NotificationCenter.appDidLogout);
    }
    private static void cancelAccount(int account) {
        // A storage queue can stop at logout. Do not retain its fragments indefinitely.
        String prefix=account+":";pending.keySet().removeIf(key->key.startsWith(prefix));releaseObserver(account);
    }
    private static void finish(int account,String key,boolean found) {
        // Remove before callbacks so an immediate retry creates a new request.
        ArrayList<Completion> callbacks=pending.remove(key);
        releaseObserver(account);
        if(callbacks==null)return;
        for(Completion completion:callbacks) {
            try {completion.done(found);}catch(RuntimeException failed){FileLog.e(failed);}
        }
    }
}
