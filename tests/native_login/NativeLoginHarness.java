package io.github.jose22yt.flexygram.login;

import java.util.*;
import java.util.concurrent.*;
import java.lang.reflect.*;
import org.telegram.tgnet.*;
import org.telegram.tgnet.tl.TL_account;
import io.github.jose22yt.flexygram.session.*;
import io.github.jose22yt.flexygram.session.AuthenticationController.*;
import io.github.jose22yt.flexygram.session.RequestCoordinator.Domain;
import io.github.jose22yt.flexygram.session.RequestCoordinator.Cancellation;
import io.github.jose22yt.flexygram.session.android.*;
import io.github.jose22yt.flexygram.session.android.OperationJournal.Phase;
import io.github.jose22yt.flexygram.login.NativeLoginProtocol.*;
import io.github.jose22yt.flexygram.login.NativeLoginProtocol.Error;
import io.github.jose22yt.flexygram.login.NativePersistenceFence.*;

/** All identity, code, proof, token and original-storage values are synthetic. No network APIs. */
public final class NativeLoginHarness {
    static final String CANARY="SYNTHETIC_NATIVE_LOGIN_PRIVATE_77291";
    static char[] data(){return CANARY.toCharArray();}
    static void need(boolean b){if(!b)throw new AssertionError("NATIVE_LOGIN_CONTRACT_FAILED");}
    static void denied(Runnable r){try{r.run();}catch(IllegalArgumentException|IllegalStateException e){need(!e.toString().contains(CANARY)&&e.getCause()==null);return;}throw new AssertionError("EXPECTED_DENIAL");}
    static SessionScope scope(int n){return SessionScope.of("realAlpha","io.github.jose22yt.flexygram.realalpha",n);}
    static ClosedRuntime runtime(int n){String p="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa:realAlpha";return ClosedRuntime.verify(scope(n),p,true,new boolean[6],0,new char[0],"FLEXYGRAM_POLICY:"+p+":auth=0:transport=0:push=0:translation=0:plugins=0:restore=0");}
    static TLRPC.TL_auth_sentCode sent(){TLRPC.TL_auth_sentCode c=new TLRPC.TL_auth_sentCode();c.phone_code_hash=CANARY;c.type=new TLRPC.TL_auth_sentCodeTypeSms();return c;}
    static TLRPC.TL_auth_authorization authorized(){TLRPC.TL_auth_authorization a=new TLRPC.TL_auth_authorization();a.user=new TLRPC.TL_user();a.user.id=1;a.user.phone=CANARY;a.future_auth_token=CANARY.getBytes(java.nio.charset.StandardCharsets.UTF_8);return a;}
    static TLRPC.TL_error error(String text){TLRPC.TL_error e=new TLRPC.TL_error();e.code=400;e.text=text;return e;}
    static TL_account.TL_password password(){TL_account.TL_password p=new TL_account.TL_password();p.has_password=true;p.current_algo=new TLRPC.TL_passwordKdfAlgoSHA256SHA256PBKDF2HMACSHA512iter100000SHA256ModPow();p.srp_B=new byte[]{1};p.srp_id=1;return p;}
    static TLRPC.TL_auth_loginToken qr(){TLRPC.TL_auth_loginToken q=new TLRPC.TL_auth_loginToken();q.token=CANARY.getBytes(java.nio.charset.StandardCharsets.UTF_8);q.expires=60;return q;}
    static TLRPC.TL_auth_loginTokenSuccess qrSuccess(TLRPC.TL_auth_authorization auth){TLRPC.TL_auth_loginTokenSuccess q=new TLRPC.TL_auth_loginTokenSuccess();q.authorization=auth;return q;}
    static class Memory implements OperationJournal.Backend {
        OperationJournal.Record row=OperationJournal.Record.empty(scope(0));int writes,failAt;boolean after;
        public synchronized OperationJournal.Record read(SessionScope s){return row;}
        public synchronized boolean compareAndSet(OperationJournal.Record old,OperationJournal.Record next){writes++;if(writes==failAt&&!after)throw new IllegalStateException(CANARY);if(!row.equals(old))return false;row=next;if(writes==failAt&&after)throw new IllegalStateException(CANARY);return true;}
    }
    static class Disk implements TelegramAuthorizationStore.OriginalFormatPort {
        final EnumMap<Artifact,Stamp> stamps=new EnumMap<>(Artifact.class);int captureCalls,commits,mutations;long version=1;
        boolean authed,failBefore,failAfter,lieFailure,omitReceipts,failCapture;Domain domain=Domain.LOCAL_SIMULATION;
        Outcome outcome=Outcome.COMPLETED;TLRPC.TL_auth_authorization sameOriginal;Action source;Runnable during=()->{};Receipt foreign;
        Disk(){for(Artifact a:Artifact.values())stamps.put(a,Stamp.absent());}
        Stamp present(){return new Stamp(Presence.PRESENT,String.format(java.util.Locale.ROOT,"%032x",version++));}
        public Domain domain(){return domain;}
        public Inventory capture(SessionScope s){captureCalls++;if(failCapture)throw new IllegalStateException(CANARY);return new Inventory(s,authed,stamps);}
        public Report commitOriginal(Lease lease,TLRPC.TL_auth_authorization original,Action source){
            commits++;this.sameOriginal=original;this.source=source;during.run();
            if(failBefore)throw new IllegalStateException(CANARY);
            if(outcome==Outcome.FAILED_WITHOUT_WRITE&&!lieFailure)return new Report(outcome);
            List<Receipt> receipts=new ArrayList<>();
            for(Artifact a:new Artifact[]{Artifact.NATIVE_CONFIG,Artifact.USER_CONFIG,Artifact.MESSAGE_DATABASE}){
                Stamp before=stamps.get(a),after=present();stamps.put(a,after);receipts.add(lease.witnessLocalWrite(a,before,after));
            }
            authed=true;mutations++;
            if(failAfter)throw new IllegalStateException(CANARY);
            if(foreign!=null)receipts.set(0,foreign);
            return new Report(outcome,omitReceipts?new Receipt[0]:receipts.toArray(new Receipt[0]));
        }
    }
    static class Time implements Clock {long now=1000;boolean fail;public long elapsedMillis(){if(fail)throw new IllegalStateException(CANARY);return now;}}
    static final class Wire {
        final Action action;final TLObject value;final TLRPC.TL_error error;
        Wire(Action a,TLObject v,TLRPC.TL_error e){action=a;value=v;error=e;}
    }
    static final class Pending {
        final Request request;final Callback callback;final Wire wire;
        Pending(Request r,Callback c,Wire w){request=r;callback=c;wire=w;}
    }
    static final class Worker extends Thread {
        private final Runnable action;volatile Throwable failure;
        Worker(Runnable action){this.action=action;}
        @Override public void run(){try{action.run();}catch(Throwable failure){this.failure=failure;}}
        void finish()throws Exception{join(5000);need(!isAlive()&&failure==null);}
    }
    static class Rpc implements LocalRpc {
        final Deque<Wire> script=new ArrayDeque<>();final List<Pending> pending=new ArrayList<>();final List<Action> actions=new ArrayList<>();
        TelegramAuthorizationStore store;Domain domain=Domain.LOCAL_SIMULATION;int cancels,closes;boolean async,throwAfterCallback,noHandle,throwDomain,duplicateAuthorization,sameResponseTwice,raceResponse;
        final List<Worker> workers=new ArrayList<>();
        public Domain domain(){if(throwDomain)throw new IllegalStateException(CANARY);return domain;}
        public SessionScope scope(){return NativeLoginHarness.scope(0);}
        void add(Action action,TLObject value){script.add(new Wire(action,value,null));}
        void fail(Action action,String text){script.add(new Wire(action,null,error(text)));}
        public Cancellation submit(Request request,Callback cb){
            actions.add(request.action);need(!script.isEmpty());Wire w=script.remove();need(w.action==request.action);
            Pending p=new Pending(request,cb,w);pending.add(p);if(!async)respond(p);
            if(duplicateAuthorization&&request.action==Action.SEND_CODE){TLRPC.TL_auth_sentCodeSuccess extra=new TLRPC.TL_auth_sentCodeSuccess();extra.authorization=authorized();cb.complete(TlAuthResponses.mapAndStageLocal(request,store,extra,null));}
            if(raceResponse&&request.action==Action.SEND_CODE){Worker worker=new Worker(()->{TLRPC.TL_auth_sentCodeSuccess extra=new TLRPC.TL_auth_sentCodeSuccess();extra.authorization=authorized();cb.complete(TlAuthResponses.mapAndStageLocal(request,store,extra,null));});workers.add(worker);worker.start();}
            if(throwAfterCallback)throw new IllegalStateException(CANARY);
            return noHandle?null:()->cancels++;
        }
        void respond(Pending p){Response response=TlAuthResponses.mapAndStageLocal(p.request,store,p.wire.value,p.wire.error);p.callback.complete(response);if(sameResponseTwice)p.callback.complete(response);}
        public void close(){closes++;}
    }
    static class C {
        final Memory memory=new Memory();final Disk disk=new Disk();final Time time=new Time();
        final OperationJournal journal=new OperationJournal(memory,scope(0));
        final TelegramAuthorizationStore store=new TelegramAuthorizationStore(runtime(0),journal,disk);
        final Rpc rpc=new Rpc();final NativeLoginTransport transport;final LoginFlowOwner owner;
        C(){rpc.store=store;transport=store.localTransport(runtime(0),rpc,time);owner=new LoginFlowOwner(runtime(0),transport,store,Runnable::run);transport.bindLocalStateSignal(owner::signalLocalAdapterState);}
        void open(){need(owner.initializeLocal(false));need(owner.snapshot().state==State.READY);}
        void code(){open();need(owner.startLocal(data()));need(owner.snapshot().state==State.CODE_REQUIRED);}
        void authorized(TLRPC.TL_auth_authorization auth){rpc.add(Action.SEND_CODE,sent());rpc.add(Action.SIGN_IN,auth);code();need(owner.verifyLocal(data()));need(owner.snapshot().state==State.LOCAL_AUTHORIZED);}
    }
    static Object staged(TelegramAuthorizationStore s)throws Exception{Field f=s.getClass().getDeclaredField("staged");f.setAccessible(true);return f.get(s);}
    public static void main(String[] args)throws Exception {
        String test=args[0];C c=new C();
        switch(test){
        case "nativeCodeAndCommit":{
            TLRPC.TL_auth_authorization auth=authorized();c.authorized(auth);need(c.disk.commits==0);c.owner.commitLocal();
            need(c.owner.snapshot().state==State.LOCAL_COMPLETE&&c.memory.row.phase==Phase.COMPLETED&&c.disk.sameOriginal==auth&&c.disk.source==Action.SIGN_IN&&c.disk.commits==1);
            need(staged(c.store)==null&&CANARY.equals(auth.user.phone));c.owner.close();need(c.disk.mutations==1);break;}
        case "passwordAndExplicitRetry":{
            c.rpc.add(Action.SEND_CODE,sent());c.rpc.fail(Action.SIGN_IN,"SESSION_PASSWORD_NEEDED");c.rpc.add(Action.GET_PASSWORD,password());c.rpc.fail(Action.CHECK_PASSWORD,"PASSWORD_HASH_INVALID");c.rpc.add(Action.CHECK_PASSWORD,authorized());
            List<NativeLoginProtocol.Stage> events=new ArrayList<>();c.owner.attachView(Runnable::run,s->events.add(c.transport.snapshot().stage));c.code();c.owner.verifyLocal(data());
            need(c.owner.snapshot().state==State.VERIFYING&&c.transport.snapshot().stage==NativeLoginProtocol.Stage.PASSWORD_REQUIRED&&c.rpc.actions.size()==2);
            need(!c.transport.loadPasswordParametersLocal(false)&&c.transport.loadPasswordParametersLocal(true));need(!c.transport.checkPasswordProofLocal(new char[0],true));
            c.transport.checkPasswordProofLocal(data(),true);need(c.transport.snapshot().error==Error.INVALID_PASSWORD&&c.rpc.actions.size()==4);
            need(!c.transport.retryLocal(data(),false));need(c.transport.retryLocal(data(),true));need(c.owner.snapshot().state==State.LOCAL_AUTHORIZED&&events.contains(NativeLoginProtocol.Stage.PASSWORD_REQUIRED));
            c.owner.commitLocal();need(c.disk.source==Action.CHECK_PASSWORD&&c.memory.row.phase==Phase.COMPLETED);break;}
        case "srpRefreshNeverAutomatic":{
            c.rpc.add(Action.SEND_CODE,sent());c.rpc.fail(Action.SIGN_IN,"SESSION_PASSWORD_NEEDED");c.rpc.add(Action.GET_PASSWORD,password());c.rpc.fail(Action.CHECK_PASSWORD,"SRP_ID_INVALID");c.rpc.add(Action.GET_PASSWORD,password());c.rpc.add(Action.CHECK_PASSWORD,authorized());
            c.code();c.owner.verifyLocal(data());c.transport.loadPasswordParametersLocal(true);c.transport.checkPasswordProofLocal(data(),true);
            need(c.rpc.actions.size()==4&&c.transport.snapshot().stage==NativeLoginProtocol.Stage.PASSWORD_REQUIRED&&!c.transport.retryLocal(data(),true));
            c.transport.loadPasswordParametersLocal(true);need(!c.transport.retryLocal(data(),true));c.transport.checkPasswordProofLocal(data(),true);need(c.owner.snapshot().state==State.LOCAL_AUTHORIZED);break;}
        case "signupRequiresConsentAndKeepsOrigin":{
            TLRPC.TL_auth_authorizationSignUpRequired signup=new TLRPC.TL_auth_authorizationSignUpRequired();signup.terms_of_service=new TLRPC.TL_help_termsOfService();
            c.rpc.add(Action.SEND_CODE,sent());c.rpc.add(Action.SIGN_IN,signup);c.rpc.add(Action.SIGN_UP,authorized());c.code();c.owner.verifyLocal(data());
            need(c.transport.snapshot().termsRequired&&!c.transport.signUpLocal(data(),false,true)&&!c.transport.signUpLocal(data(),true,false)&&c.rpc.actions.size()==2);
            need(c.transport.signUpLocal(data(),true,true));c.owner.commitLocal();need(c.disk.source==Action.SIGN_UP&&c.disk.commits==1);break;}
        case "sendCodeEarlyAuthorization":{
            TLRPC.TL_auth_sentCodeSuccess success=new TLRPC.TL_auth_sentCodeSuccess();success.authorization=authorized();c.rpc.add(Action.SEND_CODE,success);
            c.open();c.owner.startLocal(data());need(c.owner.snapshot().state==State.CODE_REQUIRED&&c.transport.snapshot().stage==NativeLoginProtocol.Stage.EARLY_AUTHORIZED&&c.disk.commits==0);
            c.owner.verifyLocal(new char[]{'L'});need(c.rpc.actions.size()==1&&c.owner.snapshot().state==State.LOCAL_AUTHORIZED);c.owner.commitLocal();need(c.disk.source==Action.SEND_CODE);break;}
        case "qrMigrationExplicitAndScoped":{
            need(c.transport.selectQrLocal(true));c.rpc.add(Action.EXPORT_QR,qr());TLRPC.TL_auth_loginTokenMigrateTo move=new TLRPC.TL_auth_loginTokenMigrateTo();move.dc_id=2;move.token=new byte[]{1};
            c.rpc.add(Action.EXPORT_QR,move);c.rpc.add(Action.IMPORT_QR,qrSuccess(authorized()));c.code();c.owner.verifyLocal(data());
            need(c.transport.snapshot().stage==NativeLoginProtocol.Stage.QR_MIGRATION&&c.rpc.actions.size()==2&&!c.transport.approveMigrationLocal(false));
            need(c.transport.approveMigrationLocal(true));need(c.rpc.pending.get(2).request.datacenter==2&&c.owner.snapshot().state==State.LOCAL_AUTHORIZED);c.owner.commitLocal();need(c.disk.source==Action.IMPORT_QR);break;}
        case "qrRefreshHasNoTimer":{
            c.transport.selectQrLocal(true);c.rpc.add(Action.EXPORT_QR,qr());c.rpc.add(Action.EXPORT_QR,qr());c.rpc.add(Action.EXPORT_QR,qrSuccess(authorized()));c.code();c.owner.verifyLocal(data());
            need(c.rpc.actions.size()==2&&c.owner.snapshot().state==State.VERIFYING&&!c.transport.pollQrLocal(false));c.transport.pollQrLocal(true);need(c.owner.snapshot().state==State.LOCAL_AUTHORIZED&&c.rpc.actions.size()==3);break;}
        case "floodWaitUsesClockAndConsent":{
            c.rpc.add(Action.SEND_CODE,sent());c.rpc.fail(Action.SIGN_IN,"FLOOD_WAIT_2");c.rpc.add(Action.SIGN_IN,authorized());c.code();c.owner.verifyLocal(data());
            need(!c.transport.retryLocal(data(),true)&&c.rpc.actions.size()==2);c.time.now=2999;need(!c.transport.retryLocal(data(),true));c.time.now=3000;need(!c.transport.retryLocal(data(),false));need(c.transport.retryLocal(data(),true)&&c.rpc.actions.size()==3);break;}
        case "codeInvalidRetryAndExpiryTerminal":{
            c.rpc.add(Action.SEND_CODE,sent());c.rpc.fail(Action.SIGN_IN,"PHONE_CODE_INVALID");c.rpc.fail(Action.SIGN_IN,"PHONE_CODE_EXPIRED");c.code();c.owner.verifyLocal(data());
            need(c.transport.snapshot().stage==NativeLoginProtocol.Stage.CODE_RETRY&&!c.transport.retryLocal(data(),false));c.transport.retryLocal(data(),true);
            need(c.owner.snapshot().state==State.FAILED&&c.rpc.actions.size()==3&&c.disk.commits==0&&c.memory.row.phase==Phase.CANCELLED);break;}
        case "cancelAndLateAuthorization":{
            c.rpc.add(Action.SEND_CODE,sent());c.code();c.rpc.async=true;c.rpc.add(Action.SIGN_IN,authorized());c.owner.verifyLocal(data());Pending p=c.rpc.pending.get(1);
            c.owner.cancelLocal();need(p.request.isClosed()&&c.rpc.cancels==1&&c.memory.row.phase==Phase.CANCELLED);c.rpc.respond(p);
            need(c.owner.snapshot().state==State.CANCELLED&&staged(c.store)==null&&c.disk.commits==0&&c.transport.discardedReplies()==1);break;}
        case "callbackThenThrowCannotCommit":{
            c.rpc.add(Action.SEND_CODE,sent());c.code();c.rpc.add(Action.SIGN_IN,authorized());c.rpc.throwAfterCallback=true;c.owner.verifyLocal(data());
            need(c.owner.snapshot().state==State.FAILED&&c.disk.commits==0&&staged(c.store)==null&&c.transport.adapterFailures()==1);break;}
        case "nullHandleCannotCommit":{
            c.rpc.add(Action.SEND_CODE,sent());c.code();c.rpc.add(Action.SIGN_IN,authorized());c.rpc.noHandle=true;c.owner.verifyLocal(data());
            need(c.owner.snapshot().state==State.FAILED&&staged(c.store)==null&&c.disk.commits==0);break;}
        case "duplicateResponseNotReused":{
            c.rpc.add(Action.SEND_CODE,sent());c.code();Pending first=c.rpc.pending.get(0);first.callback.complete(Response.of(Kind.AUTHORIZED));
            need(c.transport.snapshot().stage==NativeLoginProtocol.Stage.CODE_REQUIRED&&c.transport.discardedReplies()==1&&c.disk.commits==0);break;}
        case "duplicateRawAuthorizationCannotPoisonNextStep":{
            c.rpc.add(Action.SEND_CODE,sent());c.rpc.add(Action.SIGN_IN,authorized());c.rpc.duplicateAuthorization=true;c.code();need(staged(c.store)==null);c.owner.verifyLocal(data());need(c.owner.snapshot().state==State.LOCAL_AUTHORIZED);c.owner.commitLocal();need(c.disk.commits==1);break;}
        case "sameResponseObjectAcceptedOnce":{
            c.rpc.sameResponseTwice=true;c.authorized(authorized());c.owner.commitLocal();need(c.memory.row.phase==Phase.COMPLETED&&c.disk.commits==1&&c.transport.discardedReplies()==2);break;}
        case "concurrentFirstResponseWins":{
            for(int i=0;i<20;i++){C local=new C();local.rpc.add(Action.SEND_CODE,sent());local.rpc.raceResponse=true;local.code();local.rpc.workers.get(0).finish();need(staged(local.store)==null&&local.owner.snapshot().state==State.CODE_REQUIRED&&local.disk.commits==0);local.owner.close();}break;}
        case "domainChangeCannotDispatch":{
            c.rpc.add(Action.SEND_CODE,sent());c.code();c.rpc.domain=Domain.TELEGRAM;c.owner.verifyLocal(data());need(c.rpc.actions.size()==1&&c.owner.snapshot().state==State.FAILED&&c.disk.commits==0);break;}
        case "accountSeparation":{
            denied(()->new NativeLoginTransport(runtime(1),c.rpc,c.time));need(c.rpc.actions.isEmpty());
            Disk other=new Disk();other.domain=Domain.TELEGRAM;TelegramAuthorizationStore s=new TelegramAuthorizationStore(runtime(0),new OperationJournal(new Memory(),scope(0)),other);denied(()->s.beginExplicit(false));need(other.captureCalls==0&&other.commits==0);break;}
        case "unprovenHandshakeIsNotOwned":{
            c.authorized(authorized());c.disk.stamps.put(Artifact.NATIVE_CONFIG,c.disk.present());c.owner.commitLocal();
            need(c.owner.snapshot().state==State.STORAGE_UNCERTAIN&&c.memory.row.phase==Phase.UNCERTAIN&&c.disk.commits==0);break;}
        case "ownedHandshakeContinuesSameFormat":{
            c.rpc.add(Action.SEND_CODE,sent());c.rpc.add(Action.SIGN_IN,authorized());c.open();Lease lease=c.store.operation();Stamp a=Stamp.absent(),b=c.disk.present();c.disk.stamps.put(Artifact.NATIVE_CONFIG,b);c.store.recordLocalWrite(lease,lease.witnessLocalWrite(Artifact.NATIVE_CONFIG,a,b));
            c.owner.startLocal(data());c.owner.verifyLocal(data());c.owner.commitLocal();need(c.memory.row.phase==Phase.COMPLETED&&c.disk.commits==1);break;}
        case "preexistingSessionNeverMutated":{
            c.disk.authed=true;need(c.owner.initializeLocal(false));need(c.owner.failure()==LoginFlowOwner.Failure.LOCAL_OPERATION&&c.memory.writes==0&&c.disk.commits==0&&c.rpc.actions.isEmpty());break;}
        case "preexistingNativeFilesNeedReview":{
            c.disk.stamps.put(Artifact.NATIVE_CONFIG,c.disk.present());c.owner.initializeLocal(false);need(c.memory.writes==0&&c.disk.commits==0&&c.rpc.actions.isEmpty());break;}
        case "existingDatabaseOriginPreserved":{
            c.disk.stamps.put(Artifact.MESSAGE_DATABASE,c.disk.present());c.authorized(authorized());c.owner.commitLocal();need(c.memory.row.phase==Phase.COMPLETED&&c.disk.mutations==1);break;}
        case "missingWriteReceiptsStayUncertain":{
            c.authorized(authorized());c.disk.omitReceipts=true;c.owner.commitLocal();need(c.owner.snapshot().state==State.STORAGE_UNCERTAIN&&c.memory.row.phase==Phase.UNCERTAIN&&c.disk.authed&&c.disk.mutations==1);c.owner.close();need(c.disk.authed&&c.disk.commits==1);break;}
        case "failedWriteIsNotRetried":{
            c.authorized(authorized());c.disk.outcome=Outcome.FAILED_WITHOUT_WRITE;c.owner.commitLocal();need(c.memory.row.phase==Phase.FAILED&&c.disk.mutations==0&&c.disk.commits==1);c.owner.commitLocal();need(c.disk.commits==1);break;}
        case "writeThenThrowIsNeverRolledBack":{
            c.authorized(authorized());c.disk.failAfter=true;c.owner.commitLocal();need(c.owner.snapshot().state==State.STORAGE_UNCERTAIN&&c.memory.row.phase==Phase.UNCERTAIN&&c.disk.authed&&staged(c.store)==null);c.owner.close();need(c.disk.authed&&c.disk.commits==1);break;}
        case "lyingFailureCannotBeKnownFailed":{
            c.authorized(authorized());c.disk.outcome=Outcome.FAILED_WITHOUT_WRITE;c.disk.lieFailure=true;c.owner.commitLocal();need(c.memory.row.phase==Phase.UNCERTAIN&&c.disk.authed);break;}
        case "journalFailureAfterOriginalWrite":{
            c.authorized(authorized());c.memory.failAt=3;c.owner.commitLocal();need(c.disk.authed&&c.disk.commits==1&&c.memory.row.phase==Phase.WRITING&&c.owner.snapshot().state==State.STORAGE_UNCERTAIN);break;}
        case "foreignReceiptRejected":{
            C other=new C();other.open();Lease foreign=other.store.operation();c.disk.foreign=foreign.witnessLocalWrite(Artifact.NATIVE_CONFIG,Stamp.absent(),other.disk.present());c.authorized(authorized());c.owner.commitLocal();need(c.memory.row.phase==Phase.UNCERTAIN&&other.disk.commits==0);break;}
        case "reentrantCloseKeepsWriteOutcome":{
            c.authorized(authorized());c.disk.during=c.store::close;c.owner.commitLocal();need(c.memory.row.phase==Phase.COMPLETED&&c.disk.commits==1&&staged(c.store)==null);break;}
        case "foreignRequestCannotStageAuthorization":{
            c.open();Request foreign=new Request(scope(0),Action.SIGN_IN,data(),0);denied(()->c.store.stageLocal(c.store.operation(),foreign,authorized()));need(staged(c.store)==null&&c.disk.commits==0);foreign.close();break;}
        case "authorizationRevalidatedBeforeWrite":{
            TLRPC.TL_auth_authorization auth=authorized();c.authorized(auth);auth.user=null;c.owner.commitLocal();need(c.disk.commits==0&&staged(c.store)==null&&c.owner.snapshot().fault==io.github.jose22yt.flexygram.session.RequestCoordinator.Fault.CONFLICT);break;}
        case "androidViewRecreationNoRequestReplay":{
            c.rpc.add(Action.SEND_CODE,sent());c.open();android.os.Looper.main=true;LoginActivityAdapter ui=new LoginActivityAdapter(scope(0),c.owner);int[] old={0},fresh={0};
            AuthUiRelay.Binding first=ui.attach(new org.telegram.ui.LoginActivity(0),s->old[0]++);ui.onLocalStart(data());ui.detach(first);ui.attach(new org.telegram.ui.LoginActivity(0),s->fresh[0]++);android.os.Handler.flush();
            need(old[0]==0&&fresh[0]==1&&c.rpc.actions.size()==1&&ui.viewState().attachments==2);ui.destroyOwner();need(staged(c.store)==null);break;}
        case "processRecreationOnlyRestartsMarker":{
            android.os.Looper.main=true;LoginActivityAdapter ui=new LoginActivityAdapter(scope(0),c.owner);android.os.Bundle marker=new android.os.Bundle();ui.saveRestartMarker(marker);need(ui.restoreAfterProcessDeath(marker));need(!c.owner.initializeLocal(false)&&c.owner.snapshot().state==State.RESTART_REQUIRED&&c.rpc.actions.isEmpty()&&c.memory.writes==0);break;}
        case "typedMappingAndPrivacyMatrix":{
            String[] suffix={"App","Sms","Call","FlashCall","MissedCall","SmsWord","SmsPhrase","FragmentSms","EmailCode","SetUpEmailRequired","FirebaseSms"};
            Route[] routes={Route.APP,Route.SMS,Route.CALL,Route.FLASH_CALL,Route.MISSED_CALL,Route.WORD,Route.PHRASE,Route.FRAGMENT_SMS,Route.EMAIL,Route.SETUP_EMAIL,Route.FIREBASE};
            for(int i=0;i<suffix.length;i++){TLRPC.TL_auth_sentCode code=sent();code.type=(TLRPC.auth_SentCodeType)Class.forName("org.telegram.tgnet.TLRPC$TL_auth_sentCodeType"+suffix[i]).getDeclaredConstructor().newInstance();Response r=TlAuthResponses.map(Action.SEND_CODE,code,null);need(r.kind==Kind.CODE&&r.route==routes[i]&&!r.toString().contains(CANARY));}
            need(TlAuthResponses.map(Action.SEND_CODE,new TLRPC.TL_auth_sentCodePaymentRequired(),null).route==Route.PAYMENT);
            need(NativeLoginProtocol.error("SESSION_PASSWORD_NEEDED "+CANARY).error==Error.REMOTE&&NativeLoginProtocol.error("FLOOD_WAIT_99999999").error==Error.REMOTE);
            for(Field f:Response.class.getDeclaredFields())need(f.getType()!=String.class);
            need(!new Request(scope(0),Action.SIGN_IN,data(),0).toString().contains(CANARY));break;}
        case "unsupportedRouteHasNoFallback":{
            TLRPC.TL_auth_sentCode code=sent();code.type=new TLRPC.TL_auth_sentCodeTypeFirebaseSms();c.rpc.add(Action.SEND_CODE,code);c.open();c.owner.startLocal(data());need(c.owner.snapshot().state==State.FAILED&&c.rpc.actions.size()==1&&c.transport.snapshot().route==Route.FIREBASE);break;}
        case "malformedRepliesAndUnknownAlgorithm":{
            need(TlAuthResponses.map(Action.SIGN_IN,null,null).error==Error.PROTOCOL);need(TlAuthResponses.map(Action.SIGN_IN,authorized(),error(CANARY)).error==Error.PROTOCOL);
            TL_account.TL_password p=password();p.current_algo=new TLRPC.TL_passwordKdfAlgoUnknown();need(TlAuthResponses.map(Action.GET_PASSWORD,p,null).kind==Kind.UNSUPPORTED);
            TLRPC.TL_auth_authorization a=authorized();a.setup_password_required=true;need(TlAuthResponses.map(Action.SIGN_IN,a,null).kind==Kind.UNSUPPORTED);break;}
        case "clockAndAdapterExceptionsAreSafe":{
            c.rpc.add(Action.SEND_CODE,sent());c.rpc.fail(Action.SIGN_IN,"FLOOD_WAIT_2");c.code();c.time.fail=true;c.owner.verifyLocal(data());need(c.owner.snapshot().state==State.FAILED&&c.disk.commits==0);
            Rpc bad=new Rpc();bad.throwDomain=true;denied(()->new NativeLoginTransport(runtime(0),bad,new Time()));break;}
        default:throw new AssertionError("UNKNOWN_CASE");
        }
        need(c.disk.commits<=1);System.out.println("PASS "+test+" LOCAL_SYNTHETIC_ONLY");
    }
}
