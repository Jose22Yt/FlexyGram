"""Execute Camera Pop policy/geometry and coordinator with deterministic native hosts.
These are JVM correctness tests, not Android graphics or physical-device FPS tests.
"""
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from test_render_work_reuse import JAVA, ROOT, probe

POP = JAVA/'app/flexygram/camerapop'



def test_state_dedup_read_persistence_queue_and_quiet_hours(tmp_path):
    probe(tmp_path, {'Probe.java': '''import java.util.*;import app.flexygram.camerapop.CameraPopState;
public class Probe{
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 public static void main(String[]a){
 CameraPopState s=new CameraPopState();
 check(s.incoming(-10,7,3,1000,300000));check(!s.incoming(-10,7,3,2000,300000));
 check(s.incoming(-11,7,0,1000,300000));check(s.incoming(-10,8,3,2000,300000));
 check(s.get(-10).due==301000); // A noisy chat never postpones its first deadline.
 s.enqueue(-10);s.enqueue(-10);check(s.poll()==-10&&s.poll()==0);
 s.enqueue(1);s.enqueue(2);s.enqueue(3);s.enqueue(4);check(s.poll()==2&&s.poll()==3&&s.poll()==4&&s.poll()==0);
 s.enqueue(-10);s.read(-10);check(s.get(-10).due==0&&s.poll()==0&&!s.incoming(-10,8,3,4000,300000));
 CameraPopState restored=new CameraPopState();Set<String>saved=s.save();saved.add("bad");saved.add("1:bad:0:0");
 restored.restore(saved,new HashSet<>(Arrays.asList(-10L,-11L)));
 check(restored.get(-10).due==0&&!restored.incoming(-10,8,3,5000,300000));
 check(restored.nextDue()==301000);restored.retain(Collections.singleton(-10L));check(restored.get(-11)==null);
 check(restored.incoming(-10,9,3,5000,300000)&&restored.get(-10).due==305000);
 check(CameraPopState.quiet(23*60,22*60,8*60));check(CameraPopState.quiet(7*60,22*60,8*60));
 check(!CameraPopState.quiet(8*60,22*60,8*60));check(!CameraPopState.quiet(12*60,22*60,8*60));
 check(CameraPopState.quiet(600,600,600));check(CameraPopState.quiet(600,540,720));
 check(!CameraPopState.quiet(720,540,720));
 CameraPopState otherAccount=new CameraPopState();check(otherAccount.incoming(-10,9,0,0,1));
 restored.clear();check(restored.nextDue()==Long.MAX_VALUE&&restored.save().isEmpty());
 }}'''}, [POP/'CameraPopState.java'])


def runtime_hosts():
    """Explicit doubles for native UI/lifecycle; the production coordinator/config execute."""
    files={
'android/content/SharedPreferences.java':'''package android.content;import java.util.*;public class SharedPreferences {
 public int writes;final Map<String,Object>data=new HashMap<>();public boolean getBoolean(String k,boolean d){return (Boolean)data.getOrDefault(k,d);}
 public int getInt(String k,int d){return (Integer)data.getOrDefault(k,d);}public long getLong(String k,long d){return (Long)data.getOrDefault(k,d);}
 @SuppressWarnings("unchecked")public Set<String>getStringSet(String k,Set<String>d){return new HashSet<>((Set<String>)data.getOrDefault(k,d));}
 public Editor edit(){return new Editor();}public class Editor{public Editor putBoolean(String k,boolean v){data.put(k,v);return this;}public Editor putInt(String k,int v){data.put(k,v);return this;}public Editor putLong(String k,long v){data.put(k,v);return this;}public Editor putStringSet(String k,Set<String>v){data.put(k,new HashSet<>(v));return this;}public Editor remove(String k){data.remove(k);return this;}public void apply(){writes++;}}}''',
'android/os/Bundle.java':'package android.os;public class Bundle extends java.util.HashMap<String,Object>{public void putLong(String k,long v){put(k,v);}}',
'android/os/Build.java':'package android.os;public class Build{public static class VERSION{public static int SDK_INT=35;}}',
'android/view/Gravity.java':'package android.view;public class Gravity{public static final int TOP=48,LEFT=3;}',
'android/view/View.java':'package android.view;public class View{public interface OnClickListener{void onClick(View v);}public void postOnAnimation(Runnable r){r.run();}public void removeCallbacks(Runnable r){org.telegram.messenger.AndroidUtilities.cancelRunOnUIThread(r);}}',
'android/widget/FrameLayout.java':'package android.widget;public class FrameLayout extends android.view.View{public void addView(android.view.View v,LayoutParams p){}public static class LayoutParams{public static int WRAP_CONTENT=-2;public LayoutParams(int w,int h,int g){}}}',
'org/telegram/tgnet/TLRPC.java':'''package org.telegram.tgnet;public class TLRPC{
 public static class Dialog{public long id;public int unread_count,top_message;}
 public static class User{public String name="Peer";}public static class Chat{public String title="Group";}
 public static class TL_messageActionEmpty{}
 public static class Message{public boolean unread=true,from_scheduled;public Object action;}
}''',
'org/telegram/messenger/UserConfig.java':'''package org.telegram.messenger;public class UserConfig{public static int selectedAccount;public long owner=100;public boolean active=true;static final UserConfig[]all={new UserConfig(),new UserConfig()};public static UserConfig getInstance(int a){return all[a];}public boolean isClientActivated(){return active;}public long getClientUserId(){return owner;}}''',
'org/telegram/messenger/SharedConfig.java':'package org.telegram.messenger;public class SharedConfig{public static boolean appLocked,isWaitingForPasscodeEnter;}',
'org/telegram/messenger/AndroidUtilities.java':'''package org.telegram.messenger;import java.util.*;public class AndroidUtilities{
 public static final Map<Runnable,Long>jobs=new LinkedHashMap<>();public static int posts;
 public static void runOnUIThread(Runnable r){posts++;r.run();}public static void runOnUIThread(Runnable r,long d){jobs.put(r,d);}
 public static void cancelRunOnUIThread(Runnable r){jobs.remove(r);}public static int dp(int n){return n;}public static boolean needShowPasscode(){return false;}
 public static void shortJobs(){for(int round=0;round<20;round++){var ready=new ArrayList<Runnable>();for(var e:jobs.entrySet())if(e.getValue()<=500)ready.add(e.getKey());if(ready.isEmpty())return;for(var r:ready){jobs.remove(r);r.run();}}throw new AssertionError("callback loop");}
}''',
'org/telegram/messenger/MessageObject.java':'''package org.telegram.messenger;public class MessageObject{public org.telegram.tgnet.TLRPC.Message messageOwner=new org.telegram.tgnet.TLRPC.Message();public long dialog;public int id;public boolean out,isReactionPush,isStoryReactionPush,isOauthPush,isStoryPush;public int getId(){return id;}public long getDialogId(){return dialog;}public boolean isOutOwner(){return out;}public boolean isFcmMessage(){return false;}public boolean isImportedForward(){return false;}public static long getTopicId(int a,Object m,boolean f){return 0;}}''',
'org/telegram/messenger/MessagesController.java':'''package org.telegram.messenger;import java.util.*;import android.content.SharedPreferences;import org.telegram.tgnet.TLRPC;
 public class MessagesController{static final MessagesController[]all={new MessagesController(),new MessagesController()};public final Map<Long,TLRPC.Dialog>dialogs_dict=new HashMap<>();public final Map<Long,Integer>dialogs_read_inbox_max=new HashMap<>();public final Set<Long>muted=new HashSet<>();final SharedPreferences prefs=new SharedPreferences();public static MessagesController getInstance(int a){return all[a];}public static SharedPreferences getMainSettings(int a){return all[a].prefs;}public java.util.ArrayList<TLRPC.Dialog> getAllDialogs(){return new java.util.ArrayList<>(dialogs_dict.values());}public boolean isForum(MessageObject m){return false;}public boolean isDialogMuted(long d,long t){return muted.contains(d);}public TLRPC.User getUser(long d){return new TLRPC.User();}public TLRPC.Chat getChat(long d){return new TLRPC.Chat();}public boolean checkCanOpenChat(android.os.Bundle b,org.telegram.ui.ActionBar.BaseFragment f){return true;}}''',
'org/telegram/messenger/NotificationCenter.java':'''package org.telegram.messenger;import java.util.*;public class NotificationCenter{
 public static final int messagesRead=1,messagesDeleted=2,dialogsNeedReload=3,dialogsUnreadCounterChanged=4,notificationsSettingsUpdated=5,appDidLogout=6,didSetPasscode=7,passcodeDismissed=8,openedChatChanged=9,didReceiveNewMessages=10;
 public interface NotificationCenterDelegate{void didReceivedNotification(int e,int a,Object...args);}
 static final NotificationCenter[]all={new NotificationCenter(0),new NotificationCenter(1),new NotificationCenter(-1)};final int account;NotificationCenter(int a){account=a;}
 public final Map<Integer,Set<NotificationCenterDelegate>>listeners=new HashMap<>();public static NotificationCenter getInstance(int a){return all[a];}public static NotificationCenter getGlobalInstance(){return all[2];}
 public void addObserver(NotificationCenterDelegate d,int e){listeners.computeIfAbsent(e,k->new HashSet<>()).add(d);}public void removeObserver(NotificationCenterDelegate d,int e){listeners.getOrDefault(e,Collections.emptySet()).remove(d);}
 public void post(int e,Object...args){for(var d:new ArrayList<>(listeners.getOrDefault(e,Collections.emptySet())))d.didReceivedNotification(e,account,args);}
}''',
'org/telegram/messenger/DialogObject.java':'package org.telegram.messenger;public class DialogObject{public static boolean isEncryptedDialog(long d){return false;}public static boolean isUserDialog(long d){return d>0;}public static boolean isChatDialog(long d){return d<0;}}',
'org/telegram/messenger/LocaleController.java':'package org.telegram.messenger;public class LocaleController{public static String getString(int r){return r==R.string.CameraPopPrivateName?"PRIVATE":"DEMO";}public static String formatPluralString(String s,int n){return n+" unread";}}',
'org/telegram/messenger/R.java':'package org.telegram.messenger;public class R{public static class string{public static int CameraPopDemoName=1,CameraPopDemoMessage=2,CameraPopPrivateName=3;}}',
'org/telegram/messenger/UserObject.java':'package org.telegram.messenger;public class UserObject{public static String getUserName(org.telegram.tgnet.TLRPC.User u){return u.name;}}',
'org/telegram/ui/ActionBar/BaseFragment.java':'package org.telegram.ui.ActionBar;public class BaseFragment{public static int opened;public int getCurrentAccount(){return org.telegram.messenger.UserConfig.selectedAccount;}public boolean presentFragment(BaseFragment f){opened++;org.telegram.ui.LaunchActivity.last=f;return true;}}',
'org/telegram/ui/ChatActivity.java':'package org.telegram.ui;public class ChatActivity extends org.telegram.ui.ActionBar.BaseFragment{public static final int MODE_DEFAULT=0;public final android.os.Bundle args;public ChatActivity(android.os.Bundle b){args=b;}public long getDialogId(){return args.containsKey("user_id")?(long)args.get("user_id"):-(long)args.get("chat_id");}}',
'org/telegram/ui/LaunchActivity.java':'''package org.telegram.ui;public class LaunchActivity{public static org.telegram.ui.ActionBar.BaseFragment last=new org.telegram.ui.ActionBar.BaseFragment();public final android.widget.FrameLayout root=new android.widget.FrameLayout();public boolean focus=true;public boolean isFinishing(){return false;}public boolean isDestroyed(){return false;}public boolean hasWindowFocus(){return focus;}public boolean isInPictureInPictureMode(){return false;}public Window getWindow(){return new Window();}public class Window{public android.view.View getDecorView(){return root;}}public static org.telegram.ui.ActionBar.BaseFragment getLastFragmentIncludeMainTabs(){return last;}}''',
 'tw/nekomimi/nekogram/helpers/PasscodeHelper.java':'package tw.nekomimi.nekogram.helpers;public class PasscodeHelper{public static boolean isAccountHidden(int a){return false;}}',
'app/flexygram/camerapop/CameraPopCapsule.java':'package app.flexygram.camerapop;public class CameraPopCapsule extends android.view.View{public static int creates,releases,enters,exits;public static CameraPopCapsule last;public Object peer;public String title;public android.view.View.OnClickListener click;public Runnable closing,expansionChanged;public java.util.function.LongConsumer rowClick;public boolean expanded;public java.util.List<CameraPopInbox.Row> rows;public CameraPopCapsule(android.widget.FrameLayout r){creates++;last=this;}public void bind(String t,String d,Object p){title=t;peer=p;}public void bindRows(int a,boolean names,java.util.List<CameraPopInbox.Row> rows,java.util.function.LongConsumer click,Runnable change){this.rows=rows;peer=names?new Object():null;title=names?"PEER":"PRIVATE";rowClick=click;expansionChanged=change;}public boolean isExiting(){return closing!=null;}public boolean isExpanded(){return expanded;}public void toggleExpanded(){expanded=!expanded;if(expansionChanged!=null)expansionChanged.run();}public void setAlpha(float a){}public void setOnClickListener(android.view.View.OnClickListener c){click=c;}public void enter(){enters++;}public void exit(Runnable r){exits++;closing=r;}public void release(){releases++;closing=null;click=null;rowClick=null;} }'
    }
    files['org/telegram/messenger/NotificationsSettingsFacade.java']='package org.telegram.messenger;public class NotificationsSettingsFacade{public static final String PROPERTY_NOTIFY="notify2_",PROPERTY_NOTIFY_UNTIL="notifyuntil_";final int account;public NotificationsSettingsFacade(int a){account=a;}public int getProperty(String key,long dialog,long topic,int fallback){return key.equals(PROPERTY_NOTIFY)&&MessagesController.getInstance(account).muted.contains(dialog)?2:fallback;}}'
    files['org/telegram/tgnet/ConnectionsManager.java']='package org.telegram.tgnet;public class ConnectionsManager{public static ConnectionsManager getInstance(int a){return new ConnectionsManager();}public int getCurrentTime(){return (int)(System.currentTimeMillis()/1000);}}'
    files['org/telegram/messenger/NotificationsController.java']='package org.telegram.messenger;public class NotificationsController{public static int refreshes;public static NotificationsController getInstance(int a){return new NotificationsController();}public void showNotifications(){refreshes++;}}'
    return files


def test_coordinator_selection_privacy_read_mute_lifecycle_and_navigation(tmp_path):
    files=runtime_hosts()
    files['Probe.java']='''import java.util.*;import app.flexygram.camerapop.*;import org.telegram.messenger.*;import org.telegram.ui.*;import org.telegram.tgnet.TLRPC;
public class Probe{
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 static void unread(int a,long d,int count,int mid){TLRPC.Dialog v=new TLRPC.Dialog();v.unread_count=count;v.top_message=mid;MessagesController.getInstance(a).dialogs_dict.put(d,v);}
 static void incoming(int a,long d,int mid,boolean normal){MessageObject m=new MessageObject();m.id=mid;m.dialog=d;CameraPopRuntime.incoming(a,m);AndroidUtilities.shortJobs();}
 public static void main(String[]args){
 LaunchActivity host=new LaunchActivity();CameraPopRuntime.resume(host);check(CameraPopCapsule.creates==0);
 CameraPopConfig config=new CameraPopConfig(0);config.set("all_chats",false);config.set("enabled",true);config.set("quiet",false);config.select(new HashSet<>(Arrays.asList(10L,-20L)));
 CameraPopRuntime.configurationChanged(0);unread(0,10,2,7);incoming(0,10,7,true);check(CameraPopCapsule.creates==1&&CameraPopCapsule.last.peer!=null);
 incoming(0,10,7,true);check(CameraPopCapsule.creates==1);int posts=AndroidUtilities.posts;incoming(0,99,1,true);check(AndroidUtilities.posts==posts); // unselected never dispatched to UI
 config.set("names",false);CameraPopRuntime.configurationChanged(0);incoming(0,10,8,true);check(CameraPopCapsule.last.peer==null&&CameraPopCapsule.last.title.equals("PRIVATE"));
 CameraPopCapsule shown=CameraPopCapsule.last;shown.exit(()->{});shown.click.onClick(shown);check(org.telegram.ui.ActionBar.BaseFragment.opened==0&&shown.expanded);shown.rowClick.accept(10L);check(org.telegram.ui.ActionBar.BaseFragment.opened==1&&shown.closing==null); // no animation wait
 LaunchActivity.last=new org.telegram.ui.ActionBar.BaseFragment();unread(0,10,3,9);incoming(0,10,9,true);
 MessagesController.getInstance(0).dialogs_read_inbox_max.put(10L,9);unread(0,10,0,9);NotificationCenter.getInstance(0).post(NotificationCenter.messagesRead);AndroidUtilities.shortJobs();check(shown.releases>=1);
 int creates=CameraPopCapsule.creates;incoming(0,10,9,true);check(CameraPopCapsule.creates==creates);
 MessagesController.getInstance(0).muted.add(-20L);unread(0,-20,1,7);incoming(0,-20,7,false);check(CameraPopCapsule.creates==creates);
 config.set("respect_muted",false);CameraPopRuntime.configurationChanged(0);incoming(0,-20,8,false);check(CameraPopCapsule.creates==creates+1);
 CameraPopRuntime.pause(host);check(AndroidUtilities.jobs.isEmpty());check(NotificationCenter.getInstance(0).listeners.values().stream().allMatch(Set::isEmpty));
 creates=CameraPopCapsule.creates;unread(0,-20,2,9);incoming(0,-20,9,false);check(CameraPopCapsule.creates==creates&&AndroidUtilities.jobs.isEmpty());
 CameraPopRuntime.resume(host);SharedConfig.appLocked=true;CameraPopRuntime.conceal();incoming(0,-20,10,false);check(CameraPopCapsule.creates==creates);SharedConfig.appLocked=false;
 config.set("enabled",false);CameraPopRuntime.configurationChanged(0);check(AndroidUtilities.jobs.isEmpty());
 CameraPopState saved=new CameraPopState();new CameraPopConfig(0).load(saved);check(saved.save().isEmpty());
 CameraPopRuntime.demonstrate();check(CameraPopCapsule.last.peer==null);CameraPopRuntime.pause(host);check(AndroidUtilities.jobs.isEmpty());
 UserConfig.getInstance(0).owner=200;CameraPopConfig nextOwner=new CameraPopConfig(0);check(!nextOwner.enabled&&nextOwner.selected.isEmpty());
 }}'''
    probe(tmp_path, files, [POP/name for name in ['CameraPopState.java','CameraPopConfig.java','CameraPopRuntime.java','CameraPopInbox.java']])


def test_integration_keeps_native_dedup_and_notification_repeat():
    source=(JAVA/'org/telegram/messenger/NotificationsController.java').read_text()
    assert 'CameraPopRuntime.incoming(' not in source
    runtime=(POP/'CameraPopRuntime.java').read_text()
    assert 'NotificationCenter.didReceiveNewMessages' in runtime
    assert 'CameraPopConfig.explicitlyMuted' in runtime
    assert 'isDialogMuted(' not in runtime
    assert 'nativeAllowed' not in runtime
    launch=(JAVA/'org/telegram/ui/LaunchActivity.java').read_text()
    assert 'CameraPopRuntime.resume(this)' in launch and launch.count('CameraPopRuntime.pause(this)')==2
    assert 'CameraPopRuntime.conceal()' in launch
    view=(POP/'CameraPopCapsule.java').read_text()
    cutout=(POP/'CameraPopCutout.java').read_text();assert 'getBoundingRects()' in cutout and 'getCutoutPath()' in cutout
    assert 'removeFrameCallback(frame)' in view and 'root.removeView(this)' in view
    assert 'RenderEffect' not in view and 'blurBitmap' not in view
    assert 'ValueAnimator.areAnimatorsEnabled()' in view
    runtime=(POP/'CameraPopRuntime.java').read_text()
    assert runtime.index('int id=observing;hide();')<runtime.index('last.presentFragment(')
    assert 'SYSTEM_ALERT_WINDOW' not in ''.join(p.read_text() for p in POP.glob('*.java'))


def test_camera_pop_resources_complete_in_english_and_spanish():
    used=set(re.findall(r'R.string.(CameraPop\w+)', ''.join(p.read_text() for p in POP.glob('*.java'))))
    for locale in ['values','values-es']:
        doc=ET.parse(ROOT/f'TMessagesProj/src/main/res/{locale}/strings.xml')
        names=[e.get('name') for e in doc.getroot()]
        assert used<=set(names)
        assert {'CameraPopUnread_one','CameraPopUnread_other'}<=set(names)
        assert len(names)==len(set(names))


def test_reminders_revalidate_native_reads_quiet_hours_and_account_switch(tmp_path):
    files=runtime_hosts()
    files['Probe.java']='''import java.util.*;import java.lang.reflect.*;import app.flexygram.camerapop.*;import org.telegram.messenger.*;import org.telegram.ui.*;import org.telegram.tgnet.TLRPC;
public class Probe{
 static void check(boolean v){if(!v)throw new AssertionError();}
 static CameraPopState state(int account)throws Exception{
 Field f=CameraPopRuntime.class.getDeclaredField("INSTANCE");f.setAccessible(true);Object runtime=f.get(null);
 Method m=CameraPopRuntime.class.getDeclaredMethod("account",int.class);m.setAccessible(true);Object a=m.invoke(runtime,account);
 Field s=a.getClass().getDeclaredField("state");s.setAccessible(true);return (CameraPopState)s.get(a);
 }
 static void arrival(int a,int message){MessageObject m=new MessageObject();m.id=message;m.dialog=10;CameraPopRuntime.incoming(a,m);AndroidUtilities.shortJobs();}
 static void refresh(){NotificationCenter.getInstance(UserConfig.selectedAccount).post(NotificationCenter.dialogsNeedReload);AndroidUtilities.shortJobs();}
 public static void main(String[]args)throws Exception{
 for(int a=0;a<2;a++){CameraPopConfig c=new CameraPopConfig(a);c.set("all_chats",false);c.set("enabled",true);c.set("immediate",false);c.set("quiet",false);c.select(Collections.singleton(10L));TLRPC.Dialog d=new TLRPC.Dialog();d.unread_count=2;d.top_message=7;MessagesController.getInstance(a).dialogs_dict.put(10L,d);CameraPopRuntime.configurationChanged(a);}
 LaunchActivity host=new LaunchActivity();CameraPopRuntime.resume(host);arrival(0,8);check(CameraPopCapsule.creates==1);
 state(0).defer(10,1);refresh();check(CameraPopCapsule.creates==1&&state(0).get(10).due>System.currentTimeMillis());
 CameraPopRuntime.pause(host);check(AndroidUtilities.jobs.isEmpty());
 new CameraPopConfig(0).set("quiet",true);new CameraPopConfig(0).set("quiet_start",0);new CameraPopConfig(0).set("quiet_end",0);CameraPopRuntime.configurationChanged(0);
 CameraPopRuntime.resume(host);state(0).defer(10,1);int count=CameraPopCapsule.creates;refresh();check(CameraPopCapsule.creates==count);
 new CameraPopConfig(0).set("quiet",false);CameraPopRuntime.configurationChanged(0);MessagesController.getInstance(0).dialogs_dict.get(10L).unread_count=0;
 state(0).defer(10,1);refresh();check(state(0).get(10).due==0&&CameraPopCapsule.creates==count);
 UserConfig.selectedAccount=1;CameraPopRuntime.accountChanged(host);state(1).defer(10,1);refresh();check(CameraPopCapsule.creates==count+1);
 CameraPopRuntime.pause(host);LaunchActivity recreated=new LaunchActivity();CameraPopRuntime.resume(recreated);check(CameraPopCapsule.creates==count+1); // no duplicate on recreation
 NotificationCenter.getInstance(1).post(NotificationCenter.appDidLogout);check(AndroidUtilities.jobs.isEmpty());
 CameraPopState saved=new CameraPopState();new CameraPopConfig(1).load(saved);check(saved.save().isEmpty());CameraPopRuntime.pause(recreated);
 }}'''
    probe(tmp_path,files,[POP/name for name in ['CameraPopState.java','CameraPopConfig.java','CameraPopRuntime.java','CameraPopInbox.java']])


def test_foreground_burst_batches_preference_writes_and_pause_flushes(tmp_path):
    files=runtime_hosts()
    files['Probe.java']='''import java.util.*;import app.flexygram.camerapop.*;import org.telegram.messenger.*;import org.telegram.ui.*;import org.telegram.tgnet.TLRPC;
public class Probe{
 public static void main(String[]args){CameraPopConfig c=new CameraPopConfig(0);c.set("all_chats",false);c.set("enabled",true);c.set("immediate",false);c.set("reminders",false);c.set("quiet",false);c.select(Collections.singleton(10L));CameraPopRuntime.configurationChanged(0);
 TLRPC.Dialog d=new TLRPC.Dialog();d.unread_count=100;d.top_message=100;MessagesController.getInstance(0).dialogs_dict.put(10L,d);
 LaunchActivity host=new LaunchActivity();CameraPopRuntime.resume(host);int before=c.prefs.writes;
 for(int i=101;i<=200;i++){MessageObject m=new MessageObject();m.id=i;m.dialog=10;CameraPopRuntime.incoming(0,m);}
 if(c.prefs.writes!=before)throw new AssertionError("one preference write per message");
 CameraPopRuntime.pause(host);if(c.prefs.writes!=before+1||!AndroidUtilities.jobs.isEmpty())throw new AssertionError("pause did not flush/cancel");
 CameraPopState restored=new CameraPopState();new CameraPopConfig(0).load(restored);
 if(restored.get(10).message!=200)throw new AssertionError("latest pending state lost on pause");
 }}'''
    probe(tmp_path,files,[POP/name for name in ['CameraPopState.java','CameraPopConfig.java','CameraPopRuntime.java','CameraPopInbox.java']])


def test_seeded_unread_does_not_consume_live_arrival_and_legacy_state_migrates(tmp_path):
    probe(tmp_path,{'Probe.java':'''import java.util.*;import app.flexygram.camerapop.CameraPopState;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]a){
 CameraPopState state=new CameraPopState();check(state.seed(-42,100,1000,300000));
 check(state.get(-42).received==0);CameraPopState restored=new CameraPopState();restored.restore(state.save(),Collections.singleton(-42L));
 check(restored.incoming(-42,100,7,2000,300000));check(!restored.incoming(-42,100,7,2100,300000));
 check(restored.get(-42).due==301000&&restored.get(-42).topic==7);
 restored.read(-42);check(!restored.incoming(-42,100,7,2200,300000));
 CameraPopState old=new CameraPopState();old.restore(Collections.singleton("-42:101:0:9000"),Collections.singleton(-42L));
 check(old.get(-42).received==101&&!old.incoming(-42,101,0,0,1));
 }}'''},[POP/'CameraPopState.java'])


def test_native_message_events_ignore_system_notifications_and_survive_counter_focus_races(tmp_path):
    files=runtime_hosts()
    # Global notifications disabled makes the old isDialogMuted route fail for every chat.
    files['org/telegram/messenger/MessagesController.java']=files['org/telegram/messenger/MessagesController.java'].replace('return muted.contains(d);','return true;')
    files['Probe.java']='''import java.util.*;import app.flexygram.camerapop.*;import org.telegram.messenger.*;import org.telegram.ui.*;import org.telegram.tgnet.TLRPC;
public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 static void count(long id,int n,int msg){TLRPC.Dialog d=new TLRPC.Dialog();d.unread_count=n;d.top_message=msg;MessagesController.getInstance(0).dialogs_dict.put(id,d);}
 static MessageObject message(long dialog,int id){MessageObject m=new MessageObject();m.dialog=dialog;m.id=id;return m;}
 static void event(MessageObject m,boolean scheduled,int mode){NotificationCenter.getInstance(0).post(NotificationCenter.didReceiveNewMessages,m.dialog,new ArrayList<>(Collections.singleton(m)),scheduled,mode);AndroidUtilities.shortJobs();}
 static void refresh(){NotificationCenter.getInstance(0).post(NotificationCenter.dialogsNeedReload);AndroidUtilities.shortJobs();}
 public static void main(String[]a){
 CameraPopConfig c=new CameraPopConfig(0);c.set("all_chats",false);c.set("enabled",true);c.set("reminders",false);c.set("quiet",false);c.select(new HashSet<>(Arrays.asList(10L,-20L)));
 c.prefs.edit().putBoolean("EnableAll",false).putInt("EnableChannel2",Integer.MAX_VALUE).apply();
 count(10,1,7);LaunchActivity host=new LaunchActivity();CameraPopRuntime.resume(host);
 event(message(10,7),false,0);check(CameraPopCapsule.creates==1); // Even though native unread seeding saw ID 7 first.
 count(10,2,8);event(message(10,8),false,0);refresh();CameraPopRuntime.conceal();refresh();check(CameraPopCapsule.creates==1); // A visible update must not enqueue a duplicate capsule.
 count(10,0,7);MessagesController.getInstance(0).dialogs_read_inbox_max.put(10L,7);refresh();
 int n=CameraPopCapsule.creates;event(message(10,7),false,0);check(CameraPopCapsule.creates==n);
 MessageObject out=message(10,8);out.out=true;event(out,false,0);event(message(10,8),true,0);event(message(10,8),false,5);check(CameraPopCapsule.creates==n);
 count(-20,0,9);event(message(-20,9),false,0);refresh();check(CameraPopCapsule.creates==n); // Count hasn't caught up: never invent one.
 count(-20,1,9);refresh();check(CameraPopCapsule.creates==n+1); // Late native counter recovers the queued channel alert.
 host.focus=false;CameraPopRuntime.windowFocusChanged(host,false);count(10,1,10);event(message(10,10),false,0);check(CameraPopCapsule.creates==n+1);
 host.focus=true;CameraPopRuntime.windowFocusChanged(host,true);AndroidUtilities.shortJobs();check(CameraPopCapsule.creates==n+2);
 CameraPopRuntime.conceal();MessagesController.getInstance(0).muted.add(10L);event(message(10,11),false,0);check(CameraPopCapsule.creates==n+2);
 c.set("respect_muted",false);CameraPopRuntime.configurationChanged(0);AndroidUtilities.shortJobs();check(CameraPopCapsule.creates==n+3);
 CameraPopRuntime.conceal();event(message(99,12),false,0);check(CameraPopCapsule.creates==n+3);
 CameraPopRuntime.pause(host);check(AndroidUtilities.jobs.isEmpty());
 }}'''
    probe(tmp_path,files,[POP/n for n in ['CameraPopState.java','CameraPopConfig.java','CameraPopRuntime.java','CameraPopInbox.java']])


def test_every_foreground_entry_reminds_without_waiting_for_interval_or_initial_cache(tmp_path):
    files=runtime_hosts()
    files['Probe.java']='''import java.util.*;import app.flexygram.camerapop.*;import org.telegram.messenger.*;import org.telegram.ui.*;import org.telegram.tgnet.TLRPC;
public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 static void count(int n,int message){TLRPC.Dialog d=new TLRPC.Dialog();d.unread_count=n;d.top_message=message;MessagesController.getInstance(0).dialogs_dict.put(10L,d);}
 static void dismiss(){Runnable expire=null;for(var e:AndroidUtilities.jobs.entrySet())if(e.getValue()==5000L)expire=e.getKey();check(expire!=null);AndroidUtilities.jobs.remove(expire);expire.run();CameraPopCapsule.last.closing.run();AndroidUtilities.shortJobs();}
 static void refresh(){NotificationCenter.getInstance(0).post(NotificationCenter.dialogsNeedReload);AndroidUtilities.shortJobs();}
 public static void main(String[]a){
 CameraPopConfig c=new CameraPopConfig(0);c.set("all_chats",false);c.set("enabled",true);c.set("immediate",false);c.set("quiet",false);c.select(Collections.singleton(10L));
 count(3,7);MessagesController.getInstance(0).dialogs_read_inbox_max.put(10L,1000); // A forum/native counter must not be replaced with an ID heuristic.
 LaunchActivity host=new LaunchActivity();host.focus=false;CameraPopRuntime.resume(host);AndroidUtilities.shortJobs();check(CameraPopCapsule.creates==0);
 host.focus=true;CameraPopRuntime.windowFocusChanged(host,true);AndroidUtilities.shortJobs();check(CameraPopCapsule.creates==1);dismiss();refresh();check(CameraPopCapsule.creates==1);
 CameraPopRuntime.pause(host);CameraPopRuntime.resume(host);AndroidUtilities.shortJobs();check(CameraPopCapsule.creates==2);dismiss();
 CameraPopRuntime.pause(host);MessagesController.getInstance(0).dialogs_dict.remove(10L);CameraPopRuntime.resume(host);AndroidUtilities.shortJobs();check(CameraPopCapsule.creates==2);
 count(2,9);refresh();check(CameraPopCapsule.creates==3);dismiss();
 count(0,9);refresh();CameraPopRuntime.pause(host);CameraPopRuntime.resume(host);AndroidUtilities.shortJobs();check(CameraPopCapsule.creates==3);
 CameraPopRuntime.pause(host);check(AndroidUtilities.jobs.isEmpty());
 }}'''
    probe(tmp_path,files,[POP/n for n in ['CameraPopState.java','CameraPopConfig.java','CameraPopRuntime.java','CameraPopInbox.java']])



def test_explicit_chat_and_topic_mutes_ignore_global_disable_but_respect_expiry(tmp_path):
    from test_composer_layout import method
    config=(POP/'CameraPopConfig.java').read_text()
    facade=(JAVA/'org/telegram/messenger/NotificationsSettingsFacade.java').read_text()
    eligibility=method(config,'public static boolean explicitlyMuted(')
    getter=method(facade,'public int getProperty(String property, long dialogId, long topicId, int defaultValue)')
    probe(tmp_path,{'Probe.java':'''import java.util.*;
class Prefs{Map<String,Integer> data=new HashMap<>();boolean contains(String s){return data.containsKey(s);}int getInt(String k,int d){return data.getOrDefault(k,d);}}
class NotificationsController{static String getSharedPrefKey(long d,long t,boolean b){return t==0?Long.toString(d):d+"_"+t;}}
class ConnectionsManager{static int now=1000;static ConnectionsManager getInstance(int a){return new ConnectionsManager();}int getCurrentTime(){return now;}}
class NotificationsSettingsFacade{static final String PROPERTY_NOTIFY="notify2_",PROPERTY_NOTIFY_UNTIL="notifyuntil_";static Prefs prefs=new Prefs();NotificationsSettingsFacade(int a){}Prefs getPreferences(){return prefs;}
 GETTER
}
public class Probe{
 ELIGIBILITY
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){var p=NotificationsSettingsFacade.prefs.data;p.put("EnableAll2",Integer.MAX_VALUE);p.put("EnableChannel2",Integer.MAX_VALUE);
 check(!explicitlyMuted(0,-20,0));p.put("notify2_-20",2);check(explicitlyMuted(0,-20,0)&&explicitlyMuted(0,-20,7));
 p.put("notify2_-20_7",0);check(!explicitlyMuted(0,-20,7)&&explicitlyMuted(0,-20,0));
 p.put("notify2_-20_7",3);p.put("notifyuntil_-20_7",1020);check(explicitlyMuted(0,-20,7));ConnectionsManager.now=1021;check(!explicitlyMuted(0,-20,7));
 p.remove("notify2_-20_7");check(explicitlyMuted(0,-20,7));p.put("notify2_-20",0);check(!explicitlyMuted(0,-20,7));
 }}'''.replace('GETTER',getter).replace('ELIGIBILITY',eligibility)})
