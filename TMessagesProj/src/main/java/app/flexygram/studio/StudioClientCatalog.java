package app.flexygram.studio;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Base64;
import app.exteraless.OpenExteraConfig;
import app.exteraless.appearance.AppearanceConfig;
import app.exteraless.chats.ChatsConfig;
import app.exteraless.general.GeneralConfig;
import app.exteraless.icons.IconPacksConfig;
import app.exteraless.pillstack.PillStackConfig;
import app.exteraless.utils.UtilsConfig;
import org.telegram.messenger.ApplicationLoader;
import tw.nekomimi.nekogram.NekoConfig;
import tw.nekomimi.nekogram.config.ConfigItem;
import xyz.nextalone.nagram.NaConfig;
import java.io.*;
import java.util.*;

/** Native metadata is the allowlist. Never export a preferences directory, account database or login state. */
final class StudioClientCatalog {
    static final int BOOL=0, INT=1, STRING=2, SET=3, MAP=4, LONG=5, FLOAT=6, STRING_SET=8;
    static final class Spec {
        String section="general";
        final int type; final Object fallback; final ConfigItem item; app.flexygram.studio.core.StudioSchema.Key legacyKey; int min=Integer.MIN_VALUE,max=Integer.MAX_VALUE;
        Spec(int type,Object fallback,ConfigItem item){this.type=type;this.fallback=fallback;this.item=item;}
        Object encode(Object value) {
            if(value==null)value=fallback;
            switch(type){
                case BOOL: if(value instanceof Boolean)return value;break;
                case INT: case LONG:
                    if(value instanceof Integer||value instanceof Long){long n=((Number)value).longValue();if(type==LONG||n>=Integer.MIN_VALUE&&n<=Integer.MAX_VALUE)return n;}break;
                case FLOAT:
                    if(value instanceof Number&&Float.isFinite(((Number)value).floatValue()))return Float.toString(((Number)value).floatValue());break;
                case STRING: if(value instanceof String&&((String)value).length()<=65536)return value;break;
                case SET:
                    if(value instanceof Set){TreeSet<Long> sorted=new TreeSet<>();for(Object o:(Set<?>)value){long n=Long.parseLong(o.toString());if(n<Integer.MIN_VALUE||n>Integer.MAX_VALUE)throw invalid();sorted.add(n);}if(sorted.size()<=8192)return new ArrayList<>(sorted);}break;
                case STRING_SET:
                    if(value instanceof Set && ((Set<?>)value).size()<=8192){TreeSet<String> sorted=new TreeSet<>();for(Object o:(Set<?>)value){if(!(o instanceof String)||((String)o).length()>256)throw invalid();sorted.add((String)o);}return new ArrayList<>(sorted);}break;
                case MAP:
                    // Read the already loaded native map, never deserialize a file supplied by the importer.
                    Object map=value instanceof Map?value:item==null?fallback:item.value;
                    if(map instanceof Map){Map<String,Object> result=new TreeMap<>();for(Map.Entry<?,?> e:((Map<?,?>)map).entrySet()){int k=((Number)e.getKey()).intValue(),v=((Number)e.getValue()).intValue();result.put(Integer.toString(k),(long)v);}if(result.size()<=8192)return result;}break;
            }
            throw invalid();
        }
        Object validate(Object value) {
            if(legacyKey!=null)app.flexygram.studio.core.StudioSchema.value(legacyKey,value);
            switch(type){
                case BOOL:if(value instanceof Boolean)return value;break;
                case INT:case LONG:if(value instanceof Long){long n=(Long)value;if(type==LONG||n>=min&&n<=max)return type==INT?(Object)(int)n:n;}break;
                case STRING:if(value instanceof String&&((String)value).length()<=65536)return value;break;
                case FLOAT:if(value instanceof String){try{float f=Float.parseFloat((String)value);if(Float.isFinite(f))return f;}catch(NumberFormatException ignored){}}break;
                case SET:if(value instanceof List&&((List<?>)value).size()<=8192){Set<String> result=new HashSet<>();for(Object o:(List<?>)value){if(!(o instanceof Long)||(Long)o<Integer.MIN_VALUE||(Long)o>Integer.MAX_VALUE)throw invalid();if(!result.add(o.toString()))throw invalid();}return result;}break;
                case STRING_SET:if(value instanceof List&&((List<?>)value).size()<=8192){Set<String> result=new HashSet<>();for(Object o:(List<?>)value){if(!(o instanceof String)||((String)o).length()>256||!result.add((String)o))throw invalid();}return result;}break;
                case MAP:if(value instanceof Map&&((Map<?,?>)value).size()<=8192){HashMap<Integer,Integer> result=new HashMap<>();for(Map.Entry<?,?> e:((Map<?,?>)value).entrySet()){if(!(e.getKey() instanceof String)||!(e.getValue() instanceof Long))throw invalid();int k;try{k=Integer.parseInt((String)e.getKey());}catch(NumberFormatException bad){throw invalid();}long n=(Long)e.getValue();if(!Integer.toString(k).equals(e.getKey())||n<Integer.MIN_VALUE||n>Integer.MAX_VALUE||result.put(k,(int)n)!=null)throw invalid();}return result;}break;
            }
            throw invalid();
        }
        void write(SharedPreferences.Editor editor,String key,Object encoded) throws IOException {
            Object v=validate(encoded);
            switch(type){
                case BOOL:editor.putBoolean(key,(Boolean)v);break;
                case INT:editor.putInt(key,(Integer)v);break;
                case LONG:editor.putLong(key,(Long)v);break;
                case FLOAT:editor.putFloat(key,(Float)v);break;
                case STRING:editor.putString(key,(String)v);break;
                case STRING_SET:case SET:editor.putStringSet(key,(Set<String>)v);break;
                case MAP:
                    ByteArrayOutputStream bytes=new ByteArrayOutputStream();
                    try(ObjectOutputStream out=new ObjectOutputStream(bytes)){out.writeObject(v);}
                    editor.putString(key,Base64.encodeToString(bytes.toByteArray(),Base64.DEFAULT));break;
            }
        }
    }
    private static IllegalArgumentException invalid(){return new IllegalArgumentException("client_value");}
    private final Map<String,Map<String,Spec>> files=new TreeMap<>();
    SharedPreferences preferences(String file){if(!files.containsKey(file))throw invalid();return file.equals("neko")?NekoConfig.getPreferences():ApplicationLoader.applicationContext.getSharedPreferences(file,Context.MODE_PRIVATE);}
    Map<String,Map<String,Spec>> files(){return files;}
    private void item(ConfigItem item){item(item,"general");}
    private void item(ConfigItem item,String section){if(item.type==7||!portable(item.key))return;Spec spec=new Spec(item.type,item.defaultValue,item);spec.section=section;Spec previous=files.computeIfAbsent("neko",k->new TreeMap<>()).putIfAbsent(item.key,spec);if(previous!=null&&!section.equals("general"))previous.section=section;}
    private static boolean portable(String key){String k=key.toLowerCase(Locale.ROOT).replace("_","");return !k.matches(".*(password|passcode|authkey|token|secret|apikey|apihash|apphash|encryptionkey|deviceid|installid).*" );}
    private void add(String file,String key,int type,Object fallback){Spec spec=new Spec(type,fallback,null);spec.section=section(file,key);files.computeIfAbsent(file,k->new TreeMap<>()).put(key,spec);}
    private static String section(String file,String key){
        switch(file){
            case "flexygram_bubbles":return "bubbles";
            case "flexygram_header":return "header";
            case "flexygram_composer":return "composer";
            case "flexygram_home":case "flexy_bottom_tabs":case "flexy_signature_smart_previews":case "flexygram_scroll_effects":return "home";
            case "flexy_bubble_interaction":case "flexy_delete_motion":return "chat";
            case "aiConfig":return "ai";
            case "exteraless_plugins":return "plugins";
            case "flexygram_motion":return "appearance";
            default:return "general";
        }
    }
    private void range(String file,String key,int min,int max) { Spec spec=files.get(file).get(key);spec.min=min;spec.max=max; }
    private void bool(String f,String k,boolean d){add(f,k,BOOL,d);}private void integer(String f,String k,int d){add(f,k,INT,d);}
    StudioClientCatalog(){
        for(ConfigItem item:NekoConfig.getStudioItems())item(item);
        for(ConfigItem item:NaConfig.INSTANCE.getStudioItems())item(item);
        for(ConfigItem item:OpenExteraConfig.INSTANCE.getStudioItems())item(item);
        for(ConfigItem item:AppearanceConfig.INSTANCE.getStudioItems())item(item,"appearance");
        for(ConfigItem item:GeneralConfig.INSTANCE.getStudioItems())item(item);
        for(ConfigItem item:ChatsConfig.INSTANCE.getStudioItems())item(item,"chat");
        for(ConfigItem item:IconPacksConfig.INSTANCE.getStudioItems())item(item,"appearance");
        for(ConfigItem item:PillStackConfig.INSTANCE.getStudioItems())item(item,"navigation");
        for(ConfigItem item:UtilsConfig.INSTANCE.getStudioItems())item(item);
        for(ConfigItem item:app.exteraless.glyph.GlyphConfig.INSTANCE.getStudioItems())item(item,"appearance");
        // Legacy backups may contain layout 1 or 2; reload migrates both to the sole default.
        integer("flexygram_home","style",0);range("flexygram_home","style",0,2);
        // Retired iOS material keys remain portable metadata for existing backups only.
        // No renderer reads this file or applies its flags.
        bool("flexy_ios_glass","enabled",false);
        integer("flexy_ios_glass","surfaces",15);range("flexy_ios_glass","surfaces",0,15);
        // Retired scroll settings are decoded only for compatibility with existing backups.
        // No renderer or settings screen reads them; importing them cannot enable an effect.
        integer("flexygram_scroll_effects","chats",0);range("flexygram_scroll_effects","chats",0,3);
        integer("flexygram_scroll_effects","conversation",0);range("flexygram_scroll_effects","conversation",0,3);
        integer("flexygram_scroll_effects","intensity",1);range("flexygram_scroll_effects","intensity",0,2);
        integer("flexygram_scroll_effects","curvature",60);range("flexygram_scroll_effects","curvature",0,100);
        String f="flexygram_bubbles";
        integer(f,"shape",0);range(f,"shape",0,2);
        bool(f,"glass",false);bool(f,"border",false);bool(f,"edges",false);integer(f,"transparency",0);integer(f,"signature_border_tenths",11);
        integer(f,"surface_effect",2);bool(f,"small_timestamp",false);
        bool(f,"signature_cached_blur",false);bool(f,"signature_outline_enabled",false);integer(f,"signature_outline_style",1);integer(f,"signature_border_position",5);
        bool(f,"signature_fuse_glass",false);integer(f,"signature_fusion_mode",0);integer(f,"signature_fusion_intensity",60);bool(f,"signature_fusion_adapt",true);integer(f,"signature_pearl_intensity",55);
        f="flexygram_header";integer(f,"style",1);bool(f,"compact",false);bool(f,"counter",true);integer(f,"counter_mode",1);integer(f,"opacity",85);bool(f,"center_title",false);bool(f,"adaptive_bubble",false);
        f="flexygram_composer";integer(f,"style",0);bool(f,"pearlGlass",false);integer(f,"verticalPosition",0);integer(f,"compactLevel",0);integer(f,"iconAppearance",0);integer(f,"componentGap",0);
        f="flexy_bottom_tabs";integer(f,"density_v1",1);bool(f,"show_tabs",true);bool(f,"show_titles",true);bool(f,"double_tap_chats",true);bool(f,"double_tap_profile",true);bool(f,"always_search_chats",false);bool(f,"floating_dock",true);bool(f,"separate_search",false);bool(f,"home_defaults_v2",true);add(f,"tab_order",STRING,"0,1,2,4");
        bool("neko","flexy_quick_member_lens",false);bool("flexy_bubble_interaction","tap_panel",true);
        bool("flexygram_motion","fast_motion_enabled",true);
        integer("flexy_bubble_interaction","menu_layout",0);
        add("flexy_bubble_interaction","menu_actions",STRING_SET,new java.util.HashSet<>(java.util.Arrays.asList("REPLY","COPY","STICKER","FORWARD","PIN","DELETE")));
        integer("flexy_signature_smart_previews","palette",4);integer("flexy_bubble_interaction","interaction_style",1);integer("flexy_delete_motion","message_delete_style",0);bool("flexyfiles_local","enabled",false);
        f="neko";
        bool(f,"flexy_conversion_enabled",false);bool(f,"flexy_conversion_currency",true);add(f,"flexy_conversion_target_currency",STRING,"USD");bool(f,"flexy_conversion_time",true);add(f,"flexy_conversion_target_zone",STRING,"");bool(f,"flexy_conversion_units",true);integer(f,"flexy_conversion_unit_system",0);
        f="mainconfig";
        add(f,"language",STRING,"");
        integer(f,"fons_size",16);integer(f,"iv_font_size",16);integer(f,"bubbleRadius",12);
        for(String k:new String[]{"autoplay_gif","autoplay_video","direct_share","raise_to_listen","next_media_on_tap","inappCamera","streamMedia","saveStreamMedia","pauseMusicOnRecord","allowBigEmoji","suggestAnimatedEmoji","photoViewerBlur","useNewBlur"})bool(f,k,true);
        for(String k:new String[]{"raise_to_speak","record_via_sco","adaptableBrowser","shuffleMusic","playOrderReversed","pauseMusicOnMedia","streamAllVideo","streamMkv","sortContactsByName","sortFilesByName","useThreeLinesLayout","archiveHidden","useSystemEmoji","useSystemBoldFont","forceForumTabs","fastWallpaperDisabled","bigCameraForRound","shadowsInSections","photoHighQualityDefault","photoLiveDefault"})bool(f,k,false);
        integer(f,"lite_mode6",0);integer(f,"lite_mode_battery_level",0);bool(f,"loopStickers",true);bool(f,"chatBlur",true);
        integer(f,"mapPreviewType",2);integer(f,"searchEngineType",0);integer(f,"repeatMode",0);integer(f,"suggestStickers",0);integer(f,"distanceSystemType",0);integer(f,"ChatSwipeAction",-1);integer(f,"mediaColumnsCount",3);integer(f,"storiesColumnsCount",3);
        // Native legacy ranges also apply to the full backup path.
        for(app.flexygram.studio.core.StudioSchema.Key key:app.flexygram.studio.core.StudioSchema.keys()) {
            if(key.defaultValue instanceof Integer) {
                Map<String,Spec> file=files.get(key.file);
                Spec spec=file==null?null:file.get(key.preference);
                if(spec==null)throw new IllegalStateException("studio_catalog_schema");
                spec.legacyKey=key;
            }
        }
        range("mainconfig","fons_size",8,72);range("mainconfig","iv_font_size",8,72);range("mainconfig","bubbleRadius",0,40);
        range("mainconfig","lite_mode_battery_level",0,100);
        f="aiConfig";bool(f,"saveHistory",true);bool(f,"responseStreaming",true);bool(f,"showResponseOnly",false);bool(f,"insertAsQuote",true);bool(f,"disableTools",false);integer(f,"temperature",10);add(f,"selectedRole",STRING,"");
        f="exteraless_plugins";bool(f,"plugins_compact_view",false);
    }
}
