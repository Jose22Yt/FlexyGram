// FlexyGram read-only seam. Original Telegram/Exteraless source and GPL notices are unchanged.
#include <jni.h>
#include <unistd.h>
#include "DiagnosticPolicy.h"
extern "C" const char *flexygram_variant_policy();
static_assert(flexygram::isolatedDiagnostic && !flexygram::authenticationAllowed
    && !flexygram::telegramTransportAllowed && !flexygram::pushAllowed && !flexygram::translationAllowed
    && !flexygram::pluginsAllowed && !flexygram::sessionRestoreAllowed,"READ_ONLY_BRIDGE_REQUIRES_CLOSED_POLICY");
extern "C" JNIEXPORT jstring JNICALL
Java_io_github_jose22yt_flexygram_session_android_AndroidNativeBridge_nativePolicy(JNIEnv *env,jclass){
    return env->NewStringUTF(flexygram_variant_policy());
}
extern "C" JNIEXPORT jlongArray JNICALL
Java_io_github_jose22yt_flexygram_session_android_AndroidNativeBridge_nativeIdentity(JNIEnv *env,jclass,jint account){
    if(account<0||account>=10){jclass error=env->FindClass("java/lang/IllegalArgumentException");if(error)env->ThrowNew(error,"INVALID_ACCOUNT_SLOT");return nullptr;}
    // schema,pid,uid,slot,isolation,capability mask. No native singleton or initialization is accessed.
    const jlong values[]={1,static_cast<jlong>(getpid()),static_cast<jlong>(getuid()),account,1,0};
    jlongArray array=env->NewLongArray(6);if(array)env->SetLongArrayRegion(array,0,6,values);return array;
}
