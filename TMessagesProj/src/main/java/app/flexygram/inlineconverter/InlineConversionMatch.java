/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.inlineconverter;
import java.math.BigDecimal;
public final class InlineConversionMatch {
    public enum Type { CURRENCY, TIME, UNIT }
    public final Type type;
    public final int start,end;
    public final String raw,code;
    public final BigDecimal value;
    public final int hour,minute;
    InlineConversionMatch(Type type,int start,int end,String raw,String code,BigDecimal value,int hour,int minute){
        this.type=type;this.start=start;this.end=end;this.raw=raw;this.code=code;this.value=value;this.hour=hour;this.minute=minute;
    }
}
