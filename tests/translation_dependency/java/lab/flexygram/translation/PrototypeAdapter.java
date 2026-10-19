package lab.flexygram.translation;

import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.concurrent.CancellationException;

/** Isolated contract prototype. No HTTP, SDK, URL, credentials or production wiring. */
public final class PrototypeAdapter {
    public enum Provider { MICROSOFT, DEEPL }
    public enum Format { TEXT, HTML }
    public enum Formality { DEFAULT, PREFER_LESS, PREFER_MORE }
    public record Request(Provider provider, String text, String source, String target,
                          Format format, Formality formality) {
        @Override public String toString() { return "Request[" + provider + ",REDACTED]"; }
    }
    public record Result(String translation, String sourceLanguage) {
        @Override public String toString() { return "Result[REDACTED]"; }
    }
    public record Response(int status, String translation, String detectedSource) {
        @Override public String toString() { return "Response[status=" + status + ",REDACTED]"; }
    }
    public interface Cancellation { boolean cancelled(); }
    public interface FixtureTransport { Response exchange(Request request, Cancellation cancellation) throws Exception; }
    public static final class Failure extends Exception {
        public final int status;
        Failure(String code, int status) { super(code); this.status = status; }
    }
    private final Provider provider;
    private final Set<String> targetLanguages;
    private final FixtureTransport transport;
    public PrototypeAdapter(Provider provider, Set<String> targets, FixtureTransport transport) {
        this.provider = java.util.Objects.requireNonNull(provider);
        this.targetLanguages = Set.copyOf(targets);
        this.transport = java.util.Objects.requireNonNull(transport);
    }
    public List<String> getTargetLanguages() { return targetLanguages.stream().sorted().toList(); }
    public boolean supportLanguage(String target) { return target != null && targetLanguages.contains(target); }
    // Exact observed AAR conversion, intentionally case-sensitive; wrapper aliases below are separate.
    public static String libraryLanguage(String code, boolean reverse) {
        if (code == null) return null;
        return switch (code) {
            case "zh-CN" -> reverse ? code : "zh-Hans";
            case "zh-TW" -> reverse ? code : "zh-Hant";
            case "zh-Hans" -> reverse ? "zh-CN" : code;
            case "zh-Hant" -> reverse ? "zh-TW" : code;
            default -> code;
        };
    }
    public static String wrapperTarget(String code) {
        if (code == null) return null;
        return switch (code.toLowerCase(Locale.ROOT)) {
            case "zh", "zh-cn", "zh-hans" -> "zh-CN";
            case "zh-tw", "zh-hk", "zh-hant" -> "zh-TW";
            default -> code;
        };
    }
    private static void check(Cancellation cancellation) {
        if (cancellation.cancelled() || Thread.currentThread().isInterrupted())
            throw new CancellationException("TRANSLATION_CANCELLED");
    }
    public Result translate(String text, String source, String target, Format format,
                            Formality formality, Cancellation cancellation) throws Failure {
        check(cancellation);
        String selected = wrapperTarget(target);
        if (!supportLanguage(selected)) throw new Failure("UNSUPPORTED_LANGUAGE", 0);
        if (text == null || format == null || formality == null) throw new Failure("INVALID_INPUT", 0);
        if (provider == Provider.MICROSOFT && formality != Formality.DEFAULT)
            throw new Failure("UNSUPPORTED_FORMALITY", 0);
        Request request = new Request(provider, text,
                libraryLanguage(provider == Provider.MICROSOFT && "auto".equals(source) ? null : source, false),
                libraryLanguage(selected, false), format, formality);
        try {
            Response response = transport.exchange(request, cancellation);
            check(cancellation); // Never accept late results after cancellation.
            if (response == null) throw new Failure("INVALID_RESPONSE", 0);
            if (response.status() != 200) throw new Failure("PROVIDER_HTTP_ERROR", response.status());
            if (response.translation() == null) throw new Failure("INVALID_RESPONSE", 200);
            return new Result(response.translation(), libraryLanguage(response.detectedSource(), true));
        } catch (CancellationException e) {
            throw new CancellationException("TRANSLATION_CANCELLED");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new CancellationException("TRANSLATION_CANCELLED");
        } catch (Failure e) {
            throw e;
        } catch (Exception e) {
            // No cause, provider message, response, text or URL in diagnostics.
            throw new Failure("PROVIDER_FAILED", 0);
        }
    }
}
