package tw.nekomimi.nekogram.translate.source.fallback;

import tw.nekomimi.nekogram.translate.TranslationServicesPolicy;
import app.nekogram.translator.GoogleAppTranslator;

public class GoogleTranslatorNeko {

    public static String translate(String text, String from, String to) throws Exception {
        TranslationServicesPolicy.requireRoute(TranslationServicesPolicy.Route.GOOGLE_LEGACY_LIBRARY);
        var translator = GoogleAppTranslator.getInstance();

        var result = translator.translate(text, from, to);
        return result.translation;
    }
}
