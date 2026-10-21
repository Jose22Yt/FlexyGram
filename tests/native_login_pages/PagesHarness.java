package io.github.jose22yt.flexygram.login;
import java.util.*;import java.util.concurrent.*;import java.lang.reflect.*;
import org.telegram.tgnet.*;import org.telegram.tgnet.tl.TL_account;
import io.github.jose22yt.flexygram.session.*;import io.github.jose22yt.flexygram.session.android.*;
import io.github.jose22yt.flexygram.session.AuthenticationController.State;
import io.github.jose22yt.flexygram.session.RequestCoordinator.*;
import io.github.jose22yt.flexygram.login.local.*;import io.github.jose22yt.flexygram.login.local.EphemeralPages.*;
import static io.github.jose22yt.flexygram.login.NativeLoginHarness.*;
public class PagesHarness {
 static final char[] DATA="000000".toCharArray();static final String CANARY="SYNTHETIC_LOCAL_UI_SECRET_77121";
 static void yes(boolean b){if(!b)throw new AssertionError("LOCAL_PAGES_CONTRACT");}
 static void rejected(Runnable r){boolean bad=false;try{r.run();}catch(IllegalArgumentException|IllegalStateException e){bad=true;yes(!e.toString().contains(CANARY));}yes(bad);}
 static class Worker implements Executor {final Deque<Runnable> queue=new ArrayDeque<>();boolean fail;public void execute(Runnable r){if(fail)throw new RejectedExecutionException(CANARY);queue.add(r);}void flush(){int count=0;while(!queue.isEmpty()){yes(++count<1000);queue.remove().run();}}}
 static class Answer {final TLObject data;final TLRPC.TL_error error;Answer(TLObject d,TLRPC.TL_error e){data=d;error=e;}}
 static class Port implements TelegramRequestContext.LocalPort {
   final Deque<Answer> script=new ArrayDeque<>();final List<TelegramRequestContext.RawCallback> callbacks=new ArrayList<>();final List<Answer> answers=new ArrayList<>();final List<Class<?>> classes=new ArrayList<>();boolean async;int cancels;
   void add(TLObject value){script.add(new Answer(value,null));}void fail(String text){script.add(new Answer(null,error(text)));}
   public Domain domain(){return Domain.LOCAL_SIMULATION;}public SessionScope scope(){return NativeLoginHarness.scope(0);}
   public Cancellation submit(TLObject original,int dc,TelegramRequestContext.RawCallback callback){yes(!script.isEmpty());classes.add(original.getClass());Answer a=script.remove();callbacks.add(callback);answers.add(a);if(!async)callback.complete(a.data,a.error);return ()->cancels++;}
   void reply(int n){Answer a=answers.get(n);callbacks.get(n).complete(a.data,a.error);}public void close(){}
 }
 static class F {
   final Worker worker=new Worker();final Memory memory=new Memory();final Disk disk=new Disk();final Port port=new Port();
   final TelegramAuthorizationStore store=new TelegramAuthorizationStore(runtime(0),new OperationJournal(memory,scope(0)),disk);
   final TelegramRequestContext context=new TelegramRequestContext(runtime(0),store,port,new TelegramRequestContext.LocalProof(){public Domain domain(){return Domain.LOCAL_SIMULATION;}public TLRPC.TL_inputCheckPasswordSRP create(char[] s,TL_account.Password p){TLRPC.TL_inputCheckPasswordSRP r=new TLRPC.TL_inputCheckPasswordSRP();r.srp_id=p.srp_id;r.A=new byte[]{1};r.M1=new byte[]{2};return r;}});
   final NativeLoginTransport transport=store.localTransport(runtime(0),context,new Time());final LoginFlowOwner owner=new LoginFlowOwner(runtime(0),transport,store,worker);
   final LocalLoginSession local=new LocalLoginSession(runtime(0),owner,transport,context,worker);final List<Parameters> seen=new ArrayList<>();EphemeralPages.View view;
   F(){transport.bindLocalStateSignal(owner::signalLocalAdapterState);owner.initializeLocal(false);worker.flush();view=local.attach(0,Runnable::run,seen::add);}
   void code(){TLRPC.TL_auth_sentCode code=sent();code.type.length=6;port.add(code);yes(local.phone(view,DATA));worker.flush();yes(local.parameters(view).page==2);}
   void auth(){port.add(authorized());yes(local.code(view,DATA));worker.flush();yes(owner.snapshot().state==State.LOCAL_AUTHORIZED);}
 }
 static Object field(Object o,String n)throws Exception{Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);return f.get(o);}
 static void wiped(char[] a){for(char c:a)yes(c==0);}
 public static void main(String[] args)throws Exception {
  F f=new F();
  switch(args[0]){
  case "nativePhoneSmsGuardFlow":{
   TLRPC.TL_auth_sentCode code=sent();code.type.length=6;f.port.add(code);OriginalGuardHost host=new OriginalGuardHost(f.local,f.view);host.new PhoneView().onNextPressed(null);f.worker.flush();yes(f.local.parameters(f.view).page==2&&host.legacy==0);
   host.new LoginActivitySmsView().setParams(null,false);f.port.add(authorized());host.new LoginActivitySmsView().onNextPressed(null);f.worker.flush();yes(host.apply==1&&host.legacy==0&&f.owner.snapshot().state==State.LOCAL_AUTHORIZED&&f.disk.commits==0);break;
  }
  case "nativePasswordGuardFlow":{
   f.code();f.port.fail("SESSION_PASSWORD_NEEDED");f.local.code(f.view,DATA);f.worker.flush();yes(f.local.parameters(f.view).status==Status.PARAMETERS_PENDING);
   OriginalGuardHost host=new OriginalGuardHost(f.local,f.view);f.port.add(password());host.new LoginActivityPasswordView().onShow();f.worker.flush();yes(f.local.parameters(f.view).passwordReady);f.port.add(authorized());host.new LoginActivityPasswordView().onNextPressed(null);f.worker.flush();yes(host.legacy==0&&f.owner.snapshot().state==State.LOCAL_AUTHORIZED);break;
  }
  case "nativeRegisterGuardFlow":{
   f.code();f.port.add(new TLRPC.TL_auth_authorizationSignUpRequired());f.local.code(f.view,DATA);f.worker.flush();yes(f.local.parameters(f.view).page==5);OriginalGuardHost host=new OriginalGuardHost(f.local,f.view);f.port.add(authorized());host.new LoginActivityRegisterView().onNextPressed(null);f.worker.flush();yes(host.legacy==0&&f.owner.snapshot().state==State.LOCAL_AUTHORIZED);break;
  }
  case "consecutivePhoneTapsOneLocalRequest":{
   TLRPC.TL_auth_sentCode c=sent();c.type.length=6;f.port.add(c);yes(f.local.phone(f.view,DATA));for(int i=0;i<25;i++)yes(!f.local.phone(f.view,DATA));f.worker.flush();yes(f.port.classes.size()==1);break;
  }
  case "consecutiveCodeTapsOneLocalRequest":{
   f.code();f.port.add(authorized());yes(f.local.code(f.view,DATA));for(int i=0;i<25;i++)yes(!f.local.code(f.view,DATA));f.worker.flush();yes(f.port.classes.size()==2);break;
  }
  case "queuedSecretWipedOnViewDetach":{
   yes(f.local.phone(f.view,CANARY.toCharArray()));Set<?> pending=(Set<?>)field(f.local,"pending");Object task=pending.iterator().next();char[][] inputs=(char[][])field(task,"inputs");f.local.detach(f.view);wiped(inputs[0]);f.worker.flush();yes(f.port.classes.isEmpty());break;
  }
  case "cancelBeforeWorkerDispatch":{
   yes(f.local.phone(f.view,DATA));yes(f.local.cancel(f.view));f.worker.flush();yes(f.port.classes.isEmpty()&&f.owner.snapshot().state==State.CANCELLED);break;
  }
  case "lateResponseAfterCancelNoCallback":{
   f.port.async=true;TLRPC.TL_auth_sentCode c=sent();c.type.length=6;f.port.add(c);f.local.phone(f.view,DATA);f.worker.flush();f.local.cancel(f.view);f.worker.flush();int before=f.seen.size();f.port.reply(0);yes(f.seen.size()==before&&f.port.cancels==1&&f.disk.commits==0);break;
  }
  case "viewRecreationNoReplayAndOldRendererDetached":{
   f.port.async=true;TLRPC.TL_auth_sentCode c=sent();c.type.length=6;f.port.add(c);f.local.phone(f.view,DATA);f.worker.flush();int before=f.seen.size();EphemeralPages.View old=f.view;f.local.detach(old);List<Parameters> next=new ArrayList<>();f.view=f.local.attach(0,Runnable::run,next::add);f.port.reply(0);yes(f.seen.size()==before&&next.get(next.size()-1).page==2&&f.port.classes.size()==1&&!f.local.code(old,DATA));break;
  }
  case "accountChangeInvalidatesOldQueuedView":{
   f.local.phone(f.view,DATA);rejected(()->f.local.attach(1,Runnable::run,p->{}));f.worker.flush();yes(f.port.classes.isEmpty()&&!f.local.valid(f.view,0));break;
  }
  case "unknownLengthNotEnabled":{
   f.port.add(sent());f.local.phone(f.view,DATA);f.worker.flush();yes(f.local.parameters(f.view).status==Status.UNSUPPORTED&&!f.local.code(f.view,DATA));break;
  }
  case "appDeliveryUsesOriginalMessagePage":{
   TLRPC.TL_auth_sentCode c=sent();c.type=new TLRPC.TL_auth_sentCodeTypeApp();c.type.length=6;f.port.add(c);f.local.phone(f.view,DATA);f.worker.flush();yes(f.local.parameters(f.view).page==1&&f.local.parameters(f.view).codeLength==6);break;
  }
  case "invalidCodeLengthFailsClosed":{
   TLRPC.TL_auth_sentCode c=sent();c.type.length=13;f.port.add(c);f.local.phone(f.view,DATA);f.worker.flush();yes(f.owner.snapshot().state==State.FAILED&&!f.local.code(f.view,DATA));break;
  }
  case "unavailablePasswordParametersNoNativeFallback":{
   f.code();f.port.fail("SESSION_PASSWORD_NEEDED");f.local.code(f.view,DATA);f.worker.flush();TL_account.TL_password bad=password();bad.current_algo=new TLRPC.TL_passwordKdfAlgoUnknown();f.port.add(bad);f.local.loadPassword(f.view);f.worker.flush();OriginalGuardHost host=new OriginalGuardHost(f.local,f.view);host.new LoginActivityPasswordView().onNextPressed(null);f.worker.flush();yes(host.legacy==0&&f.owner.snapshot().state==State.FAILED&&f.port.classes.size()==3);break;
  }
  case "callDeliveryNotEnabled":{
   TLRPC.TL_auth_sentCode c=sent();c.type=new TLRPC.TL_auth_sentCodeTypeCall();c.type.length=6;f.port.add(c);f.local.phone(f.view,DATA);f.worker.flush();yes(f.local.parameters(f.view).page==-1&&f.local.parameters(f.view).status==Status.UNSUPPORTED);break;
  }
  case "qrLifecycleAlwaysBlocked":{
   f.transport.selectQrLocal(true);f.port.add(qr());f.local.phone(f.view,DATA);f.worker.flush();OriginalGuardHost host=new OriginalGuardHost(f.local,f.view);host.new LoginActivityQrView().onShow();host.new LoginActivityQrView().exportLoginToken(true);yes(host.legacy==0&&f.port.classes.size()==1&&f.local.parameters(f.view).page==-1&&!EphemeralPages.allowedPage(19));break;
  }
  case "nativeBackCancelsOnlyLocalRequest":{
   f.code();OriginalGuardHost host=new OriginalGuardHost(f.local,f.view);yes(host.new LoginActivitySmsView().onBackPressed(true));f.worker.flush();yes(host.legacy==0&&f.port.classes.size()==1&&f.owner.snapshot().state==State.CANCELLED);break;
  }
  case "uncertainStorageBlocksFurtherActions":{
   f.code();f.auth();f.disk.omitReceipts=true;yes(f.local.commit(f.view));f.worker.flush();System.err.println("STORAGE_RESULT:"+f.owner.snapshot().state+":"+f.memory.row.phase+":"+f.disk.commits+":"+f.local.parameters(f.view).status);yes(f.owner.snapshot().state==State.STORAGE_UNCERTAIN&&f.local.parameters(f.view).status==Status.STORAGE_REVIEW&&!f.local.phone(f.view,DATA)&&f.disk.commits==1);break;
  }
  case "storageFailureDoesNotDeleteOrRetry":{
   f.code();f.auth();f.disk.failAfter=true;yes(f.local.commit(f.view));f.worker.flush();System.err.println("STORAGE_RESULT:"+f.owner.snapshot().state+":"+f.memory.row.phase+":"+f.disk.commits+":"+f.local.parameters(f.view).status);yes(f.memory.row.phase==OperationJournal.Phase.UNCERTAIN&&f.disk.commits==1&&!f.local.commit(f.view));break;
  }
  case "requiredTermsNotSilentlyAccepted":{
   f.code();TLRPC.TL_auth_authorizationSignUpRequired s=new TLRPC.TL_auth_authorizationSignUpRequired();s.terms_of_service=new TLRPC.TL_help_termsOfService();f.port.add(s);f.local.code(f.view,DATA);f.worker.flush();yes(f.local.parameters(f.view).status==Status.UNSUPPORTED&&!f.local.register(f.view,DATA,DATA));break;
  }
  case "workerFailureNoFallback":{
   f.worker.fail=true;yes(!f.local.phone(f.view,DATA));yes(f.port.classes.isEmpty());break;
  }
  case "transitionTicketsRejectOldAndDestroyedCallbacks":{
   LocalTransitionFence t=new LocalTransitionFence();long old=t.next(),next=t.next();yes(!t.current(old)&&t.current(next));t.destroy();yes(!t.current(next));rejected(t::next);break;
  }
  case "hostThemeRebindPreservesParameters":{
   f.code();int count=f.port.classes.size();f.local.detach(f.view);f.view=f.local.attach(0,Runnable::run,p->{});yes(f.local.parameters(f.view).codeLength==6&&f.port.classes.size()==count);break;
  }
  case "channelMetadataContainsNoSecretsOrSerialization":{
   f.code();for(Field field:Parameters.class.getDeclaredFields())yes(field.getType().isPrimitive()||field.getType().isEnum());yes(!java.io.Serializable.class.isAssignableFrom(Parameters.class));yes(!f.local.parameters(f.view).toString().contains(CANARY));break;
  }
  case "boundedInputMissingDependencyFailsClosed":{
   yes(NativeUiInput.bounded((CharSequence)null).length==0);yes(NativeUiInput.bounded(new String(new char[257])).length==0);char[] p=NativeUiInput.copy("SYN","THETIC");yes(p.length==9);NativeUiInput.wipe(p);wiped(p);break;
  }
  case "inactiveVariantGuardPreservesLegacyPath":{
   OriginalGuardHost host=new OriginalGuardHost(f.local,f.view);host.isolated=false;host.new PhoneView().onNextPressed(null);yes(host.legacy==1&&f.port.classes.isEmpty());break;
  }
  default:throw new IllegalArgumentException("UNKNOWN_HOST_CASE");
  }
  f.local.close();System.out.println("HOST_NATIVE_GUARDS_LOCAL_ONLY:"+args[0]);
 }
}
