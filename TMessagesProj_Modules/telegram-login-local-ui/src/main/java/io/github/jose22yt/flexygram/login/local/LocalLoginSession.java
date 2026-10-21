package io.github.jose22yt.flexygram.login.local;
import java.util.*;
import java.util.concurrent.Executor;
import io.github.jose22yt.flexygram.session.*;
import io.github.jose22yt.flexygram.session.android.*;
import io.github.jose22yt.flexygram.login.*;
import io.github.jose22yt.flexygram.login.NativeLoginProtocol.*;
import io.github.jose22yt.flexygram.login.local.EphemeralPages.*;

/** Owned local UI commands; uses the existing serial worker and controller, never a new UI/executor. */
public final class LocalLoginSession implements AutoCloseable {
    public interface Renderer {void render(Parameters parameters);}
    private final SessionScope scope;private final LoginFlowOwner owner;private final NativeLoginTransport transport;
    private final TelegramRequestContext context;private final Executor worker;private final EphemeralPages channel;
    private final Set<Command> pending=new HashSet<>();private View view;private AuthUiRelay.Binding relay;
    private boolean stopped,closed;private long claimed=-1;private int claimedAction;
    private final class Command implements Runnable {
        final View ticket;final int action;final char[][] inputs;
        boolean discarded;
        Command(View ticket,int action,char[]... inputs){this.ticket=ticket;this.action=action;this.inputs=new char[inputs.length][];for(int i=0;i<inputs.length;i++)this.inputs[i]=inputs[i].clone();}
        void wipe(){discarded=true;for(char[] a:inputs)Arrays.fill(a,'\0');}
        public void run(){
            synchronized(LocalLoginSession.this){if(discarded||closed||stopped||!channel.valid(ticket)){pending.remove(this);wipe();return;}}
            try {
                switch(action){
                case 0:owner.startLocal(inputs[0]);break;
                case 1:if(transport.snapshot().stage==Stage.CODE_RETRY)transport.retryLocal(inputs[0],true);else owner.verifyLocal(inputs[0]);break;
                case 2:transport.loadPasswordParametersLocal(true);break;
                case 3:if(transport.snapshot().error==NativeLoginProtocol.Error.INVALID_PASSWORD)transport.retryLocal(inputs[0],true);else transport.checkPasswordProofLocal(inputs[0],true);break;
                case 4:context.namesLocal(inputs[0],inputs[1]);transport.signUpLocal(new char[]{'L'},true,false);break;
                case 5:owner.commitLocal();break;
                default:throw new IllegalStateException("LOCAL_COMMAND_REJECTED");
                }
            }catch(RuntimeException|LinkageError unavailable){synchronized(LocalLoginSession.this){stopped=true;}owner.cancelLocal();}
            finally{synchronized(LocalLoginSession.this){pending.remove(this);wipe();}}
        }
    }
    public LocalLoginSession(ClosedRuntime runtime,LoginFlowOwner owner,NativeLoginTransport transport,TelegramRequestContext context,Executor sameSerialWorker){
        if(runtime==null||owner==null||transport==null||context==null||sameSerialWorker==null||!runtime.scope.equals(owner.snapshot().scope)||!runtime.scope.equals(transport.scope())||!runtime.scope.equals(context.scope()))throw new IllegalArgumentException("LOCAL_SESSION_SCOPE_REQUIRED");
        scope=runtime.scope;this.owner=owner;this.transport=transport;this.context=context;worker=sameSerialWorker;channel=new EphemeralPages(runtime);
    }
    public SessionScope scope(){return scope;}
    public synchronized View attach(int account,Executor main,Renderer renderer){
        if(account!=scope.account){if(relay!=null)relay.close();relay=null;channel.detach(view);discardPending();throw new IllegalStateException("LOCAL_VIEW_SCOPE_REJECTED");}
        if(closed||main==null||renderer==null)throw new IllegalStateException("LOCAL_VIEW_REJECTED");
        if(relay!=null)relay.close();discardPending();view=channel.attach(scope);claimed=-1;final View ticket=view;
        relay=owner.attachView(main,state->{synchronized(LocalLoginSession.this){if(!channel.valid(ticket)||closed)return;renderer.render(channel.read(ticket,transport.snapshot(),state,stopped));}});return ticket;
    }
    public synchronized Parameters parameters(View ticket){return channel.read(ticket,transport.snapshot(),owner.snapshot(),stopped);}
    public synchronized boolean valid(View ticket,int account){return account==scope.account&&!closed&&channel.valid(ticket);}
    public synchronized void detach(View ticket){if(!channel.valid(ticket))return;if(relay!=null)relay.close();relay=null;channel.detach(ticket);discardPending();}
    public boolean phone(View ticket,char[] synthetic){return submit(ticket,0,Stage.READY,synthetic);}
    public synchronized boolean code(View ticket,char[] synthetic){if(!channel.valid(ticket)||synthetic==null||synthetic.length!=parameters(ticket).codeLength)return false;Stage stage=transport.snapshot().stage;return (stage==Stage.CODE_REQUIRED||stage==Stage.CODE_RETRY)&&submit(ticket,1,stage,synthetic);}
    public boolean loadPassword(View ticket){return submit(ticket,2,Stage.PASSWORD_REQUIRED);}
    public boolean password(View ticket,char[] synthetic){return submit(ticket,3,Stage.PASSWORD_PARAMETERS,synthetic);}
    public boolean register(View ticket,char[] first,char[] last){if(transport.snapshot().termsRequired)return false;return submit(ticket,4,Stage.SIGNUP_REQUIRED,first,last);}
    public boolean commit(View ticket){return submit(ticket,5,Stage.AUTHORIZED);}
    private boolean submit(View ticket,int action,Stage required,char[]... input){
        final Command command;
        synchronized(this){
            NativeLoginTransport.Snapshot state=transport.snapshot();
            boolean permitted = action==5 ? owner.snapshot().state==AuthenticationController.State.LOCAL_AUTHORIZED : state.stage==required;
            if(closed||stopped||!channel.valid(ticket)||!permitted)return false;
            if((action==1||action==3||action==4)&&parameters(ticket).status!=Status.READY)return false;
            if(claimed==state.revision&&claimedAction==action)return false;
            for(int i=0;i<input.length;i++)if(input[i]==null||input[i].length>256||(input[i].length==0&&!(action==4&&i==1)))return false;
            claimed=state.revision;claimedAction=action;command=new Command(ticket,action,input);pending.add(command);
        }
        try{worker.execute(command);return true;}catch(RuntimeException|LinkageError rejected){synchronized(this){pending.remove(command);command.wipe();stopped=true;}owner.cancelLocal();return false;}
    }
    public synchronized boolean cancel(View ticket){if(!channel.valid(ticket)||closed)return false;stopped=true;discardPending();owner.cancelLocal();return true;}
    private void discardPending(){for(Command command:pending)command.wipe();pending.clear();}
    @Override public synchronized void close(){if(closed)return;closed=true;stopped=true;discardPending();if(relay!=null)relay.close();relay=null;channel.close();owner.close();}
}
