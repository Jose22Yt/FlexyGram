package io.github.jose22yt.flexygram.login;
import java.util.*;
import java.lang.reflect.*;
import java.math.BigInteger;
import android.os.*;
import org.telegram.tgnet.*;
import org.telegram.tgnet.tl.TL_account;
import org.telegram.messenger.SRPHelper;
import org.telegram.ui.LoginActivity;
import io.github.jose22yt.flexygram.session.*;
import io.github.jose22yt.flexygram.session.android.*;
import io.github.jose22yt.flexygram.session.AuthenticationController.State;
import io.github.jose22yt.flexygram.session.RequestCoordinator.*;
import io.github.jose22yt.flexygram.login.NativeLoginProtocol.*;
import io.github.jose22yt.flexygram.login.NativeLoginProtocol.Error;
import static io.github.jose22yt.flexygram.login.NativeLoginHarness.*;

public class RequestContextHarness {
    static final String PRIVATE="SYNTHETIC_CONTEXT_SECRET_89123";
    static char[] data(){return PRIVATE.toCharArray();}
    static void yes(boolean b){if(!b)throw new AssertionError("LOCAL_CONTEXT_CONTRACT");}
    static class Sink implements OutputSerializedData {
        final List<Object> values=new ArrayList<>();
        public void writeInt32(int n){values.add(n);}public void writeInt64(long n){values.add(n);}
        public void writeBool(boolean n){values.add(n);}public void writeString(String n){values.add(n);}
        public void writeByteArray(byte[] b){values.add(b.clone());}public void writeByteArray(byte[] b,int o,int c){values.add(Arrays.copyOfRange(b,o,o+c));}
        public void writeBytes(byte[] b){values.add(b.clone());}public void writeBytes(byte[] b,int o,int c){values.add(Arrays.copyOfRange(b,o,o+c));}
        public void writeByte(int b){values.add(b);}public void writeByte(byte b){values.add(b);}
        public void writeFloat(float f){values.add(f);}public void writeDouble(double d){values.add(d);}
        public void writeByteBuffer(NativeByteBuffer b){throw new UnsupportedOperationException();}public void skip(int n){}public int getPosition(){return values.size();}
    }
    static class Step {final Class<?> type;final TLObject response;final TLRPC.TL_error error;Step(Class<?> t,TLObject r,TLRPC.TL_error e){type=t;response=r;error=e;}}
    static class Pending {final TelegramRequestContext.RawCallback callback;final Step step;Pending(TelegramRequestContext.RawCallback c,Step s){callback=c;step=s;}}
    static class Port implements TelegramRequestContext.LocalPort {
        final Deque<Step> script=new ArrayDeque<>();final List<Pending> pending=new ArrayList<>();final List<TLObject> originals=new ArrayList<>();final List<Sink> encoded=new ArrayList<>();final List<Integer> dcs=new ArrayList<>();
        Domain domain=Domain.LOCAL_SIMULATION;boolean async,duplicate,throwAfter,noHandle,failCancel;int calls,cancels,closes;
        public Domain domain(){return domain;}public SessionScope scope(){return NativeLoginHarness.scope(0);}
        void add(Class<?> t,TLObject value){script.add(new Step(t,value,null));}
        void fail(Class<?> t,String e){script.add(new Step(t,null,error(e)));}
        public Cancellation submit(TLObject original,int dc,TelegramRequestContext.RawCallback callback){
            yes(!script.isEmpty());Step s=script.remove();yes(original.getClass()==s.type);calls++;originals.add(original);dcs.add(dc);
            Sink sink=new Sink();original.serializeToStream(sink);encoded.add(sink);
            Pending p=new Pending(callback,s);pending.add(p);if(!async)reply(p);
            if(throwAfter)throw new IllegalStateException(PRIVATE);
            return noHandle?null:()->{cancels++;if(failCancel)throw new IllegalStateException(PRIVATE);};
        }
        void reply(Pending p){p.callback.complete(p.step.response,p.step.error);if(duplicate)p.callback.complete(p.step.response,p.step.error);}
        public void close(){closes++;}
    }
    static class Proof implements TelegramRequestContext.LocalProof {
        boolean fail;int calls;
        public Domain domain(){return Domain.LOCAL_SIMULATION;}
        public TLRPC.TL_inputCheckPasswordSRP create(char[] input,TL_account.Password p){calls++;if(fail)throw new IllegalStateException(PRIVATE);TLRPC.TL_inputCheckPasswordSRP value=new TLRPC.TL_inputCheckPasswordSRP();value.srp_id=p.srp_id;value.A=new byte[]{1,2};value.M1=new byte[]{3,4};return value;}
    }
    static class F {
        final Memory memory=new Memory();final Disk disk=new Disk();final Port port=new Port();final Proof proof=new Proof();
        final TelegramAuthorizationStore store=new TelegramAuthorizationStore(runtime(0),new OperationJournal(memory,scope(0)),disk);
        final TelegramRequestContext context=new TelegramRequestContext(runtime(0),store,port,proof);
        final Time time=new Time();final NativeLoginTransport transport=store.localTransport(runtime(0),context,time);
        final LoginFlowOwner owner=new LoginFlowOwner(runtime(0),transport,store,Runnable::run);
        F(){transport.bindLocalStateSignal(owner::signalLocalAdapterState);}
        void initialize(){yes(owner.initializeLocal(false));yes(owner.snapshot().state==State.READY);}
        void code(){port.add(TLRPC.TL_auth_sendCode.class,sent());initialize();owner.startLocal(data());yes(owner.snapshot().state==State.CODE_REQUIRED);}
        void auth(){port.add(TLRPC.TL_auth_signIn.class,authorized());owner.verifyLocal(data());yes(owner.snapshot().state==State.LOCAL_AUTHORIZED);}
    }
    static Request request(F f,Action action){return new Request(scope(0),action,data(),0,f.store.operation());}
    static Object field(Object o,String name)throws Exception{Field f=o.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(o);}
    static void cleared(F f)throws Exception{for(String key:new String[]{"phone","phoneHash","password","migrationToken","qrToken","first","last"})yes(field(f.context,key)==null);}
    static void rejected(Runnable r){boolean failed=false;try{r.run();}catch(IllegalArgumentException|IllegalStateException expected){yes(!expected.toString().contains(PRIVATE));failed=true;}yes(failed);}
    public static void main(String[] args)throws Exception{
        F f=new F();
        switch(args[0]){
        case "originalSendSignInSerializers":{
            f.code();TLRPC.TL_auth_sendCode sent=(TLRPC.TL_auth_sendCode)f.port.originals.get(0);yes(sent.api_id==0&&sent.api_hash.isEmpty()&&sent.phone_number==null);
            List<Object> a=f.port.encoded.get(0).values;yes(a.get(0).equals(TLRPC.TL_auth_sendCode.constructor)&&a.get(2).equals(0)&&a.get(3).equals(""));
            f.auth();a=f.port.encoded.get(1).values;yes(a.get(0).equals(TLRPC.TL_auth_signIn.constructor)&&a.get(1).equals(1)&&a.get(4).equals(PRIVATE));cleared(f);
            yes(f.owner.commitLocal()&&f.disk.sameOriginal!=null&&f.memory.row.phase==OperationJournal.Phase.COMPLETED);break;
        }
        case "passwordOriginalRequestAndProofWipe":{
            f.code();f.port.fail(TLRPC.TL_auth_signIn.class,"SESSION_PASSWORD_NEEDED");f.owner.verifyLocal(data());f.port.add(TL_account.getPassword.class,password());yes(f.transport.loadPasswordParametersLocal(true));
            f.port.add(TLRPC.TL_auth_checkPassword.class,authorized());yes(f.transport.checkPasswordProofLocal(data(),true));yes(f.proof.calls==1&&((TLRPC.TL_auth_checkPassword)f.port.originals.get(3)).password==null);cleared(f);break;
        }
        case "passwordParametersNotBorrowedFromCallback":{
            f.code();f.port.fail(TLRPC.TL_auth_signIn.class,"SESSION_PASSWORD_NEEDED");f.owner.verifyLocal(data());TL_account.TL_password received=password();received.srp_B=new byte[]{9};f.port.add(TL_account.getPassword.class,received);f.transport.loadPasswordParametersLocal(true);
            received.srp_id=55;received.srp_B[0]=7;TL_account.Password owned=(TL_account.Password)field(f.context,"password");yes(owned.srp_id==1&&owned.srp_B[0]==9);f.owner.cancelLocal();yes(received.srp_B[0]==7);break;
        }
        case "signupOriginalFieldsAndOrigin":{
            f.code();TLRPC.TL_auth_authorizationSignUpRequired signup=new TLRPC.TL_auth_authorizationSignUpRequired();signup.terms_of_service=new TLRPC.TL_help_termsOfService();f.port.add(TLRPC.TL_auth_signIn.class,signup);f.owner.verifyLocal(data());
            f.context.namesLocal("SYNTHETIC_FIRST".toCharArray(),"SYNTHETIC_LAST".toCharArray());f.port.add(TLRPC.TL_auth_signUp.class,authorized());yes(!f.transport.signUpLocal(data(),true,false));yes(f.transport.signUpLocal(data(),true,true));
            yes(f.port.encoded.get(2).values.contains("SYNTHETIC_FIRST"));yes(f.owner.commitLocal());yes(f.disk.source==Action.SIGN_UP);cleared(f);break;
        }
        case "qrOriginalMigrationTokenOwnedCopy":{
            byte[] original=new byte[]{9,8};TLRPC.TL_auth_loginTokenMigrateTo m=new TLRPC.TL_auth_loginTokenMigrateTo();m.dc_id=3;m.token=original;
            f.port.add(TLRPC.TL_auth_exportLoginToken.class,m);f.initialize();f.transport.selectQrLocal(true);f.owner.startLocal(data());
            original[0]=7;f.port.add(TLRPC.TL_auth_importLoginToken.class,qrSuccess(authorized()));yes(f.transport.approveMigrationLocal(true));yes(f.port.dcs.get(1)==3);
            byte[] encoded=(byte[])f.port.encoded.get(1).values.get(1);yes(encoded[0]==9&&((TLRPC.TL_auth_importLoginToken)f.port.originals.get(1)).token==null);cleared(f);break;
        }
        case "qrDisplayExpiryHasNoAutomaticRequest":{
            f.port.add(TLRPC.TL_auth_exportLoginToken.class,qr());f.initialize();f.transport.selectQrLocal(true);f.owner.startLocal(data());byte[] one=f.context.copyQrTokenLocal(59);yes(one!=null);byte first=one[0];one[0]=0;yes(f.context.copyQrTokenLocal(59)[0]==first);yes(f.context.copyQrTokenLocal(60)==null&&field(f.context,"qrToken")==null&&f.port.calls==1);break;
        }
        case "cancelLateReplyAndNoNativeMutation":{
            f.port.async=true;f.port.add(TLRPC.TL_auth_sendCode.class,sent());f.initialize();f.owner.startLocal(data());f.owner.cancelLocal();f.port.reply(f.port.pending.get(0));cleared(f);yes(f.port.cancels==1&&f.disk.commits==0&&f.owner.snapshot().state==State.CANCELLED);break;
        }
        case "duplicateRawReplyDiscarded":{
            f.port.duplicate=true;f.code();f.auth();yes(f.context.discardedReplies()==2&&f.disk.commits==0);break;
        }
        case "callbackThenThrowDoesNotRetainHash":{
            f.port.throwAfter=true;f.port.add(TLRPC.TL_auth_sendCode.class,sent());f.initialize();f.owner.startLocal(data());cleared(f);yes(f.context.adapterFailures()==1&&f.disk.commits==0);break;
        }
        case "missingHandleDoesNotAdvance":{
            f.port.noHandle=true;f.port.add(TLRPC.TL_auth_sendCode.class,sent());f.initialize();f.owner.startLocal(data());cleared(f);yes(f.owner.snapshot().state!=State.CODE_REQUIRED&&f.disk.commits==0);break;
        }
        case "accountAndLeaseSeparation":{
            f.initialize();Request foreign=new Request(scope(1),Action.SEND_CODE,data(),0,f.store.operation());rejected(()->f.context.submit(foreign,r->{}));foreign.close();
            Request unowned=new Request(scope(0),Action.SEND_CODE,data(),0);rejected(()->f.context.submit(unowned,r->{}));unowned.close();
            Request wrongDc=new Request(scope(0),Action.SEND_CODE,data(),7,f.store.operation());rejected(()->f.context.submit(wrongDc,r->{}));wrongDc.close();yes(f.port.calls==0);break;
        }
        case "reentryRejectedWhileLocalRequestPending":{
            f.port.async=true;f.port.add(TLRPC.TL_auth_sendCode.class,sent());f.initialize();f.owner.startLocal(data());Request r=request(f,Action.GET_PASSWORD);rejected(()->f.context.submit(r,x->{}));r.close();yes(f.port.calls==1);f.owner.cancelLocal();cleared(f);break;
        }
        case "oldOperationCannotAffectNewContext":{
            f.code();f.port.async=true;f.port.add(TLRPC.TL_auth_signIn.class,authorized());f.owner.verifyLocal(data());Pending old=f.port.pending.get(1);f.owner.cancelLocal();
            F next=new F();next.code();f.port.reply(old);yes(next.owner.snapshot().state==State.CODE_REQUIRED&&next.disk.commits==0&&f.disk.commits==0);next.owner.close();break;
        }
        case "domainChangeRejectedBeforePort":{
            f.initialize();f.port.domain=Domain.TELEGRAM;Request r=request(f,Action.SEND_CODE);rejected(()->f.context.submit(r,x->{}));r.close();yes(f.port.calls==0);break;
        }
        case "invalidCodeRetryPreservesContext":{
            f.code();f.port.fail(TLRPC.TL_auth_signIn.class,"PHONE_CODE_INVALID");f.owner.verifyLocal(data());yes(field(f.context,"phoneHash")!=null);f.port.add(TLRPC.TL_auth_signIn.class,authorized());yes(f.transport.retryLocal(data(),true));yes(f.owner.snapshot().state==State.LOCAL_AUTHORIZED);break;
        }
        case "sendCodeFloodWaitExplicitRetry":{
            f.port.fail(TLRPC.TL_auth_sendCode.class,"FLOOD_WAIT_2");f.initialize();f.owner.startLocal(data());f.time.now+=2000;f.port.add(TLRPC.TL_auth_sendCode.class,sent());yes(f.transport.retryLocal(data(),true));yes(f.owner.snapshot().state==State.CODE_REQUIRED&&f.port.calls==2);break;
        }
        case "srpRefreshRequiresNewParameters":{
            f.code();f.port.fail(TLRPC.TL_auth_signIn.class,"SESSION_PASSWORD_NEEDED");f.owner.verifyLocal(data());f.port.add(TL_account.getPassword.class,password());f.transport.loadPasswordParametersLocal(true);
            f.port.fail(TLRPC.TL_auth_checkPassword.class,"SRP_ID_INVALID");f.transport.checkPasswordProofLocal(data(),true);yes(field(f.context,"password")==null&&f.port.calls==4);yes(!f.transport.checkPasswordProofLocal(data(),true));break;
        }
        case "terminalFailureAndUnsupportedRouteClear":{
            f.code();f.port.fail(TLRPC.TL_auth_signIn.class,"PHONE_CODE_EXPIRED");f.owner.verifyLocal(data());cleared(f);
            F g=new F();TLRPC.TL_auth_sentCode s=sent();s.type=new TLRPC.TL_auth_sentCodeTypeFirebaseSms();g.port.add(TLRPC.TL_auth_sendCode.class,s);g.initialize();g.owner.startLocal(data());cleared(g);yes(g.port.calls==1);break;
        }
        case "proofFailureSanitizedAndNoRequest":{
            f.code();f.port.fail(TLRPC.TL_auth_signIn.class,"SESSION_PASSWORD_NEEDED");f.owner.verifyLocal(data());f.port.add(TL_account.getPassword.class,password());f.transport.loadPasswordParametersLocal(true);f.proof.fail=true;f.transport.checkPasswordProofLocal(data(),true);cleared(f);yes(f.port.calls==3);break;
        }
        case "originalSrpWrapperFailsWithoutCryptoClaim":{
            OriginalSrpLocalProof proof=new OriginalSrpLocalProof();rejected(()->proof.create(new char[0],password()));rejected(()->proof.create(data(),password()));
            byte[] padded=SRPHelper.getBigIntegerBytes(BigInteger.ONE);yes(padded.length==256&&padded[255]==1);break;
        }
        case "recreationReattachesWithoutRequests":{
            Looper.main=true;f.code();LoginNativeBinding binding=new LoginNativeBinding(scope(0),f.owner,f.transport,Runnable::run);int[] old={0},fresh={0};
            binding.attach(new LoginActivity(0),state->{old[0]++;return false;});binding.detach();binding.attach(new LoginActivity(0),state->{fresh[0]++;return false;});Handler.flush();yes(old[0]==0&&fresh[0]==1&&f.port.calls==1);binding.detach();break;
        }
        case "patchBindingRefusesParameterizedPage":{
            Looper.main=true;f.initialize();LoginNativeBinding binding=new LoginNativeBinding(scope(0),f.owner,f.transport,Runnable::run);
            PreparedFragmentFixture host=new PreparedFragmentFixture();host.bindPreparedLocalLogin(binding);host.markCreated();Handler.flush();yes(host.preparedLocalLoginPlan()!=null);
            f.port.add(TLRPC.TL_auth_sendCode.class,sent());yes(host.preparedLocalLoginStart(data()));Handler.flush();yes(!host.preparedLocalLoginPlan().mayEnterOriginalPage()&&host.pageCalls==0);host.detachPreparedLocalLogin();yes(!host.preparedLocalLoginVerify(data()));break;
        }
        case "pagePlanBlocksOriginalSideEffects":{
            f.code();NativePagePlan plan=NativePagePlan.from(f.transport.snapshot());yes(!plan.mayEnterOriginalPage()&&plan.page.originalViewNumber>=1);break;
        }
        case "cancellationErrorsDoNotLeak":{
            f.port.async=true;f.port.failCancel=true;f.port.add(TLRPC.TL_auth_sendCode.class,sent());f.initialize();f.owner.startLocal(data());f.owner.cancelLocal();cleared(f);yes(f.context.adapterFailures()==1);break;
        }
        case "emptySessionNoImplicitRestore":{
            f.initialize();yes(f.port.calls==0&&f.disk.commits==0&&field(f.context,"phone")==null);f.owner.close();yes(f.port.closes==1);break;
        }
        case "processDeathOnlyRestartMarker":{
            Looper.main=true;f.code();LoginNativeBinding binding=new LoginNativeBinding(scope(0),f.owner,f.transport,Runnable::run);Bundle out=new Bundle();binding.saveRestartMarker(out);F next=new F();LoginNativeBinding restored=new LoginNativeBinding(scope(0),next.owner,next.transport,Runnable::run);yes(restored.restoreMarker(out));yes(next.port.calls==0&&next.owner.snapshot().state==State.RESTART_REQUIRED);break;
        }
        default:throw new IllegalArgumentException("UNKNOWN_LOCAL_CASE");
        }
        f.owner.close();System.out.println("HOST_LOCAL_CONTEXT_ONLY:"+args[0]);
    }
}
