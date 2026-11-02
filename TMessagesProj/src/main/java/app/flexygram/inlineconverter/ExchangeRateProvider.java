/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.inlineconverter;
import java.math.BigDecimal;
import java.time.Instant;
/** No message, account, peer or contact data belongs in this interface. No provider is enabled. */
public interface ExchangeRateProvider {
    interface Cancellation {void cancel();}
    interface Callback {void completed(Quote quote);}
    final class Quote {
        public final String base,target,source;public final BigDecimal rate;public final Instant quotedAt;
        public Quote(String base,String target,BigDecimal rate,String source,Instant quotedAt){
            if(rate==null||rate.signum()<=0||source==null||source.isBlank()||quotedAt==null)throw new IllegalArgumentException("Quote provenance required");
            java.util.Currency.getInstance(base);java.util.Currency.getInstance(target);this.base=base;this.target=target;this.rate=rate;this.source=source;this.quotedAt=quotedAt;
        }
    }
    Cancellation request(String base,String target,Callback callback);
}
