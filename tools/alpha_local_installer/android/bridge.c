#include <jni.h>
#include <unistd.h>
#include "libdelivery.h"

JNIEXPORT jint JNICALL
Java_io_github_jose22yt_flexygram_delivery_MainActivity_decryptNative(
    JNIEnv *env, jclass clazz, jint cipher, jint identity, jstring directory) {
    (void)clazz;
    const char *path = (*env)->GetStringUTFChars(env, directory, NULL);
    if (path == NULL) { close(cipher); close(identity); return 3; }
    int result = DecryptDelivery(cipher, identity, (char *)path);
    (*env)->ReleaseStringUTFChars(env, directory, path);
    return result;
}
