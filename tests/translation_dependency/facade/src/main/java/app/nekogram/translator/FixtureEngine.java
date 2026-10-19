// FlexyGram laboratory facade — @Lukhou23. GPL-3.0; see repository LICENSE.
// Independent implementation against the recorded consumed ABI. Not wired into Android.
package app.nekogram.translator;

import java.util.concurrent.CancellationException;
import lab.flexygram.fixture.FixtureTransport;

final class FixtureEngine {
    private final FixtureTransport.Provider provider;
    private final FixtureTransport transport;
    private final FixtureTransport.Cancellation cancellation;

    FixtureEngine(FixtureTransport.Provider provider, FixtureTransport transport,
                  FixtureTransport.Cancellation cancellation) {
        this.provider = provider;
        this.transport = transport;
        this.cancellation = cancellation;
    }

    private void checkCancelled() {
        if (Thread.currentThread().isInterrupted()) {
            throw new CancellationException("TRANSLATION_CANCELLED");
        }
        if (cancellation == null) return;
        boolean cancelled;
        try {
            cancelled = cancellation.isCancelled();
        } catch (CancellationException error) {
            throw new CancellationException("TRANSLATION_CANCELLED");
        } catch (RuntimeException error) {
            throw new FacadeFailure("TRANSLATION_CANCELLATION_ERROR", 0);
        }
        if (cancelled) throw new CancellationException("TRANSLATION_CANCELLED");
    }

    Result translate(String text, String from, String to) {
        checkCancelled();
        if (transport == null) {
            throw new FacadeFailure("TRANSLATION_NOT_AUTHORIZED", 0);
        }
        FixtureTransport.Response response;
        try {
            response = transport.exchange(provider, text, from, to);
        } catch (InterruptedException error) {
            Thread.currentThread().interrupt();
            throw new CancellationException("TRANSLATION_CANCELLED");
        } catch (CancellationException error) {
            throw new CancellationException("TRANSLATION_CANCELLED");
        } catch (Exception error) {
            // Never retain even a facade-shaped exception supplied by the transport.
            checkCancelled();
            throw new FacadeFailure("TRANSLATION_TRANSPORT_ERROR", 0);
        }
        checkCancelled();
        if (response == null) {
            throw new FacadeFailure("TRANSLATION_INVALID_RESPONSE", 0);
        }
        if (response.status < 200 || response.status >= 300) {
            int safeStatus = response.status >= 100 && response.status <= 599
                    ? response.status : 0;
            throw new FacadeFailure("TRANSLATION_HTTP_ERROR", safeStatus);
        }
        if (response.translation == null) {
            throw new FacadeFailure("TRANSLATION_INVALID_RESPONSE", 0);
        }
        return Result.of(response.translation, response.sourceLanguage);
    }

    static String language(String code, boolean reverse) {
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
