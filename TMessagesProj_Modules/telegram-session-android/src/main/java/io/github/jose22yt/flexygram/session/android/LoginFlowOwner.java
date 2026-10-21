package io.github.jose22yt.flexygram.session.android;
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.concurrent.Executor;
import io.github.jose22yt.flexygram.session.*;
import io.github.jose22yt.flexygram.session.RequestCoordinator.*;

/** Retain OWNER across configuration changes, never the Activity/Fragment/view or an input Bundle. */
public final class LoginFlowOwner implements AutoCloseable {
    public enum Failure { NONE, LOCAL_OPERATION, WORKER_UNAVAILABLE }
    private final AuthenticationController controller;
    private final LocalSessionStore store;
    private final Executor worker;
    private final ArrayDeque<Task> tasks=new ArrayDeque<>();
    private boolean draining,closed,initialized;
    private long generation;
    private Failure failure=Failure.NONE;
    private final class Task {
        final long epoch;final int operation;final char[] input;
        Task(int operation,char[] input){this.epoch=generation;this.operation=operation;this.input=input;}
        void wipe(){if(input!=null)Arrays.fill(input,'\0');}
    }
    public LoginFlowOwner(ClosedRuntime runtime,TransportPort localTransport,JournaledLocalSessionStore store,Executor worker) {
        this(runtime,localTransport,(LocalSessionStore)store,worker);
    }
    public LoginFlowOwner(ClosedRuntime runtime,TransportPort localTransport,LocalSessionStore store,Executor worker) {
        if(runtime==null||localTransport==null||store==null||worker==null
                ||runtime.scope.variant!=SessionScope.Variant.REAL_ALPHA
                ||localTransport.domain()!=Domain.LOCAL_SIMULATION||!runtime.scope.equals(localTransport.scope()))
            throw new IllegalArgumentException("LOCAL_REHEARSAL_DEPENDENCIES_REQUIRED");
        controller=new AuthenticationController(runtime,localTransport,store);this.store=store;this.worker=worker;
    }
    public AuthenticationController.UiSnapshot snapshot(){return controller.snapshot();}
    /** Adapter phase changed; reuse the existing revisioned UI relay, without polling or requests. */
    public void signalLocalAdapterState(){controller.refreshLocalAdapterUi();}
    public synchronized Failure failure(){return failure;}
    public AuthUiRelay.Binding attachView(Executor mainExecutor,AuthUiRelay.Observer observer) {
        synchronized(this){if(closed)throw new IllegalStateException("LOGIN_OWNER_CLOSED");}
        return controller.observe(mainExecutor,observer);
    }
    /** Explicit retry uses a NEW owner and journal permitting only FAILED/CANCELLED. */
    public boolean initializeLocal(boolean userApprovedRetry) {
        synchronized(this){if(closed||initialized)return false;initialized=true;}
        return enqueue(userApprovedRetry?1:0,null);
    }
    public boolean startLocal(char[] identity){return input(2,identity);}
    public boolean verifyLocal(char[] code){return input(3,code);}
    public boolean commitLocal(){return enqueue(4,null);}
    public boolean cancelLocal(){return enqueue(5,null);}
    public boolean restoreAfterProcessDeath(AuthenticationController.UiSnapshot marker) {
        synchronized(this){
            if(closed||initialized||marker==null||!controller.snapshot().scope.equals(marker.scope))return false;
            initialized=true;
        }
        return enqueue(7,null);
    }
    private boolean input(int operation,char[] supplied) {
        if(supplied==null||supplied.length==0||supplied.length>256)return false;
        return enqueue(operation,supplied.clone());
    }
    private boolean enqueue(int operation,char[] copy) {
        boolean schedule;
        synchronized(this){
            if(closed){if(copy!=null)Arrays.fill(copy,'\0');return false;}
            tasks.add(new Task(operation,copy));schedule=!draining;draining=true;
        }
        return !schedule||schedule();
    }
    private boolean schedule() {
        try{worker.execute(this::drain);return true;}
        catch(RuntimeException|LinkageError rejected){
            synchronized(this){failure=Failure.WORKER_UNAVAILABLE;closed=true;draining=false;discard();}
            controller.close();return false;
        }
    }
    private synchronized void discard(){while(!tasks.isEmpty())tasks.remove().wipe();}
    private void drain() {
        while(true){
            Task task;
            synchronized(this){
                task=tasks.poll();if(task==null){draining=false;return;}
                if(task.operation!=6&&(closed||task.epoch!=generation)){task.wipe();continue;}
            }
            try{
                switch(task.operation){
                    case 0:case 1:store.beginExplicit(task.operation==1);if(!controller.initialize())throw new IllegalStateException("LOCAL_INITIALIZATION_FAILED");break;
                    case 2:controller.start(task.input);break;
                    case 3:controller.submitCode(task.input);break;
                    case 4:controller.commitLocal();break;
                    case 5:controller.cancel();store.close();break;
                    case 7:controller.restoreUi(AuthenticationController.UiSnapshot.recreationMarker(controller.snapshot().scope));break;
                    default:controller.close();store.close();
                }
            }catch(RuntimeException|LinkageError unavailable){
                synchronized(this){failure=Failure.LOCAL_OPERATION;generation++;discard();}
                controller.close();
                try{store.close();}catch(RuntimeException|LinkageError ignored){/* Typed failure, no raw error. */}
            }finally{task.wipe();}
        }
    }
    @Override public void close() {
        boolean schedule;
        synchronized(this){if(closed)return;closed=true;generation++;discard();tasks.add(new Task(6,null));schedule=!draining;draining=true;}
        if(schedule)schedule();
    }
}
