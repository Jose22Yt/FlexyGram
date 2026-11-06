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
  public StudioTransaction.Slot readForChange(StudioSchema.Key k,StudioTransaction.Slot scope){return new StudioTransaction.Slot(true,StudioClientBackup.snapshotLike((String)scope.value));}
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
  put("flexy_bubble_interaction","menu_actions",Set.of("REPLY","COPY","MORE"));
  String saved=StudioClientBackup.snapshot();check(!saved.contains("private"));check(!saved.contains("ApiKey"));check(!saved.contains("ApiToken"));check(!saved.contains("AuthSecret"));check(!saved.contains("userconfing"));
  var preset=StudioCodec.create("Complete.flexygram",Map.of("client",Map.of("settings",saved)));
  var decoded=StudioCodec.decode(StudioCodec.encode(preset),1291);StudioClientBackup.validate((String)decoded.sections.get("client").get("settings"));
  StudioClientBackup.apply(defaults);check(!disk.get("nkmrcfg").containsKey("flag"));check(disk.get("nkmrcfg").get("LlmApiKey").equals("private"));
  StudioClientBackup.apply(saved);check(disk.get("nkmrcfg").get("number") instanceof Integer);check(disk.get("nkmrcfg").get("number").equals(27));check(disk.get("nkmrcfg").get("float").equals(1.25f));check(disk.get("nkmrcfg").get("long").equals(Long.MIN_VALUE));check(disk.get("nkmrcfg").get("set").equals(Set.of("9","-4")));check(nativeItems.get(4).value.equals(Map.of(42,-99)));check(disk.get("flexygram_header").get("style").equals(3));check(saved.equals(StudioClientBackup.snapshot()));
  Map<String,Object> hostile=root(saved);file(hostile,"neko").put("LlmApiKey",Map.of("present",true,"value","stolen"));String secretAttempt=StudioCodec.encodeValues(hostile);reject(()->StudioClientBackup.apply(secretAttempt));check(saved.equals(StudioClientBackup.snapshot()));
  put("flexygram_header","style",4);String floating=StudioClientBackup.snapshot();StudioClientBackup.apply(defaults);StudioClientBackup.apply(floating);check(disk.get("flexygram_header").get("style").equals(4));StudioClientBackup.apply(saved);
  hostile=root(saved);file(hostile,"flexygram_header").put("style",Map.of("present",true,"value",5));String bad=StudioCodec.encodeValues(hostile);reject(()->StudioClientBackup.apply(bad));
  hostile=root(saved);file(hostile,"flexygram_composer").put("componentGap",Map.of("present",true,"value",1));String badGap=StudioCodec.encodeValues(hostile);reject(()->StudioClientBackup.apply(badGap));
  var spec=new StudioClientCatalog().files().get("neko");reject(()->spec.get("number").validate(2147483648L));reject(()->spec.get("float").validate("NaN"));reject(()->spec.get("set").validate(List.of(1L,1L)));reject(()->spec.get("map").validate(Map.of("01",2L)));
  StudioClientBackup.apply(defaults);Backend backend=new Backend();var receipt=StudioTransaction.apply(backend,preset);check(saved.equals(StudioClientBackup.snapshot()));StudioTransaction.undo(backend,receipt);check(defaults.equals(StudioClientBackup.snapshot()));
  receipt=StudioTransaction.apply(backend,preset);put("flexygram_header","compact",true);try{StudioTransaction.undo(backend,receipt);throw new AssertionError("lost edit");}catch(IllegalStateException conflict){checks++;}
  StudioClientBackup.apply(defaults);failFile="flexygram_header";try{StudioTransaction.apply(backend,preset);throw new AssertionError("ignored disk fault");}catch(StudioTransaction.Failure failure){check(!failure.rollbackFailed);}check(defaults.equals(StudioClientBackup.snapshot()));check(backend.journal==null);
  // Preview is read-only. Apply/undo only selected changed keys; unrelated later edits survive.
  StudioClientBackup.apply(defaults);
  var plan=StudioImportPlan.prepare(preset);
  check(defaults.equals(StudioClientBackup.snapshot()));
  check(plan.changedGroups().containsAll(Set.of("header","composer","chat")));
  var headerOnly=plan.select(Set.of("header"));
  var partialRoot=root((String)headerOnly.sections.get("client").get("settings"));
  check(StudioClientBackup.object(partialRoot.get("files")).keySet().equals(Set.of("flexygram_header")));
  check(!partialRoot.containsKey("theme")&&!partialRoot.containsKey("icon"));
  receipt=StudioTransaction.apply(backend,headerOnly);
  check(disk.get("flexygram_header").get("style").equals(3));
  check(!disk.get("flexygram_composer").containsKey("componentGap"));
  put("flexygram_composer","componentGap",4);StudioTransaction.undo(backend,receipt);
  check(disk.get("flexygram_composer").get("componentGap").equals(4));
  check(!disk.get("flexygram_header").containsKey("style"));
  receipt=StudioTransaction.apply(backend,headerOnly);put("flexygram_header","style",2);
  try{StudioTransaction.undo(backend,receipt);throw new AssertionError("selected conflict ignored");}catch(IllegalStateException expected){checks++;}
  reject(()->plan.select(Set.of()));reject(()->plan.select(Set.of("unknown")));
  StudioClientBackup.apply(saved);check(StudioImportPlan.prepare(preset).changedGroups().isEmpty());
  check(disk.get("flexy_bubble_interaction").get("menu_actions").equals(Set.of("REPLY","COPY","MORE")));
  var badSet=root(saved);file(badSet,"flexy_bubble_interaction").put("menu_actions",Map.of("present",true,"value",List.of(4L)));
  reject(()->StudioClientBackup.validate(StudioCodec.encodeValues(badSet)));
  // Fine-grained selection: unchecked keys in the same section and the active theme stay intact.
  {
   StudioClientBackup.apply(defaults);
   Map<String,Object> candidateRoot=root(saved);candidateRoot.put("theme",Map.of("colors",Map.of("test",2L)));
   var candidate=StudioCodec.create("Granular.flexygram",Map.of("client",Map.of("settings",StudioCodec.encodeValues(candidateRoot))));
   var granular=StudioImportPlan.prepare(candidate);
   check(granular.changedGroups().contains("theme"));
   var noTheme=root((String)granular.selectChanges(granular.defaultSelection()).sections.get("client").get("settings"));
   check(!noTheme.containsKey("theme"));
   String token=null,themeToken=null;
   for(var group:granular.groups)for(var change:group.changes){
    if(change.file.equals("flexygram_header")&&change.key.equals("style"))token=StudioImportPlan.selectionKey(group,change);
    if(group.id.equals("theme"))themeToken=StudioImportPlan.selectionKey(group,change);
   }
   check(token!=null&&themeToken!=null);var onlyStyle=granular.selectChanges(Set.of(token));
   var selectedRoot=root((String)onlyStyle.sections.get("client").get("settings"));
   check(StudioClientBackup.object(selectedRoot.get("files")).keySet().equals(Set.of("flexygram_header")));
   check(file(selectedRoot,"flexygram_header").keySet().equals(Set.of("style")));
   int themeCalls=StudioClientTheme.applies;put("flexygram_header","compact",true);
   var selectiveReceipt=StudioTransaction.apply(backend,onlyStyle);
   check(StudioClientTheme.applies==themeCalls);
   check(disk.get("flexygram_header").get("style").equals(3));
   check(disk.get("flexygram_header").get("compact").equals(true));
   check(!disk.get("flexygram_composer").containsKey("componentGap"));
   StudioTransaction.undo(backend,selectiveReceipt);
   check(StudioClientTheme.applies==themeCalls&&disk.get("flexygram_header").get("compact").equals(true));
   var onlyTheme=root((String)granular.selectChanges(Set.of(themeToken)).sections.get("client").get("settings"));
   check(onlyTheme.containsKey("theme")&&StudioClientBackup.object(onlyTheme.get("files")).isEmpty());
   reject(()->granular.selectChanges(Set.of()));reject(()->granular.selectChanges(Set.of("unknown")));
   StudioClientBackup.apply(defaults);
   var legacy=StudioImportPlan.prepare(StudioCodec.create("Legacy.flexyGram",Map.of("header",Map.of("style",1,"compact",true))));
   String compactToken=null;for(var group:legacy.groups)for(var change:group.changes)if(change.key.equals("compact"))compactToken=StudioImportPlan.selectionKey(group,change);
   check(compactToken!=null&&legacy.selectChanges(Set.of(compactToken)).sections.equals(Map.of("header",Map.of("compact",true))));
   StudioClientBackup.apply(saved);
  }
  System.out.println("Studio client checks="+checks+"; complete/default round trips, typed values, secrets excluded, undo conflicts and mid-import disk rollback passed; persistence/theme are doubles.");
 }
}
