"""Deterministic work-count/lifecycle regressions. These are not device frame-time measurements."""
from pathlib import Path
import importlib.util
import xml.etree.ElementTree as ET
import pytest
from test_render_work_reuse import JAVA, ROOT, probe
from test_composer_layout import method


def test_frame_counters_keep_bounded_private_contexts_and_reset(tmp_path):
    probe(tmp_path,{'Probe.java':'''import app.flexygram.performance.FrameWindowStats;public class Probe{
 public static void main(String[]args)throws Exception{
 FrameWindowStats stats=new FrameWindowStats();Runnable record=()->{for(int i=0;i<10000;i++)stats.record(FrameWindowStats.CHAT_SCROLL,8_000_000,i%2==0);};
 Thread a=new Thread(record),b=new Thread(record);a.start();b.start();a.join();b.join();
 stats.record(-1,5,true);stats.record(1,-1,true);stats.record(1,61_000_000_000L,true);
 stats.record(FrameWindowStats.OTHER,0,true);String result=stats.drain();if(!result.contains("chat_scroll={frames:20000,heuristic_jank:10000,total_ui_ns:160000000000,max_ui_ns:8000000}")||!result.contains("invalid:3")||!result.contains("other={frames:1,heuristic_jank:1")||result.contains("fps"))throw new AssertionError(result);
 if(!stats.drain().equals("ui_frame_stats"))throw new AssertionError();
 if(!FrameWindowStats.screen("ChatActivity").equals("chat")||!FrameWindowStats.screen("FlexyStudioActivity").equals("settings")||!FrameWindowStats.screen("contact-private-name").equals("other"))throw new AssertionError();
 if(FrameWindowStats.state("chat",true)!=FrameWindowStats.CHAT_SCROLL||FrameWindowStats.state("chat",false)!=FrameWindowStats.CHAT)throw new AssertionError();
 }}'''},[JAVA/'app/flexygram/performance/FrameWindowStats.java'])


def test_text_metrics_never_block_copy_paint_skip_spans_bound_cache_and_reject_stale_work(tmp_path):
    probe(tmp_path,{
        'android/os/Build.java':'package android.os;public class Build{public static class VERSION{public static int SDK_INT=27;}}',
        'android/os/Process.java':'package android.os;public class Process{public static int THREAD_PRIORITY_BACKGROUND=10;public static void setThreadPriority(int p){}}',
        'android/os/Looper.java':'package android.os;public class Looper{static final Looper MAIN=new Looper();public static boolean background;public static Looper myLooper(){return background?null:MAIN;}public static Looper getMainLooper(){return MAIN;}}',
        'android/text/TextPaint.java':'package android.text;public class TextPaint{public int size=18;public TextPaint(){}public TextPaint(TextPaint p){size=p.size;}}',
        'android/text/Layout.java':'package android.text;public class Layout{public static final int BREAK_STRATEGY_HIGH_QUALITY=1,HYPHENATION_FREQUENCY_NONE=0;}',
        'android/text/TextDirectionHeuristics.java':'package android.text;public class TextDirectionHeuristics{public static final Object FIRSTSTRONG_LTR=new Object();}',
        'android/text/Spanned.java':'package android.text;public interface Spanned extends CharSequence{<T>T[]getSpans(int s,int e,Class<T>t);}',
        'androidx/annotation/RequiresApi.java':'package androidx.annotation;public @interface RequiresApi{int value();}',
        'android/text/PrecomputedText.java':'''package android.text;import java.util.concurrent.*;import java.util.concurrent.atomic.*;
public class PrecomputedText implements CharSequence{
 public static volatile boolean block;public static volatile CountDownLatch entered=new CountDownLatch(1),release=new CountDownLatch(1);public static AtomicInteger calls=new AtomicInteger();
 public final String text;public final Params params;PrecomputedText(String t,Params p){text=t;params=p;}public char charAt(int i){return text.charAt(i);}public int length(){return text.length();}public CharSequence subSequence(int s,int e){return text.substring(s,e);}public String toString(){return text;}
 public static PrecomputedText create(CharSequence t,Params p){calls.incrementAndGet();if(block){CountDownLatch r=release;entered.countDown();try{r.await();}catch(InterruptedException e){throw new RuntimeException(e);}}return new PrecomputedText(t.toString(),p);}
 public static class Params{public final int size;Params(TextPaint p){size=p.size;}public boolean equals(Object o){return o instanceof Params&&size==((Params)o).size;}public int hashCode(){return size;}
 public static class Builder{TextPaint p;public Builder(TextPaint p){this.p=p;}public Builder setBreakStrategy(int n){return this;}public Builder setHyphenationFrequency(int n){return this;}public Builder setTextDirection(Object o){return this;}public Params build(){return new Params(p);}}}
}''',
        'Probe.java':'''import app.flexygram.performance.TextLayoutPrecompute;import android.text.*;import java.lang.reflect.*;import java.util.*;import java.util.concurrent.*;
public class Probe{
 static void check(boolean v){if(!v)throw new AssertionError();}
 static Map<?,?> cache()throws Exception{Class<?> c=Class.forName("app.flexygram.performance.TextLayoutPrecompute$Api28");Field f=c.getDeclaredField("ready");f.setAccessible(true);return(Map<?,?>)f.get(null);}
 static int size()throws Exception{Map<?,?>m=cache();synchronized(m){return m.size();}}
 static CharSequence await(String text,TextPaint paint)throws Exception{long end=System.nanoTime()+2_000_000_000L;while(System.nanoTime()<end){CharSequence value=TextLayoutPrecompute.getOrSchedule(text,paint);if(value instanceof PrecomputedText)return value;Thread.sleep(2);}throw new AssertionError("metrics did not arrive");}
 static class Spans implements Spanned{String text="x".repeat(200);public<T>T[]getSpans(int s,int e,Class<T>t){return(T[])new Object[]{new Object()};}public char charAt(int i){return text.charAt(i);}public int length(){return text.length();}public CharSequence subSequence(int s,int e){return text.substring(s,e);}public String toString(){return text;}}
 public static void main(String[]args)throws Exception{
 TextPaint paint=new TextPaint();String text="a".repeat(200);
 check(TextLayoutPrecompute.getOrSchedule(text,paint)==text&&PrecomputedText.calls.get()==0);
 android.os.Build.VERSION.SDK_INT=28;android.os.Looper.background=true;check(TextLayoutPrecompute.getOrSchedule(text,paint)==text&&PrecomputedText.calls.get()==0);android.os.Looper.background=false;Spans spanned=new Spans();check(TextLayoutPrecompute.getOrSchedule(spanned,paint)==spanned&&PrecomputedText.calls.get()==0);
 PrecomputedText.block=true;CountDownLatch returned=new CountDownLatch(1);Thread caller=new Thread(()->{check(TextLayoutPrecompute.getOrSchedule(text,paint)==text);returned.countDown();});caller.start();
 check(returned.await(2,TimeUnit.SECONDS));check(PrecomputedText.entered.await(2,TimeUnit.SECONDS));paint.size=40;
 PrecomputedText.block=false;PrecomputedText.release.countDown();TextPaint original=new TextPaint();
 PrecomputedText cached=(PrecomputedText)await(text,original);check(cached.params.size==18&&cached.toString().equals(text));int calls=PrecomputedText.calls.get();
 for(int i=0;i<1000;i++)check(TextLayoutPrecompute.getOrSchedule(text,original)==cached);check(calls==PrecomputedText.calls.get());
 check(((PrecomputedText)await(text,paint)).params.size==40);
 for(int i=0;i<40;i++)await("sample"+i+"b".repeat(2000),original);check(size()<=16);
 TextLayoutPrecompute.trimMemory(15);check(size()==0);
 PrecomputedText.entered=new CountDownLatch(1);PrecomputedText.release=new CountDownLatch(1);PrecomputedText.block=true;
 String stale="stale"+"c".repeat(200);TextLayoutPrecompute.getOrSchedule(stale,original);check(PrecomputedText.entered.await(2,TimeUnit.SECONDS));TextLayoutPrecompute.trimMemory(15);
 PrecomputedText.block=false;PrecomputedText.release.countDown();Thread.sleep(30);check(size()==0);check(await(stale,original) instanceof PrecomputedText);
 }}''',
    },[JAVA/'app/flexygram/performance/TextLayoutPrecompute.java'])


def test_downsampled_blur_records_primary_once_and_reuses_unchanged_nodes(tmp_path):
    source=(JAVA/'org/telegram/ui/Components/blur3/DownscaleScrollableNoiseSuppressor.java').read_text()
    body=method(source,'public void invalidateRenderNodes(RenderNode renderNode)')
    probe(tmp_path,{'Probe.java':'''public class Probe{
 static class Canvas{void drawRenderNode(RenderNode n){}void scale(float x,float y){if(!Float.isFinite(x)||!Float.isFinite(y))throw new AssertionError();}}
 static class RenderNode{static int ids;int id=++ids,w,h,records;boolean display;int getWidth(){return w;}int getHeight(){return h;}long getUniqueId(){return id;}boolean hasDisplayList(){return display;}void setPosition(int l,int t,int r,int b){w=r-l;h=b-t;}Canvas beginRecording(int w,int h){if(w<=0||h<=0)throw new AssertionError();records++;return new Canvas();}void endRecording(){display=true;}void setScaleX(float f){}void setScaleY(float f){}void setPivotX(float f){}void setPivotY(float f){}}
 static class MediaDataController{static long calcHash(long h,long v){return h*31+v;}}
 RenderNode renderNodeOriginalWithOffset=new RenderNode();RenderNode[]renderNodeDownsampled={new RenderNode(),new RenderNode()},renderNodeRestored={new RenderNode(),new RenderNode()};boolean simpleMode;int scaleX=8,scaleY=8;float k=1;long lastHash;
 BODY
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){for(boolean simple:new boolean[]{false,true}){Probe p=new Probe();p.simpleMode=simple;if(simple)p.renderNodeRestored=p.renderNodeDownsampled;RenderNode source=new RenderNode();source.setPosition(0,0,300,500);
 p.invalidateRenderNodes(source);check(p.renderNodeDownsampled[0].records==1&&p.renderNodeDownsampled[1].records==1);
 for(int i=0;i<10000;i++)p.invalidateRenderNodes(source);check(p.renderNodeDownsampled[0].records==1);
 source.setPosition(0,0,1,1);p.invalidateRenderNodes(source);check(p.renderNodeDownsampled[0].w==1&&p.renderNodeDownsampled[0].h==1);
 source.setPosition(0,0,0,0);p.invalidateRenderNodes(source);check(p.renderNodeDownsampled[0].records==2);
 }}
}'''.replace('BODY',body)})


def test_profile_import_requires_successful_device_journeys_and_real_rules(tmp_path):
    spec=importlib.util.spec_from_file_location('profile_import',ROOT/'tools/performance_profiles/import_profiles.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.ROOT=tmp_path
    profile=tmp_path/'device.txt';profile.write_text('HSPLorg/telegram/ui/LaunchActivity;->onResume()V\nLorg/telegram/ui/ChatActivity;\n')
    results=tmp_path/'results.xml';results.write_text('<testsuite><testcase classname="com.flexygram.performance.ProfileGeneration" name="startup"/><testcase classname="com.flexygram.performance.ProfileGeneration" name="chat"/><testcase classname="com.flexygram.performance.ProfileGeneration" name="settings"/></testsuite>')
    module.import_profiles([profile],profile,results,'a'*40,1301,35)
    folder=tmp_path/'TMessagesProj/src/main/generated/baselineProfiles'
    assert (folder/'baseline-prof.txt').read_text()==profile.read_text()
    assert '"measured_speedup": null' in (folder/'capture.json').read_text()
    results.write_text('<testsuite><testcase classname="ProfileGeneration" name="startup"><skipped/></testcase></testsuite>')
    with pytest.raises(ValueError):module.validate_results(results)
    profile.write_text('not an ART rule\n')
    with pytest.raises(ValueError):module.rules([profile])


def test_normal_builds_keep_diagnostics_and_optimizer_experiment_off():
    script=(ROOT/'gradle/flexygram-performance.gradle').read_text()
    assert "findProperty('flexyFrameDiagnostics') == 'true'" in script
    assert "findProperty('flexyR8Optimization') == 'true'" in script
    assert 'android.buildTypes.connectedAlpha' in script and 'android.buildTypes.beta' not in script
    manifest=ET.parse(ROOT/'TMessagesProj/src/main/AndroidManifest.xml').getroot()
    assert not any('REQUEST_PROFILING' in str(e.attrib) for e in manifest.findall('uses-permission'))
    normal=(JAVA/'org/telegram/ui/LaunchActivity.java').read_text()
    assert 'if (BuildConfig.FLEXY_FRAME_DIAGNOSTICS)' in normal
    # The ordinary compatibility rules are preserved until real minified-plugin regression testing.
    assert '-dontoptimize' in (ROOT/'TMessagesProj/proguard-rules.pro').read_text()


def test_system_profile_api_gates_and_manual_capture_cancellation(tmp_path):
    probe(tmp_path,{
        'androidx/annotation/RequiresApi.java':'package androidx.annotation;public @interface RequiresApi{int value();}',
        'android/os/Build.java':'package android.os;public class Build{public static class VERSION{public static int SDK_INT;}}',
        'android/os/Bundle.java':'package android.os;public class Bundle{}',
        'android/os/CancellationSignal.java':'package android.os;public class CancellationSignal{public boolean canceled;public void cancel(){canceled=true;}}',
        'android/util/Log.java':'package android.util;public class Log{public static int i(String t,String s){return 0;}}',
        'android/content/Context.java':'package android.content;public class Context{public final android.os.ProfilingManager manager=new android.os.ProfilingManager();public<T>T getSystemService(Class<T> t){return t.cast(manager);}}',
        'android/os/ProfilingResult.java':'package android.os;public class ProfilingResult{public int getErrorCode(){return 0;}}',
        'android/os/ProfilingTrigger.java':'''package android.os;public class ProfilingTrigger{public static final int TRIGGER_TYPE_ANR=1,TRIGGER_TYPE_OOM=2;public int type,hours;public static class Builder{ProfilingTrigger t=new ProfilingTrigger();public Builder(int type){t.type=type;}public Builder setRateLimitingPeriodHours(int h){t.hours=h;return this;}public ProfilingTrigger build(){return t;}}}''',
        'android/os/ProfilingManager.java':'''package android.os;import java.util.*;import java.util.function.*;import java.util.concurrent.*;public class ProfilingManager{
 public static final int PROFILING_TYPE_SYSTEM_TRACE=1;public int registrations,removals,requests;public List<ProfilingTrigger> triggers;public int[] removed;public CancellationSignal signal;
 public void registerForAllProfilingResults(Executor e,Consumer<ProfilingResult> c){registrations++;}public void unregisterForAllProfilingResults(Consumer<ProfilingResult> c){removals++;}
 public void addProfilingTriggers(List<ProfilingTrigger> list){triggers=list;}public void removeProfilingTriggersByType(int[] types){removed=types;}
 public void requestProfiling(int t,Bundle b,String tag,CancellationSignal s,Executor e,Consumer<ProfilingResult> c){requests++;signal=s;}
}''',
        'Probe.java':'''import java.lang.reflect.*;import android.content.Context;public class Probe{static void check(boolean v){if(!v)throw new AssertionError();}
 public static void main(String[]args)throws Exception{
 Class<?> type=Class.forName("app.flexygram.performance.SystemProfiles");Constructor<?> ctor=type.getDeclaredConstructor();ctor.setAccessible(true);Method start=type.getDeclaredMethod("start",Context.class,boolean.class),stop=type.getDeclaredMethod("stop");start.setAccessible(true);stop.setAccessible(true);
 for(int sdk:new int[]{24,34,35,36,37}){
 android.os.Build.VERSION.SDK_INT=sdk;Context context=new Context();Object instance=ctor.newInstance();
 start.invoke(instance,context,false);start.invoke(instance,context,false);
 check(context.manager.registrations==(sdk>=35?1:0));check(context.manager.requests==0);
 if(sdk>=36){check(context.manager.triggers.size()==(sdk>=37?2:1));for(var t:context.manager.triggers)check(t.hours==1);}
 else check(context.manager.triggers==null);
 stop.invoke(instance);stop.invoke(instance);check(context.manager.removals==(sdk>=35?1:0));
 if(sdk>=36)check(context.manager.removed.length==(sdk>=37?2:1));
 if(sdk>=35){start.invoke(instance,context,true);check(context.manager.requests==1&&!context.manager.signal.canceled);stop.invoke(instance);check(context.manager.signal.canceled);}
 }
 }}''',
    },[JAVA/'app/flexygram/performance/SystemProfiles.java'])


def test_future_memory_budget_callback_is_optional_throttled_and_detached(tmp_path):
    probe(tmp_path,{
        'android/os/Build.java':'package android.os;public class Build{public static class VERSION{public static int SDK_INT;}}',
        'android/os/Looper.java':'package android.os;public class Looper{public static Looper getMainLooper(){return new Looper();}}',
        'android/os/SystemClock.java':'package android.os;public class SystemClock{public static long now;public static long uptimeMillis(){return now;}}',
        'android/content/Context.java':'package android.content;public class Context{public Object service;public<T>T getSystemService(Class<T> t){return t.cast(service);}}',
        'android/app/MemoryBudgetManager.java':'''package android.app;public class MemoryBudgetManager{
 public interface OnOverBudgetListener{void overBudget(long bytes);}public OnOverBudgetListener listener;public int adds,removes;
 public void registerProcessOverBudgetListener(android.os.Looper looper,OnOverBudgetListener l){listener=l;adds++;}
 public void unregisterProcessOverBudgetListener(OnOverBudgetListener l){if(listener!=l)throw new AssertionError();removes++;}
 }''',
        'Probe.java':'''import java.lang.reflect.*;import android.content.Context;public class Probe{static void check(boolean v){if(!v)throw new AssertionError();}
 public static void main(String[]args)throws Exception{Class<?> type=Class.forName("app.flexygram.performance.MemoryBudgetBridge");Method start=type.getDeclaredMethod("start",Context.class,Runnable.class),close=type.getDeclaredMethod("close");start.setAccessible(true);close.setAccessible(true);
 Context context=new Context();android.app.MemoryBudgetManager manager=new android.app.MemoryBudgetManager();context.service=manager;int[] trims={0};Runnable trim=()->trims[0]++;
 android.os.Build.VERSION.SDK_INT=36;check(start.invoke(null,context,trim)==null&&manager.adds==0);
 android.os.Build.VERSION.SDK_INT=37;Object bridge=start.invoke(null,context,trim);check(bridge!=null&&manager.adds==1);
 manager.listener.overBudget(1);manager.listener.overBudget(1);check(trims[0]==1);android.os.SystemClock.now=5000;manager.listener.overBudget(1);check(trims[0]==2);
 close.invoke(bridge);close.invoke(bridge);check(manager.removes==1);android.os.SystemClock.now=10000;manager.listener.overBudget(1);check(trims[0]==2);
 context.service=null;check(start.invoke(null,context,trim)==null);
 }}''',
    },[JAVA/'app/flexygram/performance/MemoryBudgetBridge.java'])


def test_real_androidx_and_sdk_contracts_when_artifacts_are_available():
    import os,subprocess,shutil
    libs=Path(os.environ.get('FLEXY_PERFORMANCE_LIBS','/tmp/flexy-performance-libs'))
    sdk=Path(os.environ.get('ANDROID_HOME','/workspace/.flexygram/android-sdk'))
    if not (libs/'metrics.jar').is_file() or not (sdk/'platforms/android-37.0/android.jar').is_file() or not shutil.which('javac'):
        pytest.skip('Supply actual AndroidX jars and Android API37 for the isolated API check')
    result=subprocess.run(['python',str(ROOT/'tools/performance_profiles/check_android_apis.py'),'--sdk',str(sdk),'--libraries',str(libs)],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
