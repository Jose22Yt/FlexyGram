// FlexyGram — @Lukhou23. GPL-3.0; see repository LICENSE.
package app.nekogram.translator;
final class LanguageCodes {
    private LanguageCodes() {}
    static String convert(String code, boolean reverse) {
        if (reverse) {
            if ("zh-Hans".equals(code)) return "zh-CN";
            if ("zh-Hant".equals(code)) return "zh-TW";
        } else {
            if ("zh-CN".equals(code)) return "zh-Hans";
            if ("zh-TW".equals(code)) return "zh-Hant";
        }
        return code;
    }
}
