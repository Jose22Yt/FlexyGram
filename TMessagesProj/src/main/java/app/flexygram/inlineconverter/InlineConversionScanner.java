/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.inlineconverter;

import java.math.BigDecimal;
import java.text.DecimalFormatSymbols;
import java.util.*;
import java.util.regex.*;

/** Extended from the owner's isolated InlineMatchScanner reference. UTF-16 offsets, no Android dependency. */
public final class InlineConversionScanner {
    public static final int MAX_CHARS=4096,MAX_MATCHES=12;
    private static final String B="(?<![\\p{L}\\p{N}_@/#])",E="(?![\\p{L}\\p{N}_])";
    private static final String N="[-−]?\\d{1,12}(?:[.,\\u00a0\\u202f]\\d{1,12}){0,4}";
    private static final Pattern MONEY=Pattern.compile(B+"(?:([$€£¥]?)("+N+")\\s+([A-Z]{3})|([A-Z]{3})\\s+("+N+"))"+E,Pattern.CASE_INSENSITIVE);
    private static final Pattern UNITS=Pattern.compile(B+"("+N+")\\s*(miles?|millas?|kilometers?|kilómetros?|kilometros?|km|pounds?|lbs?|libras?|kilograms?|kilogramos?|kg|feet|foot|pies|ft|meters?|metros?|inches|inch|pulgadas?|centimeters?|centímetros?|cm|°\\s*[CF]|celsius|fahrenheit)"+E,Pattern.CASE_INSENSITIVE);
    private static final Pattern TIME=Pattern.compile(B+"(\\d{1,2})(?::([0-5]\\d))?\\s*(AM|PM)?\\s+(UTC|GMT|EST|EDT|PST|PDT|CST|IST|[A-Za-z_]+/[A-Za-z_]+(?:/[A-Za-z_]+)?)(?![+\\-\\p{L}\\p{N}_/])",Pattern.CASE_INSENSITIVE);
    // Start an email only at the beginning of its local-part run. Without this
    // boundary, find() rescans every suffix of long words that contain no '@'.
    private static final Pattern RESERVED=Pattern.compile("(?i)(?:https?://|www\\.)\\S+|(?<![\\p{L}\\p{N}._%+-])[\\p{L}\\p{N}._%+-]++@[\\p{L}\\p{N}.-]+\\.[\\p{L}]{2,}|(?:@|#)[\\p{L}\\p{N}_]+|`[^`]*`");
    private InlineConversionScanner(){}
    private static boolean isAsciiDigits(String value, int start, int end) {
        if (end <= start) return false;
        for (int i = start; i < end; i++) {
            char c = value.charAt(i);
            if (c < '0' || c > '9') return false;
        }
        return true;
    }
    public static BigDecimal number(String raw,Locale locale){
        if(raw==null||raw.length()>40||locale==null)throw new IllegalArgumentException("Number/locale required");
        DecimalFormatSymbols symbols=DecimalFormatSymbols.getInstance(locale);
        char decimal=symbols.getDecimalSeparator(),group=symbols.getGroupingSeparator();
        String s=raw.replace('−','-').replace('\u202f','\u00a0');
        if(group=='\u202f')group='\u00a0';
        String sign=s.startsWith("-")?"-":"";if(!sign.isEmpty())s=s.substring(1);
        int decPos=s.indexOf(decimal);
        if(decPos>=0&&s.indexOf(decimal,decPos+1)>=0)throw new IllegalArgumentException("Ambiguous decimal");
        String integer=decPos>=0?s.substring(0,decPos):s;
        String fraction=decPos>=0?s.substring(decPos+1):"";
        if(integer.indexOf(group)>=0){
            StringBuilder stripped=new StringBuilder(integer.length());
            int segStart=0,segIndex=0,len=integer.length();
            while(true){
                int sep=integer.indexOf(group,segStart);
                int segEnd=sep<0?len:sep;
                int segLen=segEnd-segStart;
                if(segIndex==0?(segLen<1||segLen>3):segLen!=3)throw new IllegalArgumentException("Grouping");
                if(!isAsciiDigits(integer,segStart,segEnd))throw new IllegalArgumentException("Regional number");
                stripped.append(integer,segStart,segEnd);
                if(sep<0)break;
                segStart=sep+1;segIndex++;
            }
            integer=stripped.toString();
        } else if(!isAsciiDigits(integer,0,integer.length())){
            throw new IllegalArgumentException("Regional number");
        }
        if(decPos>=0&&!isAsciiDigits(fraction,0,fraction.length()))throw new IllegalArgumentException("Regional number");
        if(integer.length()+fraction.length()>24)throw new IllegalArgumentException("Number too long");
        return new BigDecimal(sign+integer+(decPos>=0?"."+fraction:""));
    }
    private static boolean symbolMatches(String symbol,String code) {
        if (symbol==null||symbol.isEmpty()) return true;
        switch(symbol) {
            case "$":
                switch(code) {
                    case "USD": case "CAD": case "AUD": case "COP": case "MXN":
                    case "ARS": case "CLP": case "NZD": case "SGD": case "HKD":
                        return true;
                    default: return false;
                }
            case "€": return code.equals("EUR");
            case "£": return code.equals("GBP");
            case "¥": return code.equals("JPY")||code.equals("CNY");
            default: return false;
        }
    }
    public static List<InlineConversionMatch> scan(String text,Locale locale,int[][] blocked){
        if(text==null||text.isEmpty()||text.length()>MAX_CHARS)return Collections.emptyList();
        ArrayList<int[]> excluded=new ArrayList<>();
        if(blocked!=null){if(blocked.length>128)return Collections.emptyList();for(int[] range:blocked)if(range!=null&&range.length==2)excluded.add(range);}
        Matcher reserved=RESERVED.matcher(text);while(reserved.find())excluded.add(new int[]{reserved.start(),reserved.end()});
        ArrayList<InlineConversionMatch> found=new ArrayList<>();
        for(int kind=0;kind<3;kind++){
            Matcher m=(kind==0?MONEY:kind==1?TIME:UNITS).matcher(text);int budget=36;
            while(m.find()&&budget-->0){
                boolean overlap=false;for(int[] r:excluded)if(m.start()<r[1]&&r[0]<m.end()){overlap=true;break;}
                if(overlap)continue;
                try{
                    InlineConversionMatch match;
                    if(kind==0){
                        String code=m.group(3)==null?m.group(4):m.group(3);
                        // Lowercase words such as "all" (Albanian lek) must not become money.
                        if (!code.equals(code.toUpperCase(Locale.ROOT))) continue;
                        Currency.getInstance(code);
                        if (!symbolMatches(m.group(1),code)) continue;
                        match=new InlineConversionMatch(InlineConversionMatch.Type.CURRENCY,m.start(),m.end(),m.group(),code,number(m.group(2)==null?m.group(5):m.group(2),locale),0,0);
                    }else if(kind==1){
                        int h=Integer.parseInt(m.group(1)),min=m.group(2)==null?0:Integer.parseInt(m.group(2));String am=m.group(3);
                        if(am==null&&(m.group(2)==null||h>23)||am!=null&&(h<1||h>12))continue;
                        if(am!=null)h=h%12+(am.equalsIgnoreCase("PM")?12:0);
                        match=new InlineConversionMatch(InlineConversionMatch.Type.TIME,m.start(),m.end(),m.group(),m.group(4),null,h,min);
                    }else match=new InlineConversionMatch(InlineConversionMatch.Type.UNIT,m.start(),m.end(),m.group(),m.group(2).toLowerCase(Locale.ROOT).replace(" ",""),number(m.group(1),locale),0,0);
                    found.add(match);
                }catch(IllegalArgumentException malformed){/* fail closed, never guess malformed numbers */}
            }
        }
        found.sort(Comparator.comparingInt(m->m.start));ArrayList<InlineConversionMatch> result=new ArrayList<>();
        for(InlineConversionMatch m:found){if(!result.isEmpty()&&m.start<result.get(result.size()-1).end)continue;result.add(m);if(result.size()==MAX_MATCHES)break;}
        return Collections.unmodifiableList(result);
    }
}
