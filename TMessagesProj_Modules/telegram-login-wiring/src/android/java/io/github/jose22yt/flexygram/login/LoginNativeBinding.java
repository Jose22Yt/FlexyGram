package io.github.jose22yt.flexygram.login;

import android.os.Bundle;
import java.util.concurrent.Executor;
import org.telegram.ui.LoginActivity;
import io.github.jose22yt.flexygram.session.AuthUiRelay;
import io.github.jose22yt.flexygram.session.SessionScope;
import io.github.jose22yt.flexygram.session.android.LoginFlowOwner;
import io.github.jose22yt.flexygram.session.android.LoginActivityAdapter;

/** Existing fragment/relay only. Keeps no phone/code/Activity references or replacement UI. */
public final class LoginNativeBinding {
    public interface NativePages {boolean renderPreparedState(NativePagePlan state);}
    private final LoginActivityAdapter adapter;
    private final NativeLoginTransport transport;
    private final Executor worker;
    private AuthUiRelay.Binding binding;
    public LoginNativeBinding(SessionScope scope,LoginFlowOwner owner,NativeLoginTransport transport,Executor worker) {
        if(scope==null||owner==null||transport==null||worker==null||!scope.equals(transport.scope()))throw new IllegalArgumentException("NATIVE_BINDING_SCOPE_REQUIRED");
        adapter=new LoginActivityAdapter(scope,owner);this.transport=transport;this.worker=worker;
    }
    public void attach(LoginActivity original,NativePages pages) {
        if(pages==null)throw new IllegalArgumentException("NATIVE_PAGE_RENDERER_REQUIRED");
        binding=adapter.attach(original,ignored->pages.renderPreparedState(NativePagePlan.from(transport.snapshot())));
    }
    public void detach(){adapter.detach(binding);binding=null;}
    public boolean startLocal(char[] synthetic){return adapter.onLocalStart(synthetic);}
    public boolean verifyLocal(char[] synthetic){return adapter.onLocalVerify(synthetic);}
    public boolean cancelLocal(){return adapter.onLocalCancel();}
    /** Intermediate actions share the same serial worker as LoginFlowOwner. No new timers/executor. */
    public void loadPasswordLocal(){enqueue(()->transport.loadPasswordParametersLocal(true));}
    public void pollQrLocal(){enqueue(()->transport.pollQrLocal(true));}
    public void approveQrMigrationLocal(){enqueue(()->transport.approveMigrationLocal(true));}
    public void saveRestartMarker(Bundle out){adapter.saveRestartMarker(out);}
    public boolean restoreMarker(Bundle in){return adapter.restoreAfterProcessDeath(in);}
    private void enqueue(Runnable action){try{worker.execute(action);}catch(RuntimeException|LinkageError unavailable){throw new IllegalStateException("LOCAL_WORKER_UNAVAILABLE");}}
}
