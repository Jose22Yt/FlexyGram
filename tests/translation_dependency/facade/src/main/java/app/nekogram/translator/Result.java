// FlexyGram laboratory facade — @Lukhou23. GPL-3.0; see repository LICENSE.
// Independent implementation against the recorded consumed ABI. Not wired into Android.
package app.nekogram.translator;

import java.util.Objects;

public final class Result {
    public final String translation;
    public final String sourceLanguage;

    Result(String translation, String sourceLanguage) {
        this.translation = translation;
        this.sourceLanguage = sourceLanguage;
    }

    public static Result of(String translation, String sourceLanguage) {
        return new Result(translation, sourceLanguage);
    }

    @Override
    public final boolean equals(Object other) {
        if (!(other instanceof Result)) return false;
        Result result = (Result) other;
        return Objects.equals(translation, result.translation)
                && Objects.equals(sourceLanguage, result.sourceLanguage);
    }

    @Override
    public final int hashCode() {
        return Objects.hashCode(translation) ^ Objects.hashCode(sourceLanguage);
    }

    @Override
    public final String toString() {
        return "Result{redacted}";
    }
}
