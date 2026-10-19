// FlexyGram Diagnostic compatibility facade — @Lukhou23. GPL-3.0; see repository LICENSE.
// Independent implementation against the consumed ABI. Diagnostic only; no transport.
package app.nekogram.translator;

import java.util.List;
import java.util.Collections;
import java.util.Arrays;

public class MicrosoftTranslator extends BaseTranslator {
    private static final MicrosoftTranslator INSTANCE = new MicrosoftTranslator();
    private static final List<String> LANGUAGES = Collections.unmodifiableList(Arrays.asList(
            "bho", "brx", "hne", "lzh", "doi", "en-GB", "lug", "ikt",
            "iu-Latn", "ks", "gom", "mn-Cyrl", "mn-Mong", "nya", "run", "st",
            "nso", "tn", "hsb", "dsb", "zh-CN", "zh-TW", "da", "uk",
            "uz", "ur", "nb", "hy", "ig", "ru", "bg", "sd",
            "si", "tlh-Latn", "hr", "otq", "is", "gl", "ca", "hu",
            "af", "kn", "rw", "hi", "id", "gu", "kk", "iu",
            "tk", "tr", "ty", "sr-Latn", "sr-Cyrl", "or", "cy", "bn",
            "yua", "ne", "ba", "eu", "he", "el", "ku", "kmr",
            "de", "it", "lv", "cs", "ti", "fj", "sk", "sl",
            "sw", "pa", "ja", "ps", "ln", "ky", "ka", "mi",
            "to", "fo", "fr", "fr-CA", "pl", "bs", "fa", "te",
            "ta", "th", "ht", "ga", "et", "sv", "zu", "xh",
            "lt", "yue", "so", "yo", "sn", "ug", "my", "ro",
            "lo", "fi", "mww", "en", "nl", "fil", "sm", "pt",
            "pt-PT", "bo", "es", "ha", "vi", "prs", "mai", "dv",
            "az", "am", "sq", "ar", "as", "tt", "ko", "mk",
            "mg", "mr", "ml", "ms", "mt", "km"));
    public MicrosoftTranslator() {}

    public static MicrosoftTranslator getInstance() {
        return INSTANCE;
    }

    public List<String> getTargetLanguages() {
        return LANGUAGES;
    }

    protected final String convertLanguageCode(String code, boolean reverse) {
        return LanguageCodes.convert(code, reverse);
    }

    protected final Result translateImpl(String text, String from, String to) {
        throw new SecurityException("TRANSLATION_DIAGNOSTIC_DISABLED");
    }

}
