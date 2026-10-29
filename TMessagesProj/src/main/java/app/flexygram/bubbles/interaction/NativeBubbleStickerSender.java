/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.MessageObject;
import org.telegram.messenger.NotificationCenter;
import org.telegram.messenger.SendMessagesHelper;
import org.telegram.tgnet.TLRPC;

/** Native uploaded-sticker transport; confirmation must match its own account, peer and local ID.
 * No view/fragment reference is retained. A queued file belongs to Telegram's native retry lifecycle.
 */
public final class NativeBubbleStickerSender implements NotificationCenter.NotificationCenterDelegate {
    private final int account;
    private final long dialog;
    private final File file;
    private BubbleStickerWorkflow.SendResult result;
    private int localId;
    private boolean closed;
    private final Runnable timeout = () -> finish(null, new IOException("Server confirmation unavailable"));
    private NativeBubbleStickerSender(int account, long dialog, File file, BubbleStickerWorkflow.SendResult result) {
        this.account=account; this.dialog=dialog; this.file=file; this.result=result;
    }
    public static void send(int account, SendMessagesHelper.SendMessageParams params, File file,
            BubbleStickerWorkflow.SendResult result) {
        if (params == null || params.document == null || params.document.id != 0
                || !NativeStickerMetadata.isNativeStaticSticker(params.document)
                || file == null || !file.isFile() || file.length() != params.document.size
                || !file.getAbsolutePath().equals(params.path) || params.peer == 0 || params.scheduleDate != 0)
            throw new IllegalArgumentException("Invalid native sticker request");
        NativeBubbleStickerSender owner = new NativeBubbleStickerSender(account, params.peer, file, result);
        NotificationCenter events=NotificationCenter.getInstance(account);
        events.addObserver(owner,NotificationCenter.didReceiveNewMessages);
        events.addObserver(owner,NotificationCenter.messageReceivedByServer);
        events.addObserver(owner,NotificationCenter.messageSendError);
        AndroidUtilities.runOnUIThread(owner.timeout,180_000);
        try { SendMessagesHelper.getInstance(account).sendMessage(params); }
        catch (RuntimeException failure) { owner.finish(null,failure); }
    }
    @Override public void didReceivedNotification(int id, int eventAccount, Object... args) {
        if (closed || eventAccount != account) return;
        if (id == NotificationCenter.didReceiveNewMessages) {
            if (args.length < 2 || !(args[0] instanceof Long) || (Long)args[0] != dialog || !(args[1] instanceof ArrayList)) return;
            for (Object value : (ArrayList<?>)args[1]) if (value instanceof MessageObject) {
                MessageObject object=(MessageObject)value;
                if (object.getDialogId() == dialog && object.getId() < 0 && object.messageOwner != null
                        && file.getAbsolutePath().equals(object.messageOwner.attachPath)) {
                    localId=object.getId(); break;
                }
            }
        } else if (id == NotificationCenter.messageReceivedByServer) {
            if (localId == 0 || args.length < 4 || !(args[0] instanceof Integer) || (Integer)args[0] != localId
                    || !(args[3] instanceof Long) || (Long)args[3] != dialog || !(args[2] instanceof TLRPC.Message)) return;
            TLRPC.Message message=(TLRPC.Message)args[2];
            TLRPC.Document document=message.media == null ? null : message.media.document;
            if (message.id > 0 && document != null && document.id != 0
                    && NativeStickerMetadata.isNativeStaticSticker(document)) finish(document,null);
            else finish(null,new IOException("Server returned non-sticker media"));
        } else if (id == NotificationCenter.messageSendError && localId != 0 && args.length > 0
                && args[0] instanceof Integer && (Integer)args[0] == localId) {
            finish(null,new IOException("Native upload failed; use native message retry"));
        }
    }
    private void finish(TLRPC.Document document, Throwable failure) {
        if (closed) return;
        closed=true;
        AndroidUtilities.cancelRunOnUIThread(timeout);
        NotificationCenter events=NotificationCenter.getInstance(account);
        events.removeObserver(this,NotificationCenter.didReceiveNewMessages);
        events.removeObserver(this,NotificationCenter.messageReceivedByServer);
        events.removeObserver(this,NotificationCenter.messageSendError);
        BubbleStickerWorkflow.SendResult callback=result; result=null;
        // Native updateMediaPaths owns the uploaded cache entry. Never delete a pending/retry file.
        if (failure == null) file.delete();
        if (callback != null) callback.complete(document,failure);
    }
}
