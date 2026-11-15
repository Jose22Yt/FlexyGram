/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.stickers;

import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.ChatObject;
import org.telegram.messenger.MediaDataController;
import org.telegram.messenger.MessageObject;
import org.telegram.messenger.NotificationCenter;
import org.telegram.messenger.SendMessagesHelper;
import org.telegram.messenger.UserConfig;
import org.telegram.tgnet.TLRPC;
import org.telegram.ui.ChatActivity;
import org.telegram.ui.Components.AlertsCreator;
import java.io.File;
import java.io.IOException;
import java.io.InterruptedIOException;
import java.util.ArrayList;

/**
 * Handles uploading and sending static sticker documents through Telegram's native transport.
 * Optionally adds the sticker to user's favorites upon server confirmation.
 */
public final class FlexyStickerSender implements NotificationCenter.NotificationCenterDelegate {

    public interface Callback {
        void onSuccess(TLRPC.Document serverDoc);
        void onError(Throwable error);
    }

    private final int account;
    private final long dialogId;
    private final File file;
    private final boolean addToFavorites;
    private final Callback callback;
    private int localMsgId;
    private boolean completed;
    private boolean transportStarted;
    private final long ownerId;

    private final Runnable timeoutRunnable = () -> finish(null, new IOException("Timeout awaiting server confirmation"));

    private FlexyStickerSender(int account, long dialogId, File file, boolean addToFavorites, Callback callback) {
        this.account = account;
        this.dialogId = dialogId;
        this.file = file;
        this.addToFavorites = addToFavorites;
        this.callback = callback;
        this.ownerId = UserConfig.getInstance(account).getClientUserId();
    }

    /**
     * Sends a WebP sticker document to the given dialog (or Saved Messages if toFavorites is true).
     */
    public static void send(ChatActivity owner, File file, TLRPC.TL_document document,
                            boolean addToFavorites, Callback callback) {
        if (file == null || !file.exists() || document == null) {
            if (file != null) file.delete();
            if (callback != null) callback.onError(new IllegalArgumentException("Invalid file or document"));
            return;
        }

        int account = owner.getCurrentAccount();
        long targetDialog = addToFavorites ? UserConfig.getInstance(account).getClientUserId() : owner.getDialogId();
        FlexyStickerSender sender = new FlexyStickerSender(account, targetDialog, file, addToFavorites, callback);
        if (owner.isFinished || owner.getParentActivity() == null) {
            sender.finish(null, new IOException("Destination unavailable"));
            return;
        }

        MessageObject top = addToFavorites ? null : owner.getThreadMessage();
        MessageObject reply = addToFavorites ? null : owner.getReplyMessage();
        long topicId = owner.getTopicId();
        if (!addToFavorites && topicId > 1 && ChatObject.isForum(owner.getCurrentChat())
                && (top == null || top.getId() != topicId)) {
            sender.finish(null, new IOException("Forum topic unavailable"));
            return;
        }
        SendMessagesHelper.SendMessageParams params = SendMessagesHelper.SendMessageParams.of(
                document, null, file.getAbsolutePath(), targetDialog,
                reply != null ? reply : top, top, null, null, null, null, true, 0, 0, 0, null, null, false);
        if (!addToFavorites) {
            params.replyQuote = owner.getReplyQuote();
            params.sendMessageChatArguments = owner.getMessageChatSendParams();
            params.monoForumPeer = owner.getSendMonoForumPeerId();
            params.suggestionParams = owner.getSendMessageSuggestionParams();
        }
        if (!addToFavorites && owner.isInScheduleMode()) {
            try {
                AlertsCreator.createScheduleDatePickerDialog(owner.getParentActivity(), targetDialog,
                        (notify, date, repeat) -> {
                            params.notify = notify;
                            params.scheduleDate = date;
                            params.scheduleRepeatPeriod = repeat;
                            sender.enqueue(params);
                        }, () -> sender.finish(null, new InterruptedIOException("Sticker scheduling cancelled")), null);
            } catch (RuntimeException unavailable) {
                sender.finish(null, unavailable);
            }
        } else {
            sender.enqueue(params);
        }
    }

    private void enqueue(SendMessagesHelper.SendMessageParams params) {
        if (completed || transportStarted) return;
        UserConfig config = UserConfig.getInstance(account);
        if (ownerId == 0 || !config.isClientActivated() || config.getClientUserId() != ownerId) {
            finish(null, new IOException("Account changed"));
            return;
        }

        NotificationCenter center = NotificationCenter.getInstance(account);
        center.addObserver(this, NotificationCenter.didReceiveNewMessages);
        center.addObserver(this, NotificationCenter.messageReceivedByServer);
        center.addObserver(this, NotificationCenter.messageSendError);

        AndroidUtilities.runOnUIThread(timeoutRunnable, 120_000);

        try {
            // From here Telegram can retain attachPath for uploads and retries.
            transportStarted = true;
            SendMessagesHelper.getInstance(account).sendMessage(params);
        } catch (Throwable t) {
            finish(null, t);
        }
    }

    @Override
    public void didReceivedNotification(int id, int eventAccount, Object... args) {
        if (completed || eventAccount != account) {
            return;
        }

        if (id == NotificationCenter.didReceiveNewMessages) {
            if (args.length >= 2 && args[0] instanceof Long && (Long) args[0] == dialogId && args[1] instanceof ArrayList) {
                for (Object item : (ArrayList<?>) args[1]) {
                    if (item instanceof MessageObject) {
                        MessageObject msg = (MessageObject) item;
                        if (msg.getDialogId() == dialogId && msg.getId() < 0 && msg.messageOwner != null
                                && file.getAbsolutePath().equals(msg.messageOwner.attachPath)) {
                            localMsgId = msg.getId();
                            break;
                        }
                    }
                }
            }
        } else if (id == NotificationCenter.messageReceivedByServer) {
            if (localMsgId != 0 && args.length >= 4 && args[0] instanceof Integer && (Integer) args[0] == localMsgId
                    && args[3] instanceof Long && (Long) args[3] == dialogId && args[2] instanceof TLRPC.Message) {
                TLRPC.Message message = (TLRPC.Message) args[2];
                TLRPC.Document serverDoc = message.media != null ? message.media.document : null;
                if (serverDoc != null && FlexyStickerMetadata.isNativeStaticSticker(serverDoc)) {
                    if (addToFavorites) {
                        MediaDataController.getInstance(account).addRecentSticker(
                                MediaDataController.TYPE_FAVE, null, serverDoc, (int) (System.currentTimeMillis() / 1000), false);
                    }
                    finish(serverDoc, null);
                } else {
                    finish(null, new IOException("Server did not return valid sticker document"));
                }
            }
        } else if (id == NotificationCenter.messageSendError) {
            if (localMsgId != 0 && args.length > 0 && args[0] instanceof Integer && (Integer) args[0] == localMsgId) {
                finish(null, new IOException("Upload error"));
            }
        }
    }

    private void finish(TLRPC.Document serverDoc, Throwable error) {
        if (completed) return;
        completed = true;

        AndroidUtilities.cancelRunOnUIThread(timeoutRunnable);
        NotificationCenter center = NotificationCenter.getInstance(account);
        center.removeObserver(this, NotificationCenter.didReceiveNewMessages);
        center.removeObserver(this, NotificationCenter.messageReceivedByServer);
        center.removeObserver(this, NotificationCenter.messageSendError);

        // A failed/in-flight native upload may still need its source for retry.
        if ((!transportStarted || error == null) && file.exists()) {
            file.delete();
        }

        if (callback != null) {
            if (error != null) {
                callback.onError(error);
            } else {
                callback.onSuccess(serverDoc);
            }
        }
    }
}
