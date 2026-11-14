"""Run production outbound methods with a queued UI dispatcher and counted transport."""
import re
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_proxy_coalesces_sends_yields_between_batches_and_keeps_frame_order(tmp_path):
    source = (JAVA/'org/telegram/utils/proxy/WebProxyTransport.java').read_text()
    functions = '\n'.join(method(source, signature) for signature in ['private void sendFrame(', 'private void drainOutbound()'])
    constants = '\n'.join(re.findall(r'    private static final (?:int|long) (?:FRAME_HEADER|MAX_OUTBOUND_ITEMS|MAX_OUTBOUND_BYTES|DRAIN_BATCH_BYTES|DRAIN_BATCH_FRAMES|DRAIN_BUDGET_MS) = [^;]+;', source))
    probe(tmp_path, {'Probe.java': '''import java.util.*;import java.nio.ByteBuffer;
public class Probe {
 CONSTANTS
 static final String BASE64_PREFIX="b64:";
 static class SystemClock{static long now;static long uptimeMillis(){return now;}}
 static class Looper{static Looper getMainLooper(){return new Looper();}}
 static class Handler{static ArrayDeque<Runnable> tasks=new ArrayDeque<>();Handler(Looper l){}void post(Runnable r){tasks.add(r);}void fire(){tasks.remove().run();}}
 static class Base64{static final int NO_WRAP=1;static String encodeToString(byte[]b,int f){return java.util.Base64.getEncoder().encodeToString(b);}}
 static class FileLog{static void e(Exception e){}}
 static class JavaScriptReplyProxy{List<Integer>ids=new ArrayList<>();boolean fail,cost;
 void postMessage(byte[]frame){if(fail)throw new RuntimeException();ids.add(ByteBuffer.wrap(frame).getInt(4));if(cost)SystemClock.now+=4;}
 void postMessage(String frame){postMessage(java.util.Base64.getDecoder().decode(frame.substring(BASE64_PREFIX.length())));}}
 Object lock=new Object();ArrayDeque<byte[]>outbound=new ArrayDeque<>();int outboundBytes;boolean stopped,bridgeReady=true,useArrayBuffer=true,outboundDrainScheduled;
 JavaScriptReplyProxy replyProxy=new JavaScriptReplyProxy();final Handler outboundHandler=new Handler(Looper.getMainLooper());final Runnable outboundDrain=this::drainOutbound;
 void failCarrier(){replyProxy=null;outbound.clear();outboundBytes=0;}
 FUNCTIONS
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 public static void main(String[]args){
  Probe p=new Probe();for(int i=0;i<100;i++)p.sendFrame(1,i,new byte[65536+i]);
  check(Handler.tasks.size()==1&&p.replyProxy.ids.isEmpty());int[]touch={0};Handler.tasks.add(()->touch[0]++);
  p.outboundHandler.fire();check(p.replyProxy.ids.size()==4&&Handler.tasks.size()==2);
  p.outboundHandler.fire();check(touch[0]==1);while(!Handler.tasks.isEmpty())p.outboundHandler.fire();
  check(p.replyProxy.ids.size()==100&&p.outboundBytes==0&&!p.outboundDrainScheduled);
  for(int i=0;i<100;i++)check(p.replyProxy.ids.get(i)==65536+i);
  p.replyProxy.cost=true;for(int i=0;i<8;i++)p.sendFrame(1,1,new byte[1]);p.outboundHandler.fire();check(p.replyProxy.ids.size()==101);
  while(!Handler.tasks.isEmpty())p.outboundHandler.fire();
  p.useArrayBuffer=false;p.sendFrame(1,1,new byte[7]);p.outboundHandler.fire();check(p.replyProxy.ids.get(108)==7);
  p.replyProxy.fail=true;p.sendFrame(1,1,new byte[1]);p.outboundHandler.fire();check(!p.outboundDrainScheduled&&p.outboundBytes==0);
  p.replyProxy=new JavaScriptReplyProxy();p.sendFrame(1,1,new byte[2]);p.outboundHandler.fire();check(p.replyProxy.ids.equals(List.of(2)));
  p.sendFrame(1,1,new byte[1]);p.stopped=true;p.outboundHandler.fire();check(!p.outboundDrainScheduled&&Handler.tasks.isEmpty());
 }
}'''.replace('CONSTANTS', constants).replace('FUNCTIONS', functions)})
