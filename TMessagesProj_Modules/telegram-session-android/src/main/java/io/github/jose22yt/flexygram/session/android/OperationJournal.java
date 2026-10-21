package io.github.jose22yt.flexygram.session.android;
import java.util.UUID;
import io.github.jose22yt.flexygram.session.SessionScope;

/** Operation metadata, NEVER a Telegram session/key format. No credential fields or deletion API. */
public final class OperationJournal {
    public enum Phase { NONE, STARTED, WRITING, COMPLETED, FAILED, UNCERTAIN, CANCELLED }
    public enum Recovery { EMPTY, ACTIVE_OR_INTERRUPTED, WRITE_UNCERTAIN, LOCAL_RECEIPT, KNOWN_FAILED, CANCELLED }
    public interface Backend {
        Record read(SessionScope scope);
        /** Durable exact-record CAS. An exception may mean the write happened. */
        boolean compareAndSet(Record expected, Record replacement);
    }
    public static final class Record {
        public final SessionScope scope;
        public final long revision;
        public final String operation;
        public final Phase phase;
        public Record(SessionScope scope,long revision,String operation,Phase phase) {
            if(scope==null || revision<0 || phase==null || operation==null
                    || (phase==Phase.NONE ? revision!=0 || !operation.isEmpty()
                    : revision==0 || !operation.matches("[a-f0-9]{32}")))
                throw new IllegalArgumentException("INVALID_JOURNAL_RECORD");
            this.scope=scope; this.revision=revision; this.operation=operation; this.phase=phase;
        }
        public static Record empty(SessionScope scope) { return new Record(scope,0,"",Phase.NONE); }
        public Recovery recovery() {
            switch(phase) {
                case NONE:return Recovery.EMPTY;
                case STARTED:return Recovery.ACTIVE_OR_INTERRUPTED;
                case WRITING:case UNCERTAIN:return Recovery.WRITE_UNCERTAIN;
                case COMPLETED:return Recovery.LOCAL_RECEIPT;
                case FAILED:return Recovery.KNOWN_FAILED;
                default:return Recovery.CANCELLED;
            }
        }
        @Override public boolean equals(Object other) {
            if(!(other instanceof Record))return false;Record r=(Record)other;
            return scope.equals(r.scope)&&revision==r.revision&&operation.equals(r.operation)&&phase==r.phase;
        }
        @Override public int hashCode(){return scope.hashCode()*31+(int)(revision^(revision>>>32));}
        @Override public String toString(){return "OperationMetadata["+phase+","+revision+"]";}
    }
    private final Backend backend;
    private final SessionScope scope;
    private Record owned;
    public OperationJournal(Backend backend,SessionScope scope) {
        if(backend==null||scope==null)throw new IllegalArgumentException("JOURNAL_REQUIRED");
        this.backend=backend;this.scope=scope;
    }
    public synchronized Record inspect() {
        try { Record r=backend.read(scope);if(r==null||!scope.equals(r.scope))throw new IllegalStateException();return r; }
        catch(RuntimeException|LinkageError failure){throw unavailable();}
    }
    /** Explicit retry accepts only known FAILED/CANCELLED. Never auto-resumes interrupted/uncertain writes. */
    public synchronized Record begin(boolean explicitRetry) {
        if(owned!=null)throw new IllegalStateException("FLOW_ALREADY_OWNS_OPERATION");
        Record old=inspect();
        if(old.phase!=Phase.NONE&&!(explicitRetry&&(old.phase==Phase.FAILED||old.phase==Phase.CANCELLED)))
            throw new IllegalStateException("OPERATION_REVIEW_REQUIRED");
        Record next=new Record(scope,increment(old.revision),UUID.randomUUID().toString().replace("-",""),Phase.STARTED);
        replace(old,next);owned=next;return next;
    }
    public synchronized Record move(Phase phase) {
        if(owned==null||!allowed(owned.phase,phase))throw new IllegalStateException("INVALID_OPERATION_TRANSITION");
        Record next=new Record(scope,increment(owned.revision),owned.operation,phase);
        replace(owned,next);owned=next;return next;
    }
    private static boolean allowed(Phase from,Phase to) {
        return from==Phase.STARTED&&(to==Phase.WRITING||to==Phase.FAILED||to==Phase.CANCELLED)
                ||from==Phase.WRITING&&(to==Phase.COMPLETED||to==Phase.FAILED||to==Phase.UNCERTAIN);
    }
    private static long increment(long n) {
        if(n==Long.MAX_VALUE)throw new IllegalStateException("JOURNAL_REVISION_EXHAUSTED");return n+1;
    }
    private void replace(Record old,Record next) {
        try{if(!backend.compareAndSet(old,next))throw new IllegalStateException();}
        catch(RuntimeException|LinkageError failure){owned=null;throw unavailable();}
    }
    private static IllegalStateException unavailable(){return new IllegalStateException("JOURNAL_UNAVAILABLE_OR_CHANGED");}
}
