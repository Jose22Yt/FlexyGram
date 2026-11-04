package app.flexygram.studio;
import app.flexygram.studio.core.*;
import tw.nekomimi.nekogram.config.ConfigItem;
import java.lang.reflect.*;
import java.util.*;
import android.content.SharedPreferences;

/** Production catalog, backup, codec and transactions; Android persistence/theme/owners are explicit doubles. */
public class StudioClientTest {
 static int checks;static void check(boolean b){checks++;if(!b)throw new AssertionError("case "+checks);}
 interface Action{void run()throws Exception;}
 static void reject(Action action)throws Exception{try{action.run();throw new AssertionError("accepted");}catch(IllegalArgumentException expected){checks++;}}
 static final Map<String,Map<String,Object>> disk=new HashMap<>();static String failFile;
 public static SharedPreferences preferences(String file){
  return (SharedPreferences)Proxy.newProxyInstance(StudioClientTest.class.getClassLoader(),new Class[]{SharedPreferences.class},(proxy,m,args)->{
   Map<String,Object> data=disk.computeIfAbsent(file,k->new HashMap<>());
   if(m.getName().equals("getAll"))return new HashMap<>(data);
   if(m.getName().equals("contains"))return data.containsKey(args[0]);
   if(m.getName().startsWith("get"))return data.getOrDefault(args[0],args[1]);
   if(m.getName().equals("edit")){
    Map<String,Object> edits=new HashMap<>();Set<String> removed=new HashSet<>();
    return Proxy.newProxyInstance(StudioClientTest.class.getClassLoader(),new Class[]{SharedPreferences.Editor.class},(p,e,a)->{
     if(e.getName().startsWith("put")){edits.put((String)a[0],a[1]);removed.remove(a[0]);return p;}
     if(e.getName().equals("remove")){removed.add((String)a[0]);edits.remove(a[0]);return p;}
     if(e.getName().equals("commit")||e.getName().equals("apply")){
      if(file.equals(failFile)){failFile=null;return false;}
      removed.forEach(data::remove);data.putAll(edits);
      // Native ConfigItem cache is reloaded by the bridge; simulate typed native maps only.
      for(ConfigItem item:tw.nekomimi.nekogram.NekoConfig.items)if(item.type==4&&edits.containsKey(item.key)){
       try(var in=new java.io.ObjectInputStream(new java.io.ByteArrayInputStream(java.util.Base64.getDecoder().decode((String)edits.get(item.key))))){item.value=in.readObject();}
      }
      return e.getName().equals("commit")?true:null;
     }
     return null;
    });
   }
   return null;
  });
 }
 static Map<String,Object> root(String s){return StudioClientBackup.object(StudioCodec.decodeValues(s));}
 static Map<String,Object> file(Map<String,Object> root,String f){return StudioClientBackup.object(StudioClientBackup.object(root.get("files")).get(f));}
 static void put(String file,String key,Object value){disk.computeIfAbsent(file,k->new HashMap<>()).put(key,value);}
 static class Backend implements StudioTransaction.Backend {
  Map<StudioSchema.Key,StudioTransaction.Slot> journal;
  public StudioTransaction.Slot read(StudioSchema.Key k){return new StudioTransaction.Slot(true,StudioClientBackup.snapshot());}
  public void write(String f,Map<StudioSchema.Key,StudioTransaction.Slot> values)throws Exception{StudioClientBackup.apply((String)values.values().iterator().next().value);}
  public void journal(Map<StudioSchema.Key,StudioTransaction.Slot> before){journal=before;}
  public void clearJournal(){journal=null;}
 }
 public static void main(String[] args)throws Exception {
  var nativeItems=tw.nekomimi.nekogram.NekoConfig.items;
  nativeItems.addAll(List.of(new ConfigItem("flag",0,false),new ConfigItem("number",1,1),new ConfigItem("text",2,""),new ConfigItem("set",3,new HashSet<>()),new ConfigItem("map",4,new HashMap<>()),new ConfigItem("long",5,0L),new ConfigItem("float",6,0f),new ConfigItem("LlmApiKey",2,""),new ConfigItem("PushServiceTypeUnifiedWebPushAuthSecret",2,""),new ConfigItem("TranscribeProviderCfApiToken",2,"")));
  String defaults=StudioClientBackup.snapshot();check(StudioClientBackup.validate(defaults)!=null);
  var defaultPreset=StudioCodec.create("Defaults.flexyGram",Map.of("client",Map.of("settings",defaults)));check(StudioCodec.encode(defaultPreset).length>0);
  put("nkmrcfg","flag",true);put("nkmrcfg","number",27);put("nkmrcfg","text","línea 1\nlínea 2 😎");put("nkmrcfg","set",Set.of("9","-4"));put("nkmrcfg","long",Long.MIN_VALUE);put("nkmrcfg","float",1.25f);
  put("nkmrcfg","map","native serialized map");nativeItems.get(4).value=new HashMap<>(Map.of(42,-99));
  put("nkmrcfg","LlmApiKey","private");put("nkmrcfg","PushServiceTypeUnifiedWebPushAuthSecret","private");put("nkmrcfg","TranscribeProviderCfApiToken","private");
  put("userconfing","authKey","private session");put("mainconfig","passcodeHash1","private lock");
  put("flexygram_header","style",3);put("flexygram_composer","componentGap",8);put("flexygram_bubbles","signature_fusion_mode",2);put("flexy_bottom_tabs","show_titles",false);put("mainconfig","lite_mode6",4095);
  String saved=StudioClientBackup.snapshot();check(!saved.contains("private"));check(!saved.contains("ApiKey"));check(!saved.contains("ApiToken"));check(!saved.contains("AuthSecret"));check(!saved.contains("userconfing"));
  var preset=StudioCodec.create("Complete.flexygram",Map.of("client",Map.of("settings",saved)));
  var decoded=StudioCodec.decode(StudioCodec.encode(preset),1291);StudioClientBackup.validate((String)decoded.sections.get("client").get("settings"));
  StudioClientBackup.apply(defaults);check(!disk.get("nkmrcfg").containsKey("flag"));check(disk.get("nkmrcfg").get("LlmApiKey").equals("private"));
  StudioClientBackup.apply(saved);check(disk.get("nkmrcfg").get("number") instanceof Integer);check(disk.get("nkmrcfg").get("number").equals(27));check(disk.get("nkmrcfg").get("float").equals(1.25f));check(disk.get("nkmrcfg").get("long").equals(Long.MIN_VALUE));check(disk.get("nkmrcfg").get("set").equals(Set.of("9","-4")));check(nativeItems.get(4).value.equals(Map.of(42,-99)));check(disk.get("flexygram_header").get("style").equals(3));check(saved.equals(StudioClientBackup.snapshot()));
  Map<String,Object> hostile=root(saved);file(hostile,"neko").put("LlmApiKey",Map.of("present",true,"value","stolen"));String secretAttempt=StudioCodec.encodeValues(hostile);reject(()->StudioClientBackup.apply(secretAttempt));check(saved.equals(StudioClientBackup.snapshot()));
  hostile=root(saved);file(hostile,"flexygram_header").put("style",Map.of("present",true,"value",4));String bad=StudioCodec.encodeValues(hostile);reject(()->StudioClientBackup.apply(bad));
  hostile=root(saved);file(hostile,"flexygram_composer").put("componentGap",Map.of("present",true,"value",1));String badGap=StudioCodec.encodeValues(hostile);reject(()->StudioClientBackup.apply(badGap));
  var spec=new StudioClientCatalog().files().get("neko");reject(()->spec.get("number").validate(2147483648L));reject(()->spec.get("float").validate("NaN"));reject(()->spec.get("set").validate(List.of(1L,1L)));reject(()->spec.get("map").validate(Map.of("01",2L)));
  StudioClientBackup.apply(defaults);Backend backend=new Backend();var receipt=StudioTransaction.apply(backend,preset);check(saved.equals(StudioClientBackup.snapshot()));StudioTransaction.undo(backend,receipt);check(defaults.equals(StudioClientBackup.snapshot()));
  receipt=StudioTransaction.apply(backend,preset);put("flexygram_header","compact",true);try{StudioTransaction.undo(backend,receipt);throw new AssertionError("lost edit");}catch(IllegalStateException conflict){checks++;}
  StudioClientBackup.apply(defaults);failFile="flexygram_header";try{StudioTransaction.apply(backend,preset);throw new AssertionError("ignored disk fault");}catch(StudioTransaction.Failure failure){check(!failure.rollbackFailed);}check(defaults.equals(StudioClientBackup.snapshot()));check(backend.journal==null);
  System.out.println("Studio client checks="+checks+"; complete/default round trips, typed values, secrets excluded, undo conflicts and mid-import disk rollback passed; persistence/theme are doubles.");
 }
}
