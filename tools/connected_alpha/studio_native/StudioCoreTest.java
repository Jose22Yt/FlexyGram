import app.flexygram.studio.core.*;
import java.io.*;import java.nio.charset.StandardCharsets;import java.util.*;
/** JVM tests of actual production codec/transaction. No Android playback/auth/device claims. */
public class StudioCoreTest {
 static int checks;
 static void check(boolean condition){checks++;if(!condition)throw new AssertionError("case "+checks);}
 static void reject(Runnable r){try{r.run();throw new AssertionError("accepted hostile input");}catch(IllegalArgumentException expected){checks++;}}
 static Map<String,Map<String,Object>> defaults(){Map<String,Map<String,Object>> out=new LinkedHashMap<>();for(StudioSchema.Key k:StudioSchema.keys())out.computeIfAbsent(k.section,x->new LinkedHashMap<>()).put(k.id,k.defaultValue);return out;}
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
  var defaults=defaults();reject(()->StudioCodec.export("MiFlexyGram.flexyGram",defaults,Set.of()));
  defaults.get("bubbles").put("transparency",74);
  var one=StudioCodec.export("SoloBurbujas.flexyGram",defaults,Set.of());check(one.sections.keySet().equals(Set.of("bubbles")));check(one.sections.get("bubbles").size()==1);
  defaults.get("header").put("compact",true);defaults.get("composer").put("style",1);
  var three=StudioCodec.export("Tres.flexyGram",defaults,Set.of());check(three.sections.size()==3);
  var full=StudioCodec.export("Completo.flexyGram",defaults,StudioSchema.sections());check(full.sections.size()==4);check(full.sections.values().stream().mapToInt(Map::size).sum()==StudioSchema.keys().size());
  byte[] encoded=StudioCodec.encode(full);check(Arrays.equals(encoded,StudioCodec.encode(StudioCodec.decode(encoded,1274))));
  check(full.minApp==1274);reject(()->StudioCodec.decode(encoded,1273));
  Map<String,Map<String,Object>> reversed=new LinkedHashMap<>();List<String> ids=new ArrayList<>(full.sections.keySet());Collections.reverse(ids);for(String s:ids)reversed.put(s,full.sections.get(s));check(Arrays.equals(encoded,StudioCodec.encode(StudioCodec.create(full.name,reversed))));
  check(StudioCodec.decode(StudioCodec.encode(one),1273).sections.equals(one.sections));
  try{one.sections.put("icon",Map.of());throw new AssertionError();}catch(UnsupportedOperationException expected){checks++;}
  try{one.sections.get("bubbles").put("glass",true);throw new AssertionError();}catch(UnsupportedOperationException expected){checks++;}
  String json=new String(StudioCodec.encode(one),StandardCharsets.UTF_8);
  for(String mutation:new String[]{json+"{}",json.substring(0,json.length()-1),json.replace("74","75"),json.replace("\"schema\":1","\"schema\":2"),json.replace("\"minApp\":1273","\"minApp\":1274"),json.replace("\"transparency\":74","\"api_hash\":74"),json.replace("\"bubbles\"","\"auth\""),json.replace("\"transparency\":74","\"transparency\":-1"),json.replace("\"transparency\":74","\"transparency\":101"),json.replace("\"transparency\":74","\"transparency\":true"),json.replace("\"transparency\":74","\"transparency\":74.0"),json.replace("\"transparency\":74","\"transparency\":1e2"),json.replace("\"schema\":1","\"schema\":1,\"schema\":1"),json.replace("\"transparency\":74","\"transparency\":74,\"transparency\":74"),json.replace("\"transparency\":74","\"transparency\":null"),json.replace("\"name\":","\"unknown\":true,\"name\":"),json.replace("SoloBurbujas.flexyGram","../SoloBurbujas.flexyGram"),json.replace("SoloBurbujas.flexyGram","SoloBurbujas.flexygram"),json.replace("SoloBurbujas.flexyGram","\\ud800.flexyGram"),"[".repeat(40)+"0"+"]".repeat(40),"{\"x\":\""+"x".repeat(257)+"\"}"})reject(()->StudioCodec.decode(mutation.getBytes(StandardCharsets.UTF_8),1273));
  reject(()->StudioCodec.decode(new byte[]{(byte)0xff},1273));reject(()->StudioCodec.decode(new byte[StudioSchema.MAX_BYTES+1],1273));
  for(String name:new String[]{"x.flexyGram.zip","x.flexygram",".flexyGram","x.flexyGram\u202e","/x.flexyGram","x\\x.flexyGram","x\n.flexyGram"})check(!StudioSchema.filename(name));
  check(StudioSchema.filename("Синий стиль.flexyGram"));check(StudioSchema.filename("Estilo perla ✨.flexyGram"));
  var untrusted=Map.of("bubbles",Map.<String,Object>of("auth_key","secret"));reject(()->StudioCodec.create("x.flexyGram",untrusted));
  var gap=Map.of("composer",Map.<String,Object>of("gap",1));reject(()->StudioCodec.create("x.flexyGram",gap));
  try{StudioCodec.readLimited(new ByteArrayInputStream(new byte[65537]));throw new AssertionError();}catch(IOException expected){checks++;}
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
  Random random=new Random(54129);for(int i=0;i<5000;i++){byte[] mutant=StudioCodec.encode(one);for(int j=0;j<1+random.nextInt(4);j++)mutant[random.nextInt(mutant.length)]=(byte)random.nextInt(256);try{var parsed=StudioCodec.decode(mutant,1273);check(Arrays.equals(StudioCodec.encode(parsed),StudioCodec.encode(one)));}catch(IllegalArgumentException expected){checks++;}}
  System.out.println("PASS actual codec/transaction checks="+checks+" hostile_mutations=5000; Android runtime NOT_TESTED");
 }
}
