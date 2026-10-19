package tw.nekomimi.nekogram.translate.source.fallback;

import tw.nekomimi.nekogram.translate.TranslationServicesPolicy;
import app.nekogram.translator.DeepLTranslator;

public class DeepLTranslatorNeko {

    public static String translate(String text, String from, String to) throws Exception {
        TranslationServicesPolicy.requireRoute(TranslationServicesPolicy.Route.DEEPL_LIBRARY);
        var translator = DeepLTranslator.getInstance();

        var result = translator.translate(text, from, to);
        return result.translation;
    }
}
