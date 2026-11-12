"""Real startup label clock, paused-sort ownership, and native connection presentation."""
from test_render_work_reuse import JAVA,probe
from test_composer_layout import method


def test_startup_label_gate_has_bounded_delay_and_resets_between_accounts(tmp_path):
    probe(tmp_path,{'Probe.java':'''import app.flexygram.performance.StartupStatus;
public class Probe{static void check(boolean v){if(!v)throw new AssertionError();}public static void main(String[]args){StartupStatus s=new StartupStatus();
 check(s.remaining(1,1000,true)==350);check(s.remaining(1,1100,true)==250);check(s.remaining(1,1350,true)==0);check(s.remaining(1,1800,true)==0);
 check(s.remaining(1,1800,false)==0);check(s.remaining(1,1801,true)==350);check(s.remaining(2,1802,true)==350);check(s.remaining(2,1700,true)==350);
 s.reset();check(s.remaining(2,3000,true)==350);check(s.remaining(2,3001,false)==0);
}}'''},[JAVA/'app/flexygram/performance/StartupStatus.java'])


def test_background_skipped_sort_is_dirty_until_the_foreground_sorts_it(tmp_path):
    source=(JAVA/'org/telegram/messenger/MessagesController.java').read_text()
    body=method(source,'public void sortDialogs(')
    prefix=body[body.index('{')+1:body.index('        dialogsServerOnly.clear();')]
    decision=method(source,'public boolean needsDialogsSortOnResume()')
    probe(tmp_path,{'Probe.java':'''class ApplicationLoader{static boolean mainInterfacePaused;}
public class Probe{boolean dialogsLoaded,dialogsSortPending;int sorts;
 void sortDialogs(Object chatsDict){PREFIX sorts++;}
 DECISION
 static void check(boolean v){if(!v)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();check(p.needsDialogsSortOnResume());p.dialogsLoaded=true;p.sortDialogs(null);check(!p.needsDialogsSortOnResume());
 ApplicationLoader.mainInterfacePaused=true;for(int i=0;i<1000;i++)p.sortDialogs(null);check(p.sorts==1&&p.needsDialogsSortOnResume());
 ApplicationLoader.mainInterfacePaused=false;if(p.needsDialogsSortOnResume())p.sortDialogs(null);check(p.sorts==2&&!p.needsDialogsSortOnResume());
 for(int i=0;i<1000;i++)if(p.needsDialogsSortOnResume())p.sortDialogs(null);check(p.sorts==2);
 ApplicationLoader.mainInterfacePaused=true;p.sortDialogs(new Object());check(p.sorts==3&&!p.needsDialogsSortOnResume());
 }}'''.replace('PREFIX',prefix).replace('DECISION',decision)})


def test_actual_connection_title_debounces_initial_cache_but_keeps_real_network_errors(tmp_path):
    text=(JAVA/'org/telegram/ui/LaunchActivity.java').read_text()
    actual=method(text,'private void updateCurrentConnectionState(')
    cancel=method(text,'private void cancelStartupStatusRefresh()')
    probe(tmp_path,{
        'android/os/SystemClock.java':'package android.os;public class SystemClock{public static long now=1000;public static long uptimeMillis(){return now;}}',
        'Probe.java':'''import java.util.*;import app.flexygram.performance.StartupStatus;
class R{static class string{static int WaitingForNetwork=1,Updating=2,ConnectingToProxyWithDots=3,Connecting=4;}}
class ApplicationLoader{static boolean online=true;static boolean isNetworkOnline(){return online;}}
class AndroidUtilities{static boolean tablet;static Runnable pending;static void runOnUIThread(Runnable r,long t){if(pending!=null)throw new AssertionError("duplicate pending status");pending=r;}static void cancelRunOnUIThread(Runnable r){if(pending==r)pending=null;}static boolean isTablet(){return tablet;}}
class ConnectionsManager{static final int ConnectionStateWaitingForNetwork=1,ConnectionStateUpdating=2,ConnectionStateConnectingToProxy=3,ConnectionStateConnecting=4,ConnectionStateConnected=5;static int state;static ConnectionsManager getInstance(int account){return new ConnectionsManager();}int getConnectionState(){return state;}}
class MessagesController{boolean dialogsLoaded;ArrayList<Object>all=new ArrayList<>(),folder=new ArrayList<>();static MessagesController instance=new MessagesController();static MessagesController getInstance(int a){return instance;}ArrayList<Object>getAllDialogs(){return all;}ArrayList<Object>getDialogs(int folderId){return folder;}}
class BaseFragment{}class ProxyListActivity extends BaseFragment{}class ProxySettingsActivity extends BaseFragment{}
class Layout{String title;Runnable action;void setTitleOverlayText(String t,int id,Runnable r){title=t;action=r;}}
public class Probe{int currentAccount,currentConnectionState;Layout actionBarLayout=new Layout();StartupStatus startupStatus=new StartupStatus();boolean startupStatusScheduled,startupUpdatingTitleVisible;Runnable refreshStartupStatus=()->updateCurrentConnectionState(currentAccount);ArrayList<BaseFragment>layerFragmentsStack=new ArrayList<>(),mainFragmentsStack=new ArrayList<>();void presentFragment(BaseFragment f){}
 CANCEL ACTUAL
 static void check(boolean v){if(!v)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();ConnectionsManager.state=ConnectionsManager.ConnectionStateUpdating;p.updateCurrentConnectionState(0);check(p.actionBarLayout.title==null&&AndroidUtilities.pending!=null);
 android.os.SystemClock.now=1100;p.updateCurrentConnectionState(0);check(AndroidUtilities.pending!=null&&p.actionBarLayout.title==null);
 MessagesController.instance.all.add(new Object());android.os.SystemClock.now=1200;p.updateCurrentConnectionState(0);check(AndroidUtilities.pending==null&&p.actionBarLayout.title==null);
 MessagesController.instance.all.clear();android.os.SystemClock.now=1300;p.updateCurrentConnectionState(0);android.os.SystemClock.now=1650;p.updateCurrentConnectionState(0);check("Updating".equals(p.actionBarLayout.title)&&p.startupUpdatingTitleVisible);
 ConnectionsManager.state=ConnectionsManager.ConnectionStateWaitingForNetwork;ApplicationLoader.online=false;p.updateCurrentConnectionState(0);check("WaitingForNetwork".equals(p.actionBarLayout.title)&&AndroidUtilities.pending==null);
 ConnectionsManager.state=ConnectionsManager.ConnectionStateConnectingToProxy;p.updateCurrentConnectionState(0);check("ConnectingToProxyWithDots".equals(p.actionBarLayout.title)&&p.actionBarLayout.action!=null);
 ConnectionsManager.state=ConnectionsManager.ConnectionStateConnected;p.updateCurrentConnectionState(0);check(p.actionBarLayout.title==null&&!p.startupUpdatingTitleVisible);
 }}'''.replace('CANCEL',cancel).replace('ACTUAL',actual)
    },[JAVA/'app/flexygram/performance/StartupStatus.java'])


def test_startup_status_callback_uses_live_account_and_stops_after_activity_pause_or_finish(tmp_path):
    source=(JAVA/'org/telegram/ui/LaunchActivity.java').read_text()
    fields=source[source.index('    private int currentConnectionState;'):source.index('    private final ArrayList<BaseFragment> mainFragmentsStack')]
    probe(tmp_path,{'Probe.java':'''class ParentActivity{protected int currentAccount;boolean finished;boolean isFinishing(){return finished;}}
class AndroidUtilities{static Runnable pending;static void cancelRunOnUIThread(Runnable r){if(pending==r)pending=null;}}
public class Probe extends ParentActivity{
 static boolean isResumed;int updated=-1;
 FIELDS
 void updateCurrentConnectionState(int account){updated=account;}
 public static void main(String[]args){Probe p=new Probe();p.currentAccount=3;p.startupStatusScheduled=true;AndroidUtilities.pending=p.refreshStartupStatus;p.cancelStartupStatusRefresh();if(p.startupStatusScheduled||AndroidUtilities.pending!=null)throw new AssertionError("late status callback retained");
 p.refreshStartupStatus.run();if(p.updated!=-1)throw new AssertionError("paused activity updated");isResumed=true;p.refreshStartupStatus.run();if(p.updated!=3)throw new AssertionError("wrong live account");p.updated=-1;p.finished=true;p.refreshStartupStatus.run();if(p.updated!=-1)throw new AssertionError("finished activity updated");}
}'''.replace('FIELDS',fields)},[JAVA/'app/flexygram/performance/StartupStatus.java'])
    assert 'cancelStartupStatusRefresh();' in method(source,'protected void onPause()')
    assert 'cancelStartupStatusRefresh();' in method(source,'protected void onDestroy()')
