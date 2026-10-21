package org.telegram.messenger;

/** No messages, filenames, paths, thread names, values or arbitrary class/method names. */
public final class StartupFailureSanitizer {
    private StartupFailureSanitizer() {}
    public static String encode(Throwable failure) {
        StringBuilder out = new StringBuilder();
        Throwable current = failure;
        for (int depth = 0; current != null && depth < 6; depth++) {
            if (depth > 0) out.append(";");
            out.append("CAUSE=").append(depth).append(":").append(kind(current));
            int kept = 0;
            for (StackTraceElement frame : current.getStackTrace()) {
                String owner = owner(frame.getClassName());
                if (owner == null) continue;
                out.append("@").append(owner).append(":")
                        .append(Math.max(-1, Math.min(1000000, frame.getLineNumber())));
                if (++kept == 8) break;
            }
            Throwable next = current.getCause();
            if (next == current) break;
            current = next;
        }
        return out.length() == 0 ? "CAUSE=0:NONE" : out.toString();
    }
    private static String kind(Throwable t) {
        if (t instanceof UnsatisfiedLinkError) return "UNSATISFIED_LINK";
        if (t instanceof NoClassDefFoundError) return "CLASS_NOT_FOUND";
        if (t instanceof ExceptionInInitializerError) return "CLASS_INITIALIZER";
        if (t instanceof VerifyError) return "VERIFY_ERROR";
        if (t instanceof LinkageError) return "LINKAGE_ERROR";
        if (t instanceof NullPointerException) return "NULL_POINTER";
        if (t instanceof SecurityException) return "SECURITY";
        if (t instanceof IllegalStateException) return "ILLEGAL_STATE";
        if (t instanceof IllegalArgumentException) return "ILLEGAL_ARGUMENT";
        if (t instanceof OutOfMemoryError) return "OUT_OF_MEMORY";
        if (t instanceof StackOverflowError) return "STACK_OVERFLOW";
        String name = t.getClass().getName();
        if (name.equals("android.content.res.Resources$NotFoundException")) return "RESOURCE_NOT_FOUND";
        if (name.equals("android.database.sqlite.SQLiteException")) return "SQLITE";
        if (t instanceof RuntimeException) return "OTHER_RUNTIME";
        if (t instanceof Error) return "OTHER_ERROR";
        return "OTHER_EXCEPTION";
    }
    private static String owner(String name) {
        switch (name) {
            case "org.telegram.messenger.ApplicationLoader": return "APPLICATION";
            case "org.telegram.messenger.NativeLoader": return "NATIVE_LOADER";
            case "org.telegram.ui.realalpha.RealAlphaBootstrap": return "BOOTSTRAP";
            case "org.telegram.ui.realalpha.RealAlphaActivity": return "REAL_ALPHA";
            case "org.telegram.ui.LaunchActivity": return "LAUNCH";
            case "org.telegram.ui.DialogsActivity": return "DIALOGS";
            case "org.telegram.messenger.MessagesController": return "MESSAGES";
            case "org.telegram.messenger.MessagesStorage": return "STORAGE";
            case "org.telegram.tgnet.ConnectionsManager": return "CONNECTIONS";
            case "app.exteraless.glyph.GlyphController": return "GLYPH";
            default: return null;
        }
    }
}
