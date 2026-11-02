/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.inlineconverter;
import java.time.*;
import java.util.*;
public final class TimeConversionEngine {
    private TimeConversionEngine(){}
    public static List<ZoneId> sourceZones(String label){
        switch(label.toUpperCase(Locale.ROOT)){
            case "UTC":case "GMT":return List.of(ZoneOffset.UTC);
            case "EST":return List.of(ZoneOffset.ofHours(-5));case "EDT":return List.of(ZoneOffset.ofHours(-4));
            case "PST":return List.of(ZoneOffset.ofHours(-8));case "PDT":return List.of(ZoneOffset.ofHours(-7));
            case "CST":return List.of(ZoneId.of("America/Chicago"),ZoneId.of("Asia/Shanghai"),ZoneId.of("America/Havana"));
            case "IST":return List.of(ZoneId.of("Asia/Kolkata"),ZoneId.of("Europe/Dublin"),ZoneId.of("Asia/Jerusalem"));
            default:return List.of(ZoneId.of(label));
        }
    }
    public static List<ZonedDateTime> convert(int hour,int minute,LocalDate date,ZoneId from,ZoneId to){
        LocalDateTime local=date.atTime(hour,minute);ArrayList<ZonedDateTime> result=new ArrayList<>();
        for(ZoneOffset offset:from.getRules().getValidOffsets(local))result.add(ZonedDateTime.ofStrict(local,offset,from).withZoneSameInstant(to));
        return Collections.unmodifiableList(result); // 0 = DST gap; 2 = repeated local time. Never silently shift.
    }
    public static LocalDate messageDate(long epochSeconds,ZoneId source){return Instant.ofEpochSecond(epochSeconds).atZone(source).toLocalDate();}
}
