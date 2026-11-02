import app.flexygram.studio.core.*;
import java.util.*;
/** Synthetic host JVM only. Does not measure Android UI, I/O, touch latency or jank. */
public class StudioCodecBenchmark {
 public static void main(String[] args){
  Map<String,Map<String,Object>> values=new LinkedHashMap<>();
  for(StudioSchema.Key key:StudioSchema.keys())values.computeIfAbsent(key.section,k->new LinkedHashMap<>()).put(key.id,key.defaultValue);
  byte[] data=StudioCodec.encode(StudioCodec.create("Synthetic.flexyGram",values));
  for(int i=0;i<1000;i++)StudioCodec.decode(data,1273);
  long[] samples=new long[2000];
  for(int i=0;i<samples.length;i++){long begin=System.nanoTime();StudioCodec.decode(data,1273);samples[i]=System.nanoTime()-begin;}
  Arrays.sort(samples);
  System.out.printf(java.util.Locale.ROOT,"{\"environment\":\"host JVM synthetic\",\"operation\":\"decode and validate\",\"bytes\":%d,\"samples\":%d,\"median_us\":%.3f,\"p95_us\":%.3f,\"android_touch_latency\":\"NOT_MEASURED\",\"android_jank\":\"NOT_MEASURED\"}%n",data.length,samples.length,samples[samples.length/2]/1000d,samples[(int)(samples.length*.95)-1]/1000d);
 }
}
