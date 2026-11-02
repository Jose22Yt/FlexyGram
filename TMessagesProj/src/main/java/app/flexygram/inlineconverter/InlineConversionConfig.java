/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.inlineconverter;

import android.content.SharedPreferences;
import java.time.ZoneId;
import java.util.Currency;
import java.util.Locale;
import tw.nekomimi.nekogram.NekoConfig;

/** Opt-in. Immutable in-memory settings; no per-frame preference reads or idle observer. */
public final class InlineConversionConfig {
    public static final String ENABLED="flexy_conversion_enabled", CURRENCY="flexy_conversion_currency",
        TARGET_CURRENCY="flexy_conversion_target_currency", TIME="flexy_conversion_time",
        TARGET_ZONE="flexy_conversion_target_zone", UNITS="flexy_conversion_units", SYSTEM="flexy_conversion_unit_system";
    public static final class Snapshot {
        public final boolean enabled,currency,time,units;
        public final String targetCurrency,targetZone;
        public final int system,revision;
        private Snapshot(SharedPreferences p,int revision){
            enabled=p.getBoolean(ENABLED,false);currency=p.getBoolean(CURRENCY,true);
            time=p.getBoolean(TIME,true);units=p.getBoolean(UNITS,true);
            String currency=p.getString(TARGET_CURRENCY,suggestCurrency());
            try{Currency.getInstance(currency);}catch(Exception invalid){currency=suggestCurrency();}
            targetCurrency=currency;
            String zone=p.getString(TARGET_ZONE,"");
            try{if(!zone.isEmpty())ZoneId.of(zone);}catch(Exception invalid){zone="";}
            targetZone=zone;system=Math.max(0,Math.min(2,p.getInt(SYSTEM,0)));this.revision=revision;
        }
        public boolean accepts(InlineConversionMatch m){return enabled&&(m.type==InlineConversionMatch.Type.CURRENCY?currency:m.type==InlineConversionMatch.Type.TIME?time:units);}
        public ZoneId zone(){return targetZone.isEmpty()?ZoneId.systemDefault():ZoneId.of(targetZone);}
        public boolean imperial(Locale locale){return system==2||system==0&&(locale.getCountry().equals("US")||locale.getCountry().equals("LR")||locale.getCountry().equals("MM"));}
    }
    private static volatile Snapshot current;
    private InlineConversionConfig(){}
    public static Snapshot get(){Snapshot value=current;if(value==null){synchronized(InlineConversionConfig.class){if(current==null)current=new Snapshot(NekoConfig.getPreferences(),0);value=current;}}return value;}
    private static String suggestCurrency(){try{return Currency.getInstance(Locale.getDefault()).getCurrencyCode();}catch(Exception noRegion){return "USD";}}
    public static synchronized void set(String key,Object value){
        SharedPreferences.Editor e=NekoConfig.getPreferences().edit();
        if(key.equals(ENABLED)||key.equals(CURRENCY)||key.equals(TIME)||key.equals(UNITS))e.putBoolean(key,(Boolean)value);
        else if(key.equals(TARGET_CURRENCY)){Currency.getInstance((String)value);e.putString(key,(String)value);}
        else if(key.equals(TARGET_ZONE)){if(!((String)value).isEmpty())ZoneId.of((String)value);e.putString(key,(String)value);}
        else if(key.equals(SYSTEM)){int system=(Integer)value;if(system<0||system>2)throw new IllegalArgumentException("System");e.putInt(key,system);}
        else throw new IllegalArgumentException("Unknown setting");
        int revision=get().revision+1;e.apply();current=new Snapshot(NekoConfig.getPreferences(),revision);
        // No permanent observers and no retained message text after opt-out.
        if(!current.enabled)InlineConversionController.clearCache();
    }
}
