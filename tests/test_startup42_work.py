"""Execute new startup ordering, MediaStore ownership and proxy timer lifetime."""
import pytest
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method


def test_selected_account_precedes_deferred_sessions_and_headless_never_waits_for_frame(tmp_path):
    source=(JAVA/'org/telegram/messenger/ApplicationLoader.java').read_text()
    start=source.index('        for (int position = 0;',source.index('final int startupAccount ='))
    end=source.index('\n\n        // Queue the selected account',start)
    loop=source[start:end]
    helpers='\n'.join(method(source,s)for s in [
        'private static void initializeStartupAccount(int a, boolean prepareDialogs)',
        'private static void checkStartupUnsentMessages(int account)',
        'private static void initializeDeferredStartupAccount(int account)',
        'private static void initializePendingStartupAccounts()',
        'private static void initializeAccountServices(boolean incremental)',
        'private static void initializeAccountSlot(int account)',
        'private static void scheduleAccountServices(int start)'])
    probe(tmp_path,{
'android/os/Looper.java':'package android.os;public class Looper{static final Looper MAIN=new Looper();public static boolean main;public static Looper myLooper(){return main?MAIN:null;}public static Looper getMainLooper(){return MAIN;}}',
'android/os/Trace.java':'package android.os;public class Trace{public static void beginSection(String n){}public static void endSection(){}}',
'android/view/Choreographer.java':'''package android.view;public class Choreographer{static Choreographer c=new Choreographer();public static java.util.ArrayDeque<java.util.function.LongConsumer> frames=new java.util.ArrayDeque<>();public static Choreographer getInstance(){return c;}public void postFrameCallback(java.util.function.LongConsumer r){frames.add(r);}public static void tick(){frames.remove().accept(1L);}}''',
'Probe.java':'''import java.util.*;public class Probe{
 static final List<Integer> core=new ArrayList<>(),unsent=new ArrayList<>(),loaded=new ArrayList<>();static int dialogs,contacts,billing;
 static final boolean[] deferredStartupAccounts=new boolean[10];static int deferredStartupAccountCount;
 static class Handler{ArrayDeque<Runnable> tasks=new ArrayDeque<>();void post(Runnable r){tasks.add(r);}void run(){while(!tasks.isEmpty())tasks.remove().run();}}static Handler applicationHandler=new Handler();
 static class AndroidUtilities{static void runOnUIThread(Runnable r){applicationHandler.post(r);}}
 static class TLRPC{static class User{}}
 static class UserConfig{static final int MAX_ACCOUNT_COUNT=10;static int selectedAccount=3;static UserConfig[] values=new UserConfig[10];int id;boolean active;TLRPC.User user=new TLRPC.User();static UserConfig getInstance(int a){return values[a];}void loadConfig(){loaded.add(id);}boolean isClientActivated(){return active;}TLRPC.User getCurrentUser(){return active?user:null;}}
 static class MessagesController{static boolean[] ready=new boolean[10];static MessagesController getInstance(int a){if(!ready[a]){ready[a]=true;core.add(a);}return new MessagesController();}void putUser(TLRPC.User u,boolean cache){}}
 static class ConnectionsManager{static ConnectionsManager getInstance(int a){return new ConnectionsManager();}int getCurrentTime(){return 1;}}
 static class SharedConfig{static String pushStringStatus;}
 static class SendMessagesHelper{int a;static SendMessagesHelper getInstance(int a){var h=new SendMessagesHelper();h.a=a;return h;}void checkUnsentMessages(){unsent.add(a);}}
 static class MediaController{static void getInstance(){}}
 static class ContactsController{static ContactsController getInstance(int a){return new ContactsController();}void checkAppAccount(){contacts++;}}
 static class DownloadController{static void getInstance(int a){}}
 static class BillingController{static BillingController getInstance(){return new BillingController();}void startConnection(){billing++;}}
 static void prepareSelectedDialogs(){dialogs++;}
 static void launch(boolean prepareDialogs,boolean uiStartup){android.os.Looper.main=uiStartup;int startupAccount=UserConfig.selectedAccount;LOOP}
 HELPERS
 static void check(boolean b){if(!b)throw new AssertionError("core="+core+" unsent="+unsent+" pending="+deferredStartupAccountCount);}
 static void reset(int selected){core.clear();unsent.clear();loaded.clear();dialogs=contacts=billing=deferredStartupAccountCount=0;Arrays.fill(deferredStartupAccounts,false);Arrays.fill(MessagesController.ready,false);android.view.Choreographer.frames.clear();applicationHandler.tasks.clear();UserConfig.selectedAccount=selected;for(int i=0;i<10;i++){UserConfig c=new UserConfig();c.id=i;c.active=i==0||i==1||i==3||i==8;UserConfig.values[i]=c;}}
 public static void main(String[]args){
  reset(3);launch(true,true);check(core.equals(List.of(0,3))&&unsent.isEmpty()&&dialogs==1&&deferredStartupAccountCount==2);applicationHandler.run();check(unsent.equals(List.of(0,3)));check(loaded.size()==9&&loaded.get(0)==3);
  initializeDeferredStartupAccount(1);check(core.equals(List.of(0,3,1))&&deferredStartupAccountCount==1);initializeDeferredStartupAccount(1);applicationHandler.run();check(unsent.size()==3);
  UserConfig.values[8].active=false;initializePendingStartupAccounts();check(deferredStartupAccountCount==0&&!core.contains(8));
  reset(3);launch(false,false);check(core.equals(List.of(0,3,1,8))&&deferredStartupAccountCount==0&&dialogs==0);
  reset(3);launch(true,false);check(core.equals(List.of(0,3,1,8))&&deferredStartupAccountCount==0&&dialogs==1);
  reset(7);launch(true,true);check(core.equals(List.of(0,7))&&deferredStartupAccountCount==3&&dialogs==0);
  initializePendingStartupAccounts();check(core.containsAll(List.of(1,3,8))&&deferredStartupAccountCount==0);
  reset(3);launch(true,true);UserConfig.values[1].active=false;initializeAccountServices(true);
  while(!android.view.Choreographer.frames.isEmpty()){android.view.Choreographer.tick();applicationHandler.run();}
  check(deferredStartupAccountCount==0&&!core.contains(1)&&core.contains(8)&&contacts==3&&billing==1);
  reset(3);launch(true,true);UserConfig.values[3].active=false;applicationHandler.run();check(unsent.equals(List.of(0)));

 }
}'''.replace('LOOP',loop).replace('HELPERS',helpers)
    },[JAVA/'app/flexygram/performance/StartupAccounts.java'])


@pytest.mark.parametrize('initial_proxy_enabled',[False,True])
def test_proxy_timer_has_no_disabled_wakeups_and_cancels_on_setting_changes(tmp_path,initial_proxy_enabled):
    probe(tmp_path,{
'android/os/SystemClock.java':'package android.os;public class SystemClock{public static long elapsedRealtime(){return 1234;}}',
'org/telegram/messenger/AndroidUtilities.java':'''package org.telegram.messenger;public class AndroidUtilities{public static java.util.LinkedHashMap<Runnable,Long> tasks=new java.util.LinkedHashMap<>();public static void runOnUIThread(Runnable r){r.run();}public static void runOnUIThread(Runnable r,long delay){tasks.put(r,delay);}public static void cancelRunOnUIThread(Runnable r){tasks.remove(r);}public static void tick(){Runnable r=tasks.keySet().iterator().next();tasks.remove(r);r.run();}}''',
'org/telegram/messenger/SharedConfig.java':'''package org.telegram.messenger;public class SharedConfig{public static boolean enabled,restoreOnLoad;public static int loads;public static ProxyInfo currentProxy;public static boolean isProxyEnabled(){loads++;if(enabled&&restoreOnLoad&&currentProxy==null)currentProxy=new ProxyInfo();return enabled&&currentProxy!=null;}public static class ProxyInfo{public long ping,availableCheckTime;public boolean available;}}''',
'org/telegram/messenger/MessagesController.java':'package org.telegram.messenger;public class MessagesController{public static Prefs getGlobalMainSettings(){return new Prefs();}public static class Prefs{public boolean getBoolean(String k,boolean d){return SharedConfig.enabled;}}}',
'org/telegram/messenger/UserConfig.java':'package org.telegram.messenger;public class UserConfig{public static int selectedAccount;}',
'org/telegram/tgnet/ConnectionsManager.java':'package org.telegram.tgnet;public class ConnectionsManager{public static int reads,lastAccount;public static int native_getCurrentPingTime(int a){reads++;lastAccount=a;return 42;}}',
'org/telegram/messenger/NotificationCenter.java':'''package org.telegram.messenger;public class NotificationCenter{public static final int proxySettingsChanged=1,proxyPingUpdated=2;public interface NotificationCenterDelegate{void didReceivedNotification(int id,int a,Object...args);}static NotificationCenter c=new NotificationCenter();public static int additions,updates;java.util.List<NotificationCenterDelegate> observers=new java.util.ArrayList<>();public static NotificationCenter getGlobalInstance(){return c;}public void addObserver(NotificationCenterDelegate o,int id){additions++;observers.add(o);}public void postNotificationName(int id,Object...args){if(id==proxyPingUpdated)updates++;else for(var o:observers)o.didReceivedNotification(id,-1,args);}}''',
'Probe.java':'''import org.telegram.messenger.*;import org.telegram.tgnet.ConnectionsManager;import app.exteraless.proxy.ProxyPingController;public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}static void changed(){NotificationCenter.getGlobalInstance().postNotificationName(NotificationCenter.proxySettingsChanged);}
 public static void main(String[]args){
 if(INITIAL){SharedConfig.enabled=true;SharedConfig.restoreOnLoad=true;ProxyPingController.init();check(SharedConfig.loads==0&&AndroidUtilities.tasks.size()==1);AndroidUtilities.tick();check(ConnectionsManager.reads==1&&SharedConfig.loads==1);SharedConfig.enabled=false;changed();SharedConfig.restoreOnLoad=false;SharedConfig.loads=ConnectionsManager.reads=NotificationCenter.updates=0;SharedConfig.currentProxy=null;}
 ProxyPingController.init();ProxyPingController.init();check(NotificationCenter.additions==1&&AndroidUtilities.tasks.isEmpty()&&SharedConfig.loads==0);
 SharedConfig.enabled=true;changed();check(AndroidUtilities.tasks.isEmpty()&&SharedConfig.loads==0);SharedConfig.currentProxy=new SharedConfig.ProxyInfo();changed();changed();check(AndroidUtilities.tasks.size()==1&&AndroidUtilities.tasks.values().iterator().next()==10000L);
 UserConfig.selectedAccount=8;AndroidUtilities.tick();check(ConnectionsManager.reads==1&&ConnectionsManager.lastAccount==8&&NotificationCenter.updates==1&&SharedConfig.currentProxy.ping==42&&SharedConfig.currentProxy.available&&AndroidUtilities.tasks.size()==1);
 Runnable stale=AndroidUtilities.tasks.keySet().iterator().next();SharedConfig.enabled=false;changed();check(AndroidUtilities.tasks.isEmpty());stale.run();check(ConnectionsManager.reads==1&&SharedConfig.loads==1&&AndroidUtilities.tasks.isEmpty());
 SharedConfig.enabled=true;changed();check(AndroidUtilities.tasks.size()==1);SharedConfig.currentProxy=null;changed();check(AndroidUtilities.tasks.isEmpty());
 }}'''.replace('INITIAL',str(initial_proxy_enabled).lower())
    },[JAVA/'app/exteraless/proxy/ProxyPingController.java'])


def test_gallery_binder_calls_run_only_after_worker_dispatch_and_fail_independently(tmp_path):
    source=(JAVA/'org/telegram/messenger/MediaController.java').read_text()
    body=method(source,'private void registerGalleryObservers()')
    dispatch='Utilities.globalQueue.postRunnable(this::registerGalleryObservers);'
    assert dispatch in source
    probe(tmp_path,{'Probe.java':'''import java.util.*;public class Probe{
 static List<String> calls=new ArrayList<>();static int errors;
 static class ContentResolver{int n;void registerContentObserver(String uri,boolean descendants,Object observer){calls.add(Thread.currentThread().getName()+":"+uri);if(++n==2)throw new SecurityException();}}
 static class Context{ContentResolver resolver=new ContentResolver();ContentResolver getContentResolver(){return resolver;}}
 static class ApplicationLoader{static Context applicationContext=new Context();}static class FileLog{static void e(Throwable e){errors++;}}
 static class GalleryObserverExternal{}static class GalleryObserverInternal{}
 static class MediaStore{static class Images{static class Media{static String EXTERNAL_CONTENT_URI="image-external",INTERNAL_CONTENT_URI="image-internal";}}static class Video{static class Media{static String EXTERNAL_CONTENT_URI="video-external",INTERNAL_CONTENT_URI="video-internal";}}}
 static class Utilities{static Queue globalQueue=new Queue();}static class Queue{Runnable task;void postRunnable(Runnable r){task=r;}}
 void request(){DISPATCH} BODY
 public static void main(String[]args)throws Exception{Probe p=new Probe();p.request();if(!calls.isEmpty())throw new AssertionError("binder on caller");Thread worker=new Thread(Utilities.globalQueue.task,"gallery-worker");worker.start();worker.join();if(calls.size()!=4||errors!=1||calls.stream().anyMatch(s->!s.startsWith("gallery-worker:")))throw new AssertionError(calls.toString());}
}'''.replace('DISPATCH',dispatch).replace('BODY',body)})


def test_overlapping_animation_notification_leases_expire_and_do_not_leave_idle_callbacks(tmp_path):
    source=(JAVA/'org/telegram/messenger/NotificationCenter.java').read_text()
    bodies='\n'.join(method(source,s)for s in [
        'public int setAnimationInProgress(int oldIndex, int[] allowedNotifications, boolean stopHeavyOperations)',
        'private void checkForExpiredNotifications()',
        'public void onAnimationFinish(int index)'])
    probe(tmp_path,{
'android/os/SystemClock.java':'package android.os;public class SystemClock{public static long now;public static long elapsedRealtime(){return now;}}',
'Probe.java':'''import java.util.*;import android.os.SystemClock;public class Probe{
 static final long EXPIRE_NOTIFICATIONS_TIME=5017;
 static class AllowedNotifications{int[] allowedIds;long time=SystemClock.elapsedRealtime();}
 static class Sparse<T>{LinkedHashMap<Integer,T> data=new LinkedHashMap<>();T get(int k){return data.get(k);}void put(int k,T v){data.put(k,v);}void delete(int k){data.remove(k);}int size(){return data.size();}T valueAt(int i){return new ArrayList<>(data.values()).get(i);}int keyAt(int i){return new ArrayList<>(data.keySet()).get(i);}}
 Sparse<AllowedNotifications> allowedNotifications=new Sparse<>();HashSet<Integer> heavyOperationsCounter=new HashSet<>();int animationInProgressCount,animationInProgressPointer=1,drains;Runnable checkForExpiredNotifications;
 static class AndroidUtilities{static LinkedHashMap<Runnable,Long> tasks=new LinkedHashMap<>();static void runOnUIThread(Runnable r,long delay){tasks.put(r,SystemClock.now+delay);}static void cancelRunOnUIThread(Runnable r){tasks.remove(r);}static void at(long t){SystemClock.now=t;for(;;){Runnable due=null;for(var e:tasks.entrySet())if(e.getValue()<=t){due=e.getKey();break;}if(due==null)return;tasks.remove(due);due.run();}}}
 static class NotificationCenter{static final int stopAllHeavyOperations=1,startAllHeavyOperations=2;static NotificationCenter global=new NotificationCenter();static Runnable onResume;static NotificationCenter getGlobalInstance(){return global;}void postNotificationName(int id,int flags){if(id==startAllHeavyOperations&&onResume!=null){Runnable r=onResume;onResume=null;r.run();}}}
 static final int stopAllHeavyOperations=1,startAllHeavyOperations=2;
 static NotificationCenter getGlobalInstance(){return NotificationCenter.getGlobalInstance();}
 void runDelayedNotifications(){drains++;}
 BODIES
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){
  Probe p=new Probe();SystemClock.now=0;int old=p.setAnimationInProgress(0,null,true);SystemClock.now=4800;int latest=p.setAnimationInProgress(0,null,true);
  check(AndroidUtilities.tasks.size()==1&&p.animationInProgressCount==2);AndroidUtilities.at(5017);check(p.animationInProgressCount==1&&p.allowedNotifications.get(latest)!=null&&AndroidUtilities.tasks.size()==1);
  AndroidUtilities.at(9817);check(p.animationInProgressCount==0&&p.drains==1&&p.checkForExpiredNotifications==null&&AndroidUtilities.tasks.isEmpty());
  SystemClock.now=10000;int cancel=p.setAnimationInProgress(0,null,true);p.onAnimationFinish(cancel);check(AndroidUtilities.tasks.isEmpty());
  Probe q=new Probe();SystemClock.now=20000;q.setAnimationInProgress(0,null,true);SystemClock.now=24800;int passive=q.setAnimationInProgress(0,null,false);int[] reentrant={0};
  NotificationCenter.onResume=()->reentrant[0]=q.setAnimationInProgress(0,null,true);
  AndroidUtilities.at(25017);check(q.animationInProgressCount==2&&AndroidUtilities.tasks.size()==1&&q.checkForExpiredNotifications!=null);
  q.onAnimationFinish(passive);q.onAnimationFinish(reentrant[0]);check(q.animationInProgressCount==0&&AndroidUtilities.tasks.isEmpty());
 }
}'''.replace('BODIES',bodies)
    })


def test_background_entry_after_ui_init_requests_pending_core_work_without_a_frame(tmp_path):
    source=(JAVA/'org/telegram/messenger/ApplicationLoader.java').read_text()
    guard=method(source,'if (applicationInited)')
    # Rename only the containing class for this isolated compilation.
    guard=guard.replace('ApplicationLoader::initializePendingStartupAccounts','Probe::initializePendingStartupAccounts')
    holder=method(source,'private static final class PendingStartupAccounts').replace('ApplicationLoader::initializePendingStartupAccounts','Probe::initializePendingStartupAccounts')
    probe(tmp_path,{'Probe.java':'''import java.util.*;public class Probe{
 static int deferredStartupAccountCount=2,drains,dialogs;static List<Runnable> jobs=new ArrayList<>();
 static class AndroidUtilities{static void runOnUIThread(Runnable r){jobs.add(r);}}
 static void initializePendingStartupAccounts(){drains++;deferredStartupAccountCount=0;}
 static void prepareSelectedDialogs(){dialogs++;}
 HOLDER
 static void postInitAgain(boolean prepareDialogs){boolean applicationInited=true;GUARD}
 public static void main(String[]args){for(int i=0;i<1000;i++)postInitAgain(false);if(jobs.size()!=1||drains!=0)throw new AssertionError();jobs.remove(0).run();postInitAgain(false);if(drains!=1||!jobs.isEmpty())throw new AssertionError();postInitAgain(true);if(dialogs!=1||!jobs.isEmpty())throw new AssertionError();}
}'''.replace('GUARD',guard).replace('HOLDER',holder)},[JAVA/'app/flexygram/performance/CoalescedTask.java'])
