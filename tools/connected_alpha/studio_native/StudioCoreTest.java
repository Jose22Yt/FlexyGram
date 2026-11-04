import app.flexygram.studio.core.*;
import java.io.*;import java.nio.charset.StandardCharsets;import java.util.*;
/** JVM tests of actual production codec/transaction. No Android playback/auth/device claims. */
public class StudioCoreTest {
 static int checks;
 static void check(boolean condition){checks++;if(!condition)throw new AssertionError("case "+checks);}
 static void reject(Runnable r){try{r.run();throw new AssertionError("accepted hostile input");}catch(IllegalArgumentException expected){checks++;}}
 static Map<String,Map<String,Object>> defaults(){Map<String,Map<String,Object>> out=new LinkedHashMap<>();for(StudioSchema.Key k:StudioSchema.keys())if(!k.section.equals("client"))out.computeIfAbsent(k.section,x->new LinkedHashMap<>()).put(k.id,k.defaultValue);return out;}
 static StudioCodec.Preset bubbles(){Map<String,Map<String,Object>> m=new HashMap<>();m.put("bubbles",new HashMap<>(Map.of("transparency",74)));return StudioCodec.create("SoloBurbujas.flexyGram",m);}
 static final class Memory implements StudioTransaction.Backend {
  Map<StudioSchema.Key,StudioTransaction.Slot> data=new LinkedHashMap<>(),journal;
  Map<String,Integer> writes=new HashMap<>();int failAt=-1,attempt;boolean failRollback;
  public StudioTransaction.Slot read(StudioSchema.Key k){return data.getOrDefault(k,new StudioTransaction.Slot(false,k.defaultValue));}
  public void journal(Map<StudioSchema.Key,StudioTransaction.Slot> old){journal=new LinkedHashMap<>(old);}
  public void clearJournal(){journal=null;}
  public void write(String file,Map<StudioSchema.Key,StudioTransaction.Slot> values)throws Exception{
   writes.merge(file,1,Integer::sum);data.putAll(values);
   if(attempt++==failAt||failRollback&&attempt>failAt)throw new IOException("synthetic disk fault");
  }
 }
 public static void main(String[] args)throws Exception {
  check(StudioSchema.keys().size()==24);
  for(String key:new String[]{"outlineStyle","pearlIntensity","outlineEnabled"}){
   Object valid=key.equals("outlineEnabled")?Boolean.FALSE:key.equals("outlineStyle")?1:72;
   var preset=StudioCodec.create("Pearl.flexyGram",Map.of("bubbles",Map.of(key,valid)));check(preset.minApp==1274);
   check(StudioCodec.decode(StudioCodec.encode(preset),1274).sections.get("bubbles").get(key).equals(valid));reject(()->StudioCodec.decode(StudioCodec.encode(preset),1273));
  }
  reject(()->StudioCodec.create("bad.flexyGram",Map.of("bubbles",Map.of("outlineStyle",4))));
  for(int style:new int[]{2,3}){
   var newStyle=StudioCodec.create("Finish.flexyGram",Map.of("bubbles",Map.of("outlineStyle",style)));
   check(newStyle.minApp==1276);check(StudioCodec.decode(StudioCodec.encode(newStyle),1276).sections.get("bubbles").get("outlineStyle").equals(style));
   reject(()->StudioCodec.decode(StudioCodec.encode(newStyle),1275));
  }
  var fusion=StudioCodec.create("Fusion.flexyGram",Map.of("header",Map.of("style",2)));
  check(fusion.minApp==1276);check(StudioCodec.decode(StudioCodec.encode(fusion),1276).sections.get("header").get("style").equals(2));
  reject(()->StudioCodec.decode(StudioCodec.encode(fusion),1275));
  check(StudioCodec.create("new.flexyGram",Map.of("header",Map.of("style",3))).minApp==1290);reject(()->StudioCodec.create("bad.flexyGram",Map.of("header",Map.of("style",4))));
  for(String key:new String[]{"borderPosition","fuseGlass"}){
   Object value=key.equals("borderPosition")?3:Boolean.TRUE;var newSetting=StudioCodec.create("Contour.flexyGram",Map.of("bubbles",Map.of(key,value)));
   check(newSetting.minApp==1276);check(StudioCodec.decode(StudioCodec.encode(newSetting),1276).sections.get("bubbles").get(key).equals(value));
   reject(()->StudioCodec.decode(StudioCodec.encode(newSetting),1275));
  }
  reject(()->StudioCodec.create("bad.flexyGram",Map.of("bubbles",Map.of("pearlIntensity",101))));
  reject(()->StudioCodec.create("bad.flexyGram",Map.of("header",Map.of("counterPresentation",0))));
  var defaults=defaults();reject(()->StudioCodec.export("MiFlexyGram.flexyGram",defaults,Set.of()));
  defaults.get("bubbles").put("transparency",74);
  var one=StudioCodec.export("SoloBurbujas.flexyGram",defaults,Set.of());check(one.sections.keySet().equals(Set.of("bubbles")));check(one.sections.get("bubbles").size()==1);
  defaults.get("header").put("compact",true);defaults.get("composer").put("style",1);
  var three=StudioCodec.export("Tres.flexyGram",defaults,Set.of());check(three.sections.size()==3);
  var full=StudioCodec.export("Completo.flexyGram",defaults,StudioSchema.sections());check(full.sections.size()==4);check(full.sections.values().stream().mapToInt(Map::size).sum()==StudioSchema.keys().size()-1);
  byte[] encoded=StudioCodec.encode(full);check(Arrays.equals(encoded,StudioCodec.encode(StudioCodec.decode(encoded,1276))));
  check(full.minApp==1276);reject(()->StudioCodec.decode(encoded,1275));
  var legacy=defaults();legacy.get("bubbles").remove("borderPosition");legacy.get("bubbles").remove("fuseGlass");
  var legacyPreset=StudioCodec.export("Legacy.flexyGram",legacy,StudioSchema.sections());check(legacyPreset.minApp==1274);check(StudioCodec.decode(StudioCodec.encode(legacyPreset),1276).sections.equals(legacyPreset.sections));
  Map<String,Map<String,Object>> reversed=new LinkedHashMap<>();List<String> ids=new ArrayList<>(full.sections.keySet());Collections.reverse(ids);for(String s:ids)reversed.put(s,full.sections.get(s));check(Arrays.equals(encoded,StudioCodec.encode(StudioCodec.create(full.name,reversed))));
  check(StudioCodec.decode(StudioCodec.encode(one),1273).sections.equals(one.sections));
  try{one.sections.put("icon",Map.of());throw new AssertionError();}catch(UnsupportedOperationException expected){checks++;}
  try{one.sections.get("bubbles").put("glass",true);throw new AssertionError();}catch(UnsupportedOperationException expected){checks++;}
  String json=new String(StudioCodec.encode(one),StandardCharsets.UTF_8);
  for(String mutation:new String[]{json+"{}",json.substring(0,json.length()-1),json.replace("74","75"),json.replace("\"schema\":1","\"schema\":2"),json.replace("\"minApp\":1273","\"minApp\":1274"),json.replace("\"transparency\":74","\"api_hash\":74"),json.replace("\"bubbles\"","\"auth\""),json.replace("\"transparency\":74","\"transparency\":-1"),json.replace("\"transparency\":74","\"transparency\":101"),json.replace("\"transparency\":74","\"transparency\":true"),json.replace("\"transparency\":74","\"transparency\":74.0"),json.replace("\"transparency\":74","\"transparency\":1e2"),json.replace("\"schema\":1","\"schema\":1,\"schema\":1"),json.replace("\"transparency\":74","\"transparency\":74,\"transparency\":74"),json.replace("\"transparency\":74","\"transparency\":null"),json.replace("\"name\":","\"unknown\":true,\"name\":"),json.replace("SoloBurbujas.flexyGram","../SoloBurbujas.flexyGram"),json.replace("SoloBurbujas.flexyGram" ,"SoloBurbujas.flexygram"),json.replace("SoloBurbujas.flexyGram","\\ud800.flexyGram"),"[".repeat(40)+"0"+"]".repeat(40),"{\"x\":\""+"x".repeat(257)+"\"}"})reject(()->StudioCodec.decode(mutation.getBytes(StandardCharsets.UTF_8),1273));
  reject(()->StudioCodec.decode(new byte[]{(byte)0xff},1273));reject(()->StudioCodec.decode(new byte[StudioSchema.MAX_BYTES+1],1273));
  for(String name:new String[]{"x.flexyGram.zip",".flexyGram","x.flexyGram\u202e","/x.flexyGram","x\\x.flexyGram","x\n.flexyGram"})check(!StudioSchema.filename(name));
  check(StudioSchema.filename("x.flexygram"));check(StudioSchema.filename("Синий стиль.flexyGram"));check(StudioSchema.filename("Estilo perla ✨.flexyGram"));
  var untrusted=Map.of("bubbles",Map.<String,Object>of("auth_key","secret"));reject(()->StudioCodec.create("x.flexyGram",untrusted));
  var gap=Map.of("composer",Map.<String,Object>of("gap",1));reject(()->StudioCodec.create("x.flexyGram",gap));
  try{StudioCodec.readLimited(new ByteArrayInputStream(new byte[StudioSchema.MAX_BYTES+1]));throw new AssertionError();}catch(IOException expected){checks++;}
  check(StudioCodec.readLimited(new ByteArrayInputStream(new byte[65536])).length==65536);
  Memory backend=new Memory();var receipt=StudioTransaction.apply(backend,three);check(backend.journal==null);check(backend.writes.size()==3);check(backend.writes.values().stream().allMatch(v->v==1));
  StudioTransaction.undo(backend,receipt);for(StudioSchema.Key key:receipt.before.keySet())check(backend.read(key).equals(receipt.before.get(key)));
  var second=StudioTransaction.apply(backend,one);StudioSchema.Key transparency=StudioSchema.key("bubbles","transparency");backend.data.put(transparency,new StudioTransaction.Slot(true,52));
  try{StudioTransaction.undo(backend,second);throw new AssertionError();}catch(IllegalStateException conflict){checks++;}check(backend.read(transparency).value.equals(52));
  for(int fail=0;fail<3;fail++){Memory broken=new Memory();broken.failAt=fail;try{StudioTransaction.apply(broken,three);throw new AssertionError();}catch(StudioTransaction.Failure expected){check(!expected.rollbackFailed);}check(broken.journal==null);for(StudioSchema.Key k:receipt.before.keySet())check(!broken.read(k).present);}
  Memory persistent=new Memory();persistent.failAt=0;persistent.failRollback=true;
  try{StudioTransaction.apply(persistent,three);throw new AssertionError();}catch(StudioTransaction.Failure expected){check(expected.rollbackFailed);}check(persistent.journal!=null);
  persistent.failAt=-1;persistent.failRollback=false;StudioTransaction.recover(persistent,persistent.journal);check(persistent.journal==null);
  // Bounded hostile corpus; acceptance can only be a fully validated known-key preset.
  var bundle=StudioCodec.encodeValues(Map.of("version",1,"files",Map.of("native",Map.of("flag",Map.of("present",true,"value",true))),"text","a\n\t\"☀️","long",Long.MIN_VALUE));
  check(StudioCodec.encodeValues(StudioCodec.decodeValues(bundle)).equals(bundle));
  var client=StudioCodec.create("All.flexygram",Map.of("client",Map.of("settings",bundle)));
  check(client.minApp==1291);check(StudioCodec.decode(StudioCodec.encode(client),1291).sections.equals(client.sections));
  reject(()->StudioCodec.decode(StudioCodec.encode(client),1290));
  reject(()->StudioCodec.create("All.flexyGram",Map.of("client",Map.of("settings",bundle),"bubbles",Map.of("glass",true))));
  var longString="x".repeat(100000);check(StudioCodec.decodeValues(StudioCodec.encodeValues(longString)).equals(longString));
  reject(()->StudioCodec.decodeValues("{\"x\":1,\"x\":2}"));
  reject(()->StudioCodec.decodeValues("9223372036854775808"));
  var journalBytes=new ByteArrayOutputStream();
  var journalSlots=Map.of(StudioSchema.key("client","settings"),new StudioTransaction.Slot(true,longString));
  StudioJournal.write(journalBytes,journalSlots);byte[] binary=journalBytes.toByteArray();
  check(StudioJournal.read(new ByteArrayInputStream(binary),binary.length).equals(journalSlots));
  try{StudioJournal.read(new ByteArrayInputStream(Arrays.copyOf(binary,binary.length-1)),binary.length-1);throw new AssertionError();}catch(IOException expected){checks++;}
  var oldBytes=new ByteArrayOutputStream();var oldOut=new DataOutputStream(oldBytes);
  oldOut.writeInt(0x46534731);oldOut.writeInt(1);oldOut.writeUTF("header");oldOut.writeUTF("compact");oldOut.writeBoolean(false);oldOut.writeBoolean(true);
  check(StudioJournal.read(new ByteArrayInputStream(oldBytes.toByteArray()),oldBytes.size()).get(StudioSchema.key("header","compact")).equals(new StudioTransaction.Slot(false,true)));
  Random random=new Random(54129);for(int i=0;i<5000;i++){byte[] mutant=StudioCodec.encode(one);for(int j=0;j<1+random.nextInt(4);j++)mutant[random.nextInt(mutant.length)]=(byte)random.nextInt(256);try{var parsed=StudioCodec.decode(mutant,1273);check(Arrays.equals(StudioCodec.encode(parsed),StudioCodec.encode(one)));}catch(IllegalArgumentException expected){checks++;}}
  System.out.println("PASS actual codec/transaction checks="+checks+" hostile_mutations=5000; Android runtime NOT_TESTED");
 }
}
