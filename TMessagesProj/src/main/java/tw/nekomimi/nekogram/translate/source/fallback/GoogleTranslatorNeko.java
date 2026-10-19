package tw.nekomimi.nekogram.translate.source.fallback;

import tw.nekomimi.nekogram.translate.TranslationServicesPolicy;

/** Diagnostic compatibility entry point. Legacy transport is deliberately unavailable. */
public class GoogleTranslatorNeko {
    public static String translate(String text, String from, String to) throws Exception {
        TranslationServicesPolicy.requireRoute(TranslationServicesPolicy.Route.GOOGLE_LEGACY_LIBRARY);
        // Remains closed even if a future policy accidentally grants the legacy route.
        throw TranslationServicesPolicy.denied();
    }
}
