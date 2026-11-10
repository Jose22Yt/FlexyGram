/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.performance;

import android.os.Bundle;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.FileLog;
import org.telegram.messenger.MessagesController;
import org.telegram.messenger.MessagesStorage;
import org.telegram.tgnet.TLRPC;

/** Resolve cold peers on Telegram's storage queue before ChatActivity's synchronous lifecycle. */
public final class ChatPeerPreloader {
    public interface Completion { void done(boolean found); }
    private ChatPeerPreloader() { }

    public static boolean prepare(int account, Bundle args, Completion completion) {
        if (args == null) return false;
        long chatId = args.getLong("chat_id", 0), userId = args.getLong("user_id", 0);
        int encryptedId = args.getInt("enc_id", 0);
        MessagesController controller = MessagesController.getInstance(account);
        TLRPC.EncryptedChat cachedEncrypted = encryptedId == 0 ? null : controller.getEncryptedChat(encryptedId);
        if (chatId != 0) {
            if (controller.getChat(chatId) != null) return false;
        } else if (userId != 0) {
            if (controller.getUser(userId) != null) return false;
        } else if (encryptedId != 0) {
            if (cachedEncrypted != null && controller.getUser(cachedEncrypted.user_id) != null) return false;
        } else return false;

        MessagesStorage storage = MessagesStorage.getInstance(account);
        storage.getStorageQueue().postRunnable(() -> {
            TLRPC.Chat chat = null;
            TLRPC.User user = null;
            TLRPC.EncryptedChat encrypted = null;
            try {
                if (chatId != 0) chat = storage.getChat(chatId);
                else if (userId != 0) user = storage.getUser(userId);
                else {
                    encrypted = cachedEncrypted != null ? cachedEncrypted : storage.getEncryptedChat(encryptedId);
                    if (encrypted != null) user = storage.getUser(encrypted.user_id);
                }
            } catch (Exception failed) { FileLog.e(failed); }
            TLRPC.Chat loadedChat = chat;
            TLRPC.User loadedUser = user;
            TLRPC.EncryptedChat loadedEncrypted = encrypted;
            AndroidUtilities.runOnUIThread(() -> {
                if (loadedChat != null) controller.putChat(loadedChat, true);
                if (loadedUser != null) controller.putUser(loadedUser, true);
                if (loadedEncrypted != null) controller.putEncryptedChat(loadedEncrypted, true);
                boolean found = chatId != 0 ? controller.getChat(chatId) != null
                        : userId != 0 ? controller.getUser(userId) != null
                        : controller.getEncryptedChat(encryptedId) != null
                          && controller.getUser(controller.getEncryptedChat(encryptedId).user_id) != null;
                completion.done(found);
            });
        });
        return true;
    }
}
