"""Execute startup policies; these are ordering/allocation checks, not device launch timings."""
import re
from test_render_work_reuse import JAVA,probe
from test_composer_layout import method


def test_message_paints_reuse_identity_but_apply_font_and_density_updates(tmp_path):
    source=(JAVA/'org/telegram/ui/ActionBar/Theme.java').read_text()
    body=method(source,'public static void createCommonMessageResources()')
    names=sorted(set(re.findall(r'\b(chat_\w+)\s*=\s*new TextPaint\(',body)))
    constant=re.search(r'private static final float\[\] CHAT_EMOJI_SIZE_PERCENTS = [^;]+;',source).group()
    probe(tmp_path,{'Probe.java':'''class Paint{static final int ANTI_ALIAS_FLAG=1;static int allocations;Paint(int f){allocations++;}}
class TextPaint extends Paint{float size;TextPaint(int f){super(f);}void setTypeface(Object t){}void setTextSize(float s){size=s;}}
class SharedConfig{static int fontSize=16;}class AndroidUtilities{static Object bold(){return null;}static Object mono(){return null;}}
public class Probe{
 static Object sync=new Object();static float density=1;static float dp(float n){return n*density;}
 static TextPaint[] chat_msgTextPaintEmoji;FIELDS
 CONSTANT
 BODY
 public static void main(String[]args){
 createCommonMessageResources();TextPaint[] original=chat_msgTextPaintEmoji.clone();int count=Paint.allocations;
 for(int n=0;n<1000;n++){createCommonMessageResources();for(int i=0;i<6;i++)if(chat_msgTextPaintEmoji[i]!=original[i])throw new AssertionError("emoji paint recreated");}
 if(Paint.allocations!=count)throw new AssertionError("warm resource setup allocated paints");
 SharedConfig.fontSize=28;density=2;createCommonMessageResources();
 if(chat_msgTextPaint.size!=56||chat_msgGameTextPaint.size!=28||Math.abs(original[0].size-163.2f)>.001f)throw new AssertionError("font/density update lost");
 if(Paint.allocations!=count)throw new AssertionError();
 }}'''.replace('FIELDS','static TextPaint '+','.join(names)+';').replace('CONSTANT',constant).replace('BODY',body)})


def test_webview_preferences_are_lazy_singleton_and_cold_logout_still_cleans_disk(tmp_path):
    probe(tmp_path,{
'android/content/Context.java':'''package android.content;public class Context{public static final int MODE_PRIVATE=0;public int reads;public final SharedPreferences prefs=new SharedPreferences();public synchronized SharedPreferences getSharedPreferences(String f,int m){reads++;return prefs;}}''',
'android/content/SharedPreferences.java':'''package android.content;import java.util.*;public class SharedPreferences{
 final java.util.concurrent.ConcurrentHashMap<String,Object> values=new java.util.concurrent.ConcurrentHashMap<>();public boolean getBoolean(String k,boolean d){return (Boolean)values.getOrDefault(k,d);}public Map<String,?> getAll(){return new HashMap<>(values);}public Editor edit(){return new Editor();}
 public class Editor{Map<String,Object> updates=new HashMap<>();Set<String> removals=new HashSet<>();public Editor putBoolean(String k,boolean v){updates.put(k,v);return this;}public Editor remove(String k){removals.add(k);return this;}public void apply(){values.putAll(updates);for(String k:removals)values.remove(k);}}
}''',
'org/telegram/messenger/ApplicationLoader.java':'''package org.telegram.messenger;public class ApplicationLoader{public static final android.content.Context applicationContext=new android.content.Context();}''',
'Probe.java':'''import org.telegram.messenger.*;public class Probe{
 public static void main(String[]a)throws Exception{
 Class.forName("org.telegram.messenger.SharedPrefsHelper");var context=ApplicationLoader.applicationContext;if(context.reads!=0)throw new AssertionError();
 Thread[] threads=new Thread[12];for(int i=0;i<threads.length;i++)threads[i]=new Thread(SharedPrefsHelper::getWebViewBotsPrefs);
 for(Thread t:threads)t.start();for(Thread t:threads)t.join();if(context.reads!=1)throw new AssertionError("duplicate pref open");
 SharedPrefsHelper.setWebViewConfirmShown(0,42,true);SharedPrefsHelper.setWebViewConfirmShown(1,42,true);
 var field=SharedPrefsHelper.class.getDeclaredField("webViewBotsPrefs");field.setAccessible(true);field.set(null,null);
 SharedPrefsHelper.cleanupAccount(0);
 if(SharedPrefsHelper.isWebViewConfirmShown(0,42)||!SharedPrefsHelper.isWebViewConfirmShown(1,42)||context.reads!=2)throw new AssertionError("cold account cleanup lost");
 }}'''
},[JAVA/'org/telegram/messenger/SharedPrefsHelper.java'])


def test_plugin_start_requests_prepare_storage_once_on_worker_before_python(tmp_path):
    source=(JAVA/'app/exteraless/plugins/PythonPluginsEngine.java').read_text()
    body=method(source,'public void ensureStarted(Context appContext, StartCallback callback)')
    storage=method(source,'private void prepareRuntimeStorage(Context context)')
    probe(tmp_path,{
'android/content/Context.java':'''package android.content;public class Context{public final java.io.File directory;public Context(String path){directory=new java.io.File(path);}public java.io.File getFilesDir(){return directory;}}''',
'Probe.java':'''import android.content.Context;import java.io.File;import java.util.*;
class PyObject{PyObject callAttr(String name,Object...args){return this;}}
class AndroidPlatform{AndroidPlatform(Context c){}}
class Python{static int starts,modules;static boolean live;static boolean isStarted(){return live;}static void start(AndroidPlatform p){if(PluginGrantStore.calls!=1)throw new AssertionError("permissions not ready");live=true;starts++;}static Python getInstance(){return new Python();}PyObject getModule(String n){modules++;return new PyObject();}}
class PluginGrantStore{static int calls;static boolean fail;static void warmUp(){calls++;if(fail)throw new IllegalStateException("storage unavailable");}}
class AndroidUtilities{static void runOnUIThread(Runnable r){r.run();}}class PythonThreadState{static void pinCurrentThread(){}}
class FileLog{static void d(String s){}static void e(String s,Throwable t){}}class PluginsController{static PluginsController getInstance(){return new PluginsController();}boolean isDeveloperMode(){return false;}}
public class Probe{
 interface StartCallback{void onStarted(boolean ok);}
 static class Worker{ArrayDeque<Runnable> jobs=new ArrayDeque<>();void execute(Runnable r){jobs.add(r);}void drain(){while(!jobs.isEmpty())jobs.remove().run();}}
 Worker executor=new Worker();boolean started,startFailed;PyObject loader;
 BODY
 STORAGE
 public static void main(String[]args)throws Exception{
 File root=java.nio.file.Files.createTempDirectory("engine-storage").toFile();try{
 Context c=new Context(root.getAbsolutePath());Probe p=new Probe();int[]yes={0},no={0};
 for(int i=0;i<10;i++)p.ensureStarted(c,ok->{if(ok)yes[0]++;else no[0]++;});
 if(PluginGrantStore.calls!=0||Python.starts!=0||new File(root,"plugins").exists())throw new AssertionError("work ran before worker dispatch");
 p.executor.drain();if(yes[0]!=10||no[0]!=0||Python.starts!=1||Python.modules!=2||PluginGrantStore.calls!=1||!new File(root,"plugins").isDirectory())throw new AssertionError("duplicate startup");
 Probe failed=new Probe();PluginGrantStore.fail=true;PluginGrantStore.calls=0;Python.starts=0;
 failed.ensureStarted(c,ok->{if(!ok)no[0]++;});failed.ensureStarted(c,ok->{if(!ok)no[0]++;});failed.executor.drain();
 if(no[0]!=2||Python.starts!=0||PluginGrantStore.calls!=1||!failed.startFailed)throw new AssertionError("unsafe startup or repeat after failure");
 }finally{new File(root,"plugins").delete();root.delete();}
 }}'''.replace('BODY',body).replace('STORAGE',storage)})


def test_disabled_engine_init_never_migrates_grants_or_creates_directory():
    controller=(JAVA/'app/exteraless/plugins/PluginsController.java').read_text()
    init=method(controller,'public void init(Context context)')
    assert 'PluginGrantStore.get()' not in init and 'mkdirs()' not in init and 'PluginGrantStore.warmUp()' not in init
    assert init.index('if (!isEngineEnabled())')<init.index('PythonPluginsEngine.getInstance().ensureStarted(')
    engine=(JAVA/'app/exteraless/plugins/PythonPluginsEngine.java').read_text()
    start=method(engine,'public void ensureStarted(Context appContext, StartCallback callback)')
    assert start.index('executor.execute(')<start.index('prepareRuntimeStorage(appContext)')<start.index('Python.start(')


def test_leak_scans_and_gc_are_explicit_debug_tools_only(tmp_path):
    blocks=[]
    for path,marker in [('org/telegram/ui/LaunchActivity.java','LeakDetector.getInstance().start();'),
                         ('org/telegram/ui/ActionBar/BaseFragment.java','LeakDetector.getInstance().add(this);'),
                         ('org/telegram/ui/ActionBar/BottomSheet.java','LeakDetector.getInstance().add(this);'),
                         ('org/telegram/messenger/ApplicationLoader.java','new ANRDetector(FileLog::dumpANR);')]:
        source=(JAVA/path).read_text();end=source.index(marker);start=source.rfind('if (',0,end)
        block=method(source[start:],source[start:source.index('{',start)+1]);assert block.startswith('if (BuildConfig.DEBUG_TOOLS)')
        blocks.append(block)
    probe(tmp_path,{'Probe.java':'''class BuildConfig{static boolean DEBUG_TOOLS;}class LeakDetector{static int gets,starts,adds;static LeakDetector getInstance(){gets++;return new LeakDetector();}void start(){starts++;}void add(Object o){adds++;}}
class FileLog{static void dumpANR(){}}class ANRDetector{static int count;ANRDetector(Runnable r){count++;}}
public class Probe{void launch(){BLOCKS}public static void main(String[]a){Probe p=new Probe();p.launch();
 if(LeakDetector.gets!=0||ANRDetector.count!=0)throw new AssertionError("diagnostics enabled in normal beta");
 BuildConfig.DEBUG_TOOLS=true;p.launch();if(LeakDetector.starts!=1||LeakDetector.adds!=2||ANRDetector.count!=1)throw new AssertionError("explicit diagnostics lost");}}'''.replace('BLOCKS','\n'.join(blocks))})


def test_glyph_ui_bind_is_after_frame_but_headless_is_immediate(tmp_path):
    source=(JAVA/'org/telegram/messenger/ApplicationLoader.java').read_text()
    start=method(source,'public static void postInitApplication(boolean prepareDialogs)')
    glyph=method(start,'if (!prepareDialogs || android.os.Looper.myLooper() != android.os.Looper.getMainLooper())')
    sign='if (prepareDialogs && android.os.Looper.myLooper() == android.os.Looper.getMainLooper())'
    ui=method(start,sign);tail=start[start.index(sign)+len(ui):];headless=method(tail,'else')
    probe(tmp_path,{
'android/os/Looper.java':'package android.os;public class Looper{public static boolean main=true;static Object m=new Object();public static Object myLooper(){return main?m:null;}public static Object getMainLooper(){return m;}}',
'android/view/Choreographer.java':'package android.view;public class Choreographer{public static java.util.ArrayDeque<java.util.function.LongConsumer> frames=new java.util.ArrayDeque<>();public static Choreographer getInstance(){return new Choreographer();}public void postFrameCallback(java.util.function.LongConsumer r){frames.add(r);}}',
'app/exteraless/glyph/GlyphController.java':'package app.exteraless.glyph;public class GlyphController{public static int binds;public static GlyphController getInstance(){return new GlyphController();}public void init(){binds++;}}',
'Probe.java':'''import java.util.*;import app.exteraless.glyph.GlyphController;public class Probe{
 static class Handler{ArrayDeque<Runnable> jobs=new ArrayDeque<>();void post(Runnable r){jobs.add(r);}}
 static Handler applicationHandler=new Handler();static int services;static void initializeAccountServices(){services++;}static void initializeAccountServices(boolean incremental){services++;}
 static void run(boolean prepareDialogs){GLYPH UI HEADLESS}
 public static void main(String[]a){run(true);if(GlyphController.binds!=0||services!=0)throw new AssertionError("binder before first traversal");
 android.view.Choreographer.frames.remove().accept(1);if(GlyphController.binds!=0)throw new AssertionError();applicationHandler.jobs.remove().run();
 if(GlyphController.binds!=1||services!=1)throw new AssertionError();
 GlyphController.binds=services=0;run(false);if(GlyphController.binds!=1||services!=1||!applicationHandler.jobs.isEmpty())throw new AssertionError("headless waited for frame");
 GlyphController.binds=services=0;android.os.Looper.main=false;run(true);if(GlyphController.binds!=1||services!=1)throw new AssertionError();
 }}'''.replace('GLYPH',glyph).replace('UI',ui).replace('HEADLESS',headless)})
