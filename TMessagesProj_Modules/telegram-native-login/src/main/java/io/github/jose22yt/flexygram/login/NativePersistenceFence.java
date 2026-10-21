package io.github.jose22yt.flexygram.login;

import java.util.EnumMap;
import io.github.jose22yt.flexygram.session.*;
import io.github.jose22yt.flexygram.session.AuthenticationController.*;
import io.github.jose22yt.flexygram.session.RequestCoordinator.Domain;
import io.github.jose22yt.flexygram.session.android.OperationJournal;
import io.github.jose22yt.flexygram.session.android.OperationJournal.Phase;

/** Metadata fence for ORIGINAL-format writers. No key format, file deletion or native writer supplied. */
public final class NativePersistenceFence implements AutoCloseable {
    public enum Artifact { USER_CONFIG, NATIVE_CONFIG, NATIVE_BACKUP, MESSAGE_DATABASE }
    public enum Presence { ABSENT, PRESENT, UNKNOWN }
    public enum Origin { ABSENT, PREEXISTING, OWNED_CURRENT_FLOW, UNPROVEN }
    public enum Outcome { COMPLETED, FAILED_WITHOUT_WRITE, UNCERTAIN }
    public static final class Stamp {
        public final Presence presence;
        private final String version;
        /** Opaque writer generation, NOT contents, keys, credentials or a user identifier. */
        public Stamp(Presence presence,String version) {
            if(presence==null||version==null||(presence==Presence.PRESENT?!version.matches("[a-f0-9]{32}"):!version.isEmpty()))
                throw new IllegalArgumentException("INVALID_ARTIFACT_METADATA");
            this.presence=presence;this.version=version;
        }
        public static Stamp absent(){return new Stamp(Presence.ABSENT,"");}
        @Override public boolean equals(Object o){return o instanceof Stamp&&presence==((Stamp)o).presence&&version.equals(((Stamp)o).version);}
        @Override public int hashCode(){return presence.hashCode()*31+version.hashCode();}
        @Override public String toString(){return "ArtifactMetadata["+presence+"]";}
    }
    public static final class Inventory {
        public final SessionScope scope;
        public final boolean authorizedAccount;
        private final EnumMap<Artifact,Stamp> stamps=new EnumMap<>(Artifact.class);
        public Inventory(SessionScope scope,boolean authorized,EnumMap<Artifact,Stamp> values) {
            if(scope==null||values==null||values.size()!=Artifact.values().length)throw new IllegalArgumentException("COMPLETE_INVENTORY_REQUIRED");
            for(Artifact artifact:Artifact.values()){Stamp stamp=values.get(artifact);if(stamp==null)throw new IllegalArgumentException("COMPLETE_INVENTORY_REQUIRED");stamps.put(artifact,stamp);}
            this.scope=scope;authorizedAccount=authorized;
        }
        public Stamp stamp(Artifact artifact){return stamps.get(artifact);}
        private boolean same(Inventory other){return scope.equals(other.scope)&&authorizedAccount==other.authorizedAccount&&stamps.equals(other.stamps);}
    }
    public interface InventoryPort {
        Domain domain();
        Inventory capture(SessionScope scope);
    }
    public interface LocalOriginalWrite {Report commit(Lease lease);}
    public static final class Receipt {
        private final Lease owner;
        private final Artifact artifact;
        private final Stamp before,after;
        private Receipt(Lease owner,Artifact artifact,Stamp before,Stamp after){this.owner=owner;this.artifact=artifact;this.before=before;this.after=after;}
        @Override public String toString(){return "OriginalWriteReceipt[REDACTED]";}
    }
    public static final class Report {
        public final Outcome outcome;
        private final Receipt[] receipts;
        public Report(Outcome outcome,Receipt... receipts) {
            if(outcome==null||receipts==null)throw new IllegalArgumentException("WRITE_REPORT_REQUIRED");
            this.outcome=outcome;this.receipts=receipts.clone();
        }
    }
    /** In-process ownership capability, not a grant for networking or native writes. */
    public final class Lease {
        private final String operation;
        private Lease(String operation){this.operation=operation;}
        public SessionScope scope(){return scope;}
        public String operationId(){return operation;}
        public Receipt witnessLocalWrite(Artifact artifact,Stamp before,Stamp after) {
            synchronized(NativePersistenceFence.this) {
                requireLease(this);
                if(artifact==null||before==null||after==null)throw new IllegalArgumentException("WRITE_METADATA_REQUIRED");
                return new Receipt(this,artifact,before,after);
            }
        }
        @Override public String toString(){return "OperationLease[REDACTED]";}
    }
    private final SessionScope scope;
    private final OperationJournal journal;
    private final InventoryPort port;
    private final EnumMap<Artifact,Stamp> owned=new EnumMap<>(Artifact.class);
    private Inventory baseline;
    private Lease lease;
    private long revision;
    private boolean active,committing,closeRequested,ended;
    public NativePersistenceFence(ClosedRuntime runtime,OperationJournal journal,InventoryPort port) {
        if(runtime==null||journal==null||port==null||runtime.scope.variant!=SessionScope.Variant.REAL_ALPHA)
            throw new IllegalArgumentException("NATIVE_PERSISTENCE_DEPENDENCIES_REQUIRED");
        scope=runtime.scope;this.journal=journal;this.port=port;
    }
    private Inventory capture() {
        try {
            if(port.domain()!=Domain.LOCAL_SIMULATION)throw new IllegalStateException();
            Inventory inventory=port.capture(scope);
            if(inventory==null||!scope.equals(inventory.scope))throw new IllegalStateException();
            for(Artifact artifact:Artifact.values())if(inventory.stamp(artifact).presence==Presence.UNKNOWN)throw new IllegalStateException();
            return inventory;
        }catch(RuntimeException|LinkageError failure){throw new IllegalStateException("ORIGINAL_INVENTORY_UNAVAILABLE");}
    }
    public synchronized Lease beginExplicit(boolean retryApproved) {
        if(active||ended)throw new IllegalStateException("OPERATION_ALREADY_STARTED");
        Inventory inventory=capture();
        if(inventory.authorizedAccount||inventory.stamp(Artifact.USER_CONFIG).presence!=Presence.ABSENT
                ||inventory.stamp(Artifact.NATIVE_CONFIG).presence!=Presence.ABSENT||inventory.stamp(Artifact.NATIVE_BACKUP).presence!=Presence.ABSENT)
            throw new IllegalStateException("PREEXISTING_AUTH_STATE_REQUIRES_REVIEW");
        OperationJournal.Record row=journal.begin(retryApproved);
        baseline=inventory;revision=row.revision;lease=new Lease(row.operation);active=true;return lease;
    }
    public synchronized Lease currentLease(){requireLease(lease);return lease;}
    private void requireLease(Lease requested) {
        if(!active||ended||requested==null||requested!=lease)throw new IllegalStateException("OPERATION_OWNERSHIP_REJECTED");
    }
    public synchronized void recordLocalWrite(Lease requested,Receipt receipt) {
        requireLease(requested);
        if(receipt==null||receipt.owner!=lease)throw new IllegalStateException("FOREIGN_WRITE_RECEIPT");
        Stamp expected=owned.containsKey(receipt.artifact)?owned.get(receipt.artifact):baseline.stamp(receipt.artifact);
        if(!expected.equals(receipt.before))throw new IllegalStateException("WRITE_RECEIPT_CHAIN_MISMATCH");
        owned.put(receipt.artifact,receipt.after);
    }
    public synchronized Origin origin(Artifact artifact,Inventory inventory) {
        if(baseline==null||inventory==null||!scope.equals(inventory.scope))throw new IllegalStateException("INVENTORY_SCOPE_REJECTED");
        Stamp before=baseline.stamp(artifact),now=inventory.stamp(artifact);
        if(before.presence==Presence.PRESENT)return Origin.PREEXISTING;
        if(now.presence==Presence.ABSENT)return Origin.ABSENT;
        return now.presence==Presence.PRESENT&&now.equals(owned.get(artifact))?Origin.OWNED_CURRENT_FLOW:Origin.UNPROVEN;
    }
    private void validateChanges(Inventory inventory) {
        for(Artifact artifact:Artifact.values()) {
            Stamp before=baseline.stamp(artifact),now=inventory.stamp(artifact);
            // A scoped DB transaction may update an existing DB, but its origin stays PREEXISTING.
            if(before.presence==Presence.PRESENT&&!before.equals(now)
                    &&(artifact!=Artifact.MESSAGE_DATABASE||!now.equals(owned.get(artifact))))
                throw new IllegalStateException("PREEXISTING_ARTIFACT_CHANGED");
            if(before.presence!=Presence.PRESENT&&!before.equals(now)&&!now.equals(owned.get(artifact)))throw new IllegalStateException("UNOWNED_ARTIFACT_CHANGED");
        }
    }
    public synchronized StoreSnapshot inspect(SessionScope requested) {
        if(!scope.equals(requested))throw new IllegalArgumentException("ACCOUNT_SCOPE_MISMATCH");
        requireLease(lease);Inventory current=capture();validateChanges(current);
        OperationJournal.Record row=journal.inspect();
        if(current.authorizedAccount||row.revision!=revision||row.phase!=Phase.STARTED||!row.operation.equals(lease.operation))
            throw new IllegalStateException("ACCOUNT_OR_OPERATION_CHANGED");
        return new StoreSnapshot(scope,revision,false);
    }
    public synchronized Commit commitLocal(Lease requested,long expected,LocalOriginalWrite writer) {
        requireLease(requested);
        if(writer==null||committing||expected!=revision)return Commit.CONFLICT;
        Inventory before=capture();validateChanges(before);
        if(before.authorizedAccount)throw new IllegalStateException("ACCOUNT_APPEARED_BEFORE_COMMIT");
        committing=true;
        try {
            journal.move(Phase.WRITING);
            Report report;
            try{report=port.domain()==Domain.LOCAL_SIMULATION?writer.commit(lease):null;}
            catch(RuntimeException|LinkageError failure){report=null;}
            Inventory after;
            try {
                after=capture();
                if(report!=null)for(Receipt receipt:report.receipts)recordLocalWrite(lease,receipt);
                validateChanges(after);
            } catch(RuntimeException|LinkageError failure){return uncertain();}
            if(report!=null&&report.outcome==Outcome.FAILED_WITHOUT_WRITE&&before.same(after)) {
                journal.move(Phase.FAILED);return Commit.CONFLICT;
            }
            if(report!=null&&report.outcome==Outcome.COMPLETED&&after.authorizedAccount
                    &&origin(Artifact.USER_CONFIG,after)==Origin.OWNED_CURRENT_FLOW
                    &&origin(Artifact.NATIVE_CONFIG,after)==Origin.OWNED_CURRENT_FLOW
                    &&after.stamp(Artifact.MESSAGE_DATABASE).presence==Presence.PRESENT
                    &&after.stamp(Artifact.MESSAGE_DATABASE).equals(owned.get(Artifact.MESSAGE_DATABASE))) {
                journal.move(Phase.COMPLETED);return Commit.COMMITTED;
            }
            return uncertain();
        } finally {
            committing=false;active=false;ended=true;
            if(closeRequested)close();
        }
    }
    private Commit uncertain() {
        try{journal.move(Phase.UNCERTAIN);}catch(RuntimeException|LinkageError unavailable){/* WRITING remains a review barrier. */}
        return null;
    }
    @Override public synchronized void close() {
        if(committing){closeRequested=true;return;}
        if(active&&!ended){active=false;ended=true;journal.move(Phase.CANCELLED);}
        active=false;ended=true;
    }
}
