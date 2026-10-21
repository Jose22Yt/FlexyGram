package org.telegram.messenger;

import android.content.Context;
import android.util.AtomicFile;
import java.io.*;
import java.nio.charset.StandardCharsets;

/** Opt-in exact identity. No-op in Debug realAlpha, Diagnostic, Beta and Production. */
public final class StartupTrace {
    public enum Stage {
        PROBE_REQUESTED, APPLICATION_ATTACH, APPLICATION_ENTER, APPLICATION_RETURN,
        APP_NATIVE_BEGIN, APP_NATIVE_RETURN, APP_NATIVE_JAVA_RETURN,
        REAL_ALPHA_ENTER, POLICY_BEGIN, POLICY_RETURN, ACCOUNTS_BEFORE, POST_INIT_BEGIN,
        LOCALE_RETURN, CONFIG_BEGIN, GLYPH_BEGIN, GLYPH_RETURN, PLUGINS_BEGIN,
        CONTROLLERS_BEGIN, CONTROLLERS_RETURN, MEDIA_BEGIN, POST_INIT_RETURN,
        ACCOUNTS_AFTER, BOOTSTRAP_READY, LAUNCH_BEGIN, LAUNCH_ENTER,
        LAUNCH_FRAMEWORK_RETURN, DIALOGS_FACTORY, DIALOGS_FRAGMENT_BEGIN,
        DIALOGS_VIEW_BEGIN, DIALOGS_VIEW_RETURN, LAUNCH_RETURN, ACTIVITY_RESUMED,
        FIRST_DRAW, ACTIVITY_DESTROYED, ACTIVITY_FINISHING
    }
    private static Context context;
    private static final int MAX_BYTES = 16384;
    private StartupTrace() {}
    public static boolean enabled() {
        return "realAlpha".equals(BuildConfig.FLEXYGRAM_VARIANT)
                && "startupDiagnostic".equals(BuildConfig.BUILD_TYPE)
                && "io.github.jose22yt.flexygram.realalpha.startupdiagnostic".equals(BuildConfig.APPLICATION_ID)
                && BuildConfig.ISOLATED_DIAGNOSTIC && BuildConfig.APP_ID == 0
                && "".equals(BuildConfig.APP_HASH)
                && !BuildConfig.FLEXYGRAM_CAP_AUTHENTICATION && !BuildConfig.FLEXYGRAM_CAP_TELEGRAMTRANSPORT
                && !BuildConfig.FLEXYGRAM_CAP_PUSH && !BuildConfig.FLEXYGRAM_CAP_TRANSLATION
                && !BuildConfig.FLEXYGRAM_CAP_PLUGINS && !BuildConfig.FLEXYGRAM_CAP_SESSIONRESTORE;
    }
    public static void attach(Context value) { if (enabled()) context = value; }
    private static AtomicFile file() throws IOException {
        File directory = context.getNoBackupFilesDir();
        if (directory == null || !directory.isDirectory()) throw new IOException("JOURNAL_UNAVAILABLE");
        return new AtomicFile(new File(directory, "startup-sanitized-v1.txt"));
    }
    public static synchronized void begin(Stage stage) { write(stage.name(), true); }
    public static synchronized void stage(Stage stage) { write(stage.name(), false); }
    public static synchronized void observed(Throwable error) {
        if (!enabled()) return;
        try { write("OBSERVED " + StartupFailureSanitizer.encode(error), false); } catch (Throwable ignored) {}
    }
    public static synchronized void failure(Throwable error) {
        if (!enabled()) return;
        try { write("ERROR " + StartupFailureSanitizer.encode(error), false); } catch (Throwable ignored) {}
    }
    public static synchronized String read() {
        if (!enabled() || context == null) return "NO_DIAGNOSTIC_CONTEXT";
        try {
            AtomicFile target = file();
            if (target.getBaseFile().length() > MAX_BYTES) return "INVALID_DIAGNOSTIC_LENGTH";
            byte[] bytes = target.readFully();
            if (bytes.length > MAX_BYTES) return "INVALID_DIAGNOSTIC_LENGTH";
            String text = new String(bytes, StandardCharsets.US_ASCII);
            if (!text.matches("[A-Z0-9_ @:;=\\n-]*")) return "INVALID_DIAGNOSTIC_CONTENT";
            return text;
        } catch (Exception ignored) { return "NO_STAGE_RECORD"; }
    }
    private static void write(String line, boolean reset) {
        if (!enabled() || context == null) return;
        FileOutputStream stream = null;
        AtomicFile target = null;
        try {
            target = file();
            String before = reset ? "" : read();
            if (before.startsWith("NO_") || before.startsWith("INVALID_")) before = "";
            String text = before + line + "\n";
            if (text.length() > MAX_BYTES) text = text.substring(text.indexOf('\n', text.length() - MAX_BYTES) + 1);
            stream = target.startWrite();
            stream.write(text.getBytes(StandardCharsets.US_ASCII));
            target.finishWrite(stream);
        } catch (Throwable ignored) {
            if (stream != null && target != null) {
                try { target.failWrite(stream); } catch (Throwable ignoredAgain) {}
            }
        }
    }
}
