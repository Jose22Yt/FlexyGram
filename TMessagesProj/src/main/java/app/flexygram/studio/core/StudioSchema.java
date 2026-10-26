/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.studio.core;

import java.util.*;

/** Explicit visual-only schema. Never enumerate or copy arbitrary preferences. */
public final class StudioSchema {
    public static final String EXTENSION = ".flexyGram";
    public static final String MIME = "application/vnd.flexygram.configuration+json";
    public static final int SCHEMA = 1, MIN_APP = 1273, MAX_BYTES = 65536, MAX_KEYS = 32;
    public static final class Key {
        public final String section, id, file, preference;
        public final Object defaultValue;
        private final int min, max;
        private final Set<String> choices;
        private Key(String section,String id,String file,String preference,Object value,int min,int max,String...choices) {
            this.section=section;this.id=id;this.file=file;this.preference=preference;this.defaultValue=value;
            this.min=min;this.max=max;this.choices=Collections.unmodifiableSet(new HashSet<>(Arrays.asList(choices)));
        }
        public Object validate(Object value) {
            if (defaultValue instanceof Boolean && value instanceof Boolean) return value;
            if (defaultValue instanceof Integer && value instanceof Long) {
                long n=(Long)value;if(n>=min&&n<=max)return (int)n;
            }
            if (defaultValue instanceof Integer && value instanceof Integer && (Integer)value>=min && (Integer)value<=max)return value;
            if (defaultValue instanceof String && value instanceof String && choices.contains(value))return value;
            throw new IllegalArgumentException("value");
        }
    }
    private static Key b(String s,String id,String f,String p,boolean d){return new Key(s,id,f,p,d,0,0);}
    private static Key i(String s,String id,String f,String p,int d,int min,int max){return new Key(s,id,f,p,d,min,max);}
    private static final List<Key> KEYS=Collections.unmodifiableList(Arrays.asList(
        b("bubbles","glass","flexygram_bubbles","glass",false),
        b("bubbles","border","flexygram_bubbles","border",false),
        b("bubbles","edges","flexygram_bubbles","edges",false),
        i("bubbles","transparency","flexygram_bubbles","transparency",35,0,100),
        i("bubbles","borderTenths","flexygram_bubbles","signature_border_tenths",11,5,20),
        b("bubbles","cachedBlur","flexygram_bubbles","signature_cached_blur",false),
        b("bubbles","outlineEnabled","flexygram_bubbles","signature_outline_enabled",true),
        i("bubbles","outlineStyle","flexygram_bubbles","signature_outline_style",1,0,3),
        i("bubbles","borderPosition","flexygram_bubbles","signature_border_position",5,0,5),
        b("bubbles","fuseGlass","flexygram_bubbles","signature_fuse_glass",false),
        i("bubbles","pearlIntensity","flexygram_bubbles","signature_pearl_intensity",55,0,100),
        i("header","style","flexygram_header","style",0,0,2),
        b("header","compact","flexygram_header","compact",false),
        b("header","counter","flexygram_header","counter",true),
        i("header","counterPresentation","flexygram_header","counter_mode",1,1,2),
        i("header","opacity","flexygram_header","opacity",85,0,100),
        i("composer","style","flexygram_composer","style",0,0,1),
        b("composer","glass","flexygram_composer","pearlGlass",false),
        i("composer","position","flexygram_composer","verticalPosition",0,-4,16),
        i("composer","density","flexygram_composer","compactLevel",0,0,2),
        i("composer","icons","flexygram_composer","iconAppearance",0,0,1),
        // Zero means the native density-dependent gap; values1 is not supported.
        new Key("composer","gap","flexygram_composer","componentGap",0,0,8),
        new Key("icon","selected","flexy_launcher","selected","EXTERALESS",0,0,
            "EXTERALESS","FLEX_GREEN","FLEX_CORAL","FLEX_MONO","FLEX_BLUEPRINT","FLEX_NYA","FLEX_QUACK","FLEX_GO",
            "LEGACY_EXTERALESS","BLUEPRINT","RED","NYA","AYU","QUACK","GO","HAND","MONO","NOTHING","PLUS","TELEGRAM","VINTAGE","AQUA","PREMIUM","TURBO","NOX")
    ));
    public static final class Unsupported extends IllegalArgumentException {
        public final String identifier;
        public Unsupported(String id){super("unsupported");identifier=id.matches("[A-Za-z0-9_.=]{1,120}")?id:"schema";}
    }
    private StudioSchema(){}
    public static List<Key> keys(){return KEYS;}
    public static Set<String> sections(){return Collections.unmodifiableSet(new LinkedHashSet<>(Arrays.asList("bubbles","header","composer","icon")));}
    public static Key key(String section,String id) {
        for(Key k:KEYS)if(k.section.equals(section)&&k.id.equals(id))return k;
        throw new Unsupported(section+"."+id);
    }
    public static Object value(Key key,Object raw) {
        Object result=key.validate(raw);
        if(key.section.equals("composer")&&key.id.equals("gap")&&result.equals(1))throw new IllegalArgumentException("value");
        return result;
    }
    /** Additive schema1 keys require Alpha1274; older valid schema1 files remain accepted. */
    public static int minimumApp(Map<String,Map<String,Object>> sections) {
        Map<String,Object> bubbles=sections.get("bubbles"),header=sections.get("header");
        if (header != null && header.get("style") instanceof Number && ((Number)header.get("style")).intValue() == 2) return 1276;
        if (bubbles != null && (bubbles.containsKey("borderPosition") || bubbles.containsKey("fuseGlass")
                || bubbles.get("outlineStyle") instanceof Number && ((Number)bubbles.get("outlineStyle")).intValue() >= 2)) return 1276;
        return bubbles!=null&&(bubbles.containsKey("outlineEnabled")||bubbles.containsKey("outlineStyle")||bubbles.containsKey("pearlIntensity"))
            ||header!=null&&header.containsKey("counterPresentation")?1274:MIN_APP;
    }
    public static boolean filename(String name) {
        if(name==null||name.length()>192||!name.endsWith(EXTENSION)||name.length()<=EXTENSION.length())return false;
        for(int j=0;j<name.length();j++) {
            char c=name.charAt(j);
            if(Character.isHighSurrogate(c)){if(j+1>=name.length()||!Character.isLowSurrogate(name.charAt(++j)))return false;}else if(Character.isLowSurrogate(c))return false;
            if(c=='/'||c=='\\'||c<32||c==127||(c>=0x202a&&c<=0x202e)||(c>=0x2066&&c<=0x2069))return false;
        }
        return true;
    }
}
