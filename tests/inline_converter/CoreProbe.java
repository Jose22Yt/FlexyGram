import app.flexygram.inlineconverter.*;
import java.util.*;
import java.time.*;
import java.math.*;

/** Executes the real platform-independent production classes. No fake exchange rates. */
public class CoreProbe {
    static void check(boolean ok){if(!ok)throw new AssertionError();}
    static List<InlineConversionMatch> scan(String value,Locale locale){return InlineConversionScanner.scan(value,locale,null);}
    static void equal(String expected,BigDecimal value){check(new BigDecimal(expected).compareTo(value)==0);}
    public static void main(String[] args){switch(args[0]){
        case "scanner":{
            var matches=scan("😀 Meet at 3:00 PM EST, price $45 USD; travel 70 miles and 180 lbs.",Locale.US);
            check(matches.size()==4);check(matches.get(0).hour==15);check(matches.get(1).code.equals("USD"));
            equal("45",matches.get(1).value);equal("70",matches.get(2).value);
            for(var m:matches)check(m.raw.equals("😀 Meet at 3:00 PM EST, price $45 USD; travel 70 miles and 180 lbs.".substring(m.start,m.end)));
            check(matches.get(0).start==11);check(matches.get(1).raw.equals("$45 USD"));
            check(scan("EUR 120 / 45 USD / 250.000 COP",Locale.forLanguageTag("es-CO")).size()==3);
            equal("250000",scan("250.000 COP",Locale.forLanguageTag("es-CO")).get(0).value);break;
        }
        case "numbers":{
            equal("1234.56",InlineConversionScanner.number("1,234.56",Locale.US));
            equal("1234.56",InlineConversionScanner.number("1.234,56",Locale.GERMANY));
            equal("1234.56",InlineConversionScanner.number("1\u202f234,56",Locale.FRANCE));
            equal("-32.5",InlineConversionScanner.number("−32,5",Locale.GERMANY));
            for(String bad:new String[]{"1,23","1.234,56","1,234,56","1..2","NaN","123456789012345678901234567","1e9"}){boolean rejected=false;try{InlineConversionScanner.number(bad,Locale.US);}catch(IllegalArgumentException expected){rejected=true;}check(rejected);}break;
        }
        case "reserved":{
            check(scan("https://example.org/70miles @70miles #180lbs user70miles@example.org `45 USD`",Locale.US).isEmpty());
            check(InlineConversionScanner.scan("70 miles and 45 USD",Locale.US,new int[][]{{0,8},{13,19}}).isEmpty());
            check(scan("$45 | €45 USD | 10 all | USD 1,23 | 15:00 UTC+2 | 15:00 UTC-2 | 99:00 UTC | 3 PST | 25:00 UTC | 13 PM EST | 5 m | 7 in | abc70miles",Locale.US).isEmpty());break;
        }
        case "limits":{
            check(scan("70 miles ".repeat(1000),Locale.US).isEmpty());check(scan("70 miles ".repeat(100),Locale.US).size()==12);
            check(InlineConversionScanner.scan("70 miles",Locale.US,new int[129][2]).isEmpty());
            boolean immutable=false;try{scan("70 miles",Locale.US).clear();}catch(UnsupportedOperationException expected){immutable=true;}check(immutable);break;
        }
        case "units":{
            equal("112.654080",UnitConversionEngine.convert(new BigDecimal("70"),"miles",false).value);
            equal("81.6466266",UnitConversionEngine.convert(new BigDecimal("180"),"lbs",false).value);
            equal("0.3048",UnitConversionEngine.convert(BigDecimal.ONE,"ft",false).value);
            equal("2.54",UnitConversionEngine.convert(BigDecimal.ONE,"inch",false).value);
            equal("-40",UnitConversionEngine.convert(new BigDecimal("-40"),"°c",true).value);
            equal("0",UnitConversionEngine.convert(new BigDecimal("32"),"°f",false).value);
            equal("70",UnitConversionEngine.convert(new BigDecimal("70"),"miles",true).value);
            var back=UnitConversionEngine.convert(UnitConversionEngine.convert(new BigDecimal("12.345"),"km",true).value,"miles",false).value;
            check(back.subtract(new BigDecimal("12.345")).abs().compareTo(new BigDecimal("1e-30"))<0);
            check(scan("0 °C, −40 °F, 180 libras, 12 pulgadas, 2 metros",Locale.US).size()==5);break;
        }
        case "time":{
            check(scan("8:30 AM PST / 15:00 UTC / 12 AM GMT / 12 PM EST / 18:00 America/New_York",Locale.US).size()==5);
            check(scan("12 AM GMT",Locale.US).get(0).hour==0);check(scan("12 PM GMT",Locale.US).get(0).hour==12);
            var converted=TimeConversionEngine.convert(15,0,LocalDate.of(2026,1,1),ZoneId.of("UTC"),ZoneId.of("America/Bogota")).get(0);check(converted.getHour()==10);
            check(TimeConversionEngine.sourceZones("EST").get(0).equals(ZoneOffset.ofHours(-5)));
            check(TimeConversionEngine.sourceZones("CST").size()==3);check(TimeConversionEngine.sourceZones("IST").size()==3);
            check(TimeConversionEngine.convert(23,30,LocalDate.of(2026,1,1),ZoneOffset.UTC,ZoneId.of("Asia/Tokyo")).get(0).getDayOfMonth()==2);
            check(TimeConversionEngine.messageDate(Instant.parse("2026-01-02T00:30:00Z").getEpochSecond(),ZoneId.of("America/Bogota")).equals(LocalDate.of(2026,1,1)));break;
        }
        case "dst":{
            var ny=ZoneId.of("America/New_York");check(TimeConversionEngine.convert(2,30,LocalDate.of(2026,3,8),ny,ZoneOffset.UTC).isEmpty());
            var repeated=TimeConversionEngine.convert(1,30,LocalDate.of(2026,11,1),ny,ZoneOffset.UTC);check(repeated.size()==2);check(Duration.between(repeated.get(0),repeated.get(1)).toHours()==1);
            check(TimeConversionEngine.convert(15,0,LocalDate.of(2026,7,1),ny,ZoneOffset.UTC).get(0).getHour()==19);break;
        }
        case "cache":{
            var cache=new InlineConversionCache();for(int i=0;i<32;i++)cache.put("account1:peer2:msg"+i+":edit0:70 miles",scan("70 miles",Locale.US));
            String key="account1:peer2:msg0:edit0:70 miles";check(cache.get(key)!=null);cache.put("new",List.of());check(cache.size()==32);check(cache.get("account1:peer2:msg1:edit0:70 miles")==null);check(cache.get(key)!=null);
            check(cache.get("account1:peer2:msg0:edit1:70 miles")==null);check(cache.get("account2:peer2:msg0:edit0:70 miles")==null);cache.clear();check(cache.size()==0);break;
        }
        case "provider":{
            int rejected=0;for(BigDecimal value:new BigDecimal[]{null,BigDecimal.ZERO,BigDecimal.ONE.negate()})try{new ExchangeRateProvider.Quote("USD","EUR",value,"future authorized provider",Instant.EPOCH);}catch(IllegalArgumentException expected){rejected++;}check(rejected==3);
            // Validate provenance rejection only. No quotation is fabricated/displayed.
            boolean invalid=false;try{new ExchangeRateProvider.Quote("USD","EUR",BigDecimal.ONE,"",Instant.EPOCH);}catch(IllegalArgumentException expected){invalid=true;}check(invalid);break;
        }
        case "benchmark":{
            String value=("Hello 3:00 PM EST, $45 USD, 70 miles. ").repeat(100);
            for(int i=0;i<400;i++)scan(value,Locale.US);
            long[] nanos=new long[600];for(int i=0;i<nanos.length;i++){long start=System.nanoTime();scan(value,Locale.US);nanos[i]=System.nanoTime()-start;}
            Arrays.sort(nanos);System.out.println("HOST_ONLY scanner chars="+value.length()+" samples="+nanos.length+" median_ns="+nanos[300]+" p95_ns="+nanos[570]+"; not Android tap/frame latency");break;
        }
        default:throw new IllegalArgumentException(args[0]);
    }System.out.println("PASS "+args[0]);}
}
