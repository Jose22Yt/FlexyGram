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
        Step step=Step.CONTEXT;
        try{
            if(ApplicationLoader.applicationContext==null
                    ||!application.getPackageName().equals(ApplicationLoader.applicationContext.getPackageName()))
                return unavailable(Diagnostic.INSPECTION_UNAVAILABLE,step);
            step=Step.POLICY;
            if(!DiagnosticPolicy.isIsolated())return unavailable(Diagnostic.INSPECTION_UNAVAILABLE,step);
            step=Step.ACCOUNT_HANDLE;
            AccountInstance account=AccountInstance.getInstance(scope.account);
            if(account==null||account.getCurrentAccount()!=scope.account)return unavailable(Diagnostic.CONTROLLERS_UNAVAILABLE,step);
            step=Step.USER_CONFIG;
            UserConfig user=account.getUserConfig();
            if(user==null)return unavailable(Diagnostic.CONTROLLERS_UNAVAILABLE,step);
            // Presence only: no phone, credential or serialized user is read or returned.
            if(user.isClientActivated()||user.getCurrentUser()!=null||user.getClientUserId()!=0||user.getPreferences().contains("user"))
                return new Snapshot(scope,Evidence.EXISTING_ACCOUNT,false,Diagnostic.EXISTING_ACCOUNT,step);
            if(user.getPreferences().contains("tmpPassword"))return unavailable(Diagnostic.PROTECTED_AUTH_MATERIAL,step);
            step=Step.PRIVATE_ROOT;
            File root=ApplicationLoader.getFilesDirFixed();
            File trustedRoot=application.getFilesDir().getCanonicalFile();
            if(root==null||!root.getCanonicalFile().equals(trustedRoot))return unavailable(Diagnostic.INSPECTION_UNAVAILABLE,step);
            step=Step.ACCOUNT_DIRECTORY;
            File directory=scope.account==0?root:new File(root,"account"+scope.account);
            // Android can expose the private root through /data/data or /data/user/0.
            // Resolve that trusted root first, but reject a redirected account child.
            File expected=scope.account==0?trustedRoot:new File(trustedRoot,"account"+scope.account);
            if(!directory.getCanonicalFile().equals(expected))return unavailable(Diagnostic.INSPECTION_UNAVAILABLE,step);
            step=Step.AUTH_FILES;
            if(new File(directory,"tgnet.dat").exists()||new File(directory,"tgnet.dat.bak").exists())
                return new Snapshot(scope,Evidence.NATIVE_FILES_PRESENT,false,Diagnostic.AUTH_FILES_PRESENT,step);
            // Request local handles only after preexisting-artifact rejection: storage may open/recover a DB.
            step=Step.STORAGE_HANDLE;
            MessagesStorage storage=account.getMessagesStorage();
            if(storage==null||storage.getStorageQueue()==null)return unavailable(Diagnostic.CONTROLLERS_UNAVAILABLE,step);
            step=Step.CONNECTION_HANDLE;
            ConnectionsManager connections=account.getConnectionsManager();
            if(connections==null)return unavailable(Diagnostic.CONTROLLERS_UNAVAILABLE,step);
            // Handle availability is NOT evidence that DB/MTProto initialization completed.
            return new Snapshot(scope,Evidence.EMPTY,true,Diagnostic.EMPTY,Step.COMPLETE);
        }catch(SecurityException failure){return unavailable(Diagnostic.ACCESS_DENIED,step);
        }catch(IOException failure){return unavailable(Diagnostic.IO_UNAVAILABLE,step);
        }catch(LinkageError failure){return unavailable(Diagnostic.INITIALIZATION_FAILED,step);
        }catch(RuntimeException failure){return unavailable(
            step==Step.ACCOUNT_HANDLE||step==Step.STORAGE_HANDLE||step==Step.CONNECTION_HANDLE
                ?Diagnostic.INITIALIZATION_FAILED:Diagnostic.INTERNAL_EXCEPTION,step);}
    }
    private Snapshot unavailable(Diagnostic diagnostic,Step step){return new Snapshot(scope,Evidence.UNAVAILABLE,false,diagnostic,step);}
}
