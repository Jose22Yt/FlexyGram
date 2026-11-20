"""Execute optional-work ordering, lifetime and lazy map setup; no device timing claims."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, ROOT, probe


def test_idle_work_waits_for_usable_content_and_is_one_shot_and_cancellable(tmp_path):
    probe(tmp_path, {
        'android/os/MessageQueue.java': '''package android.os;import java.util.*;
public class MessageQueue{public interface IdleHandler{boolean queueIdle();}public List<IdleHandler>jobs=new ArrayList<>();public int additions;public void addIdleHandler(IdleHandler h){additions++;jobs.add(h);}public void removeIdleHandler(IdleHandler h){jobs.remove(h);}public void fire(){for(var h:new ArrayList<>(jobs))if(!h.queueIdle())jobs.remove(h);}}''',
        'Probe.java': '''import android.os.MessageQueue;import app.flexygram.performance.StartupIdleWork;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]a){
 MessageQueue q=new MessageQueue();boolean[]ready={false};int[]calls={0};StartupIdleWork w=new StartupIdleWork(q,()->ready[0],()->calls[0]++);
 for(int i=0;i<10000;i++)w.afterDraw();check(q.additions==0);
 ready[0]=true;for(int i=0;i<10000;i++)w.afterDraw();check(q.additions==1&&calls[0]==0);
 ready[0]=false;q.fire();check(q.jobs.isEmpty()&&calls[0]==0); // paused/locked between draw and idle
 ready[0]=true;w.afterDraw();q.fire();check(calls[0]==1&&q.jobs.isEmpty());for(int i=0;i<10000;i++)w.afterDraw();check(q.additions==2);
 StartupIdleWork gone=new StartupIdleWork(q,()->true,()->calls[0]++);gone.afterDraw();var stale=q.jobs.get(0);gone.close();stale.queueIdle();check(q.jobs.isEmpty()&&calls[0]==1);
 StartupIdleWork recreated=new StartupIdleWork(q,()->true,()->calls[0]++);recreated.afterDraw();q.fire();check(calls[0]==2);recreated.close();
}}'''
    }, [JAVA/'app/flexygram/performance/StartupIdleWork.java'])


def test_process_maintenance_uses_workers_and_deduplicates_activity_recreation(tmp_path):
    app=(JAVA/'org/telegram/messenger/ApplicationLoader.java').read_text()
    body=method(app, 'public static void scheduleOptionalStartupWork()')
    traced=method(app, 'private static void runOptionalStartupWork(String section, Runnable work)')
    probe(tmp_path, {
        'android/os/Trace.java': 'package android.os;public class Trace{public static int depth;public static void beginSection(String s){depth++;}public static void endSection(){depth--;}}',
        'app/exteraless/links/LinkCleaner.java': 'package app.exteraless.links;public class LinkCleaner{public static int calls;public static void preloadIfEnabled(){calls++;}}',
        'app/exteraless/appearance/M3CircularProgress.java': 'package app.exteraless.appearance;public class M3CircularProgress{public static int calls;public static void prewarm(){calls++;}}',
        'Probe.java': '''import java.util.*;import java.util.concurrent.atomic.AtomicBoolean;
public class Probe{
 static AtomicBoolean optionalStartupScheduled=new AtomicBoolean();static class Queue{List<Runnable>jobs=new ArrayList<>();synchronized void postRunnable(Runnable r){jobs.add(r);}}
 static class Utilities{static Queue globalQueue=new Queue();}static class LauncherIconController{static int calls;static void tryFixLauncherIconIfNeeded(){calls++;}}
 BODY TRACED
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a)throws Exception{Thread[]threads=new Thread[16];for(int i=0;i<threads.length;i++)threads[i]=new Thread(Probe::scheduleOptionalStartupWork);for(Thread t:threads)t.start();for(Thread t:threads)t.join();
 check(Utilities.globalQueue.jobs.size()==3&&LauncherIconController.calls==0&&app.exteraless.links.LinkCleaner.calls==0&&app.exteraless.appearance.M3CircularProgress.calls==0);
 for(Runnable r:Utilities.globalQueue.jobs)r.run();check(LauncherIconController.calls==1&&app.exteraless.links.LinkCleaner.calls==1&&app.exteraless.appearance.M3CircularProgress.calls==1);
 scheduleOptionalStartupWork();check(Utilities.globalQueue.jobs.size()==3&&android.os.Trace.depth==0);
 try{runOptionalStartupWork("failure",()->{throw new IllegalStateException();});throw new AssertionError();}catch(IllegalStateException expected){}check(android.os.Trace.depth==0);
}}'''.replace('BODY',body).replace('TRACED',traced)
    })
    create=method(app,'public void onCreate()')
    assert 'scheduleOptionalStartupWork()' not in create
    assert create.count('if (!BuildConfig.NATIVE_BASELINE_TEST)') == 2
    assert 'org.osmdroid' not in create
    launch=(JAVA/'org/telegram/ui/LaunchActivity.java').read_text()
    assert 'startupIdleWork.close()' in method(launch,'protected void onDestroy()')
    assert 'this::isStartupContentReady, startupAuxiliary' in launch
    assert 'startupIdleWork.afterDraw()' in launch


def test_maps_configure_once_before_first_map_without_startup_race(tmp_path):
    maps=(JAVA/'org/telegram/messenger/OSMDroidMapsProvider.java').read_text()
    configure=method(maps,'private static synchronized void ensureConfigured(Context context)')
    probe(tmp_path, {
        'org/osmdroid/config/IConfigurationProvider.java': 'package org.osmdroid.config;public interface IConfigurationProvider{void setUserAgentValue(String s);void setOsmdroidBasePath(java.io.File f);void setOsmdroidTileCache(java.io.File f);}',
        'org/osmdroid/config/Configuration.java': '''package org.osmdroid.config;public class Configuration implements IConfigurationProvider{static Configuration instance=new Configuration();public static Configuration getInstance(){return instance;}public boolean fail;public int writes;public String agent;public java.io.File base,tiles;public void setUserAgentValue(String s){if(fail)throw new SecurityException();agent=s;writes++;}public void setOsmdroidBasePath(java.io.File f){base=f;writes++;}public void setOsmdroidTileCache(java.io.File f){tiles=f;writes++;}}''',
        'Probe.java': '''public class Probe{static class FileLog{static int errors;static void e(Throwable t){errors++;}}static boolean configured;static class BuildConfig{static String VERSION_NAME="test";}static class Context{Context getApplicationContext(){return this;}java.io.File getCacheDir(){return new java.io.File("/cache");}}
 CONFIGURE
 public static void main(String[]a)throws Exception{var initial=org.osmdroid.config.Configuration.getInstance();initial.fail=true;ensureConfigured(new Context());if(configured||FileLog.errors!=1)throw new AssertionError();initial.fail=false;Thread[]threads=new Thread[16];for(int i=0;i<threads.length;i++)threads[i]=new Thread(()->ensureConfigured(new Context()));for(Thread t:threads)t.start();for(Thread t:threads)t.join();var c=org.osmdroid.config.Configuration.getInstance();if(c.writes!=3||!c.base.toString().equals("/cache/osmdroid")||!c.tiles.toString().equals("/cache/osmdroid/tiles")||!c.agent.startsWith("FlexyGram/test"))throw new AssertionError();}
}'''.replace('CONFIGURE',configure)
    })
    assert 'ensureConfigured(context);' in method(maps,'public void initializeMaps(Context context)')
    view=method(maps,'private OSMDroidMapView(Context context)')
    assert view.index('ensureConfigured(context)') < view.index('new MapView(context)')


def test_force_reload_preserves_datacenter_identity_and_has_no_duplicate_growth(tmp_path):
    neko=(JAVA/'tw/nekomimi/nekogram/NekoConfig.java').read_text()
    body=method(neko,'if (datacenterInfos.isEmpty())')
    probe(tmp_path, {'Probe.java': '''import java.util.*;public class Probe{
 static class DatacenterInfo{final int id;long ping=47;DatacenterInfo(int n){id=n;}}
 static ArrayList<DatacenterInfo>datacenterInfos=new ArrayList<>();static void reload(){BODY}
 public static void main(String[]a){reload();var first=datacenterInfos.get(0);for(int i=0;i<10000;i++)reload();if(datacenterInfos.size()!=5||datacenterInfos.get(0)!=first||first.ping!=47||datacenterInfos.get(4).id!=5)throw new AssertionError();}
}'''.replace('BODY',body)})
    na=(ROOT/'TMessagesProj/src/main/kotlin/xyz/nextalone/nagram/NaConfig.kt').read_text()
    assert 'if (!BuildVars.LOGS_ENABLED && showRPCError.Bool())' in na


def test_preference_prefetch_opens_only_required_files_without_waiting_for_values(tmp_path):
    app=(JAVA/'org/telegram/messenger/ApplicationLoader.java').read_text()
    body=method(app,'private static void preloadStartupPreferences()')
    probe(tmp_path, {
        'app/exteraless/plugins/PluginsConstants.java': (JAVA/'app/exteraless/plugins/PluginsConstants.java').read_text(),
        'android/os/Trace.java': 'package android.os;public class Trace{public static int depth;public static void beginSection(String s){depth++;}public static void endSection(){depth--;}}',
        'Probe.java': '''import java.util.*;public class Probe{static class Context{static final int MODE_PRIVATE=0;List<String>opened=new ArrayList<>();Object getSharedPreferences(String name,int mode){if(mode!=0)throw new AssertionError();opened.add(name);return new Object();}}static Context applicationContext=new Context();
 BODY
 public static void main(String[]a){preloadStartupPreferences();if(!applicationContext.opened.equals(List.of("nkmrcfg","mainconfig","userconfing","exteraless_plugins"))||android.os.Trace.depth!=0)throw new AssertionError();}
}'''.replace('BODY',body)
    })
    create=method(app,'public void onCreate()')
    assert create.index('preloadStartupPreferences()') < create.index('AndroidUtilities.getHelloWorld()') < create.index('NativeLoader.initNativeLibs(')
    assert 'NekoConfig' not in body and '.getAll(' not in body
