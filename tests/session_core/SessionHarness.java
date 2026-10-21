package io.github.jose22yt.flexygram.session;

import java.util.*;
import java.util.concurrent.*;
import java.lang.reflect.*;
import io.github.jose22yt.flexygram.session.RequestCoordinator.*;
import io.github.jose22yt.flexygram.session.AuthenticationController.*;

/** Only fake local adapters. No Android, network, real identity, key, token or session. */
public final class SessionHarness {
    static final String CANARY="SYNTHETIC_PRIVATE_NOT_A_REAL_TOKEN_49127";
    static char[] secret() { return CANARY.toCharArray(); }
    static SessionScope scope(int n) { return SessionScope.of("realAlpha","io.github.jose22yt.flexygram.realalpha",n); }
    static void need(boolean value) { if(!value) throw new AssertionError("CONTRACT_FAILED"); }
    static void denied(Runnable action) {
        try { action.run(); } catch(IllegalArgumentException | IllegalStateException expected) {
            need(!expected.toString().contains(CANARY));need(expected.getCause()==null);return;
        }
        throw new AssertionError("EXPECTED_DENIAL");
    }
    static ClosedRuntime closed(SessionScope scope) {
        String policy="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa:"+scope.variant.name;
        return ClosedRuntime.verify(scope,policy,true,new boolean[6],0,new char[0],"FLEXYGRAM_POLICY:"+policy+":auth=0:transport=0:push=0:translation=0:plugins=0:restore=0");
    }
    static class Transport implements TransportPort {
        Domain domain=Domain.LOCAL_SIMULATION;
        public Domain domain(){return domain;}
        final SessionScope scope;
        int init,submits,cancels,closes;
        boolean failInit,failSubmit,failCancel,failClose,noHandle,replyThenThrow;
        Reply immediate;
        Listener callback;
        Attempt attempt;
        Runnable duringInit=()->{}, duringSubmit=()->{};
        Transport(SessionScope scope) { this.scope=scope; }
        public SessionScope scope(){return scope;}
        public void initialize(){init++;duringInit.run();if(failInit)throw new IllegalStateException(CANARY);}
        public Cancellation submit(Attempt attempt,Listener callback){
            submits++;this.attempt=attempt;this.callback=callback;duringSubmit.run();
            if(immediate!=null)callback.complete(immediate);
            if(failSubmit || replyThenThrow)throw new IllegalStateException(CANARY);
            return noHandle?null:()->{cancels++;if(failCancel)throw new IllegalStateException(CANARY);};
        }
        public void close(){closes++;if(failClose)throw new IllegalStateException(CANARY);}
        void respond(Reply reply){callback.complete(reply);}
    }
    static class Store implements SessionStore {
        SessionScope reported=scope(0);
        long version;
        int reads,writes;
        char[] retained,lastArgument;
        boolean failRead,failWrite,failAfterWrite,conflict,nullSnapshot,nullCommit;
        Runnable duringCommit=()->{};
        public StoreSnapshot inspect(SessionScope asked){
            reads++;if(failRead)throw new IllegalStateException(CANARY);
            return nullSnapshot?null:new StoreSnapshot(reported,version,retained!=null);
        }
        public Commit commitLocalIfEmpty(SessionScope asked,long expected,char[] material){
            writes++;lastArgument=material;duringCommit.run();
            if(failWrite)throw new IllegalStateException(CANARY);
            if(nullCommit)return null;
            if(conflict || expected!=version || retained!=null)return Commit.CONFLICT;
            need(asked.equals(reported));retained=material.clone();version++;
            if(failAfterWrite)throw new IllegalStateException(CANARY);
            return Commit.COMMITTED;
        }
    }
    static class Box { int count;Kind kind;Fault fault;Reply retained;
        void accept(Reply r){count++;kind=r.kind;fault=r.fault;retained=r;}
    }
    static Input input(){return new Input(secret(),secret());}
    static AuthenticationController auth(Transport t,Store s){return new AuthenticationController(closed(scope(0)),t,s);}
    static void code(AuthenticationController a,Transport t){need(a.initialize());need(a.start(secret()));t.respond(Reply.codeSent(secret()));need(a.snapshot().state==State.CODE_REQUIRED);}
    static void authorized(AuthenticationController a,Transport t){code(a,t);need(a.submitCode(secret()));t.respond(Reply.localSession(secret()));need(a.snapshot().state==State.LOCAL_AUTHORIZED);}
    static void zero(char[] chars){for(char c:chars)need(c==0);}
    static char[] field(Object owner,String name)throws Exception{Field f=owner.getClass().getDeclaredField(name);f.setAccessible(true);return(char[])f.get(owner);}
    static final class Worker extends Thread {
        volatile Throwable failure;
        Worker(Runnable action){super(()->{});this.action=action;}
        private final Runnable action;
        @Override public void run(){try{action.run();}catch(Throwable failure){this.failure=failure;}}
        void finish()throws Exception{join(5000);need(!isAlive());need(failure==null);}
    }
    static void await(CountDownLatch latch){try{need(latch.await(5,TimeUnit.SECONDS));}catch(InterruptedException e){throw new AssertionError("INTERRUPTED");}}
    public static void main(String[] args)throws Exception {
        String test=args[0];SessionScope sc=scope(0);Transport t=new Transport(sc);RequestCoordinator b=new RequestCoordinator(closed(sc),t);Box box=new Box();Store s=new Store();AuthenticationController a=auth(t,s);
        switch(test){
        case "realTransportDenied":t.domain=Domain.TELEGRAM;need(!b.initialize());need(b.submit(sc,Operation.REQUEST_CODE,input(),box::accept)==null);need(t.init==0&&t.submits==0&&t.closes==0);break;
        case "domainChangedAfterInit":need(b.initialize());t.domain=Domain.TELEGRAM;need(b.submit(sc,Operation.REQUEST_CODE,input(),box::accept)==null);need(box.kind==Kind.DENIED&&t.submits==0);break;
        case "authRealTransportDenied":t.domain=Domain.TELEGRAM;need(!a.initialize());need(a.snapshot().fault==Fault.INITIALIZATION&&!a.start(secret()));need(t.init==0&&t.submits==0&&s.writes==0);break;
        case "uiStalePublication":{UiSnapshot old=a.snapshot();AuthUiRelay relay=new AuthUiRelay(old);List<UiSnapshot> observed=new ArrayList<>();relay.attach(Runnable::run,observed::add);need(a.initialize());relay.publish(a.snapshot());relay.publish(old);need(observed.get(observed.size()-1).state==State.READY&&observed.size()==2);break;}
        case "uiReplay":{List<UiSnapshot> observed=new ArrayList<>();a.observe(Runnable::run,observed::add);need(observed.size()==1&&observed.get(0).state==State.NEW);break;}
        case "uiFlowEvents":{List<UiSnapshot> observed=new ArrayList<>();a.observe(Runnable::run,observed::add);code(a,t);need(observed.get(observed.size()-1).state==State.CODE_REQUIRED);for(UiSnapshot snap:observed)need(!snap.toString().contains(CANARY));break;}
        case "uiDetachQueued":{List<Runnable> queue=new ArrayList<>();Box count=new Box();AuthUiRelay.Binding binding=a.observe(queue::add,snap->count.count++);binding.close();for(Runnable task:queue)task.run();need(count.count==0);break;}
        case "uiRecreation":{List<Runnable> queue=new ArrayList<>();int[] oldCalls={0},newCalls={0};a.observe(queue::add,snap->oldCalls[0]++);need(a.initialize());a.start(secret());a.observe(queue::add,snap->newCalls[0]++);for(Runnable task:new ArrayList<>(queue))task.run();need(oldCalls[0]==0&&newCalls[0]==1&&t.submits==1);break;}
        case "uiOutOfOrder":{List<Runnable> queue=new ArrayList<>();List<UiSnapshot> observed=new ArrayList<>();a.observe(queue::add,observed::add);need(a.initialize());a.start(secret());Collections.reverse(queue);for(Runnable task:queue)task.run();need(observed.size()==1&&observed.get(0).state==State.STARTING);break;}
        case "uiCloseDropsQueued":{List<Runnable> queue=new ArrayList<>();int[] count={0};a.observe(queue::add,snap->count[0]++);a.close();for(Runnable task:queue)task.run();need(count[0]==0);denied(()->a.observe(Runnable::run,snap->{}));break;}
        case "uiObserverFailure":{AuthUiRelay relay=new AuthUiRelay(a.snapshot());relay.attach(Runnable::run,snap->{throw new IllegalStateException(CANARY);});need(relay.observerFailures()==1&&a.snapshot().state==State.NEW&&t.submits==0);break;}
        case "uiExecutorFailure":{AuthUiRelay relay=new AuthUiRelay(a.snapshot());relay.attach(task->{throw new IllegalStateException(CANARY);},snap->{throw new AssertionError();});need(relay.executorFailures()==1&&t.submits==0);break;}
        case "uiScopeRejected":{AuthUiRelay relay=new AuthUiRelay(a.snapshot());AuthenticationController other=new AuthenticationController(closed(scope(1)),new Transport(scope(1)),s);denied(()->relay.publish(other.snapshot()));break;}
        case "uiOldBindingCannotCloseNew":{AuthUiRelay.Binding old=a.observe(Runnable::run,snap->{});int[] calls={0};a.observe(Runnable::run,snap->calls[0]++);old.close();need(a.initialize());need(calls[0]>=2);break;}
        case "uiBindingReleasesObserver":{AuthUiRelay.Binding binding=a.observe(task->{},snap->{});binding.close();Field observer=binding.getClass().getDeclaredField("observer");observer.setAccessible(true);need(observer.get(binding)==null);break;}
        case "scopeBounds":for(int n:new int[]{-1,10,100})denied(()->scope(n));need(scope(0).equals(scope(0)));need(!scope(0).equals(scope(1)));break;
        case "scopeVariantMismatch":denied(()->SessionScope.of("diagnostic",sc.variant.applicationId,0));denied(()->SessionScope.of("production","io.github.jose22yt.flexygram.app",0));break;
        case "storageNamespaces":Set<String> keys=new HashSet<>();for(SessionScope.Variant v:SessionScope.Variant.values())for(int n=0;n<10;n++)need(keys.add(SessionScope.of(v.name,v.applicationId,n).storageKey()));need(keys.size()==30);break;
        case "closedNative":{String p="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa:realAlpha";ClosedRuntime r=ClosedRuntime.verify(sc,p,true,new boolean[6],0,new char[0],"FLEXYGRAM_POLICY:"+p+":auth=0:transport=0:push=0:translation=0:plugins=0:restore=0");for(ClosedRuntime.Operation op:ClosedRuntime.Operation.values())need(r.authorize(op)==ClosedRuntime.Decision.DENIED);break;}
        case "capMutation":{String p="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa:realAlpha";boolean[] flags=new boolean[6];ClosedRuntime r=ClosedRuntime.verify(sc,p,true,flags,0,new char[0],"FLEXYGRAM_POLICY:"+p+":auth=0:transport=0:push=0:translation=0:plugins=0:restore=0");Arrays.fill(flags,true);need(r.authorize(ClosedRuntime.Operation.INITIALIZE_MTPROTO)==ClosedRuntime.Decision.DENIED);break;}
        case "actualNativeAttestation":{String statement=args[1];String policy=statement.substring("FLEXYGRAM_POLICY:".length(),statement.indexOf(":auth="));ClosedRuntime runtime=ClosedRuntime.verify(sc,policy,true,new boolean[6],0,new char[0],statement);need(runtime.authorize(ClosedRuntime.Operation.INITIALIZE_MTPROTO)==ClosedRuntime.Decision.DENIED);break;}
        case "recreationMarker":need(a.restoreUi(UiSnapshot.recreationMarker(sc)));need(a.snapshot().state==State.RESTART_REQUIRED&&!a.start(secret()));break;
        case "badCapabilities":{String p="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa:realAlpha";for(int i=0;i<6;i++){boolean[] f=new boolean[6];f[i]=true;denied(()->ClosedRuntime.verify(sc,p,true,f,0,new char[0],""));}break;}
        case "badBuildFacts":{String p="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa:realAlpha";denied(()->ClosedRuntime.verify(sc,p,false,new boolean[6],0,new char[0],""));denied(()->ClosedRuntime.verify(sc,p,true,new boolean[5],0,new char[0],""));denied(()->ClosedRuntime.verify(sc,p,true,new boolean[6],6,new char[0],""));denied(()->ClosedRuntime.verify(sc,p,true,new boolean[6],0,secret(),CANARY));break;}
        case "badNative":{String p="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa:realAlpha";String prefix="FLEXYGRAM_POLICY:"+p;for(String row:new String[]{prefix+":auth=1:transport=0:push=0:translation=0:plugins=0:restore=0",prefix+":auth=0:transport=1:push=0:translation=0:plugins=0:restore=0",CANARY,""})denied(()->ClosedRuntime.verify(sc,p,true,new boolean[6],0,new char[0],row));break;}
        case "badPolicyScope":for(String p:new String[]{"abc:realAlpha","aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"+":diagnostic",CANARY})denied(()->ClosedRuntime.verify(sc,p,true,new boolean[6],0,new char[0],""));break;
        case "initOnce":need(b.initialize());need(b.initialize());need(t.init==1);break;
        case "initFailure":t.failInit=true;need(!b.initialize());need(!b.initialize());need(t.init==1&&t.closes==1);break;
        case "initReentry":t.duringInit=()->need(!b.initialize());need(b.initialize());need(t.init==1);break;
        case "initForeignAdapter":{Transport other=new Transport(scope(1));RequestCoordinator local=new RequestCoordinator(closed(sc),other);need(!local.initialize());local.close();need(other.init==0&&other.closes==0);break;}
        case "closeBeforeInit":b.close();need(!b.initialize());need(t.init==0&&t.closes==0);break;
        case "cancelDuringInit":{CountDownLatch started=new CountDownLatch(1),release=new CountDownLatch(1);t.duringInit=()->{started.countDown();await(release);};Worker worker=new Worker(()->need(!b.initialize()));worker.start();await(started);b.close();need(t.closes==0);release.countDown();worker.finish();need(t.closes==1);break;}
        case "requestBeforeInit":{Input i=input();need(b.submit(sc,Operation.REQUEST_CODE,i,box::accept)==null);need(i.isClosed()&&t.submits==0&&box.fault==Fault.INVALID_STATE);break;}
        case "crossAccountRequest":need(b.initialize());need(b.submit(scope(1),Operation.REQUEST_CODE,input(),box::accept)==null);need(t.submits==0&&box.fault==Fault.INVALID_SCOPE);break;
        case "destructiveDenied":need(b.initialize());for(Operation op:new Operation[]{Operation.LOGOUT,Operation.REVOKE_CURRENT,Operation.REVOKE_OTHERS,Operation.RESET_ALL_SESSIONS})need(b.submit(sc,op,input(),box::accept)==null);need(t.submits==0&&box.count==4&&box.kind==Kind.DENIED);break;
        case "requestSuccess":{need(b.initialize());Input i=input();Ticket ticket=b.submit(sc,Operation.REQUEST_CODE,i,box::accept);Reply r=Reply.codeSent(secret());t.respond(r);need(ticket!=null&&box.count==1&&box.kind==Kind.CODE_SENT&&i.isClosed()&&r.isClosed()&&b.activeCount()==0);break;}
        case "requestException":t.failSubmit=true;need(b.initialize());b.submit(sc,Operation.REQUEST_CODE,input(),box::accept);need(box.count==1&&box.fault==Fault.ADAPTER&&t.submits==1&&b.activeCount()==0);break;
        case "noHandle":t.noHandle=true;need(b.initialize());b.submit(sc,Operation.REQUEST_CODE,input(),box::accept);need(box.fault==Fault.ADAPTER);break;
        case "syncThenException":t.replyThenThrow=true;t.immediate=Reply.codeSent(secret());need(b.initialize());b.submit(sc,Operation.REQUEST_CODE,input(),box::accept);need(box.fault==Fault.ADAPTER&&box.count==1&&t.immediate.isClosed());break;
        case "syncSuccess":t.immediate=Reply.codeSent(secret());need(b.initialize());b.submit(sc,Operation.REQUEST_CODE,input(),box::accept);need(box.count==1&&box.kind==Kind.CODE_SENT&&t.cancels==0);break;
        case "duplicateReply":need(b.initialize());b.submit(sc,Operation.REQUEST_CODE,input(),box::accept);t.respond(Reply.codeSent(secret()));Reply duplicate=Reply.localSession(secret());t.respond(duplicate);need(box.count==1&&box.kind==Kind.CODE_SENT&&duplicate.isClosed()&&b.discardedReplies()==1);break;
        case "nullReply":need(b.initialize());b.submit(sc,Operation.REQUEST_CODE,input(),box::accept);t.respond(null);need(box.count==1&&box.fault==Fault.PROTOCOL);break;
        case "cancel":{need(b.initialize());Ticket id=b.submit(sc,Operation.REQUEST_CODE,input(),box::accept);need(b.cancel(id));need(!b.cancel(id));need(box.kind==Kind.CANCELLED&&box.count==1&&t.cancels==1);break;}
        case "cancelBeforeHandle":need(b.initialize());t.duringSubmit=b::close;b.submit(sc,Operation.REQUEST_CODE,input(),box::accept);need(box.count==1&&box.kind==Kind.CANCELLED&&t.cancels==1&&t.closes==1);break;
        case "lateReply":{need(b.initialize());Ticket id=b.submit(sc,Operation.REQUEST_CODE,input(),box::accept);b.cancel(id);Reply late=Reply.localSession(secret());t.respond(late);need(box.count==1&&box.kind==Kind.CANCELLED&&late.isClosed()&&b.activeCount()==0);break;}
        case "foreignTicket":{need(b.initialize());Transport other=new Transport(scope(1));RequestCoordinator otherBroker=new RequestCoordinator(closed(scope(1)),other);need(otherBroker.initialize());Ticket own=b.submit(sc,Operation.REQUEST_CODE,input(),box::accept);Ticket foreign=otherBroker.submit(scope(1),Operation.REQUEST_CODE,input(),r->{});need(own.id==foreign.id);need(!b.cancel(foreign));need(b.activeCount()==1&&otherBroker.activeCount()==1&&t.cancels==0&&other.cancels==0);break;}
        case "cancelThrows":{t.failCancel=true;need(b.initialize());Ticket id=b.submit(sc,Operation.REQUEST_CODE,input(),box::accept);need(b.cancel(id));need(box.kind==Kind.CANCELLED&&b.adapterFailures()==1);break;}
        case "listenerThrows":need(b.initialize());b.submit(sc,Operation.REQUEST_CODE,input(),r->{throw new IllegalStateException(CANARY);});Reply r=Reply.codeSent(secret());t.respond(r);need(b.listenerFailures()==1&&r.isClosed()&&b.activeCount()==0);break;
        case "closeOnce":need(b.initialize());t.failClose=true;b.close();b.close();need(t.closes==1&&b.adapterFailures()==1);break;
        case "inputWipe":{Input i=input();char[] raw=field(i,"primary");i.close();zero(raw);denied(i::primaryCopy);break;}
        case "replyWipe":{Reply reply=Reply.localSession(secret());char[] raw=field(reply,"material");reply.close();zero(raw);denied(reply::materialCopy);break;}
        case "copyIsolation":{char[] original=secret();Input i=new Input(original,new char[0]);char[] copy=i.primaryCopy();copy[0]='X';need(Arrays.equals(i.primaryCopy(),original));i.close();need(CANARY.equals(new String(original)));break;}
        case "cancelBufferedReply":{final RequestCoordinator[] holder=new RequestCoordinator[1];Reply pending=Reply.codeSent(secret());Transport custom=new Transport(sc){public Cancellation submit(Attempt x,Listener cb){cb.complete(pending);holder[0].close();return ()->cancels++;}};holder[0]=new RequestCoordinator(closed(sc),custom);need(holder[0].initialize());holder[0].submit(sc,Operation.REQUEST_CODE,input(),box::accept);need(box.kind==Kind.CANCELLED&&box.count==1&&pending.isClosed()&&custom.cancels==1);break;}
        case "parallelFirstReply":{for(int i=0;i<100;i++){
            Box result=new Box();CountDownLatch fire=new CountDownLatch(1);List<Worker> workers=new ArrayList<>();
            Transport parallel=new Transport(sc){public Cancellation submit(Attempt request,Listener cb){cb.complete(Reply.codeSent(secret()));Worker w=new Worker(()->{await(fire);cb.complete(Reply.localSession(secret()));});workers.add(w);w.start();return ()->{};}};
            RequestCoordinator owner=new RequestCoordinator(closed(sc),parallel);need(owner.initialize());owner.submit(sc,Operation.REQUEST_CODE,input(),result::accept);fire.countDown();workers.get(0).finish();need(result.count==1&&result.kind==Kind.CODE_SENT);owner.close();
        }break;}
        case "authCancelBeforeTicket":t.duringSubmit=()->need(a.cancel());need(a.initialize());a.start(secret());need(a.snapshot().state==State.CANCELLED&&t.cancels==1&&t.closes==1&&s.writes==0);break;
        case "authCancelDuringInit":{CountDownLatch started=new CountDownLatch(1),release=new CountDownLatch(1);t.duringInit=()->{started.countDown();await(release);};Worker worker=new Worker(()->need(!a.initialize()));worker.start();await(started);need(a.cancel());release.countDown();worker.finish();need(a.snapshot().state==State.CANCELLED&&t.closes==1&&s.writes==0);break;}
        case "authCommitVsCancel":{authorized(a,t);CountDownLatch entered=new CountDownLatch(1),release=new CountDownLatch(1);s.duringCommit=()->{entered.countDown();await(release);};Worker writer=new Worker(()->need(a.commitLocal()));writer.start();await(entered);Worker canceller=new Worker(()->need(!a.cancel()));canceller.start();release.countDown();writer.finish();canceller.finish();need(a.snapshot().state==State.LOCAL_COMPLETE&&s.retained!=null&&s.writes==1);break;}
        case "authSessionAppearsDuringInit":t.duringInit=()->s.retained=secret();need(!a.initialize());need(a.snapshot().fault==Fault.EXISTING_SESSION&&s.retained!=null&&s.writes==0&&t.closes==1);break;
        case "authEmpty":need(a.initialize());need(a.snapshot().state==State.READY&&s.reads==2&&s.writes==0&&t.init==1);break;
        case "authExisting":s.retained=secret();need(!a.initialize());need(a.snapshot().fault==Fault.EXISTING_SESSION&&t.init==0&&s.writes==0);break;
        case "authForeignStore":s.reported=scope(1);need(!a.initialize());need(a.snapshot().fault==Fault.INVALID_SCOPE&&t.init==0&&s.writes==0);break;
        case "authNullStore":s.nullSnapshot=true;need(!a.initialize());need(a.snapshot().fault==Fault.INVALID_SCOPE&&t.init==0);break;
        case "authReadFailure":s.failRead=true;need(!a.initialize());need(!a.initialize());need(a.snapshot().fault==Fault.STORAGE&&t.init==0);break;
        case "authInitFailure":t.failInit=true;need(!a.initialize());need(!a.initialize());need(a.snapshot().fault==Fault.INITIALIZATION&&t.init==1&&t.closes==1);break;
        case "authStartReentry":need(a.initialize());need(a.start(secret()));need(!a.start(secret()));need(t.submits==1&&a.snapshot().state==State.STARTING);break;
        case "authCodeBeforeStart":need(a.initialize());need(!a.submitCode(secret()));need(t.submits==0);break;
        case "authCodeReentry":code(a,t);need(a.submitCode(secret()));need(!a.submitCode(secret()));need(t.submits==2&&a.snapshot().state==State.VERIFYING);break;
        case "authWrongPhaseReply":need(a.initialize());a.start(secret());t.respond(Reply.localSession(secret()));need(a.snapshot().fault==Fault.PROTOCOL&&s.writes==0&&t.closes==1);break;
        case "authEmptyChallenge":need(a.initialize());a.start(secret());t.respond(Reply.codeSent(new char[0]));need(a.snapshot().fault==Fault.PROTOCOL&&s.writes==0);break;
        case "authError":need(a.initialize());a.start(secret());t.respond(Reply.failure(Fault.ADAPTER));need(a.snapshot().fault==Fault.ADAPTER&&!a.start(secret())&&t.submits==1);break;
        case "authExplicitCommit":authorized(a,t);need(s.writes==0&&t.closes==1);need(a.commitLocal());need(a.snapshot().state==State.LOCAL_COMPLETE&&s.writes==1);need(!a.commitLocal());zero(s.lastArgument);break;
        case "authConflict":authorized(a,t);s.conflict=true;need(!a.commitLocal());need(a.snapshot().fault==Fault.CONFLICT&&s.writes==1&&s.retained==null);break;
        case "authWriteFailure":authorized(a,t);s.failWrite=true;need(!a.commitLocal());need(a.snapshot().state==State.STORAGE_UNCERTAIN&&s.writes==1&&!a.commitLocal());zero(s.lastArgument);break;
        case "authUnknownCommit":authorized(a,t);s.failAfterWrite=true;need(!a.commitLocal());need(a.snapshot().state==State.STORAGE_UNCERTAIN&&s.retained!=null);a.close();need(s.retained!=null&&s.writes==1);break;
        case "authNullCommit":authorized(a,t);s.nullCommit=true;need(!a.commitLocal());need(a.snapshot().state==State.STORAGE_UNCERTAIN);break;
        case "authConcurrentSession":authorized(a,t);s.retained="OTHER_LOCAL_SESSION".toCharArray();s.version++;need(!a.commitLocal());need("OTHER_LOCAL_SESSION".equals(new String(s.retained))&&a.snapshot().fault==Fault.CONFLICT);break;
        case "authCancelPending":need(a.initialize());a.start(secret());need(a.cancel());t.respond(Reply.codeSent(secret()));need(a.snapshot().state==State.CANCELLED&&t.cancels==1&&s.writes==0);break;
        case "authCancelChallenge":code(a,t);char[] raw=field(a,"challenge");need(a.cancel());zero(raw);need(!a.submitCode(secret())&&s.writes==0);break;
        case "authCancelAuthorized":authorized(a,t);char[] stagedRaw=field(a,"stagedSession");need(a.cancel());zero(stagedRaw);need(!a.commitLocal()&&s.writes==0);break;
        case "authCompleteNoLogout":authorized(a,t);a.commitLocal();need(!a.cancel());a.close();need(s.retained!=null&&s.writes==1);break;
        case "authCancelReentrantInit":t.duringInit=()->need(a.cancel());need(!a.initialize());need(a.snapshot().state==State.CANCELLED&&t.closes==1);break;
        case "authCommitReentry":authorized(a,t);s.duringCommit=()->{need(!a.cancel());need(!a.commitLocal());};need(a.commitLocal());need(s.writes==1);break;
        case "activityRecreationRetained":need(a.initialize());a.start(secret());UiSnapshot before=a.snapshot();need(before.state==State.STARTING);need(!a.initialize()&&!a.start(secret()));t.respond(Reply.codeSent(secret()));need(a.snapshot().state==State.CODE_REQUIRED&&t.submits==1);break;
        case "processRecreationNoReplay":need(a.initialize());a.start(secret());AuthenticationController fresh=auth(new Transport(sc),new Store());need(fresh.restoreUi(a.snapshot()));need(fresh.snapshot().state==State.RESTART_REQUIRED&&!fresh.initialize()&&!fresh.start(secret()));break;
        case "restoreWrongAccount":need(!new AuthenticationController(closed(scope(1)),new Transport(scope(1)),new Store()).restoreUi(a.snapshot()));break;
        case "snapshotNoSecret":code(a,t);String text=a.snapshot().toString();need(!text.contains(CANARY)&&!text.contains("LocalInput")&&!text.contains("challenge"));need(text.contains("CODE_REQUIRED"));break;
        case "allDestructiveDenied":for(ClosedRuntime.Operation op:ClosedRuntime.Operation.values())need(a.requestDestructiveOperation(op)==ClosedRuntime.Decision.DENIED);need(t.submits==0&&s.writes==0);break;
        case "noSensitiveExceptions":t.failSubmit=true;need(a.initialize());a.start(secret());need(!a.snapshot().toString().contains(CANARY));need(a.snapshot().fault==Fault.ADAPTER);break;
        case "localNoFallbackRetry":need(a.initialize());a.start(secret());t.respond(Reply.failure(Fault.ADAPTER));need(t.init==1&&t.submits==1&&!a.start(secret()));a.cancel();need(t.submits==1&&t.cancels==0);break;
        case "allStringsRedacted":need(!input().toString().contains(CANARY));need(!Reply.localSession(secret()).toString().contains(CANARY));need(!a.snapshot().toString().contains(CANARY));break;
        default:throw new AssertionError("UNKNOWN_CASE");
        }
        System.out.println("PASS "+test+" LOCAL_ADAPTERS_ONLY");
    }
}
