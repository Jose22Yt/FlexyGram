// FlexyGram laboratory facade — @Lukhou23. GPL-3.0; see repository LICENSE.
// Independent implementation against the recorded consumed ABI. Not wired into Android.
package app.nekogram.translator;

import com.google.gson.Gson;
import java.util.List;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

public abstract class BaseTranslator {
    // ABI compatibility only; Gson is already a production dependency.
    protected static final Gson a = new Gson();

    public BaseTranslator() {}

    // Legacy protected helper, not a credential or a new security primitive.
    protected static String a(String value) {
        try {
            byte[] bytes = MessageDigest.getInstance("MD5").digest(value.getBytes());
            StringBuilder out = new StringBuilder();
            for (byte b : bytes) {
                out.append(Integer.toHexString((b & 255) | 256).substring(1, 3));
            }
            return out.toString();
        } catch (NoSuchAlgorithmException error) {
            return null;
        }
    }

    public final Result translate(String text, String from, String to) throws Exception {
        Result result = translateImpl(text, convertLanguageCode(from, false),
                convertLanguageCode(to, false));
        return Result.of(result.translation, convertLanguageCode(result.sourceLanguage, true));
    }

    protected abstract Result translateImpl(String text, String from, String to) throws Exception;

    protected Result[] translateImpl(String[] text, String from, String to) throws Exception {
        Result[] out = new Result[text.length];
        for (int i = 0; i < text.length; i++) {
            out[i] = translateImpl(text[i], from, to);
        }
        return out;
    }

    public abstract List<String> getTargetLanguages();

    protected String convertLanguageCode(String code, boolean reverse) {
        return code;
    }

    public final boolean supportLanguage(String code) {
        return getTargetLanguages().contains(code);
    }
}
