package io.github.jose22yt.flexygram.login;

import org.telegram.tgnet.TLRPC;
import io.github.jose22yt.flexygram.session.*;
import io.github.jose22yt.flexygram.session.AuthenticationController.*;
import io.github.jose22yt.flexygram.session.android.LocalSessionStore;
import io.github.jose22yt.flexygram.session.android.OperationJournal;
import io.github.jose22yt.flexygram.login.NativePersistenceFence.*;

/** Hands the SAME original TL object to a LOCAL original-format writer, never serializes it. */
public final class TelegramAuthorizationStore implements LocalSessionStore {
    public interface OriginalFormatPort extends InventoryPort {
        Report commitOriginal(Lease operation,TLRPC.TL_auth_authorization original,NativeLoginProtocol.Action source);
    }
    private final SessionScope scope;
    private final OriginalFormatPort port;
    private final NativePersistenceFence fence;
    private Lease lease;
    private TLRPC.TL_auth_authorization staged;
    private NativeLoginProtocol.Action source;
    private boolean closed,committing,closeRequested;
    public TelegramAuthorizationStore(ClosedRuntime runtime,OperationJournal journal,OriginalFormatPort port) {
        if(runtime==null||port==null)throw new IllegalArgumentException("ORIGINAL_STORAGE_REQUIRED");
        scope=runtime.scope;this.port=port;fence=new NativePersistenceFence(runtime,journal,port);
    }
    /** Binds operation ownership and failure cleanup together; no network adapter is supplied. */
    public NativeLoginTransport localTransport(ClosedRuntime runtime,NativeLoginProtocol.LocalRpc rpc,NativeLoginProtocol.Clock clock) {
        if(runtime==null||!scope.equals(runtime.scope))throw new IllegalArgumentException("TRANSPORT_SCOPE_MISMATCH");
        return new NativeLoginTransport(runtime,rpc,clock,this::operation,this::close);
    }
    @Override public synchronized void beginExplicit(boolean retryApproved) {
        if(closed||lease!=null)throw new IllegalStateException("AUTHORIZATION_STORE_NOT_NEW");
        lease=fence.beginExplicit(retryApproved);
    }
    public synchronized Lease operation(){if(closed)throw new IllegalStateException("AUTHORIZATION_STORE_CLOSED");return fence.currentLease();}
    public synchronized void stageLocal(Lease requested,NativeLoginProtocol.Request request,TLRPC.auth_Authorization authorization) {
        if(closed||committing||requested==null||requested!=lease||staged!=null
                ||request==null||request.isClosed()||!request.belongsTo(lease)||!scope.equals(request.scope)
                ||request.action==NativeLoginProtocol.Action.GET_PASSWORD
                ||!(authorization instanceof TLRPC.TL_auth_authorization))throw new IllegalStateException("AUTHORIZATION_STAGE_REJECTED");
        TLRPC.TL_auth_authorization original=(TLRPC.TL_auth_authorization)authorization;
        if(original.user==null||original.setup_password_required)throw new IllegalStateException("AUTHORIZATION_NOT_SUPPORTED");
        fence.currentLease();staged=original;source=request.action;
    }
    public synchronized void recordLocalWrite(Lease operation,Receipt receipt){fence.recordLocalWrite(operation,receipt);}
    @Override public synchronized StoreSnapshot inspect(SessionScope requested){return fence.inspect(requested);}
    @Override public synchronized Commit commitLocalIfEmpty(SessionScope requested,long version,char[] localReceipt) {
        if(!scope.equals(requested))throw new IllegalArgumentException("ACCOUNT_SCOPE_MISMATCH");
        if(closed||committing||staged==null||localReceipt==null||localReceipt.length==0)return Commit.CONFLICT;
        if(staged.user==null||staged.setup_password_required){staged=null;source=null;return Commit.CONFLICT;}
        committing=true;TLRPC.TL_auth_authorization original=staged;
        try{return fence.commitLocal(lease,version,operation->port.commitOriginal(operation,original,source));}
        finally{staged=null;source=null;committing=false;if(closeRequested)close();}
    }
    @Override public synchronized void close() {
        if(committing){closeRequested=true;return;}
        closed=true;staged=null;source=null;fence.close();
    }
    @Override public String toString(){return "TelegramAuthorizationStore[REDACTED]";}
}
