package org.telegram.ui.beta;

import android.content.Context;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import org.telegram.messenger.NativeLoader;

final class LocalPythonProbe {
    private LocalPythonProbe() { }
    // Keep the original internal boolean contract for the original Activity regression harness.
    static boolean run(Context application) { return inspect(application) == ProbeState.Outcome.READY; }
    static ProbeState.Outcome inspect(Context application) {
        try {
            if (!NativeLoader.loaded()) return ProbeState.Outcome.JNI_UNAVAILABLE;
        } catch (RuntimeException | LinkageError unavailable) {
            return ProbeState.Outcome.JNI_UNAVAILABLE;
        }
        try {
            synchronized (Python.class) {
                if (!Python.isStarted()) Python.start(new AndroidPlatform(application));
            }
        } catch (Exception | LinkageError startFailed) {
            return ProbeState.Outcome.PYTHON_START_FAILED;
        }
        try {
            Python.getInstance().getModule("sys");
            return ProbeState.Outcome.READY;
        } catch (Exception | LinkageError importFailed) {
            return ProbeState.Outcome.PYTHON_IMPORT_FAILED;
        }
        // Stage enums only: never expose exception text, private paths or Python tracebacks.
    }
}
