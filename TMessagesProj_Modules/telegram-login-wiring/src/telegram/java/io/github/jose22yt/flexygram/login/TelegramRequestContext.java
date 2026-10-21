package io.github.jose22yt.flexygram.login;

import java.util.Arrays;
import org.telegram.tgnet.TLObject;
import org.telegram.tgnet.TLRPC;
import org.telegram.tgnet.tl.TL_account;
import io.github.jose22yt.flexygram.session.ClosedRuntime;
import io.github.jose22yt.flexygram.session.SessionScope;
import io.github.jose22yt.flexygram.session.RequestCoordinator.*;
import io.github.jose22yt.flexygram.login.NativeLoginProtocol.*;
import io.github.jose22yt.flexygram.login.NativeLoginProtocol.Error;
import io.github.jose22yt.flexygram.login.NativeLoginProtocol.Kind;

/** Original request types, LOCAL port only. Never a ConnectionsManager adapter or credential resolver. */
public final class TelegramRequestContext implements LocalRpc {
    public interface RawCallback {void complete(TLObject response,TLRPC.TL_error error);}
    public interface LocalPort {
        Domain domain(); SessionScope scope();
        Cancellation submit(TLObject original,int datacenter,RawCallback callback);
        void close();
    }
    public interface LocalProof {
        Domain domain();
        TLRPC.TL_inputCheckPasswordSRP create(char[] synthetic,TL_account.Password parameters);
    }
    private static final class Raw {
        TLObject response;TLRPC.TL_error error;
        Raw(TLObject r,TLRPC.TL_error e){response=r;error=e;}
        void clear(){response=null;error=null;}
    }
    private static final class Flight {
        final long epoch; final Request request; final Callback callback;
        TLObject original;Raw buffered;Cancellation handle;
        boolean returned,done;
        Flight(long epoch,Request r,Callback c,TLObject original){this.epoch=epoch;request=r;callback=c;this.original=original;}
    }
    private final SessionScope scope;
    private final TelegramAuthorizationStore store;
    private final LocalPort port;
    private final LocalProof proof;
    private char[] phone,first,last;
    private String phoneHash;
    private TL_account.Password password;
    private byte[] migrationToken;
    private int migrationDc,failures,discarded;
    private long epoch;
    private boolean closed;
    private Flight flight;
    public TelegramRequestContext(ClosedRuntime runtime,TelegramAuthorizationStore store,LocalPort port,LocalProof proof) {
        if(runtime==null||runtime.scope.variant!=SessionScope.Variant.REAL_ALPHA||store==null||port==null||proof==null)
            throw new IllegalArgumentException("LOCAL_REQUEST_CONTEXT_REQUIRED");
        scope=runtime.scope;this.store=store;this.port=port;this.proof=proof;
        if(!local())throw new IllegalArgumentException("LOCAL_REQUEST_CONTEXT_REQUIRED");
    }
    private boolean local(){try{return port.domain()==Domain.LOCAL_SIMULATION&&scope.equals(port.scope())&&proof.domain()==Domain.LOCAL_SIMULATION;}catch(RuntimeException|LinkageError e){return false;}}
    @Override public Domain domain(){return Domain.LOCAL_SIMULATION;}
    @Override public SessionScope scope(){return scope;}
    public synchronized int adapterFailures(){return failures;}
    public synchronized int discardedReplies(){return discarded;}
    /** Explicit synthetic names; consent/terms are checked by NativeLoginTransport before SIGN_UP. */
    public synchronized void namesLocal(char[] first,char[] last) {
        if(closed||flight!=null||first==null||first.length==0||last==null||first.length>128||last.length>128)
            throw new IllegalStateException("LOCAL_NAMES_REJECTED");
        wipe(this.first);wipe(this.last);this.first=first.clone();this.last=last.clone();
    }
    @Override public Cancellation submit(Request request,Callback callback) {
        final Flight current;
        synchronized(this) {
            if(closed||flight!=null||request==null||request.isClosed()||callback==null||!scope.equals(request.scope)||!local()||!request.belongsTo(store.operation())
                    ||request.action!=Action.IMPORT_QR&&request.datacenter!=0)
                throw new IllegalStateException("LOCAL_REQUEST_REJECTED");
            TLObject original;
            try{original=build(request);}catch(RuntimeException|LinkageError unavailable){clearState();throw new IllegalStateException("LOCAL_REQUEST_BUILD_FAILED");}
            current=new Flight(++epoch,request,callback,original);flight=current;
        }
        Cancellation handle=null;boolean failed=false;
        try{handle=port.submit(current.original,request.datacenter,(response,error)->receive(current,new Raw(response,error)));}
        catch(RuntimeException|LinkageError unavailable){failed=true;synchronized(this){failures++;}}
        Raw selected;boolean cancel;
        synchronized(this) {
            current.returned=true;current.handle=handle;cancel=current.done||flight!=current||closed;
            selected=current.buffered;current.buffered=null;
            if(!cancel) {
                if(failed||handle==null){if(selected!=null)selected.clear();selected=new Raw(null,null);}
                if(selected!=null)current.done=true;
            } else if(selected!=null){selected.clear();selected=null;}
        }
        if(cancel)cancel(handle);
        if(selected!=null)complete(current,selected);
        return ()->cancelFlight(current);
    }
    private TLObject build(Request request) {
        char[] input=request.copyInput();
        try {
            switch(request.action) {
            case SEND_CODE:
                if(input.length==0||phone!=null&&!Arrays.equals(phone,input))throw new IllegalStateException();
                wipe(phone);phoneHash=null;
                phone=input.clone();TLRPC.TL_auth_sendCode send=new TLRPC.TL_auth_sendCode();
                send.phone_number=new String(phone);send.api_id=0;send.api_hash="";send.settings=new TLRPC.TL_codeSettings();return send;
            case SIGN_IN:
                requirePhone();if(input.length==0)throw new IllegalStateException();
                TLRPC.TL_auth_signIn sign=new TLRPC.TL_auth_signIn();sign.flags=1;sign.phone_number=new String(phone);sign.phone_code_hash=phoneHash;sign.phone_code=new String(input);return sign;
            case GET_PASSWORD:return new TL_account.getPassword();
            case CHECK_PASSWORD:
                if(password==null||input.length==0)throw new IllegalStateException();
                TLRPC.TL_inputCheckPasswordSRP checked=proof.create(input,password);
                if(checked==null||checked.A==null||checked.A.length==0||checked.M1==null||checked.M1.length==0||checked.srp_id!=password.srp_id)throw new IllegalStateException();
                TLRPC.TL_auth_checkPassword check=new TLRPC.TL_auth_checkPassword();check.password=checked;return check;
            case SIGN_UP:
                requirePhone();if(first==null)throw new IllegalStateException();
                TLRPC.TL_auth_signUp signup=new TLRPC.TL_auth_signUp();signup.phone_number=new String(phone);signup.phone_code_hash=phoneHash;signup.first_name=new String(first);signup.last_name=new String(last);return signup;
            case EXPORT_QR:
                TLRPC.TL_auth_exportLoginToken export=new TLRPC.TL_auth_exportLoginToken();export.api_id=0;export.api_hash="";return export;
            case IMPORT_QR:
                if(migrationToken==null||request.datacenter!=migrationDc)throw new IllegalStateException();
                TLRPC.TL_auth_importLoginToken imported=new TLRPC.TL_auth_importLoginToken();imported.token=migrationToken.clone();Arrays.fill(migrationToken,(byte)0);migrationToken=null;migrationDc=0;return imported;
            default:throw new IllegalStateException();
            }
        }finally{wipe(input);}
    }
    private void requirePhone(){if(phone==null||phoneHash==null||phoneHash.isEmpty())throw new IllegalStateException();}
    private void receive(Flight current,Raw raw) {
        synchronized(this) {
            if(closed||flight!=current||current.done||current.request.isClosed()){discarded++;raw.clear();return;}
            if(!current.returned){if(current.buffered==null)current.buffered=raw;else{discarded++;raw.clear();}return;}
            current.done=true;
        }
        complete(current,raw);
    }
    private void complete(Flight current,Raw raw) {
        Response result;
        synchronized(this) {
            if(closed||flight!=current||current.epoch!=epoch||current.request.isClosed()) {raw.clear();discarded++;return;}
            try {
                result=TlAuthResponses.mapAndStageLocal(current.request,store,raw.response,raw.error);
                if(result.kind==Kind.CODE&&raw.response instanceof TLRPC.TL_auth_sentCode)phoneHash=((TLRPC.TL_auth_sentCode)raw.response).phone_code_hash;
                if(result.kind==Kind.PASSWORD_PARAMETERS&&raw.response instanceof TL_account.Password)password=(TL_account.Password)raw.response;
                if(result.error==Error.SRP_REFRESH)password=null;
                if(result.kind==Kind.QR_MIGRATION&&raw.response instanceof TLRPC.TL_auth_loginTokenMigrateTo) {
                    TLRPC.TL_auth_loginTokenMigrateTo migration=(TLRPC.TL_auth_loginTokenMigrateTo)raw.response;
                    if(migrationToken!=null)Arrays.fill(migrationToken,(byte)0);
                    migrationToken=migration.token.clone();migrationDc=migration.dc_id;
                }
                boolean retryError=result.error==Error.INVALID_CODE||result.error==Error.INVALID_PASSWORD||result.error==Error.WAIT||result.error==Error.SRP_REFRESH;
                boolean blockedRoute=result.kind==Kind.CODE&&(result.route==Route.EMAIL||result.route==Route.SETUP_EMAIL||result.route==Route.FIREBASE||result.route==Route.PAYMENT||result.route==Route.FRAGMENT_SMS);
                if(result.kind==Kind.AUTHORIZED||result.kind==Kind.UNSUPPORTED||blockedRoute||result.kind==Kind.ERROR&&!retryError)clearState();
            }catch(RuntimeException|LinkageError unavailable){failures++;clearState();result=Response.failure(Error.ADAPTER);}
            finally{raw.clear();clearOriginal(current.original);current.original=null;flight=null;}
        }
        try{current.callback.complete(result);}catch(RuntimeException|LinkageError unavailable){result.close();synchronized(this){failures++;clearState();}}
    }
    private void cancelFlight(Flight current) {
        Cancellation handle;
        synchronized(this) {
            if(flight!=current)return;
            flight=null;current.done=true;++epoch;handle=current.handle;
            if(current.buffered!=null)current.buffered.clear();current.buffered=null;
            clearOriginal(current.original);current.original=null;clearState();
        }
        cancel(handle);
    }
    @Override public void close() {
        Flight current;
        synchronized(this){if(closed)return;closed=true;current=flight;clearState();}
        if(current!=null)cancelFlight(current);
        try{port.close();}catch(RuntimeException|LinkageError unavailable){synchronized(this){failures++;}}
    }
    private void cancel(Cancellation handle){if(handle!=null)try{handle.cancel();}catch(RuntimeException|LinkageError unavailable){synchronized(this){failures++;}}}
    private void clearState(){wipe(phone);wipe(first);wipe(last);phone=first=last=null;phoneHash=null;password=null;if(migrationToken!=null)Arrays.fill(migrationToken,(byte)0);migrationToken=null;migrationDc=0;}
    private static void wipe(char[] a){if(a!=null)Arrays.fill(a,'\0');}
    private static void clearOriginal(TLObject value) {
        if(value instanceof TLRPC.TL_auth_sendCode){TLRPC.TL_auth_sendCode r=(TLRPC.TL_auth_sendCode)value;r.phone_number=null;r.api_hash="";r.settings=null;}
        if(value instanceof TLRPC.TL_auth_signIn){TLRPC.TL_auth_signIn r=(TLRPC.TL_auth_signIn)value;r.phone_number=r.phone_code_hash=r.phone_code=null;r.email_verification=null;}
        if(value instanceof TLRPC.TL_auth_signUp){TLRPC.TL_auth_signUp r=(TLRPC.TL_auth_signUp)value;r.phone_number=r.phone_code_hash=r.first_name=r.last_name=null;}
        if(value instanceof TLRPC.TL_auth_checkPassword){TLRPC.TL_auth_checkPassword r=(TLRPC.TL_auth_checkPassword)value;if(r.password instanceof TLRPC.TL_inputCheckPasswordSRP){TLRPC.TL_inputCheckPasswordSRP p=(TLRPC.TL_inputCheckPasswordSRP)r.password;if(p.A!=null)Arrays.fill(p.A,(byte)0);if(p.M1!=null)Arrays.fill(p.M1,(byte)0);}r.password=null;}
        if(value instanceof TLRPC.TL_auth_importLoginToken){TLRPC.TL_auth_importLoginToken r=(TLRPC.TL_auth_importLoginToken)value;if(r.token!=null)Arrays.fill(r.token,(byte)0);r.token=null;}
    }
    @Override public String toString(){return "TelegramRequestContext[LOCAL_ONLY_REDACTED]";}
}
