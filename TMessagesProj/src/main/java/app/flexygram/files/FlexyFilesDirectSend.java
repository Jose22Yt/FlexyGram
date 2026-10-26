/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.files;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.concurrent.atomic.AtomicBoolean;
import org.telegram.messenger.*;
import org.telegram.tgnet.TLRPC;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.Components.AlertsCreator;

/** Reviewed native adapter from the prepared Signature Editor package.
 * File validation runs in the existing explicit export worker; this class owns no engine.
 * A request queued in Telegram is not confirmation of delivery. */
final class FlexyFilesDirectSend {
    private FlexyFilesDirectSend() { }
    static final class Copy {
        final File file;
        final String name;
        private Copy(File file) { this.file=file;name=file.getName(); }
    }
    /** Worker-only: authorize only the bounded generated copy, never the received original. */
    static Copy prepare(File candidate) throws IOException {
        File root=FilesCache.root().getCanonicalFile(),file=candidate.getCanonicalFile();
        long bytes=file.length();
        if(!file.getPath().startsWith(root.getPath()+File.separator)||!file.isFile()||bytes<=0||bytes>80L*1024*1024)
            throw new IOException("Expected bounded generated copy");
        return new Copy(file);
    }
    static boolean topicSupported(int account,long dialog) {
        return !ChatObject.isForum(account,dialog)&&!ChatObject.isMonoForum(account,dialog);
    }
    private static boolean allowed(int account,long dialog) {
        if(account<0||account>=UserConfig.MAX_ACCOUNT_COUNT||dialog==0||DialogObject.isEncryptedDialog(dialog)
                ||!UserConfig.getInstance(account).isClientActivated()||!topicSupported(account,dialog))return false;
        if(dialog<0){
            TLRPC.Chat chat=MessagesController.getInstance(account).getChat(-dialog);
            if(chat==null||ChatObject.isNotInChat(chat)||!ChatObject.canSendMessages(chat)||!ChatObject.canSendDocument(chat))return false;
            // Never synchronously load ChatFull on UI through the native slow-mode check.
            if(chat.slowmode_enabled&&!ChatObject.hasAdminRights(chat)&&MessagesController.getInstance(account).getChatFull(chat.id)==null)return false;
        }
        return true;
    }
    /** Called only after the editor's explicit named-destination confirmation. */
    static void enqueueCopy(BaseFragment owner,Copy copy,long dialog,int account,Runnable queued)throws IOException {
        if(copy==null||owner.isFinished||owner.getParentActivity()==null||!allowed(account,dialog))throw new IOException("Destination unavailable");
        if(AlertsCreator.checkSlowMode(owner.getParentActivity(),account,dialog,false))return;
        AtomicBoolean once=new AtomicBoolean();
        AlertsCreator.ensurePaidMessageConfirmation(account,dialog,1,payStars->{
            if(owner.isFinished||owner.getParentActivity()==null||!allowed(account,dialog))return;
            if(AlertsCreator.checkSlowMode(owner.getParentActivity(),account,dialog,false)||!once.compareAndSet(false,true))return;
            ArrayList<String> paths=new ArrayList<>();paths.add(copy.file.getAbsolutePath());
            SendMessagesHelper.prepareSendingDocuments(AccountInstance.getInstance(account),paths,paths,null,
                    null,null,null,dialog,null,null,null,null,null,true,0,0,null,
                    SendMessageChatArguments.EMPTY,0,false,payStars,null,null);
            queued.run();
        });
    }
}
