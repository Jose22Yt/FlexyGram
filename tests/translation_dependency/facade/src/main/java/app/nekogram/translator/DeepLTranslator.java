// FlexyGram laboratory facade — @Lukhou23. GPL-3.0; see repository LICENSE.
// Independent implementation against the recorded consumed ABI. Not wired into Android.
package app.nekogram.translator;

import java.util.List;
import java.util.Collections;
import java.util.Arrays;
import lab.flexygram.fixture.FixtureTransport;

public class DeepLTranslator extends BaseTranslator {
    private static final DeepLTranslator INSTANCE = new DeepLTranslator();
    private static final List<String> LANGUAGES = Collections.unmodifiableList(Arrays.asList(
            "ace", "af", "an", "ar", "as", "ay", "az", "ba",
            "be", "bg", "bho", "bn", "br", "bs", "ca", "ceb",
            "ckb", "cs", "cy", "da", "de", "de-DE", "el", "en",
            "en-GB", "en-US", "eo", "es", "es-419", "et", "eu", "fa",
            "fi", "fr", "fr-FR", "ga", "gl", "gn", "gom", "gu",
            "ha", "he", "hi", "hr", "ht", "hu", "hy", "id",
            "ig", "is", "it", "ja", "jv", "ka", "kk", "kmr",
            "ko", "ky", "la", "lb", "lmo", "ln", "lt", "lv",
            "mai", "mg", "mi", "mk", "ml", "mn", "mr", "ms",
            "mt", "my", "nb", "ne", "nl", "oc", "om", "pa",
            "pag", "pam", "pl", "prs", "ps", "pt", "pt-BR", "pt-PT",
            "qu", "ro", "ru", "sa", "scn", "sk", "sl", "sq",
            "sr", "st", "su", "sv", "sw", "ta", "te", "tg",
            "th", "tk", "tl", "tn", "tr", "ts", "tt", "uk",
            "ur", "uz", "vi", "wo", "xh", "yi", "yue", "zh",
            "zh-CN", "zh-TW", "zu"));
    private final FixtureEngine engine;

    public DeepLTranslator() {
        engine = new FixtureEngine(FixtureTransport.Provider.DEEPL, null, null);
    }

    /** Laboratory injection only. There is no network transport implementation. */
    public DeepLTranslator(FixtureTransport transport, FixtureTransport.Cancellation cancellation) {
        engine = new FixtureEngine(FixtureTransport.Provider.DEEPL, transport, cancellation);
    }

    public static DeepLTranslator getInstance() {
        return INSTANCE;
    }

    public List<String> getTargetLanguages() {
        return LANGUAGES;
    }

    protected final String convertLanguageCode(String code, boolean reverse) {
        return FixtureEngine.language(code, reverse);
    }

    protected final Result translateImpl(String text, String from, String to) {
        return engine.translate(text, from, to);
    }

    /** ABI retained, deliberately refuses every value; no JWT is stored or used. */
    public static void setJwt(String ignored) {
        throw new SecurityException("TRANSLATION_NOT_AUTHORIZED");
    }

}
