package org.telegram.ui.beta;

import android.content.Context;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import org.telegram.messenger.NativeLoader;

final class LocalPythonProbe {
    private LocalPythonProbe() { }
    static boolean run(Context application) {
        try {
            if (!NativeLoader.loaded()) return false;
            synchronized (Python.class) {
                if (!Python.isStarted()) Python.start(new AndroidPlatform(application));
            }
            Python.getInstance().getModule("sys");
            return true;
        } catch (Exception | LinkageError error) {
            return false; // no private paths, exceptions or Python tracebacks in output
        }
    }
}
