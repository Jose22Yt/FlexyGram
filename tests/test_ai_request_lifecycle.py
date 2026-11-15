"""Real OkHttp/Okio/JSON with an in-memory interceptor; no remote requests.

Set FLEXY_AI_JAR_DIR to the host jars matching okhttp-jvm 5.5.0 and its
runtime dependencies. Android services/config are explicit doubles.
"""
import os
from pathlib import Path
import subprocess
import pytest
from test_render_work_reuse import JAVA, probe


def test_message_equality_preserves_role_and_hash_collection_contract(tmp_path):
    probe(tmp_path, {'Probe.java': '''import java.util.*;import app.exteraless.ai.data.Message;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){
 Message user=new Message("user","hello"),assistant=new Message("assistant","hello"),same=new Message("user","hello");
 check(!user.equals(assistant)&&user.equals(same)&&same.equals(user)&&user.hashCode()==same.hashCode());
 Set<Message> messages=new HashSet<>();messages.add(user);messages.add(assistant);messages.add(same);check(messages.size()==2);
 Map<Message,String> map=new HashMap<>();map.put(user,"user");map.put(assistant,"assistant");check("user".equals(map.get(same)));
 check(!user.equals(null)&&!user.equals("hello")&&new Message(null,null).equals(new Message(null,null)));
}}'''}, [JAVA/'app/exteraless/ai/data/Message.java'])


def test_real_ai_client_cancellation_stream_limits_and_tool_rounds(tmp_path):
    directory = Path(os.environ.get('FLEXY_AI_JAR_DIR', ''))
    names = ['okhttp-jvm-5.5.0.jar', 'okio-jvm-3.18.1.jar', 'kotlin-stdlib-2.1.21.jar',
             'json-20250517.jar', 'annotations-26.0.2.jar']
    if not all((directory / name).is_file() for name in names):
        pytest.skip('Set FLEXY_AI_JAR_DIR with the pinned host dependencies')
    files = {
        'android/text/TextUtils.java': '''package android.text;public class TextUtils{public static boolean isEmpty(CharSequence s){return s==null||s.length()==0;}public static boolean equals(CharSequence a,CharSequence b){return a==b||a!=null&&b!=null&&a.toString().contentEquals(b);}}''',
        'android/util/Base64.java': '''package android.util;public class Base64{public static final int NO_WRAP=2;public static String encodeToString(byte[] b,int flags){return java.util.Base64.getEncoder().encodeToString(b);}}''',
        'android/graphics/Bitmap.java': '''package android.graphics;public class Bitmap{public enum CompressFormat{JPEG}public boolean compress(CompressFormat f,int q,java.io.OutputStream out){return false;}public void recycle(){}}''',
        'android/graphics/BitmapFactory.java': '''package android.graphics;public class BitmapFactory{public static class Options{public boolean inJustDecodeBounds;public int outWidth,outHeight,inSampleSize;}public static Bitmap decodeFile(String p,Options o){throw new AssertionError("image decoder should not run");}}''',
        'org/telegram/messenger/AndroidUtilities.java': '''package org.telegram.messenger;public class AndroidUtilities{public static final java.util.concurrent.ConcurrentLinkedQueue<Runnable> ui=new java.util.concurrent.ConcurrentLinkedQueue<>();public static void runOnUIThread(Runnable r){ui.add(r);}public static void fire(){Runnable r;while((r=ui.poll())!=null)r.run();}}''',
        'org/telegram/messenger/FileLog.java': '''package org.telegram.messenger;public class FileLog{public static void e(Throwable t){}public static void e(String s){}}''',
        'org/telegram/messenger/Utilities.java': '''package org.telegram.messenger;public class Utilities{public interface Callback2<A,B>{void run(A a,B b);}public static class Queue{public boolean reject;public java.util.ArrayDeque<Runnable>jobs=new java.util.ArrayDeque<>();public boolean postRunnable(Runnable r){if(reject)return false;jobs.add(r);return true;}public void fire(){while(!jobs.isEmpty())jobs.remove().run();}}public static final Queue globalQueue=new Queue();}''',
        'app/exteraless/ai/data/Service.java': '''package app.exteraless.ai.data;public class Service{public static final int REASONING_LOW=1,REASONING_HIGH=3;public String getUrl(){return "https://ai.test/v1";}public String getModel(){return "test";}public String getKey(){return "test-only";}public int getReasoningEffort(){return 0;}public static String normalizeUrl(String u){return u;}}''',
        'app/exteraless/ai/data/Role.java': '''package app.exteraless.ai.data;public class Role{public String getName(){return "none";}public String getPrompt(){return "";}}''',
        'app/exteraless/ai/data/Suggestions.java': '''package app.exteraless.ai.data;public enum Suggestions{NONE;public Role getRole(){return new Role();}}''',
        'app/exteraless/ai/AiConfig.java': '''package app.exteraless.ai;import java.util.*;import app.exteraless.ai.data.*;public class AiConfig{public static int historySaves;public static Service getSelectedService(){return new Service();}public static String getSelectedRole(){return "";}public static List<Role>getRoles(){return Collections.emptyList();}public static ArrayList<Message>getConversationHistory(){return new ArrayList<>();}public static void saveConversationHistory(ArrayList<Message>m){historySaves++;}public static boolean getResponseStreaming(){return true;}public static int getTemperature(){return 10;}}''',
        'app/exteraless/ai/network/ModelsCatalog.java': '''package app.exteraless.ai.network;public class ModelsCatalog{public static boolean supportsReasoning(String s){return false;}}''',
        'Probe.java': r'''import app.exteraless.ai.network.*;import app.exteraless.ai.data.*;import app.exteraless.ai.AiConfig;import org.telegram.messenger.*;import org.json.*;import okhttp3.*;import java.io.*;import java.util.*;import java.util.concurrent.*;import java.util.concurrent.atomic.*;
public class Probe {
 interface Scenario{Response respond(Interceptor.Chain chain)throws IOException;}
 static AtomicReference<Scenario> scenario=new AtomicReference<>();static AtomicInteger calls=new AtomicInteger();
 static OkHttpClient transport=new OkHttpClient.Builder().addInterceptor(chain->{calls.incrementAndGet();return scenario.get().respond(chain);}).build();
 static class Result implements GenerationCallback{StringBuilder chunks=new StringBuilder(),thoughts=new StringBuilder();String text;int successes,errors,thinking;
  public void onChunk(String s){chunks.append(s);}public void onReasoning(String s){thoughts.append(s);}public void onThinking(){thinking++;}
  public void onResponse(String s){text=s;successes++;}public void onError(int code,String s){errors++;}int events(){return chunks.length()+thoughts.length()+successes+errors+thinking;}}
 static void check(boolean b){if(!b)throw new AssertionError();}
 static Response response(Interceptor.Chain chain,String content){return new Response.Builder().request(chain.request()).protocol(Protocol.HTTP_1_1).code(200).message("OK").body(ResponseBody.create(content,MediaType.get("application/json"))).build();}
 static String single(){return "{\"choices\":[{\"message\":{\"content\":\"ok\"}}]}";}
 static String event(String text,String thought){JSONObject delta=new JSONObject();if(text!=null)delta.put("content",text);if(thought!=null)delta.put("reasoning_content",thought);return "data: "+new JSONObject().put("choices",new JSONArray().put(new JSONObject().put("delta",delta)))+"\n\n";}
 static void idle()throws Exception{long end=System.nanoTime()+TimeUnit.SECONDS.toNanos(5);while((transport.dispatcher().runningCallsCount()!=0||transport.dispatcher().queuedCallsCount()!=0)&&System.nanoTime()<end)Thread.sleep(1);check(transport.dispatcher().runningCallsCount()==0&&transport.dispatcher().queuedCallsCount()==0);}
 static void awaitUi()throws Exception{long end=System.nanoTime()+TimeUnit.SECONDS.toNanos(5);while(AndroidUtilities.ui.isEmpty()&&System.nanoTime()<end)Thread.sleep(1);check(!AndroidUtilities.ui.isEmpty());idle();}
 static Client client()throws Exception{var f=Client.class.getDeclaredField("sharedHttpClient");f.setAccessible(true);f.set(null,transport);return new Client.Builder().serviceOverride(new Service()).build();}
 static List<Message> messages(){return List.of(new Message("user","hello"));}
 public static void main(String[]args)throws Exception{try{
  scenario.set(chain->response(chain,single()));Client c=client();Result result=new Result();
  String id=c.getResponse("hello",result);check(c.isGenerating());c.cancel(id);Utilities.globalQueue.fire();idle();AndroidUtilities.fire();check(!c.isGenerating()&&calls.get()==0&&result.events()==0);
  c.getResponse("a",result);c.getResponse("b",result);c.cancelAll();Utilities.globalQueue.fire();idle();AndroidUtilities.fire();check(!c.isGenerating()&&calls.get()==0&&result.events()==0);
  for(int i=0;i<10000;i++)c.cancel("unknown-"+i);check(!c.isGenerating());
  Utilities.globalQueue.reject=true;result=new Result();c.getResponse("rejected",result);AndroidUtilities.fire();check(result.errors==1&&!c.isGenerating());Utilities.globalQueue.reject=false;
  result=new Result();id=c.getResponse("history",true,false,null,result);Utilities.globalQueue.fire();idle();check(c.isGenerating());c.cancel(id);AndroidUtilities.fire();check(result.events()==0&&AiConfig.historySaves==0&&!c.isGenerating());
  result=new Result();c.generate("normal",messages(),false,result);idle();check(c.isGenerating());AndroidUtilities.fire();check(result.successes==1&&"ok".equals(result.text)&&!c.isGenerating());
  scenario.set(chain->response(chain,": keepalive\n\n"+event("hello","thought")+event(" world",null)+"data: [DONE]\n"));
  result=new Result();c.generate("mixed",messages(),true,result);idle();AndroidUtilities.fire();check("hello world".equals(result.text)&&result.chunks.toString().equals(result.text)&&"thought".contentEquals(result.thoughts)&&result.thinking==1&&!c.isGenerating());
  result=new Result();c.generate("cancelled-stream",messages(),true,result);idle();c.cancel("cancelled-stream");AndroidUtilities.fire();check(result.events()==0&&!c.isGenerating());
  for(String text:new String[]{"a".repeat(20000),"a".repeat(16383)+"\ud83d\ude00tail","a".repeat(16384)+"<th"}){
   scenario.set(chain->response(chain,event(text,null)+"data: [DONE]\n"));result=new Result();c.generate("limit",messages(),true,result);idle();AndroidUtilities.fire();
   check(result.successes==1&&result.text.length()<=16384&&result.text.equals(result.chunks.toString()));
   check(!Character.isHighSurrogate(result.text.charAt(result.text.length()-1)));
   check(result.text.length()==(text.contains("\ud83d")?16383:16384));
  }
  String splitSurrogate=event("a".repeat(16383),null)+event("HIGH",null).replace("HIGH","\\ud83d")+event("LOW",null).replace("LOW","\\ude00")+"data: [DONE]\\n";
  scenario.set(chain->response(chain,splitSurrogate));result=new Result();c.generate("split-surrogate",messages(),true,result);idle();AndroidUtilities.fire();check(result.successes==1&&result.text.equals("a".repeat(16383)));
  scenario.set(chain->response(chain,"data: "+"x".repeat(300000)+"\n"));result=new Result();c.generate("oversized-line",messages(),true,result);idle();AndroidUtilities.fire();check(result.errors==1&&result.successes==0&&!c.isGenerating());
  scenario.set(chain->response(chain,single()));Result throwing=new Result(){public void onResponse(String text){throw new IllegalStateException("consumer");}};
  c.generate("throwing-consumer",messages(),false,throwing);idle();try{AndroidUtilities.fire();throw new AssertionError();}catch(IllegalStateException expected){}check(!c.isGenerating());
  // Reusing a cancelled ID cannot let an old completion remove the new owner.
  CountDownLatch entered=new CountDownLatch(1),release=new CountDownLatch(1);AtomicInteger sequence=new AtomicInteger();
  scenario.set(chain->{if(sequence.incrementAndGet()==1){entered.countDown();try{release.await(5,TimeUnit.SECONDS);}catch(InterruptedException e){throw new IOException(e);}}return response(chain,single());});
  Result old=new Result(),next=new Result();c.generate("same-id",messages(),false,old);check(entered.await(3,TimeUnit.SECONDS));c.cancel("same-id");c.generate("same-id",messages(),false,next);
  release.countDown();idle();check(c.isGenerating());AndroidUtilities.fire();check(old.events()==0&&next.successes==1&&!c.isGenerating());
  AtomicInteger fallbackSequence=new AtomicInteger();scenario.set(chain->{Response r=response(chain,single());return fallbackSequence.incrementAndGet()==1?r.newBuilder().code(400).message("tools unsupported").build():r;});
  ToolHandler fallbackHandler=new ToolHandler(){public JSONArray definitions(){return new JSONArray();}public List<Message>fallback(){return messages();}public String describe(String n,JSONObject a){return n;}public String call(String n,JSONObject a){throw new AssertionError();}};
  Client fallbackClient=new Client.Builder().serviceOverride(new Service()).tools(fallbackHandler).build();result=new Result();fallbackClient.generate("fallback",messages(),false,result);awaitUi();AndroidUtilities.fire();check(fallbackSequence.get()==2&&result.successes==1&&result.errors==0&&!fallbackClient.isGenerating());
  // Cancellation between tool rounds stops the second tool and the next HTTP request.
  CountDownLatch toolEntered=new CountDownLatch(1),toolRelease=new CountDownLatch(1);AtomicInteger tools=new AtomicInteger();
  ToolHandler handler=new ToolHandler(){public JSONArray definitions(){return new JSONArray();}public List<Message>fallback(){return List.of();}public String describe(String n,JSONObject a){return n;}
   public String call(String n,JSONObject a){tools.incrementAndGet();toolEntered.countDown();try{toolRelease.await(5,TimeUnit.SECONDS);}catch(InterruptedException e){}return "done";}};
  String toolResponse="{\"choices\":[{\"message\":{\"content\":null,\"tool_calls\":[{\"id\":\"1\",\"function\":{\"name\":\"first\",\"arguments\":\"{}\"}},{\"id\":\"2\",\"function\":{\"name\":\"second\",\"arguments\":\"{}\"}}]}}]}";
  scenario.set(chain->response(chain,toolResponse));Client toolClient=new Client.Builder().serviceOverride(new Service()).tools(handler).build();result=new Result();int before=calls.get();
  toolClient.generate("tools",messages(),false,result);check(toolEntered.await(3,TimeUnit.SECONDS));toolClient.cancelAll();toolRelease.countDown();
  long end=System.nanoTime()+TimeUnit.SECONDS.toNanos(3);while(Thread.getAllStackTraces().keySet().stream().anyMatch(t->t.isAlive()&&t.getName().equals("ai-tools"))&&System.nanoTime()<end)Thread.sleep(1);
  AndroidUtilities.fire();check(tools.get()==1&&calls.get()==before+1&&result.events()==0&&!toolClient.isGenerating());
 }finally{transport.dispatcher().executorService().shutdownNow();transport.connectionPool().evictAll();}}
}''',
    }
    paths = []
    for name, content in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        paths.append(path)
    actual = [JAVA/'app/exteraless/ai/network'/name for name in
              ('Client.java', 'GenerationCallback.java', 'ReasoningFilter.java', 'ToolHandler.java')]
    actual.append(JAVA/'app/exteraless/ai/data/Message.java')
    classpath = os.pathsep.join(str(directory / name) for name in names)
    result = subprocess.run(['java', '-m', 'jdk.compiler/com.sun.tools.javac.Main', '-cp', classpath,
                             '-d', str(tmp_path), *map(str, paths + actual)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run(['java', '-cp', str(tmp_path) + os.pathsep + classpath, 'Probe'],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
