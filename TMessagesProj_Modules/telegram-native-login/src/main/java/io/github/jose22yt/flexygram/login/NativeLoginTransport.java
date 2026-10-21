package io.github.jose22yt.flexygram.login;

import java.util.Arrays;
import io.github.jose22yt.flexygram.session.*;
import io.github.jose22yt.flexygram.session.RequestCoordinator.*;
import io.github.jose22yt.flexygram.login.NativeLoginProtocol.*;
import io.github.jose22yt.flexygram.login.NativeLoginProtocol.Error;
import io.github.jose22yt.flexygram.login.NativeLoginProtocol.Kind;

/** Adapts typed LOCAL replies to the existing AuthenticationController, without a second auth UI. */
public final class NativeLoginTransport implements TransportPort {
    public static final class Snapshot {
        public final SessionScope scope;
        public final Stage stage;
        public final Error error;
        public final Route route;
        public final int codeLength;
        public final boolean termsRequired;
        public final long revision;
        private Snapshot(SessionScope scope,Stage stage,Error error,Route route,int codeLength,boolean terms,long revision) {
            this.scope=scope;this.stage=stage;this.error=error;this.route=route;this.codeLength=codeLength;termsRequired=terms;this.revision=revision;
        }
        @Override public String toString(){return "NativeLogin["+stage+","+error+"]";}
    }
    private static final class Parent {
        final Operation operation;final Listener listener;
        Parent(Attempt attempt,Listener listener){operation=attempt.operation;this.listener=listener;}
    }
    private static final class Call {
        final Parent parent;final Request request;
        boolean returned,done;Response buffered,selected;Cancellation cancellation;
        Call(Parent parent,Request request){this.parent=parent;this.request=request;}
    }
    private final SessionScope scope;
    private final LocalRpc rpc;
    private final Clock clock;
    private Stage stage=Stage.NEW;
    private Error error=Error.NONE;
    private Route route=Route.NONE;
    private Parent parent;
    private Call call;
    private boolean initialized,closed,qr,termsRequired,migrated;
    private int targetDc,discarded,adapterFailures,codeLength;
    private long revision,deadline;
    private Action retryAction;
    private Runnable stateSignal=()->{};
    private final java.util.function.Supplier<?> operationOwnerProvider;
    private final Runnable discardUncommitted;
    private Object operationOwner;
    public NativeLoginTransport(ClosedRuntime runtime,LocalRpc rpc,Clock clock) {
        this(runtime,rpc,clock,()->new Object(),()->{});
    }
    public NativeLoginTransport(ClosedRuntime runtime,LocalRpc rpc,Clock clock,java.util.function.Supplier<?> operationOwnerProvider,Runnable discardUncommitted) {
        if(runtime==null||rpc==null||clock==null||operationOwnerProvider==null||discardUncommitted==null||runtime.scope.variant!=SessionScope.Variant.REAL_ALPHA)
            throw new IllegalArgumentException("LOCAL_NATIVE_LOGIN_REQUIRED");
        scope=runtime.scope;this.rpc=rpc;this.clock=clock;this.operationOwnerProvider=operationOwnerProvider;this.discardUncommitted=discardUncommitted;
        if(!local())throw new IllegalArgumentException("LOCAL_NATIVE_LOGIN_REQUIRED");
    }
    private boolean local(){
        try{return rpc.domain()==Domain.LOCAL_SIMULATION&&scope.equals(rpc.scope());}
        catch(RuntimeException|LinkageError unavailable){return false;}
    }
    private long elapsed(){try{return clock.elapsedMillis();}catch(RuntimeException|LinkageError unavailable){return -1;}}
    @Override public Domain domain(){return Domain.LOCAL_SIMULATION;}
    @Override public SessionScope scope(){return scope;}
    @Override public void initialize() {
        synchronized(this) {
            if(closed||initialized||!local())throw new IllegalStateException("LOCAL_INITIALIZATION_REJECTED");
            try{operationOwner=operationOwnerProvider.get();if(operationOwner==null)throw new IllegalStateException();}
            catch(RuntimeException|LinkageError unavailable){throw new IllegalStateException("OPERATION_OWNER_UNAVAILABLE");}
            initialized=true;change(Stage.READY,Error.NONE);
        }
        notifyUi();
    }
    public synchronized void bindLocalStateSignal(Runnable signal) {
        if(signal==null||initialized||closed)throw new IllegalStateException("STATE_SIGNAL_BINDING_REJECTED");
        stateSignal=signal;
    }
    public synchronized Snapshot snapshot(){return new Snapshot(scope,stage,error,route,codeLength,termsRequired,revision);}
    public synchronized int discardedReplies(){return discarded;}
    public synchronized int adapterFailures(){return adapterFailures;}
    public synchronized boolean selectQrLocal(boolean explicitChoice) {
        if(!explicitChoice||closed||parent!=null||(stage!=Stage.NEW&&stage!=Stage.READY))return false;
        qr=true;return true;
    }
    @Override public Cancellation submit(Attempt attempt,Listener listener) {
        final Parent owner;
        Action action=null;Runnable complete=null;
        synchronized(this) {
            if(attempt==null||listener==null||!scope.equals(attempt.scope)||closed||!initialized||parent!=null)
                throw new IllegalStateException("LOCAL_REQUEST_STATE_REJECTED");
            owner=new Parent(attempt,listener);
            if(attempt.operation==Operation.REQUEST_CODE&&stage==Stage.READY)action=qr?Action.EXPORT_QR:Action.SEND_CODE;
            else if(attempt.operation==Operation.VERIFY_CODE&&(stage==Stage.CODE_REQUIRED||stage==Stage.QR_TOKEN))action=qr?Action.EXPORT_QR:Action.SIGN_IN;
            else if(attempt.operation==Operation.VERIFY_CODE&&stage==Stage.EARLY_AUTHORIZED) {
                parent=owner;change(Stage.AUTHORIZED,Error.NONE);complete=finish(true);
            } else throw new IllegalStateException("LOCAL_REQUEST_STATE_REJECTED");
            if(action!=null)parent=owner;
        }
        if(action!=null) {
            char[] copy=attempt.input.primaryCopy();
            try{dispatch(action,copy,0);}finally{Arrays.fill(copy,'\0');}
        } else deliver(complete);
        return ()->abandon(owner);
    }
    public boolean loadPasswordParametersLocal(boolean explicitChoice) {
        return auxiliary(Action.GET_PASSWORD,new char[0],explicitChoice,Stage.PASSWORD_REQUIRED);
    }
    public boolean checkPasswordProofLocal(char[] syntheticProof,boolean explicitChoice) {
        return auxiliary(Action.CHECK_PASSWORD,syntheticProof,explicitChoice,Stage.PASSWORD_PARAMETERS);
    }
    public boolean signUpLocal(char[] syntheticNames,boolean explicitConsent,boolean termsAccepted) {
        synchronized(this){if(termsRequired&&!termsAccepted)return false;}
        return auxiliary(Action.SIGN_UP,syntheticNames,explicitConsent,Stage.SIGNUP_REQUIRED);
    }
    public boolean pollQrLocal(boolean explicitChoice) {
        return auxiliary(Action.EXPORT_QR,new char[0],explicitChoice,Stage.QR_TOKEN);
    }
    public boolean approveMigrationLocal(boolean explicitChoice) {
        return auxiliary(Action.IMPORT_QR,new char[0],explicitChoice,Stage.QR_MIGRATION);
    }
    public boolean retryLocal(char[] freshSyntheticInput,boolean explicitChoice) {
        Action action;
        synchronized(this) {
            if(!explicitChoice||closed||parent==null||call!=null||retryAction==null
                    ||error!=Error.INVALID_CODE&&error!=Error.INVALID_PASSWORD&&error!=Error.WAIT)return false;
            if(stage==Stage.WAITING) {long now=elapsed();if(now<0||now<deadline)return false;}
            else if(stage!=Stage.CODE_RETRY&&stage!=Stage.PASSWORD_PARAMETERS)return false;
            action=retryAction;
            if(freshSyntheticInput==null||freshSyntheticInput.length>4096||NativeLoginProtocol.needsInput(action)&&freshSyntheticInput.length==0)return false;
            change(Stage.BUSY,Error.NONE);
        }
        dispatch(action,freshSyntheticInput,0);return true;
    }
    private boolean auxiliary(Action action,char[] input,boolean explicitChoice,Stage required) {
        int dc;
        synchronized(this) {
            if(!explicitChoice||closed||parent==null||call!=null||stage!=required||input==null||input.length>4096
                    ||NativeLoginProtocol.needsInput(action)&&input.length==0)return false;
            if(action==Action.IMPORT_QR&&migrated)return false;
            dc=action==Action.IMPORT_QR?targetDc:0;
            if(action==Action.IMPORT_QR)migrated=true;
            change(Stage.BUSY,Error.NONE);
        }
        dispatch(action,input,dc);return true;
    }
    private void dispatch(Action action,char[] input,int dc) {
        final Call current;
        synchronized(this) {
            if(closed||parent==null||call!=null)return;
            current=new Call(parent,new Request(scope,action,input,dc,operationOwner));call=current;change(Stage.BUSY,Error.NONE);
        }
        Cancellation handle=null;boolean failed=false;
        try {if(!local())throw new IllegalStateException();handle=rpc.submit(current.request,response->accept(current,response));}
        catch(RuntimeException|LinkageError unavailable){failed=true;synchronized(this){adapterFailures++;}}
        Response response;boolean cancel,selected=false;
        synchronized(this) {
            current.returned=true;current.cancellation=handle;cancel=current.done;
            if(failed||handle==null){dispose(current.buffered);response=Response.failure(Error.ADAPTER);}
            else response=current.buffered;
            current.buffered=null;
            if(!current.done&&call==current&&!closed&&response!=null) {
                // Reserve the first synchronous result before a later asynchronous callback can win.
                current.done=true;current.selected=response;selected=true;
            }
        }
        if(cancel)cancel(handle);
        if(selected)completeSelected(current,response);else if(response!=null)dispose(response);
        notifyUi();
    }
    private void accept(Call current,Response response) {
        if(response==null)response=Response.failure(Error.PROTOCOL);
        synchronized(this) {
            if(current.done||call!=current||closed){discarded++;if(current.selected!=response&&current.buffered!=response)dispose(response);return;}
            if(!current.returned){if(current.buffered==null)current.buffered=response;else{discarded++;if(current.buffered!=response)dispose(response);}return;}
            current.done=true;current.selected=response;
        }
        completeSelected(current,response);
    }
    private void completeSelected(Call current,Response response) {
        Response accepted=response;Runnable completion=null;
        // Stage only the winning, handle-validated response, outside transport locks.
        try{if(!response.acceptOriginal(current.request))accepted=Response.failure(Error.PROTOCOL);}
        catch(RuntimeException|LinkageError unavailable){accepted=Response.failure(Error.PROTOCOL);}
        synchronized(this) {
            if(call==current&&parent==current.parent&&!closed) {
                call=null;current.request.close();completion=apply(current.request.action,accepted);
            } else discarded++;
            current.selected=null;
        }
        dispose(response);if(accepted!=response)dispose(accepted);
        deliver(completion);notifyUi();
    }
    private static void dispose(Response response){if(response!=null)response.close();}
    private Runnable apply(Action action,Response response) {
        if(response.kind==Kind.ERROR) {
            retryAction=action;
            if(response.error==Error.INVALID_CODE&&action==Action.SIGN_IN){change(Stage.CODE_RETRY,response.error);return null;}
            if(response.error==Error.INVALID_PASSWORD&&action==Action.CHECK_PASSWORD){change(Stage.PASSWORD_PARAMETERS,response.error);return null;}
            if(response.error==Error.SRP_REFRESH&&action==Action.CHECK_PASSWORD){change(Stage.PASSWORD_REQUIRED,response.error);return null;}
            if(response.error==Error.WAIT) {
                long now=elapsed(),delay=response.value*1000L;
                if(now>=0&&Long.MAX_VALUE-now>=delay){deadline=now+delay;change(Stage.WAITING,response.error);return null;}
            }
            change(Stage.FAILED,response.error);return finish(false);
        }
        retryAction=null;
        if(response.kind==Kind.PASSWORD_NEEDED&&(action==Action.SEND_CODE||action==Action.SIGN_IN||action==Action.EXPORT_QR||action==Action.IMPORT_QR)) {
            change(Stage.PASSWORD_REQUIRED,Error.NONE);return null;
        }
        if(response.kind==Kind.PASSWORD_PARAMETERS&&action==Action.GET_PASSWORD){change(Stage.PASSWORD_PARAMETERS,Error.NONE);return null;}
        if(response.kind==Kind.SIGNUP&&(action==Action.SEND_CODE||action==Action.SIGN_IN)) {
            termsRequired=response.termsRequired;change(Stage.SIGNUP_REQUIRED,Error.NONE);return null;
        }
        if(response.kind==Kind.AUTHORIZED&&(action==Action.SEND_CODE||action==Action.SIGN_IN||action==Action.CHECK_PASSWORD||action==Action.SIGN_UP||action==Action.EXPORT_QR||action==Action.IMPORT_QR)) {
            change(parent.operation==Operation.REQUEST_CODE?Stage.EARLY_AUTHORIZED:Stage.AUTHORIZED,Error.NONE);
            return finish(true);
        }
        if(response.kind==Kind.CODE&&action==Action.SEND_CODE) {
            route=response.route;codeLength=response.value;
            if(route==Route.EMAIL||route==Route.SETUP_EMAIL||route==Route.FIREBASE||route==Route.PAYMENT||route==Route.FRAGMENT_SMS) {
                change(Stage.FAILED,Error.PROTOCOL);return finish(false);
            }
            change(Stage.CODE_REQUIRED,Error.NONE);return finish(true);
        }
        if(response.kind==Kind.QR_TOKEN&&action==Action.EXPORT_QR) {
            change(Stage.QR_TOKEN,Error.NONE);
            return parent.operation==Operation.REQUEST_CODE?finish(true):null;
        }
        if(response.kind==Kind.QR_MIGRATION&&action==Action.EXPORT_QR&&!migrated) {
            targetDc=response.value;change(Stage.QR_MIGRATION,Error.NONE);return null;
        }
        change(Stage.FAILED,Error.PROTOCOL);return finish(false);
    }
    private Runnable finish(boolean success) {
        Parent done=parent;parent=null;
        if(done==null)return null;
        // Local receipts only, never phone_code_hash, QR token, SRP proof or auth_key.
        Reply reply=success?(done.operation==Operation.REQUEST_CODE?Reply.codeSent(new char[]{'L'}):Reply.localSession(new char[]{'L'})):Reply.failure(Fault.PROTOCOL);
        return ()->done.listener.complete(reply);
    }
    private void abandon(Parent owner) {
        Cancellation handle=null;
        synchronized(this) {
            if(parent!=owner)return;parent=null;
            if(call!=null){call.done=true;call.request.close();dispose(call.buffered);call.buffered=null;handle=call.cancellation;call=null;}
            change(Stage.FAILED,Error.NONE);
        }
        cancel(handle);
    }
    private void cancel(Cancellation handle) {
        if(handle!=null)try{handle.cancel();}catch(RuntimeException|LinkageError failure){synchronized(this){adapterFailures++;}}
    }
    private void deliver(Runnable completion) {
        if(completion!=null)try{completion.run();}catch(RuntimeException|LinkageError failure){synchronized(this){adapterFailures++;}}
    }
    private void change(Stage next,Error reason){stage=next;error=reason;revision++;}
    private void notifyUi() {
        Runnable signal;
        synchronized(this){if(closed)return;signal=stateSignal;}
        try{signal.run();}catch(RuntimeException|LinkageError failure){synchronized(this){adapterFailures++;}}
    }
    @Override public void close() {
        Cancellation handle=null;boolean release,discard;
        synchronized(this) {
            if(closed)return;discard=stage!=Stage.AUTHORIZED;closed=true;parent=null;release=initialized;stateSignal=()->{};
            if(call!=null){call.done=true;call.request.close();dispose(call.buffered);call.buffered=null;handle=call.cancellation;call=null;}
            change(Stage.CLOSED,error);
        }
        cancel(handle);
        if(discard)try{discardUncommitted.run();}catch(RuntimeException|LinkageError failure){synchronized(this){adapterFailures++;}}
        if(release)try{if(local())rpc.close();}catch(RuntimeException|LinkageError failure){synchronized(this){adapterFailures++;}}
    }
}
