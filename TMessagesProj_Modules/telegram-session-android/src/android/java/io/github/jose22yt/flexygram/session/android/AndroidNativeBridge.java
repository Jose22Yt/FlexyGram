package io.github.jose22yt.flexygram.session.android;
import android.content.Context;
import android.os.Process;
import org.telegram.messenger.BuildConfig;
import io.github.jose22yt.flexygram.session.SessionScope;

/** No library loading, native account initialization or tgnet operation. */
public final class AndroidNativeBridge {
    private AndroidNativeBridge(){}
    private static native String nativePolicy();
    private static native long[] nativeIdentity(int account);
    public static ReadOnlyAttestation read(Context context,int account) {
        try{
            SessionScope scope=SessionScope.of(BuildConfig.FLEXYGRAM_VARIANT,context.getPackageName(),account);
            if(scope.variant!=SessionScope.Variant.REAL_ALPHA||!BuildConfig.ISOLATED_DIAGNOSTIC
                    ||BuildConfig.APP_ID!=0||BuildConfig.APP_HASH==null||!BuildConfig.APP_HASH.isEmpty())throw new IllegalStateException();
            return ReadOnlyAttestation.verify(scope,context.getPackageName(),BuildConfig.FLEXYGRAM_POLICY_SCOPE,
                BuildConfig.ISOLATED_DIAGNOSTIC,new boolean[]{BuildConfig.FLEXYGRAM_CAP_AUTHENTICATION,
                BuildConfig.FLEXYGRAM_CAP_TELEGRAMTRANSPORT,BuildConfig.FLEXYGRAM_CAP_PUSH,BuildConfig.FLEXYGRAM_CAP_TRANSLATION,
                BuildConfig.FLEXYGRAM_CAP_PLUGINS,BuildConfig.FLEXYGRAM_CAP_SESSIONRESTORE},0,new char[0],nativePolicy(),nativeIdentity(account),Process.myPid(),Process.myUid());
        }catch(RuntimeException|LinkageError failure){throw new IllegalStateException("READ_ONLY_JNI_ATTESTATION_UNAVAILABLE");}
    }
}
