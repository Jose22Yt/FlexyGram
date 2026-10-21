package io.github.jose22yt.flexygram.session.android;
import android.content.Context;
import java.io.File;
import java.io.IOException;
import org.telegram.messenger.*;
import org.telegram.tgnet.ConnectionsManager;
import io.github.jose22yt.flexygram.session.SessionScope;

/** Fixed-slot metadata adapter. Does not change selectedAccount, load UserConfig or initialize native transport. */
public final class TelegramAccountAdapter implements AccountProbe {
    private final SessionScope scope;
    private final Context application;
    public TelegramAccountAdapter(Context context,ReadOnlyAttestation attestation) {
        if(context==null||attestation==null||context.getApplicationContext()==null
                ||!attestation.runtime.scope.variant.applicationId.equals(context.getPackageName()))throw new IllegalArgumentException("ACCOUNT_CONTEXT_MISMATCH");
        application=context.getApplicationContext();scope=attestation.runtime.scope;
    }
    @Override public Snapshot inspect() {
        AndroidJournalBackend.requireWorker();
        try{
            if(!DiagnosticPolicy.isIsolated()||ApplicationLoader.applicationContext==null
                    ||!application.getPackageName().equals(ApplicationLoader.applicationContext.getPackageName()))return unavailable();
            AccountInstance account=AccountInstance.getInstance(scope.account);if(account.getCurrentAccount()!=scope.account)return unavailable();
            UserConfig user=account.getUserConfig();if(user==null)return unavailable();
            // Presence only: no phone, credential or serialized user is read or returned.
            if(user.isClientActivated()||user.getCurrentUser()!=null||user.getClientUserId()!=0||user.getPreferences().contains("user"))
                return new Snapshot(scope,Evidence.EXISTING_ACCOUNT,false);
            if(user.getPreferences().contains("tmpPassword"))return unavailable();
            File root=ApplicationLoader.getFilesDirFixed();
            if(root==null||!root.getCanonicalFile().equals(application.getFilesDir().getCanonicalFile()))return unavailable();
            File directory=scope.account==0?root:new File(root,"account"+scope.account);
            if(!directory.getCanonicalFile().equals(directory.getAbsoluteFile()))return unavailable();
            if(new File(directory,"tgnet.dat").exists()||new File(directory,"tgnet.dat.bak").exists())return new Snapshot(scope,Evidence.NATIVE_FILES_PRESENT,false);
            // Request local handles only after preexisting-artifact rejection: storage may open/recover a DB.
            MessagesStorage storage=account.getMessagesStorage();ConnectionsManager connections=account.getConnectionsManager();
            if(storage==null||storage.getStorageQueue()==null||connections==null)return unavailable();
            // Handle availability is NOT evidence that DB/MTProto initialization completed.
            return new Snapshot(scope,Evidence.EMPTY,true);
        }catch(IOException|RuntimeException|LinkageError failure){return unavailable();}
    }
    private Snapshot unavailable(){return new Snapshot(scope,Evidence.UNAVAILABLE,false);}
}
