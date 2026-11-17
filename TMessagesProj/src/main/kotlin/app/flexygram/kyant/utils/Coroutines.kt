package app.flexygram.kyant.utils

/** Android implementation of the catalog's expect/actual frame awaiter. */
suspend fun awaitFrame() {
    kotlinx.coroutines.android.awaitFrame()
}
