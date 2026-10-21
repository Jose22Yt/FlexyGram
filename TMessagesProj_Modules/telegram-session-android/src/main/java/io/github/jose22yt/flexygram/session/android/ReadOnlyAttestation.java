package io.github.jose22yt.flexygram.session.android;
import io.github.jose22yt.flexygram.session.*;

/** Coherence evidence, not authorization or a sandbox against malicious in-process code. */
public final class ReadOnlyAttestation {
    public enum Availability { AVAILABLE, UNKNOWN }
    public final ClosedRuntime runtime;
    public final Availability linkedBridge=Availability.AVAILABLE;
    public final Availability nativeEngineInitialized=Availability.UNKNOWN;
    private ReadOnlyAttestation(ClosedRuntime runtime){this.runtime=runtime;}
    public static ReadOnlyAttestation verify(SessionScope scope,String packageName,String policyScope,
            boolean isolated,boolean[] capabilities,int apiId,char[] apiHash,String statement,
            long[] identity,int javaPid,int javaUid) {
        if(scope==null||scope.variant!=SessionScope.Variant.REAL_ALPHA||!scope.variant.applicationId.equals(packageName)
                ||identity==null||identity.length!=6||identity[0]!=1||javaPid<=0||javaUid<0
                ||identity[1]!=javaPid||identity[2]!=javaUid||identity[3]!=scope.account||identity[4]!=1||identity[5]!=0)
            throw new IllegalStateException("NATIVE_IDENTITY_OR_CAPABILITY_MISMATCH");
        return new ReadOnlyAttestation(ClosedRuntime.verify(scope,policyScope,isolated,capabilities,apiId,apiHash,statement));
    }
}
