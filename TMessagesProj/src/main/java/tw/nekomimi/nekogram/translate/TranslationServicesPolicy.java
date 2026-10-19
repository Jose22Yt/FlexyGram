package tw.nekomimi.nekogram.translate;

import org.telegram.messenger.DiagnosticPolicy;

/** Fail-closed execution boundary. Preferences are selections, never service grants.
 * No provider has an approved grant/resolver in this version. Enabling a future
 * integration requires a separately reviewed policy change, not a runtime flag.
 */
public final class TranslationServicesPolicy {
    private TranslationServicesPolicy() {}

    public enum Route {
        GOOGLE_DISPATCH, GOOGLE_LEGACY_PA, GOOGLE_LEGACY_LIBRARY,
        GOOGLE_LEGACY_WEB, GOOGLE_CLOUD, LLM, YANDEX, LINGO,
        MICROSOFT, MICROSOFT_LIBRARY, DEEPL, DEEPL_LIBRARY, TELEGRAM, TRANSMART
    }

    public static boolean isProviderAuthorized(int provider) {
        // Immutable Diagnostic and default-deny for unknown/unconfigured variants.
        // Deliberately no preference, API key presence or experimental flag grants access.
        return false;
    }

    public static void requireProvider(int provider) {
        if (!isProviderAuthorized(provider)) throw denied();
    }

    public static void requireRoute(Route route) {
        // Even direct calls bypassing Translator must pass this boundary before
        // building a request, reading private configuration or initializing an SDK.
        throw denied();
    }

    public static int bulkProvider(int provider) {
        // Capacity selection must not silently remap DeepL to Google.
        return provider;
    }

    public static SecurityException denied() {
        return new SecurityException(DiagnosticPolicy.isIsolated()
                ? "TRANSLATION_DIAGNOSTIC_DISABLED" : "TRANSLATION_PROVIDER_NOT_AUTHORIZED");
    }

    public static String safeErrorCode(Throwable error) {
        // Never inspect message/toString/cause, which may contain text, URLs or keys.
        if (error instanceof SecurityException) return "TRANSLATION_NOT_AUTHORIZED";
        if (error instanceof UnsupportedOperationException) return "TRANSLATION_UNSUPPORTED";
        return "TRANSLATION_FAILED";
    }

    public static RuntimeException safeFailure(Throwable error) {
        // Drop the original exception and its cause rather than wrapping private data.
        String code = safeErrorCode(error);
        if (error instanceof SecurityException) return new SecurityException(code);
        if (error instanceof UnsupportedOperationException) return new UnsupportedOperationException(code);
        return new IllegalStateException(code);
    }
}
