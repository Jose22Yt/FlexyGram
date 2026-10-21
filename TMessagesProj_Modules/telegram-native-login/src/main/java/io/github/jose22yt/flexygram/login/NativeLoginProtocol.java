package io.github.jose22yt.flexygram.login;

import io.github.jose22yt.flexygram.session.SessionScope;
import io.github.jose22yt.flexygram.session.RequestCoordinator.Domain;
import io.github.jose22yt.flexygram.session.RequestCoordinator.Cancellation;
import java.util.Arrays;

/** Typed metadata only. No TL serialization, password algorithm, phone hash or token storage. */
public final class NativeLoginProtocol {
    private NativeLoginProtocol() {}
    public enum Action { SEND_CODE, SIGN_IN, GET_PASSWORD, CHECK_PASSWORD, SIGN_UP, EXPORT_QR, IMPORT_QR }
    public enum Kind { CODE, PASSWORD_NEEDED, PASSWORD_PARAMETERS, SIGNUP, QR_TOKEN, QR_MIGRATION, AUTHORIZED, ERROR, UNSUPPORTED }
    public enum Route { NONE, APP, SMS, CALL, FLASH_CALL, MISSED_CALL, WORD, PHRASE, FRAGMENT_SMS, EMAIL, SETUP_EMAIL, FIREBASE, PAYMENT }
    public enum Error { NONE, INVALID_CODE, EXPIRED_CODE, INVALID_PASSWORD, SRP_REFRESH, WAIT, PHONE_INVALID, PHONE_BANNED, SESSION_REVOKED, REMOTE, PROTOCOL, ADAPTER }
    public enum Stage { NEW, READY, BUSY, CODE_REQUIRED, CODE_RETRY, PASSWORD_REQUIRED, PASSWORD_PARAMETERS,
        SIGNUP_REQUIRED, QR_TOKEN, QR_MIGRATION, WAITING, EARLY_AUTHORIZED, AUTHORIZED, FAILED, CLOSED }
    public static final class Response {
        public final Kind kind;
        public final Route route;
        public final Error error;
        public final int value;
        public final boolean termsRequired;
        private Response(Kind kind,Route route,Error error,int value,boolean terms) {
            this.kind=kind;this.route=route;this.error=error;this.value=value;termsRequired=terms;
        }
        public static Response of(Kind kind) {
            if(kind==null || kind==Kind.ERROR || kind==Kind.CODE || kind==Kind.QR_MIGRATION)throw new IllegalArgumentException("RESPONSE_METADATA_REQUIRED");
            return new Response(kind,Route.NONE,Error.NONE,0,false);
        }
        public static Response code(Route route) {
            if(route==null||route==Route.NONE)throw new IllegalArgumentException("CODE_ROUTE_REQUIRED");
            return new Response(Kind.CODE,route,Error.NONE,0,false);
        }
        public static Response signup(boolean terms) {return new Response(Kind.SIGNUP,Route.NONE,Error.NONE,0,terms);}
        public static Response migration(int dc) {
            if(dc<1||dc>1000)return failure(Error.PROTOCOL);
            return new Response(Kind.QR_MIGRATION,Route.NONE,Error.NONE,dc,false);
        }
        public static Response waitSeconds(int seconds) {
            if(seconds<1||seconds>604800)return failure(Error.REMOTE);
            return new Response(Kind.ERROR,Route.NONE,Error.WAIT,seconds,false);
        }
        public static Response failure(Error error) {
            if(error==null||error==Error.NONE||error==Error.WAIT)throw new IllegalArgumentException("ERROR_METADATA_REQUIRED");
            return new Response(Kind.ERROR,Route.NONE,error,0,false);
        }
        @Override public String toString(){return "AuthResponse["+kind+","+error+"]";}
    }
    /** Owned copy. Synthetic inputs only until a separately reviewed native adapter exists. */
    public static final class Request implements AutoCloseable {
        public final SessionScope scope;
        public final Action action;
        public final int datacenter;
        private final Object operationOwner;
        private char[] input;
        public Request(SessionScope scope,Action action,char[] synthetic,int dc) {
            this(scope,action,synthetic,dc,new Object());
        }
        Request(SessionScope scope,Action action,char[] synthetic,int dc,Object owner) {
            if(scope==null||action==null||synthetic==null||synthetic.length>4096||owner==null)throw new IllegalArgumentException("LOCAL_REQUEST_REQUIRED");
            this.scope=scope;this.action=action;datacenter=dc;input=synthetic.clone();operationOwner=owner;
        }
        public boolean belongsTo(Object owner){return owner!=null&&operationOwner==owner;}
        public synchronized char[] copyInput(){if(input==null)throw new IllegalStateException("REQUEST_CLOSED");return input.clone();}
        public synchronized boolean isClosed(){return input==null;}
        @Override public synchronized void close(){if(input!=null){Arrays.fill(input,'\0');input=null;}}
        @Override public String toString(){return "LocalAuthRequest["+action+"]";}
    }
    public interface Callback {void complete(Response response);}
    public interface LocalRpc {
        Domain domain();
        SessionScope scope();
        Cancellation submit(Request request,Callback callback);
        /** Flow ownership only; never clean native account state or revoke sessions. */
        void close();
    }
    public interface Clock {long elapsedMillis();}
    public static boolean needsInput(Action action) {
        return action==Action.SEND_CODE||action==Action.SIGN_IN||action==Action.CHECK_PASSWORD||action==Action.SIGN_UP;
    }
    public static Response error(String text) {
        if("SESSION_PASSWORD_NEEDED".equals(text))return Response.of(Kind.PASSWORD_NEEDED);
        if("PHONE_CODE_INVALID".equals(text)||"PHONE_CODE_EMPTY".equals(text))return Response.failure(Error.INVALID_CODE);
        if("PHONE_CODE_EXPIRED".equals(text))return Response.failure(Error.EXPIRED_CODE);
        if("PASSWORD_HASH_INVALID".equals(text))return Response.failure(Error.INVALID_PASSWORD);
        if("SRP_ID_INVALID".equals(text))return Response.failure(Error.SRP_REFRESH);
        if("PHONE_NUMBER_INVALID".equals(text))return Response.failure(Error.PHONE_INVALID);
        if("PHONE_NUMBER_BANNED".equals(text))return Response.failure(Error.PHONE_BANNED);
        if("SESSION_REVOKED".equals(text)||"AUTH_KEY_UNREGISTERED".equals(text))return Response.failure(Error.SESSION_REVOKED);
        if(text!=null&&text.matches("FLOOD_WAIT_[0-9]{1,8}")) {
            try{return Response.waitSeconds(Integer.parseInt(text.substring(11)));}catch(NumberFormatException malformed){return Response.failure(Error.REMOTE);}
        }
        return Response.failure(Error.REMOTE);
    }
}
