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
    private static final Pattern RESERVED=Pattern.compile("(?i)(?:https?://|www\\.)\\S+|[\\p{L}\\p{N}._%+-]+@[\\p{L}\\p{N}.-]+\\.[\\p{L}]{2,}|(?:@|#)[\\p{L}\\p{N}_]+|`[^`]*`");
    private InlineConversionScanner(){}
    public static BigDecimal number(String raw,Locale locale){
        if(raw==null||raw.length()>40||locale==null)throw new IllegalArgumentException("Number/locale required");
        DecimalFormatSymbols symbols=DecimalFormatSymbols.getInstance(locale);
        char decimal=symbols.getDecimalSeparator(),group=symbols.getGroupingSeparator();
        String s=raw.replace('−','-').replace('\u202f','\u00a0');
        if(group=='\u202f')group='\u00a0';
        String sign=s.startsWith("-")?"-":"";if(!sign.isEmpty())s=s.substring(1);
        String[] parts=s.split(Pattern.quote(String.valueOf(decimal)),-1);
        if(parts.length>2)throw new IllegalArgumentException("Ambiguous decimal");
        String integer=parts[0];
        if(integer.indexOf(group)>=0){
            String[] groups=integer.split(Pattern.quote(String.valueOf(group)),-1);
            if(groups[0].length()<1||groups[0].length()>3)throw new IllegalArgumentException("Grouping");
            for(int i=1;i<groups.length;i++)if(groups[i].length()!=3)throw new IllegalArgumentException("Grouping");
            integer=String.join("",groups);
        }
        String fraction=parts.length==2?parts[1]:"";
        if(!integer.matches("[0-9]+")||parts.length==2&&!fraction.matches("[0-9]+"))throw new IllegalArgumentException("Regional number");
        if(integer.length()+fraction.length()>24)throw new IllegalArgumentException("Number too long");
        return new BigDecimal(sign+integer+(parts.length==2?"."+fraction:""));
    }
    private static boolean symbolMatches(String symbol,String code) {
        if (symbol==null||symbol.isEmpty()) return true;
        switch(symbol) {
            case "$": return Arrays.asList("USD","CAD","AUD","COP","MXN","ARS","CLP","NZD","SGD","HKD").contains(code);
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
