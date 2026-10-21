package io.github.jose22yt.flexygram.session.android;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import java.util.concurrent.Executor;
import org.telegram.ui.LoginActivity;
import io.github.jose22yt.flexygram.session.*;

/** Seam for the original LoginActivity BaseFragment. Creates no replacement UI and patches no RPC. */
public final class LoginActivityAdapter {
    private static final String KEY="flexygram_local_auth_restart",SLOT="flexygram_local_auth_slot";
    private final SessionScope scope;private final LoginFlowOwner owner;
    private AuthUiRelay.Binding current;private long attachments;private boolean ownerDestroyed;
    public static final class ViewState {
        public final boolean attached,ownerDestroyed;public final long attachments;
        private ViewState(boolean attached,boolean destroyed,long count){this.attached=attached;ownerDestroyed=destroyed;attachments=count;}
    }
    public LoginActivityAdapter(SessionScope scope,LoginFlowOwner owner) {
        if(scope==null||owner==null||!scope.equals(owner.snapshot().scope))throw new IllegalArgumentException("LOGIN_SCOPE_MISMATCH");this.scope=scope;this.owner=owner;
    }
    public static Executor mainExecutor() {
        Handler handler=new Handler(Looper.getMainLooper());return task->{if(!handler.post(task))throw new IllegalStateException("AUTH_MAIN_HANDLER_UNAVAILABLE");};
    }
    public AuthUiRelay.Binding attach(LoginActivity fragment,AuthUiRelay.Observer renderNativeState) {
        requireMain();
        if(ownerDestroyed||fragment==null||fragment.getCurrentAccount()!=scope.account)throw new IllegalArgumentException("LOGIN_FRAGMENT_ACCOUNT_MISMATCH");
        current=owner.attachView(mainExecutor(),renderNativeState);attachments++;return current;
    }
    public void detach(AuthUiRelay.Binding binding){requireMain();if(binding!=null)binding.close();if(binding==current)current=null;}
    public ViewState viewState(){requireMain();return new ViewState(current!=null,ownerDestroyed,attachments);}
    public boolean onLocalStart(char[] identity){requireMain();return current!=null&&owner.startLocal(identity);}
    public boolean onLocalVerify(char[] code){requireMain();return current!=null&&owner.verifyLocal(code);}
    public boolean onLocalCancel(){requireMain();return current!=null&&owner.cancelLocal();}
    public void saveRestartMarker(Bundle destination){requireMain();destination.putBoolean(KEY,true);destination.putInt(SLOT,scope.account);}
    public AuthenticationController.UiSnapshot processRecreationMarker(Bundle source) {
        requireMain();if(source==null||!source.getBoolean(KEY,false))return null;
        if(source.getInt(SLOT,-1)!=scope.account)throw new IllegalArgumentException("LOGIN_RECREATION_ACCOUNT_MISMATCH");
        return AuthenticationController.UiSnapshot.recreationMarker(scope);
    }
    public boolean restoreAfterProcessDeath(Bundle source){AuthenticationController.UiSnapshot marker=processRecreationMarker(source);return marker!=null&&owner.restoreAfterProcessDeath(marker);}
    public void destroyOwner(){requireMain();detach(current);ownerDestroyed=true;owner.close();}
    private static void requireMain(){if(Looper.myLooper()!=Looper.getMainLooper())throw new IllegalStateException("AUTH_VIEW_REQUIRES_MAIN");}
}
