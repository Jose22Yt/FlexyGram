package io.github.jose22yt.flexygram.session.android;
import java.util.Arrays;
import io.github.jose22yt.flexygram.session.SessionScope;
import io.github.jose22yt.flexygram.session.AuthenticationController.*;
import io.github.jose22yt.flexygram.session.android.OperationJournal.*;

/** Bridge to LOCAL controller contract, not a real MTProto persistence adapter. */
public final class JournaledLocalSessionStore implements SessionStore,AutoCloseable {
    public enum Outcome { COMPLETED, FAILED_WITHOUT_WRITE, UNCERTAIN }
    public interface LocalSink {
        /** Synthetic rehearsal only. Never store MTProto keys or activate UserConfig. */
        Outcome commitSynthetic(SessionScope scope,char[] temporaryMaterial);
    }
    private final SessionScope scope;
    private final OperationJournal journal;
    private final AccountProbe probe;
    private final LocalSink sink;
    private Record started;
    private boolean committing,closeRequested,ended;
    public JournaledLocalSessionStore(SessionScope scope,OperationJournal journal,AccountProbe probe,LocalSink sink) {
        if(scope==null||journal==null||probe==null||sink==null)throw new IllegalArgumentException("LOCAL_STORE_REQUIRED");
        this.scope=scope;this.journal=journal;this.probe=probe;this.sink=sink;
    }
    public synchronized void beginExplicit(boolean retryApproved) {
        if(started!=null||ended)throw new IllegalStateException("LOCAL_FLOW_ALREADY_STARTED");
        requireEmpty();started=journal.begin(retryApproved);
    }
    private void requireEmpty() {
        AccountProbe.Snapshot s;
        try{s=probe.inspect();}catch(RuntimeException|LinkageError failure){throw new IllegalStateException("ACCOUNT_INSPECTION_UNAVAILABLE");}
        if(s==null||!scope.equals(s.scope)||!s.controllerHandlesAvailable||s.evidence!=AccountProbe.Evidence.EMPTY)
            throw new IllegalStateException("ACCOUNT_NOT_PROVEN_EMPTY");
    }
    @Override public synchronized StoreSnapshot inspect(SessionScope requested) {
        requireScope(requested);
        if(started==null||ended)throw new IllegalStateException("LOCAL_OPERATION_NOT_ACTIVE");
        requireEmpty();if(!journal.inspect().equals(started))throw new IllegalStateException("OPERATION_CHANGED");
        return new StoreSnapshot(scope,started.revision,false);
    }
    @Override public synchronized Commit commitLocalIfEmpty(SessionScope requested,long expected,char[] material) {
        requireScope(requested);
        if(material==null||material.length==0||material.length>4096)throw new IllegalArgumentException("LOCAL_MATERIAL_REQUIRED");
        if(started==null||ended||committing||expected!=started.revision)return Commit.CONFLICT;
        requireEmpty();committing=true;
        char[] copy=material.clone();
        try {
            journal.move(Phase.WRITING);
            Outcome result;
            try{result=sink.commitSynthetic(scope,copy);}catch(RuntimeException|LinkageError failure){result=Outcome.UNCERTAIN;}
            if(result==Outcome.COMPLETED){journal.move(Phase.COMPLETED);return Commit.COMMITTED;}
            if(result==Outcome.FAILED_WITHOUT_WRITE){journal.move(Phase.FAILED);return Commit.CONFLICT;}
            journal.move(Phase.UNCERTAIN);return null;
        } finally {
            Arrays.fill(copy,'\0');committing=false;ended=true;
            // Never replace a write outcome with cancellation, rollback or retry.
            if(closeRequested)close();
        }
    }
    private void requireScope(SessionScope requested) {
        if(!scope.equals(requested))throw new IllegalArgumentException("ACCOUNT_SCOPE_MISMATCH");
    }
    @Override public synchronized void close() {
        if(committing){closeRequested=true;return;}
        if(!ended&&started!=null){ended=true;journal.move(Phase.CANCELLED);}
        ended=true;
    }
}
