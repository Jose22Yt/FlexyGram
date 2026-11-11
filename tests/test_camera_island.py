"""Island behavior with production models/coordinator; Android hosts are explicit doubles."""
from test_camera_pop import POP, runtime_hosts
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method

ACTUAL=[POP/n for n in ['CameraPopState.java','CameraPopConfig.java','CameraPopRuntime.java','CameraPopInbox.java']]


def test_inbox_groups_counts_preserves_order_and_handles_large_lists(tmp_path):
    probe(tmp_path,{'Probe.java':'''import java.util.*;import app.flexygram.camerapop.CameraPopInbox;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]a){
 CameraPopInbox box=new CameraPopInbox();box.update(1,2,true);box.update(-20,4,true);box.update(1,3,true);
 check(box.size()==2&&box.total()==7&&box.snapshot().get(0).dialog==1);
 long revision=box.revision();Object row=box.snapshot().get(0);box.update(1,3,false);check(box.revision()==revision&&box.snapshot().get(0)==row);
 box.update(1,0,false);check(box.size()==1&&box.total()==4&&box.newest()==-20);
 box.retain(Collections.emptySet());check(box.total()==0&&box.size()==0);
 for(int i=1;i<=10000;i++)box.update(i,10,false);check(box.size()==10000&&box.total()==100000&&box.snapshot().size()==10000);
 box.update(1,Integer.MAX_VALUE,true);check(box.total()==Integer.MAX_VALUE);box.clear();check(box.size()==0);
 }}'''},[POP/'CameraPopInbox.java'])


def test_compact_anchor_is_camera_center_at_multiple_densities_and_safe_fallback(tmp_path):
    probe(tmp_path,{'Probe.java':'''import app.flexygram.camerapop.CameraPopGeometry;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]a){
 for(float density:new float[]{1,2,3.5f})for(float cameraX:new float[]{25,180,335}){
 int w=Math.round(360*density),h=Math.round(800*density);float cx=cameraX*density,cy=18*density;
 var p=CameraPopGeometry.island(w,h,0,Math.round(28*density),0,Math.round(24*density),density,20,cx-10*density,cy-10*density,cx+10*density,cy+10*density);
 check(p.cutout&&Math.abs(p.x+p.anchorX-cx)<.01&&Math.abs(p.y+p.anchorY-cy)<.01);
 check(p.x>=0&&p.x+p.width<=w&&p.y>=0&&p.y+p.height<=h);
 check(p.compactLeft>=0&&p.compactLeft+p.compactWidth<=p.width);
 check(p.anchorX>=p.compactLeft&&p.anchorX<=p.compactLeft+p.compactWidth);
 }
 check(!CameraPopGeometry.contains(100,0,250,40,20,101,1));
 check(CameraPopGeometry.contains(100,0,250,40,20,120,1));
 check(CameraPopGeometry.contains(100,0,250,40,20,175,20));
 check(!CameraPopGeometry.contains(100,0,250,40,20,90,20));
 var fallback=CameraPopGeometry.island(360,800,0,28,0,24,1,2,0,0,0,0);
 check(!fallback.cutout&&fallback.y>=28);
 var notch=CameraPopGeometry.island(360,800,0,40,0,24,1,2,80,0,280,40);check(!notch.cutout&&notch.y>=40);
 var land=CameraPopGeometry.island(800,360,30,0,0,24,1,100,0,0,0,0);check(land.y+land.height<=336);
 }}'''},[POP/'CameraPopGeometry.java'])


def test_spring_retarget_keeps_velocity_and_settles_without_idle_work(tmp_path):
    probe(tmp_path,{'Probe.java':'''import app.flexygram.camerapop.CameraPopSpring;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]a){
 CameraPopSpring s=new CameraPopSpring();s.target(1);float before=0;
 for(int i=0;i<8;i++){s.step(1f/60);check(s.value>=before&&s.value<=1);before=s.value;}
 float value=s.value,velocity=s.velocity;s.target(0);check(s.value==value&&s.velocity==velocity);
 int frames=0;while(s.step(1f/120)&&frames++<300)check(s.value>=0&&s.value<=1);
 check(frames<300&&s.value==0&&s.velocity==0);check(!s.step(1f/60));
 s.target(1);for(int i=0;i<80;i++)s.step(.016f);check(s.value==1&&s.velocity==0);
 s.snap(0);check(s.target==0&&s.value==0&&s.velocity==0);
 }}'''},[POP/'CameraPopSpring.java'])


def test_production_animation_clock_finishes_and_retarget_cancels_old_completion(tmp_path):
    source=(POP/'CameraPopCapsule.java').read_text()
    methods='\n'.join(method(source,m) for m in ['private void animateTo(', 'private void finish()', 'private void cancelFrame()'])
    probe(tmp_path,{'Probe.java':'''import java.util.*;import app.flexygram.camerapop.CameraPopSpring;
class Choreographer{interface FrameCallback{void doFrame(long t);}static final Choreographer c=new Choreographer();ArrayList<FrameCallback>q=new ArrayList<>();static Choreographer getInstance(){return c;}void postFrameCallback(FrameCallback f){if(q.contains(f))throw new AssertionError();q.add(f);}void removeFrameCallback(FrameCallback f){q.remove(f);}void step(long t){var copy=new ArrayList<>(q);q.clear();for(var f:copy)f.doFrame(t);}}
public class Probe{CameraPopSpring presence=new CameraPopSpring(),expansion=new CameraPopSpring();Choreographer.FrameCallback frame;Runnable completed;boolean expanded,reduced;long started,previousFrame;static final int GONE=8;static class Panel{void setVisibility(int v){}}Panel panel=new Panel();boolean reducedMotion(){return reduced;}void apply(){}
 METHODS
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){Probe p=new Probe();var c=Choreographer.c;int[]calls={0};
 p.animateTo(1,0,null);for(int i=0;i<8;i++)c.step(1+i*16_000_000L);
 float value=p.presence.value,velocity=p.presence.velocity;p.animateTo(0,0,()->calls[0]++);check(p.presence.value==value&&p.presence.velocity==velocity);
 p.animateTo(1,1,null);for(int i=8;i<100;i++)c.step(1+i*16_000_000L);check(p.frame==null&&c.q.isEmpty()&&p.presence.value==1&&p.expansion.value==1&&calls[0]==0);
 p.animateTo(0,1,()->calls[0]++);for(int i=100;i<200;i++)c.step(1+i*16_000_000L);check(calls[0]==1&&p.frame==null&&c.q.isEmpty());
 p.reduced=true;p.animateTo(1,0,null);check(p.presence.value==1&&p.expansion.value==0&&c.q.isEmpty());
 }}'''.replace('METHODS',methods)},[POP/'CameraPopSpring.java'])


def test_all_chats_aggregate_tap_opens_list_and_row_opens_chat(tmp_path):
    files=runtime_hosts()
    files['Probe.java']='''import java.util.*;import app.flexygram.camerapop.*;import org.telegram.ui.*;import org.telegram.messenger.*;import org.telegram.tgnet.TLRPC;
public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 static void count(long id,int n){TLRPC.Dialog d=new TLRPC.Dialog();d.id=id;d.unread_count=n;d.top_message=100;MessagesController.getInstance(0).dialogs_dict.put(id,d);}
 static void refresh(){NotificationCenter.getInstance(0).post(NotificationCenter.dialogsNeedReload);AndroidUtilities.shortJobs();}
 public static void main(String[]a){CameraPopConfig c=new CameraPopConfig(0);c.set("enabled",true);c.set("duration",0);c.set("quiet",false);
 count(1,3);count(-20,2);count(3,1);LaunchActivity host=new LaunchActivity();CameraPopRuntime.resume(host);AndroidUtilities.shortJobs();
 CameraPopCapsule view=CameraPopCapsule.last;check(view!=null&&view.rows.size()==3);int total=0;for(var r:view.rows)total+=r.unread;check(total==6);
 check(AndroidUtilities.jobs.values().stream().noneMatch(t->t>=1000&&t<=300000));
 view.click.onClick(view);check(view.expanded&&org.telegram.ui.ActionBar.BaseFragment.opened==0);
 view.rowClick.accept(3);check(org.telegram.ui.ActionBar.BaseFragment.opened==1&&((ChatActivity)LaunchActivity.last).getDialogId()==3);
 count(3,0);refresh();check(CameraPopCapsule.last.rows.size()==2);
 count(-20,0);refresh();check(CameraPopCapsule.last.rows.size()==1);
 count(1,0);refresh();check(CameraPopCapsule.last.closing!=null);CameraPopCapsule.last.closing.run();
 CameraPopRuntime.pause(host);check(AndroidUtilities.jobs.isEmpty());
 }}'''
    probe(tmp_path,files,ACTUAL)


def test_duration_expanded_list_pauses_hiding_and_message_routes_restore_on_background(tmp_path):
    files=runtime_hosts()
    files['Probe.java']='''import java.util.*;import app.flexygram.camerapop.*;import org.telegram.ui.*;import org.telegram.messenger.*;import org.telegram.tgnet.TLRPC;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]a){
 CameraPopConfig c=new CameraPopConfig(0);c.set("enabled",true);c.set("duration",1);c.set("quiet",false);
 TLRPC.Dialog d=new TLRPC.Dialog();d.id=1;d.unread_count=1;d.top_message=7;MessagesController.getInstance(0).dialogs_dict.put(1L,d);
 LaunchActivity host=new LaunchActivity();CameraPopRuntime.resume(host);AndroidUtilities.shortJobs();
 MessageObject m=new MessageObject();m.dialog=1;m.id=7;check(CameraPopRuntime.routesToIsland(0,m));
 var view=CameraPopCapsule.last;check(AndroidUtilities.jobs.containsValue(1000L));view.click.onClick(view);check(!AndroidUtilities.jobs.containsValue(1000L));
 view.click.onClick(view);check(AndroidUtilities.jobs.containsValue(1000L));
 CameraPopRuntime.pause(host);check(!CameraPopRuntime.routesToIsland(0,m)&&AndroidUtilities.jobs.isEmpty());
 c.set("only_island",true);check(CameraPopRuntime.routesToIsland(0,m));m.isReactionPush=true;check(!CameraPopRuntime.routesToIsland(0,m));m.isReactionPush=false;
 c.set("all_chats",false);c.select(Collections.singleton(2L));check(!CameraPopRuntime.routesToIsland(0,m));m.dialog=2;check(CameraPopRuntime.routesToIsland(0,m));
 c.set("enabled",false);check(!CameraPopRuntime.routesToIsland(0,m));
 }}'''
    probe(tmp_path,files,ACTUAL)


def test_android_filter_retains_native_queue_and_restores_without_duplicate_state(tmp_path):
    source=(JAVA/'org/telegram/messenger/NotificationsController.java').read_text()
    helper=method(source,'private ArrayList<MessageObject> islandVisibleMessages()')
    probe(tmp_path,{
        'org/telegram/messenger/MessageObject.java':'package org.telegram.messenger;public class MessageObject{public long dialog;public MessageObject(long d){dialog=d;}public long getDialogId(){return dialog;}}',
        'app/flexygram/camerapop/CameraPopRuntime.java':'package app.flexygram.camerapop;public class CameraPopRuntime{public static boolean foreground=true;public static boolean filtersAndroid(int a){return foreground;}public static boolean routesToIsland(int a,org.telegram.messenger.MessageObject m){return foreground&&m.dialog==1;}}',
        'Probe.java':'''import java.util.*;import org.telegram.messenger.MessageObject;import app.flexygram.camerapop.CameraPopRuntime;
 public class Probe{int currentAccount;ArrayList<MessageObject>pushMessages=new ArrayList<>();
 HELPER
 public static void main(String[]a){Probe p=new Probe();var x=new MessageObject(1);var y=new MessageObject(2);p.pushMessages.add(x);p.pushMessages.add(y);
 var visible=p.islandVisibleMessages();if(visible.size()!=1||visible.get(0)!=y||p.pushMessages.size()!=2)throw new AssertionError();
 CameraPopRuntime.foreground=false;if(p.islandVisibleMessages()!=p.pushMessages||p.pushMessages.get(0)!=x)throw new AssertionError();
 }}'''.replace('HELPER',helper),
    })
    show=method(source,'private void showOrUpdateNotification(boolean notifyAboutLast)')
    assert 'hideNotificationSurfaces();' in show
    assert 'islandVisibleMessages()' in method(source,'private void showExtraNotifications(')
    hide=method(source,'private void hideNotificationSurfaces()')
    assert 'pushMessages.clear' not in hide and 'pushMessagesDict.clear' not in hide


def test_explicit_native_cache_reload_reindexes_even_when_dialog_count_is_unchanged(tmp_path):
    files=runtime_hosts()
    files['Probe.java']='''import java.util.*;import app.flexygram.camerapop.*;import org.telegram.ui.*;import org.telegram.messenger.*;import org.telegram.tgnet.TLRPC;
public class Probe{public static void main(String[]a){
 CameraPopConfig c=new CameraPopConfig(0);c.set("enabled",true);c.set("quiet",false);c.set("duration",0);
 TLRPC.Dialog old=new TLRPC.Dialog();old.id=1;old.top_message=1;MessagesController.getInstance(0).dialogs_dict.put(1L,old);
 LaunchActivity host=new LaunchActivity();CameraPopRuntime.resume(host);AndroidUtilities.shortJobs();if(CameraPopCapsule.creates!=0)throw new AssertionError();
 TLRPC.Dialog fresh=new TLRPC.Dialog();fresh.id=-20;fresh.top_message=8;fresh.unread_count=2;
 MessagesController.getInstance(0).dialogs_dict.clear();MessagesController.getInstance(0).dialogs_dict.put(-20L,fresh);
 NotificationCenter.getInstance(0).post(NotificationCenter.dialogsNeedReload,true);AndroidUtilities.shortJobs();
 if(CameraPopCapsule.last==null||CameraPopCapsule.last.rows.size()!=1||CameraPopCapsule.last.rows.get(0).dialog!=-20)throw new AssertionError("same-size cache reload lost pending channel");
 CameraPopRuntime.pause(host);if(!AndroidUtilities.jobs.isEmpty())throw new AssertionError();
 }}'''
    probe(tmp_path,files,ACTUAL)


def test_continuous_arrivals_do_not_postpone_the_first_counter_refresh(tmp_path):
    files=runtime_hosts()
    files['org/telegram/messenger/AndroidUtilities.java']=files['org/telegram/messenger/AndroidUtilities.java'].replace(
        'public static final Map<Runnable,Long>jobs=',
        'public static final Map<Runnable,Integer>postingCounts=new java.util.IdentityHashMap<>();public static final Map<Runnable,Long>jobs=').replace(
        'jobs.put(r,d);','postingCounts.put(r,postingCounts.getOrDefault(r,0)+1);jobs.put(r,d);')
    files['Probe.java']='''import java.util.*;import app.flexygram.camerapop.*;import org.telegram.ui.*;import org.telegram.messenger.*;import org.telegram.tgnet.TLRPC;
public class Probe{public static void main(String[]a){CameraPopConfig c=new CameraPopConfig(0);c.set("enabled",true);c.set("quiet",false);c.set("duration",0);
 TLRPC.Dialog d=new TLRPC.Dialog();d.id=1;d.top_message=1;d.unread_count=1;MessagesController.getInstance(0).dialogs_dict.put(1L,d);
 LaunchActivity host=new LaunchActivity();CameraPopRuntime.resume(host);AndroidUtilities.shortJobs();AndroidUtilities.postingCounts.clear();
 for(int i=2;i<=100;i++){d.unread_count=i;MessageObject m=new MessageObject();m.id=i;m.dialog=1;CameraPopRuntime.incoming(0,m);}
 Runnable refresh=null;for(var e:AndroidUtilities.jobs.entrySet())if(e.getValue()==80L)refresh=e.getKey();
 if(refresh==null||AndroidUtilities.postingCounts.get(refresh)!=1)throw new AssertionError("continuous arrivals postpone refresh");
 AndroidUtilities.shortJobs();if(CameraPopCapsule.creates!=1||CameraPopCapsule.last.rows.get(0).unread!=100)throw new AssertionError("counter not grouped");
 CameraPopRuntime.pause(host);if(!AndroidUtilities.jobs.isEmpty())throw new AssertionError();
 }}'''
    probe(tmp_path,files,ACTUAL)
