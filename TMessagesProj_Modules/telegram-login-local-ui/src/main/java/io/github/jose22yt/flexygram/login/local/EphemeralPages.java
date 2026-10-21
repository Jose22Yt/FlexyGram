package io.github.jose22yt.flexygram.login.local;
import io.github.jose22yt.flexygram.session.*;
import io.github.jose22yt.flexygram.login.*;
import io.github.jose22yt.flexygram.login.NativeLoginProtocol.*;
import io.github.jose22yt.flexygram.session.AuthenticationController.State;

/** Metadata only. No Bundle, preferences, TL secrets, code, password or serializable session state. */
public final class EphemeralPages {
    public enum Status { READY, BUSY, PARAMETERS_PENDING, UNSUPPORTED, STOPPED, STORAGE_REVIEW, COMPLETE }
    public static final class View {
        private final EphemeralPages owner;private final long epoch;
        private View(EphemeralPages owner,long epoch){this.owner=owner;this.epoch=epoch;}
    }
    public static final class Parameters {
        public final int page,codeLength;public final boolean passwordReady,termsRequired;
        public final Status status;public final NativeLoginProtocol.Error error;
        private Parameters(int page,int length,boolean ready,boolean terms,Status status,NativeLoginProtocol.Error error){this.page=page;codeLength=length;passwordReady=ready;termsRequired=terms;this.status=status;this.error=error;}
        @Override public String toString(){return "LocalNativePage["+page+","+status+"]";}
    }
    private final SessionScope scope;private long epoch;private boolean closed,attached;
    public EphemeralPages(ClosedRuntime runtime){if(runtime==null||runtime.scope.variant!=SessionScope.Variant.REAL_ALPHA)throw new IllegalArgumentException("CLOSED_REALALPHA_REQUIRED");scope=runtime.scope;}
    public synchronized View attach(SessionScope requested){if(closed||!scope.equals(requested))throw new IllegalStateException("LOCAL_VIEW_SCOPE_REJECTED");attached=true;return new View(this,++epoch);}
    public synchronized boolean valid(View view){return !closed&&attached&&view!=null&&view.owner==this&&view.epoch==epoch;}
    public synchronized void detach(View view){if(valid(view)){attached=false;++epoch;}}
    public synchronized void close(){closed=true;attached=false;++epoch;}
    public static boolean allowedPage(int page){return page==0||page==1||page==2||page==5||page==6;}
    public Parameters read(View view,NativeLoginTransport.Snapshot nativeState,AuthenticationController.UiSnapshot controller,boolean stopped){
        synchronized(this){if(!valid(view)||nativeState==null||controller==null||!scope.equals(nativeState.scope)||!scope.equals(controller.scope))throw new IllegalStateException("LOCAL_PARAMETERS_UNAVAILABLE");}
        int page=-1,length=0;boolean ready=false;Status status=Status.READY;
        if(controller.state==State.STORAGE_UNCERTAIN)status=Status.STORAGE_REVIEW;
        else if(stopped||controller.state==State.CANCELLED||controller.state==State.CLOSED){page=0;status=Status.STOPPED;}
        else if(controller.state==State.FAILED||controller.state==State.RESTART_REQUIRED)status=Status.STOPPED;
        else if(controller.state==State.LOCAL_COMPLETE||controller.state==State.LOCAL_AUTHORIZED)status=Status.COMPLETE;
        else switch(nativeState.stage){
        case NEW:case READY:page=0;break;
        case CODE_REQUIRED:case CODE_RETRY:
            if(nativeState.route==Route.APP)page=1;else if(nativeState.route==Route.SMS)page=2;
            if(page<0||nativeState.codeLength<1||nativeState.codeLength>12){page=-1;status=Status.UNSUPPORTED;}else length=nativeState.codeLength;break;
        case PASSWORD_REQUIRED:page=6;status=Status.PARAMETERS_PENDING;break;
        case PASSWORD_PARAMETERS:page=6;ready=true;break;
        case SIGNUP_REQUIRED:if(nativeState.termsRequired)status=Status.UNSUPPORTED;else page=5;break;
        case BUSY:case WAITING:status=Status.BUSY;break;
        default:status=Status.UNSUPPORTED;
        }
        return new Parameters(page,length,ready,nativeState.termsRequired,status,nativeState.error);
    }
}
