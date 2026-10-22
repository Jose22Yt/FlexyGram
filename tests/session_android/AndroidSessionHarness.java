package io.github.jose22yt.flexygram.session.android;
import java.io.*;
import java.nio.channels.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import java.lang.reflect.*;
import android.content.Context;
import android.os.*;
import org.telegram.messenger.*;
import org.telegram.ui.LoginActivity;
import io.github.jose22yt.flexygram.session.*;
import io.github.jose22yt.flexygram.session.RequestCoordinator.*;
import io.github.jose22yt.flexygram.session.AuthenticationController.*;
import io.github.jose22yt.flexygram.session.android.OperationJournal.*;
import io.github.jose22yt.flexygram.session.android.OperationJournal.Record;

/** HOST: Android/controller doubles; real new Java, real AccountInstance and real new JNI on Linux. */
public final class AndroidSessionHarness {
    static final String CANARY="SYNTHETIC_PRIVATE_ADAPTER_401";
    static char[] material(){return CANARY.toCharArray();}
    static SessionScope scope(int n){return SessionScope.of("realAlpha","io.github.jose22yt.flexygram.realalpha",n);}
    static String statement(){return "FLEXYGRAM_POLICY:"+BuildConfig.FLEXYGRAM_POLICY_SCOPE+":auth=0:transport=0:push=0:translation=0:plugins=0:restore=0";}
    static ReadOnlyAttestation attestation(int n){return ReadOnlyAttestation.verify(scope(n),scope(n).variant.applicationId,BuildConfig.FLEXYGRAM_POLICY_SCOPE,true,new boolean[6],0,new char[0],statement(),new long[]{1,1,0,n,1,0},1,0);}
    static void need(boolean b){if(!b)throw new AssertionError("INTEGRATION_CONTRACT_FAILED");}
    static void denied(Runnable r){try{r.run();}catch(IllegalStateException|IllegalArgumentException e){need(e.getCause()==null&&!e.toString().contains(CANARY));return;}throw new AssertionError("EXPECTED_DENIAL");}
    static void zero(char[] c){for(char v:c)need(v==0);}
    static class Memory implements Backend {
        Record row=Record.empty(scope(0));int writes,failAt;boolean failRead,after;Runnable beforeWriting=()->{};
        public synchronized Record read(SessionScope s){if(failRead)throw new IllegalStateException(CANARY);return row;}
        public synchronized boolean compareAndSet(Record old,Record next){writes++;if(writes==2)beforeWriting.run();if(failAt==writes&&!after)throw new IllegalStateException(CANARY);if(!row.equals(old))return false;row=next;if(failAt==writes&&after)throw new IllegalStateException(CANARY);return true;}
    }
    static class Probe implements AccountProbe {
        Evidence evidence=Evidence.EMPTY;SessionScope sc=scope(0);
        public Snapshot inspect(){return new Snapshot(sc,evidence,true);}
    }
    static class Sink implements JournaledLocalSessionStore.LocalSink {
        int writes;char[] borrowed;boolean fail;Runnable during=()->{};JournaledLocalSessionStore.Outcome outcome=JournaledLocalSessionStore.Outcome.COMPLETED;
        public JournaledLocalSessionStore.Outcome commitSynthetic(SessionScope s,char[] m){writes++;borrowed=m;during.run();if(fail)throw new IllegalStateException(CANARY);return outcome;}
    }
    static class Transport implements TransportPort {
        int starts,requests,cancels,closes;boolean async;Listener listener;
        public Domain domain(){return Domain.LOCAL_SIMULATION;}public SessionScope scope(){return AndroidSessionHarness.scope(0);}
        public void initialize(){starts++;}public void close(){closes++;}
        public Cancellation submit(Attempt a,Listener l){requests++;listener=l;if(!async)l.complete(a.operation==Operation.REQUEST_CODE?Reply.codeSent(material()):Reply.localSession(material()));return ()->cancels++;}
    }
    static class Queue implements Executor {final List<Runnable> tasks=new ArrayList<>();public void execute(Runnable r){tasks.add(r);}void flush(){while(!tasks.isEmpty())tasks.remove(0).run();}}
    static JournaledLocalSessionStore store(Memory m,Probe p,Sink sink){return new JournaledLocalSessionStore(scope(0),new OperationJournal(m,scope(0)),p,sink);}
    static void authorize(AuthenticationController c){need(c.initialize());need(c.start(material()));need(c.submitCode(material()));need(c.snapshot().state==State.LOCAL_AUTHORIZED);}
    public static void main(String[] args)throws Exception {
        String test=args[0];Context context=new Context(new File(args[1]));ApplicationLoader.applicationContext=context;
        Memory memory=new Memory();Probe probe=new Probe();Sink sink=new Sink();OperationJournal journal=new OperationJournal(memory,scope(0));
        JournaledLocalSessionStore store=store(memory,probe,sink);Transport transport=new Transport();
        AuthenticationController controller=new AuthenticationController(attestation(0).runtime,transport,store);
        switch(test){
        case "recordValidation":denied(()->new Record(scope(0),-1,"",Phase.NONE));denied(()->new Record(scope(0),1,CANARY,Phase.STARTED));denied(()->new Record(scope(0),0,"",Phase.WRITING));break;
        case "journalBeginAndRecovery":{need(journal.inspect().recovery()==Recovery.EMPTY);Record first=journal.begin(false);need(first.phase==Phase.STARTED&&first.recovery()==Recovery.ACTIVE_OR_INTERRUPTED);denied(()->journal.begin(false));break;}
        case "journalTransitions":journal.begin(false);journal.move(Phase.WRITING);need(journal.inspect().recovery()==Recovery.WRITE_UNCERTAIN);journal.move(Phase.COMPLETED);need(journal.inspect().recovery()==Recovery.LOCAL_RECEIPT);denied(()->journal.move(Phase.STARTED));break;
        case "journalNoAutoResume":journal.begin(false);denied(()->new OperationJournal(memory,scope(0)).begin(true));need(memory.writes==1);break;
        case "journalUncertainBlocksRetry":journal.begin(false);journal.move(Phase.WRITING);journal.move(Phase.UNCERTAIN);denied(()->new OperationJournal(memory,scope(0)).begin(true));break;
        case "journalRetryExplicitOnly":{String old=journal.begin(false).operation;journal.move(Phase.FAILED);denied(()->new OperationJournal(memory,scope(0)).begin(false));Record fresh=new OperationJournal(memory,scope(0)).begin(true);need(!old.equals(fresh.operation)&&fresh.revision==3);break;}
        case "journalRaceOwnership":journal.begin(false);denied(()->new OperationJournal(memory,scope(0)).begin(false));need(memory.writes==1);break;
        case "journalWrongScope":denied(()->new OperationJournal(memory,scope(1)).inspect());break;
        case "journalReadFailureSafe":memory.failRead=true;denied(journal::inspect);break;
        case "journalWriteThenThrow":memory.failAt=1;memory.after=true;denied(()->journal.begin(false));need(memory.row.phase==Phase.STARTED);denied(()->journal.move(Phase.WRITING));denied(()->new OperationJournal(memory,scope(0)).begin(true));break;
        case "storeExistingPreserved":probe.evidence=AccountProbe.Evidence.EXISTING_ACCOUNT;denied(()->store.beginExplicit(false));need(memory.writes==0&&sink.writes==0);break;
        case "storeNativeFilesRequireReview":probe.evidence=AccountProbe.Evidence.NATIVE_FILES_PRESENT;denied(()->store.beginExplicit(false));need(memory.writes==0);break;
        case "storeUnknownBlocked":probe.evidence=AccountProbe.Evidence.UNAVAILABLE;denied(()->store.beginExplicit(false));break;
        case "storeForeignAccountBlocked":probe.sc=scope(1);denied(()->store.beginExplicit(false));need(memory.writes==0);break;
        case "storeCompletedLocalReceipt":store.beginExplicit(false);authorize(controller);need(controller.commitLocal());need(memory.row.phase==Phase.COMPLETED&&controller.snapshot().state==State.LOCAL_COMPLETE&&sink.writes==1);zero(sink.borrowed);break;
        case "storeKnownFailure":sink.outcome=JournaledLocalSessionStore.Outcome.FAILED_WITHOUT_WRITE;store.beginExplicit(false);authorize(controller);need(!controller.commitLocal());need(memory.row.phase==Phase.FAILED&&sink.writes==1);zero(sink.borrowed);break;
        case "storeUnknownWrite":sink.outcome=JournaledLocalSessionStore.Outcome.UNCERTAIN;store.beginExplicit(false);authorize(controller);need(!controller.commitLocal());need(memory.row.phase==Phase.UNCERTAIN&&controller.snapshot().state==State.STORAGE_UNCERTAIN);need(!controller.commitLocal());zero(sink.borrowed);break;
        case "storeSinkException":sink.fail=true;store.beginExplicit(false);authorize(controller);need(!controller.commitLocal());need(memory.row.phase==Phase.UNCERTAIN&&sink.writes==1);zero(sink.borrowed);break;
        case "storeCompletionEvidenceFailure":memory.failAt=3;store.beginExplicit(false);authorize(controller);need(!controller.commitLocal());need(memory.row.phase==Phase.WRITING&&sink.writes==1&&controller.snapshot().state==State.STORAGE_UNCERTAIN);zero(sink.borrowed);denied(()->new OperationJournal(memory,scope(0)).begin(true));break;
        case "storeBeginWriteEvidenceFailure":memory.failAt=2;memory.after=true;store.beginExplicit(false);authorize(controller);need(!controller.commitLocal());need(memory.row.phase==Phase.WRITING&&sink.writes==0);break;
        case "storeAccountAppearsBeforeCommit":store.beginExplicit(false);authorize(controller);probe.evidence=AccountProbe.Evidence.EXISTING_ACCOUNT;need(!controller.commitLocal());need(sink.writes==0&&memory.row.phase==Phase.STARTED);break;
        case "storeCloseReentrant":store.beginExplicit(false);authorize(controller);sink.during=store::close;need(controller.commitLocal());need(memory.row.phase==Phase.COMPLETED&&sink.writes==1);store.close();need(memory.row.phase==Phase.COMPLETED);break;
        case "storeCloseDuringJournalWrite":store.beginExplicit(false);authorize(controller);memory.beforeWriting=store::close;need(controller.commitLocal());need(memory.row.phase==Phase.COMPLETED&&sink.writes==1);zero(sink.borrowed);break;
        case "storeCancelNoSessionMutation":store.beginExplicit(false);store.close();store.close();need(memory.row.phase==Phase.CANCELLED&&sink.writes==0);break;
        case "storeWrongScope":store.beginExplicit(false);denied(()->store.inspect(scope(1)));need(sink.writes==0);break;
        case "deniedNativeTransport":{DeniedTelegramTransport port=new DeniedTelegramTransport(scope(0));denied(port::initialize);denied(()->port.submit(null,null));RequestCoordinator c=new RequestCoordinator(attestation(0).runtime,port);need(!c.initialize());port.close();break;}
        case "ownerLocalFlow":{LoginFlowOwner o=new LoginFlowOwner(attestation(0).runtime,transport,store,Runnable::run);need(o.initializeLocal(false));o.startLocal(material());need(o.snapshot().state==State.CODE_REQUIRED);o.verifyLocal(material());o.commitLocal();need(o.snapshot().state==State.LOCAL_COMPLETE&&memory.row.phase==Phase.COMPLETED);o.close();need(o.snapshot().state==State.CLOSED&&sink.writes==1);break;}
        case "ownerRejectsTelegram":denied(()->new LoginFlowOwner(attestation(0).runtime,new DeniedTelegramTransport(scope(0)),store,Runnable::run));break;
        case "ownerCancelDropsLateCallback":{transport.async=true;LoginFlowOwner o=new LoginFlowOwner(attestation(0).runtime,transport,store,Runnable::run);o.initializeLocal(false);o.startLocal(material());o.cancelLocal();transport.listener.complete(Reply.codeSent(material()));need(o.snapshot().state==State.CANCELLED&&memory.row.phase==Phase.CANCELLED&&sink.writes==0&&transport.cancels==1);break;}
        case "ownerQueuedInputsWipedOnClose":{Queue worker=new Queue();LoginFlowOwner o=new LoginFlowOwner(attestation(0).runtime,transport,store,worker);o.initializeLocal(false);o.startLocal(material());Field tasks=LoginFlowOwner.class.getDeclaredField("tasks");tasks.setAccessible(true);Object task=((ArrayDeque<?>)tasks.get(o)).peekLast();Field input=task.getClass().getDeclaredField("input");input.setAccessible(true);char[] borrowed=(char[])input.get(task);o.close();zero(borrowed);worker.flush();need(memory.writes==0&&transport.requests==0&&o.snapshot().state==State.CLOSED);break;}
        case "ownerWorkerRejectsSafely":{LoginFlowOwner o=new LoginFlowOwner(attestation(0).runtime,transport,store,r->{throw new RejectedExecutionException(CANARY);});need(!o.initializeLocal(false));need(o.failure()==LoginFlowOwner.Failure.WORKER_UNAVAILABLE&&transport.requests==0&&memory.writes==0);break;}
        case "ownerExplicitRetry":{LoginFlowOwner old=new LoginFlowOwner(attestation(0).runtime,transport,store,Runnable::run);old.initializeLocal(false);old.cancelLocal();LoginFlowOwner fresh=new LoginFlowOwner(attestation(0).runtime,new Transport(),store(memory,probe,sink),Runnable::run);need(fresh.initializeLocal(true));need(fresh.snapshot().state==State.READY&&memory.row.phase==Phase.STARTED);break;}
        case "ownerRecreationDetachesView":{LoginFlowOwner o=new LoginFlowOwner(attestation(0).runtime,transport,store,Runnable::run);Queue main=new Queue();int[] old={0},fresh={0};AuthUiRelay.Binding binding=o.attachView(main,s->old[0]++);o.initializeLocal(false);o.startLocal(material());binding.close();o.attachView(main,s->fresh[0]++);main.flush();need(old[0]==0&&fresh[0]==1&&transport.requests==1&&memory.writes==1);break;}
        case "androidJournalRoundtrip":{OperationJournal j=new OperationJournal(new AndroidJournalBackend(context,attestation(0).runtime),scope(0));j.begin(false);j.move(Phase.WRITING);j.move(Phase.COMPLETED);OperationJournal reopened=new OperationJournal(new AndroidJournalBackend(context,attestation(0).runtime),scope(0));need(reopened.inspect().phase==Phase.COMPLETED);denied(()->reopened.begin(true));break;}
        case "androidJournalNoCredentials":{OperationJournal j=new OperationJournal(new AndroidJournalBackend(context,attestation(0).runtime),scope(0));j.begin(false);File f=new File(context.getNoBackupFilesDir(),"flexygram-local-auth-operations-v1/account-0.metadata");byte[] bytes=Files.readAllBytes(f.toPath());need(bytes.length<=512&&!new String(bytes,"UTF-8").contains(CANARY));break;}
        case "androidJournalRejectsMainThread":Looper.main=true;denied(()->new AndroidJournalBackend(context,attestation(0).runtime));break;
        case "androidJournalRejectsCorruption":{AndroidJournalBackend b=new AndroidJournalBackend(context,attestation(0).runtime);File f=new File(context.getNoBackupFilesDir(),"flexygram-local-auth-operations-v1/account-0.metadata");Files.write(f.toPath(),new byte[]{0,1,2});denied(()->b.read(scope(0)));need(f.length()==3);break;}
        case "androidJournalRejectsOversize":{AndroidJournalBackend b=new AndroidJournalBackend(context,attestation(0).runtime);File f=new File(context.getNoBackupFilesDir(),"flexygram-local-auth-operations-v1/account-0.metadata");Files.write(f.toPath(),new byte[513]);denied(()->b.read(scope(0)));break;}
        case "androidJournalLockContention":{AndroidJournalBackend b=new AndroidJournalBackend(context,attestation(0).runtime);File f=new File(context.getNoBackupFilesDir(),"flexygram-local-auth-operations-v1/account-0.lock");try(RandomAccessFile lock=new RandomAccessFile(f,"rw");FileLock held=lock.getChannel().lock()){denied(()->b.read(scope(0)));}need(b.read(scope(0)).phase==Phase.NONE);break;}
        case "androidJournalCasConflict":{AndroidJournalBackend b=new AndroidJournalBackend(context,attestation(0).runtime);Record empty=b.read(scope(0)),one=new Record(scope(0),1,"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",Phase.STARTED);need(b.compareAndSet(empty,one));need(!new AndroidJournalBackend(context,attestation(0).runtime).compareAndSet(empty,one));need(b.read(scope(0)).equals(one));break;}
        case "androidJournalSeparateAccounts":{OperationJournal a0=new OperationJournal(new AndroidJournalBackend(context,attestation(0).runtime),scope(0)),a1=new OperationJournal(new AndroidJournalBackend(context,attestation(1).runtime),scope(1));a0.begin(false);need(a1.inspect().phase==Phase.NONE);a1.begin(false);need(!a0.inspect().operation.equals(a1.inspect().operation));break;}
        case "androidBackendWrongPackage":context.pkg="com.example.unapproved";denied(()->new AndroidJournalBackend(context,attestation(0).runtime));break;
        case "androidProbeTrustedRootAlias":{
            File alias=new File(args[1],"private-alias");Files.createSymbolicLink(alias.toPath(),context.getFilesDir().toPath());
            ApplicationLoader.overrideFiles=alias;
            need(new TelegramAccountAdapter(context,attestation(0)).inspect().evidence==AccountProbe.Evidence.EMPTY);
            need(new TelegramAccountAdapter(context,attestation(1)).inspect().evidence==AccountProbe.Evidence.EMPTY);break;}
        case "androidProbeAliasStillRejectsAuth":{
            File alias=new File(args[1],"private-alias");Files.createSymbolicLink(alias.toPath(),context.getFilesDir().toPath());
            ApplicationLoader.overrideFiles=alias;File f=new File(context.getFilesDir(),"tgnet.dat");Files.write(f.toPath(),new byte[]{1});
            AccountProbe.Snapshot p=new TelegramAccountAdapter(context,attestation(0)).inspect();
            need(p.evidence==AccountProbe.Evidence.NATIVE_FILES_PRESENT&&p.diagnostic==AccountProbe.Diagnostic.AUTH_FILES_PRESENT&&f.length()==1);break;}
        case "androidProbeAccountRedirectRejected":{
            Files.createSymbolicLink(new File(context.getFilesDir(),"account1").toPath(),context.getNoBackupFilesDir().toPath());
            AccountProbe.Snapshot p=new TelegramAccountAdapter(context,attestation(1)).inspect();
            need(p.evidence==AccountProbe.Evidence.UNAVAILABLE&&p.step==AccountProbe.Step.ACCOUNT_DIRECTORY);break;}
        case "androidProbeSafeControllerDiagnostic":{
            MessagesStorage.fail=true;AccountProbe.Snapshot p=new TelegramAccountAdapter(context,attestation(0)).inspect();
            need(p.diagnostic==AccountProbe.Diagnostic.INITIALIZATION_FAILED&&p.step==AccountProbe.Step.STORAGE_HANDLE&&!p.toString().contains(CANARY));break;}
        case "androidProbeFixedSlot":{TelegramAccountAdapter p=new TelegramAccountAdapter(context,attestation(1));need(p.inspect().evidence==AccountProbe.Evidence.EMPTY&&UserConfig.selectedAccount==9);UserConfig.getInstance(0).active=true;need(p.inspect().evidence==AccountProbe.Evidence.EMPTY);UserConfig.getInstance(1).active=true;need(p.inspect().evidence==AccountProbe.Evidence.EXISTING_ACCOUNT);break;}
        case "androidProbePersistedUser":UserConfig.getInstance(0).keys.add("user");need(new TelegramAccountAdapter(context,attestation(0)).inspect().evidence==AccountProbe.Evidence.EXISTING_ACCOUNT);break;
        case "androidProbeBeforeStorageExisting":UserConfig.getInstance(0).keys.add("user");MessagesStorage.fail=true;need(new TelegramAccountAdapter(context,attestation(0)).inspect().evidence==AccountProbe.Evidence.EXISTING_ACCOUNT);break;
        case "androidProbeBeforeStorageNative":{File f=new File(context.getFilesDir(),"tgnet.dat");Files.write(f.toPath(),new byte[]{1});MessagesStorage.fail=true;need(new TelegramAccountAdapter(context,attestation(0)).inspect().evidence==AccountProbe.Evidence.NATIVE_FILES_PRESENT);break;}
        case "androidProbeNativeArtifacts":{File f=new File(context.getFilesDir(),"tgnet.dat.bak");Files.write(f.toPath(),new byte[]{1});need(new TelegramAccountAdapter(context,attestation(0)).inspect().evidence==AccountProbe.Evidence.NATIVE_FILES_PRESENT&&f.length()==1);break;}
        case "androidProbeControllerFailure":MessagesStorage.fail=true;need(new TelegramAccountAdapter(context,attestation(0)).inspect().evidence==AccountProbe.Evidence.UNAVAILABLE);break;
        case "androidProbeTmpPasswordBlocked":UserConfig.getInstance(0).keys.add("tmpPassword");need(new TelegramAccountAdapter(context,attestation(0)).inspect().evidence==AccountProbe.Evidence.UNAVAILABLE);break;
        case "androidProbeForeignFilesRejected":ApplicationLoader.overrideFiles=context.getNoBackupFilesDir();need(new TelegramAccountAdapter(context,attestation(0)).inspect().evidence==AccountProbe.Evidence.UNAVAILABLE);break;
        case "androidLoginMarkerNoInput":{LoginFlowOwner o=new LoginFlowOwner(attestation(0).runtime,transport,store,Runnable::run);LoginActivityAdapter adapter=new LoginActivityAdapter(scope(0),o);Looper.main=true;Bundle b=new Bundle();adapter.saveRestartMarker(b);need(b.values.size()==2&&!b.values.toString().contains(CANARY));need(adapter.processRecreationMarker(b).state==State.RESTART_REQUIRED&&transport.requests==0);break;}
        case "androidProcessDeathNoAutomaticRestart":{LoginFlowOwner o=new LoginFlowOwner(attestation(0).runtime,transport,store,Runnable::run);LoginActivityAdapter adapter=new LoginActivityAdapter(scope(0),o);Looper.main=true;Bundle b=new Bundle();adapter.saveRestartMarker(b);need(adapter.restoreAfterProcessDeath(b));need(!o.initializeLocal(false));o.startLocal(material());o.verifyLocal(material());need(o.snapshot().state==State.RESTART_REQUIRED&&transport.requests==0&&memory.writes==0);break;}
        case "androidLoginWrongAccount":{LoginFlowOwner o=new LoginFlowOwner(attestation(0).runtime,transport,store,Runnable::run);LoginActivityAdapter adapter=new LoginActivityAdapter(scope(0),o);Looper.main=true;denied(()->adapter.attach(new LoginActivity(1),s->{}));break;}
        case "androidLoginDetachedNoCallbacks":{LoginFlowOwner o=new LoginFlowOwner(attestation(0).runtime,transport,store,Runnable::run);LoginActivityAdapter adapter=new LoginActivityAdapter(scope(0),o);Looper.main=true;int[] calls={0};AuthUiRelay.Binding b=adapter.attach(new LoginActivity(0),s->calls[0]++);adapter.detach(b);Handler.flush();need(calls[0]==0);break;}
        case "androidLoginHandlerRejected":Looper.main=true;Handler.accept=false;denied(()->LoginActivityAdapter.mainExecutor().execute(()->{}));break;
        case "androidLoginNativeCallbackSeam":{LoginFlowOwner o=new LoginFlowOwner(attestation(0).runtime,transport,store,Runnable::run);o.initializeLocal(false);LoginActivityAdapter adapter=new LoginActivityAdapter(scope(0),o);Looper.main=true;need(!adapter.onLocalStart(material()));AuthUiRelay.Binding first=adapter.attach(new LoginActivity(0),s->{});need(adapter.onLocalStart(material())&&o.snapshot().state==State.CODE_REQUIRED);adapter.detach(first);need(!adapter.onLocalVerify(material())&&!adapter.viewState().attached);adapter.attach(new LoginActivity(0),s->{});need(adapter.viewState().attachments==2&&adapter.onLocalVerify(material())&&o.snapshot().state==State.LOCAL_AUTHORIZED);adapter.destroyOwner();need(adapter.viewState().ownerDestroyed&&o.snapshot().state==State.CLOSED&&sink.writes==0);break;}
        case "androidLoginForeignRecreation":{LoginFlowOwner o=new LoginFlowOwner(attestation(0).runtime,transport,store,Runnable::run);LoginActivityAdapter adapter=new LoginActivityAdapter(scope(0),o);Looper.main=true;Bundle b=new Bundle();b.putBoolean("flexygram_local_auth_restart",true);b.putInt("flexygram_local_auth_slot",1);denied(()->adapter.restoreAfterProcessDeath(b));need(memory.writes==0&&transport.requests==0);break;}
        case "jniMissingFailsClosed":denied(()->AndroidNativeBridge.read(context,0));break;
        case "jniActualReadOnlyBridge":{System.load(args[2]);ReadOnlyAttestation a=AndroidNativeBridge.read(context,0);need(a.nativeEngineInitialized==ReadOnlyAttestation.Availability.UNKNOWN&&a.linkedBridge==ReadOnlyAttestation.Availability.AVAILABLE&&a.runtime.authorize(ClosedRuntime.Operation.REQUEST_CODE)==ClosedRuntime.Decision.DENIED);break;}
        case "jniPidMismatch":System.load(args[2]);android.os.Process.deltaPid=1;denied(()->AndroidNativeBridge.read(context,0));break;
        case "jniUidMismatch":System.load(args[2]);android.os.Process.deltaUid=1;denied(()->AndroidNativeBridge.read(context,0));break;
        case "jniInvalidAccount":System.load(args[2]);denied(()->AndroidNativeBridge.read(context,10));break;
        case "jniDirectInvalidAccount":{System.load(args[2]);Method m=AndroidNativeBridge.class.getDeclaredMethod("nativeIdentity",int.class);m.setAccessible(true);try{m.invoke(null,-1);throw new AssertionError();}catch(InvocationTargetException e){need(e.getCause() instanceof IllegalArgumentException&&!e.getCause().toString().contains(CANARY));}break;}
        case "jniCapabilityMismatch":System.load(args[2]);BuildConfig.FLEXYGRAM_CAP_TELEGRAMTRANSPORT=true;denied(()->AndroidNativeBridge.read(context,0));break;
        case "jniApiCredentialsRejected":BuildConfig.APP_ID=6;BuildConfig.APP_HASH=CANARY;denied(()->AndroidNativeBridge.read(context,0));break;
        case "jniPolicyScopeMismatch":System.load(args[2]);BuildConfig.FLEXYGRAM_POLICY_SCOPE="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa:realAlpha";denied(()->AndroidNativeBridge.read(context,0));break;
        case "jniWrongPackage":context.pkg="com.example.unapproved";denied(()->AndroidNativeBridge.read(context,0));break;
        default:throw new AssertionError("UNKNOWN_TEST");
        }
        need(org.telegram.tgnet.ConnectionsManager.sends==0&&org.telegram.tgnet.ConnectionsManager.cancels==0&&org.telegram.tgnet.ConnectionsManager.initializations==0);
        System.out.println("PASS "+test+" HOST_DOUBLES_NO_TELEGRAM");
    }
}
