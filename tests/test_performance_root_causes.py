"""Execute affected production paths with counted work and deterministic UI/engine queues.

These checks establish redundant work/retry behavior; they do not measure Android FPS.
"""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_plugin_crash_recovery_never_blocks_caller_and_precedes_python(tmp_path):
    source=(JAVA/'app/exteraless/plugins/PluginsController.java').read_text()
    init=method(source,'public void init(Context context)')
    probe(tmp_path, {'Probe.java': '''import java.util.*;
public class Probe {
 static class Context {static final int MODE_PRIVATE=0;Context getApplicationContext(){return this;}Object getSharedPreferences(String n,int m){return new Object();}}
 static class PluginSinkGate {static boolean refuseFromPlugin(String n,boolean b){return false;}}
 static class PluginsConstants {static final String PREFS_NAME="plugins",EVENT_APP_START="start";}
 static class FileLog {static void e(String s){}}
 static class PluginsWatchdog {static int recoveries,starts;PluginsWatchdog(Object p){}String recoverAfterCrash(){check(PythonPluginsEngine.worker);recoveries++;return null;}void start(){check(PythonPluginsEngine.worker);starts++;}}
 interface Callback {void done(boolean ok);}
 static class PythonPluginsEngine {
  static final PythonPluginsEngine engine=new PythonPluginsEngine();static boolean worker;List<Runnable> queue=new ArrayList<>();int starts;
  static PythonPluginsEngine getInstance(){return engine;}void runOnEngine(Runnable r){queue.add(r);}
  void ensureStarted(Context c,Callback callback){check(worker&&PluginsWatchdog.recoveries>0);starts++;callback.done(true);}
  void drain(){worker=true;try{while(!queue.isEmpty())queue.remove(0).run();}finally{worker=false;}}
 }
 boolean initialized,enabled=true;Context appContext;Object preferences;PluginsWatchdog watchdog;int scans,events;
 boolean isEngineEnabled(){return enabled;}void rescanAndLoadEnabled(){check(PythonPluginsEngine.worker);scans++;}void executeOnAppEvent(String event){events++;}
 INIT
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){
  var engine=PythonPluginsEngine.getInstance();Probe p=new Probe();Context c=new Context();
  for(int i=0;i<100;i++)p.init(c);
  check(p.initialized&&p.appContext==c&&p.preferences!=null&&engine.queue.size()==1);
  check(PluginsWatchdog.recoveries==0&&PluginsWatchdog.starts==0&&engine.starts==0);
  engine.drain();check(PluginsWatchdog.recoveries==1&&PluginsWatchdog.starts==1&&engine.starts==1&&p.scans==1&&p.events==1);
  Probe disabled=new Probe();disabled.enabled=false;disabled.init(c);check(engine.queue.isEmpty());
  Probe changed=new Probe();changed.init(c);changed.enabled=false;engine.drain();
  check(engine.starts==1&&PluginsWatchdog.recoveries==1&&changed.events==0);
 }
}'''.replace('INIT',init)})


def test_failed_dialog_load_releases_latch_without_retry_storm_or_stale_logout_callback(tmp_path):
    source=(JAVA/'org/telegram/messenger/MessagesController.java').read_text()
    load=method(source,'public void loadDialogs(final int folderId, int offset, int count, boolean fromCache, Runnable onEmptyCallback)')
    prefix=load[load.index('        if (loadingDialogs.get(folderId)'):load.index('        if (BuildVars.LOGS_ENABLED)')]
    callback=method(load,'getConnectionsManager().sendRequest(req, (response, error) ->')+');'
    cleanup=method(source,'public void cleanup()')
    assert 'dialogsLoadRetryAfter.clear();' in cleanup and 'dialogsLoadGeneration++;' in cleanup
    probe(tmp_path, {'Probe.java': '''import java.util.*;
public class Probe {
 static class SystemClock {static long now=100;static long elapsedRealtime(){return now;}}
 static class AndroidUtilities {static List<Runnable> queue=new ArrayList<>();static void runOnUIThread(Runnable r){queue.add(r);}static void drain(){while(!queue.isEmpty())queue.remove(0).run();}}
 static class Flags {Map<Integer,Boolean> values=new HashMap<>();boolean get(int k){return values.getOrDefault(k,false);}void put(int k,boolean b){values.put(k,b);}}
 static class Deadlines {Map<Integer,Long> values=new HashMap<>();long get(int k){return values.getOrDefault(k,0L);}void put(int k,long v){values.put(k,v);}void delete(int k){values.remove(k);}}
 static class TLRPC {static class messages_Dialogs {List<Object> dialogs=new ArrayList<>();}}
 interface Completion {void done(Object response,Object error);}
 static class Network {List<Completion> calls=new ArrayList<>();void sendRequest(Object req,Completion c){calls.add(c);}}
 static class NotificationCenter {static final int dialogsNeedReload=1;Runnable observer;int events;void postNotificationName(int event){events++;if(observer!=null)observer.run();}}
 Flags loadingDialogs=new Flags();Deadlines dialogsLoadRetryAfter=new Deadlines();int dialogsLoadGeneration,processed;boolean resetingDialogs;
 Network network=new Network();NotificationCenter center=new NotificationCenter();Network getConnectionsManager(){return network;}NotificationCenter getNotificationCenter(){return center;}
 void processLoadedDialogs(Object...args){processed++;}
 void load(int folderId,boolean fromCache,Runnable onEmptyCallback){int count=32;
 PREFIX
 Object req=new Object();CALLBACK
 }
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){
  Probe p=new Probe();p.load(0,false,null);check(p.network.calls.size()==1&&p.loadingDialogs.get(0));
  p.center.observer=()->p.load(0,false,null);
  p.network.calls.get(0).done(null,new Object());check(p.loadingDialogs.get(0));AndroidUtilities.drain();
  check(!p.loadingDialogs.get(0)&&p.network.calls.size()==1);
  for(int i=0;i<10000;i++)p.load(0,false,null);check(p.network.calls.size()==1);
  p.load(1,false,null);check(p.network.calls.size()==2); // Failure is folder scoped.
  SystemClock.now+=3001;p.load(0,false,null);check(p.network.calls.size()==3&&p.loadingDialogs.get(0));
  var old=p.network.calls.get(2);p.dialogsLoadGeneration++;p.loadingDialogs.put(0,false);p.dialogsLoadRetryAfter.values.clear();
  p.load(0,false,null);check(p.network.calls.size()==4);old.done(null,new Object());AndroidUtilities.drain();check(p.loadingDialogs.get(0));
  p.center.observer=null;p.network.calls.get(3).done(null,new Object());AndroidUtilities.drain();
  long deadline=p.dialogsLoadRetryAfter.get(0);p.load(0,true,null);check(p.network.calls.size()==5&&p.dialogsLoadRetryAfter.get(0)==deadline); // Local cache is never delayed by network backoff.
  int[] empty={0};p.load(2,false,()->empty[0]++);p.network.calls.get(5).done(new TLRPC.messages_Dialogs(),null);AndroidUtilities.drain();
  check(p.processed==1&&empty[0]==1);
 }
}'''.replace('PREFIX',prefix).replace('CALLBACK',callback)})


def test_home_blur_reuses_clean_content_and_refreshes_scroll_animation_search_and_transitions(tmp_path):
    source=(JAVA/'org/telegram/ui/DialogsActivity.java').read_text()
    capture=method(source,'iBlur3Capture = new IBlur3Capture()')+';'
    utils=(JAVA/'org/telegram/ui/Components/blur3/utils/Blur3Utils.java').read_text()
    relative=method(utils,'public static void captureRelativeParent(IBlur3Capture capture, Canvas canvas, RectF position, View view, ViewGroup parent, int alpha)')
    hash_relative=method(utils,'public static void calculateHashRelativeParent(')
    suppress=(JAVA/'org/telegram/ui/Components/blur3/DownscaleScrollableNoiseSuppressor.java').read_text()
    update=method(suppress,'public boolean invalidateResultRenderNodes(IBlur3Capture capture, int width, int height)')
    probe(tmp_path, {'Probe.java': '''import java.util.*;
public class Probe {
 static class PointF {float x,y;}
 static class RectF {float left,top,right,bottom;RectF(){}RectF(float l,float t,float r,float b){left=l;top=t;right=r;bottom=b;}void set(RectF r){left=r.left;top=r.top;right=r.right;bottom=r.bottom;}void set(Rect r){left=r.left;top=r.top;right=r.right;bottom=r.bottom;}void offset(float x,float y){left+=x;right+=x;top+=y;bottom+=y;}}
 static class Rect {int left,top,right,bottom;Rect(int l,int t,int r,int b){left=l;top=t;right=r;bottom=b;}}
 static class Canvas {void save(){}void restore(){}void clipRect(RectF r){}void translate(float x,float y){}void saveLayerAlpha(RectF r,int a){}}
 static class View {static final int VISIBLE=0;int visibility;float x,y,alpha=1;boolean dirty;boolean isDirty(){return dirty;}boolean isLayoutRequested(){return false;}float getAlpha(){return alpha;}int getVisibility(){return visibility;}}
 static class ViewGroup extends View {}
 static class RecyclerView {static final int SCROLL_STATE_IDLE=0;}
 interface IBlur3Hash {void add(long v);void unsupported();default void addF(float f){add(Float.floatToIntBits(f));}default void add(View v){if(v.dirty)unsupported();addF(v.x);addF(v.y);addF(v.alpha);}}
 static class Blur3HashImpl implements IBlur3Hash {long hash;boolean unsupported;void start(){hash=0;unsupported=false;}public void add(long v){hash=hash*31+v;}public void unsupported(){unsupported=true;}boolean isUnsupported(){return unsupported;}long get(){return unsupported?-1:hash;}}
 interface IBlur3Capture {void capture(Canvas c,RectF r);default void captureCalculateHash(IBlur3Hash b,RectF r){b.unsupported();}}
 static class ListView extends View implements IBlur3Capture {int captures,hashes,scroll;int getScrollState(){return scroll;}long content=1;boolean unsupported;RectF last=new RectF();public void capture(Canvas c,RectF r){captures++;last.set(r);}public void captureCalculateHash(IBlur3Hash b,RectF r){hashes++;if(unsupported)b.unsupported();b.add(content);b.addF(r.top);}void dispatchDraw(Canvas c){captures++;}}
 static class Search extends ListView {public void captureCalculateHash(IBlur3Hash b,RectF r){b.unsupported();}}
 static class ViewPage extends View {ListView listView=new ListView();Object animationSupportListView;}
 static class ViewPositionWatcher {static boolean computeRectInParent(View v,ViewGroup p,RectF r){r.left=v.x;r.top=v.y;return true;}static boolean computeCoordinatesInParent(View v,ViewGroup p,PointF f){f.x=v.x;f.y=v.y;return true;}}
 static class Blur3Utils {static final RectF captureTmpRectF=new RectF(),captureTmpChildPos=new RectF();RELATIVE HASH_RELATIVE}
 static class RenderNode {boolean display;boolean hasDisplayList(){return display;}}
 static class SourcePart {Rect position;long lastHash;RenderNode renderNode=new RenderNode();SourcePart(Rect p){position=p;}}
 static class Suppressor {final RectF tmpRectF=new RectF();final Blur3HashImpl builder=new Blur3HashImpl();List<SourcePart> rectRenderNodes=List.of(new SourcePart(new Rect(0,0,400,100)),new SourcePart(new Rect(0,700,400,800)));int rectRenderNodesCount=2,recording,records;
 Canvas beginRecordingRect(int a){recording=a;records++;return new Canvas();}void endRecordingRect(){rectRenderNodes.get(recording).renderNode.display=true;}boolean invalidateResultRenderNodes(int w,int h){return false;}
 UPDATE
 }
 ViewPage[] viewPages={new ViewPage()};Search searchViewPager;float sliding;float getRightSlidingProgress(){return sliding;}
 IBlur3Capture iBlur3Capture;
 void setup(){ViewGroup contentView=new ViewGroup();final PointF tmpPoint=new PointF();CAPTURE}
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){
  Probe p=new Probe();p.setup();Suppressor s=new Suppressor();
  // Previous lambda uses IBlur3Capture's unsupported default: two recordings on every frame.
  IBlur3Capture previous=(c,r)->p.iBlur3Capture.capture(c,r);
  for(int i=0;i<10000;i++)s.invalidateResultRenderNodes(previous,400,800);
  check(s.records==20000);
  s=new Suppressor();for(int i=0;i<10000;i++)s.invalidateResultRenderNodes(p.iBlur3Capture,400,800);
  check(s.records==2); // Same production suppressor, real new capture hash.
  p.viewPages[0].listView.content++;s.invalidateResultRenderNodes(p.iBlur3Capture,400,800);check(s.records==4);
  p.viewPages[0].listView.y=12;s.invalidateResultRenderNodes(p.iBlur3Capture,400,800);check(s.records==6&&p.viewPages[0].listView.last.top==688);
  p.viewPages[0].listView.dirty=true;
  for(int i=0;i<5;i++)s.invalidateResultRenderNodes(p.iBlur3Capture,400,800);check(s.records==16);
  int hashes=p.viewPages[0].listView.hashes;p.viewPages[0].listView.dirty=false;p.viewPages[0].listView.scroll=2;
  for(int i=0;i<10000;i++)s.invalidateResultRenderNodes(p.iBlur3Capture,400,800);
  check(p.viewPages[0].listView.hashes==hashes);p.viewPages[0].listView.scroll=0;s.records=16;
  p.viewPages[0].listView.unsupported=true;
  for(int i=0;i<5;i++)s.invalidateResultRenderNodes(p.iBlur3Capture,400,800);check(s.records==26);
  p.viewPages[0].listView.unsupported=false;p.searchViewPager=new Search();p.searchViewPager.alpha=.5f;
  for(int i=0;i<5;i++)s.invalidateResultRenderNodes(p.iBlur3Capture,400,800);check(s.records==36&&p.searchViewPager.captures==10);
  p.searchViewPager=null;p.sliding=.5f;p.viewPages[0].animationSupportListView=new Object();
  for(int i=0;i<5;i++)s.invalidateResultRenderNodes(p.iBlur3Capture,400,800);check(s.records==46);
  p.sliding=0;p.viewPages[0].animationSupportListView=null;s.invalidateResultRenderNodes(p.iBlur3Capture,400,800);int records=s.records;
  s.invalidateResultRenderNodes(p.iBlur3Capture,400,800);check(s.records==records);
  s.rectRenderNodes.get(0).renderNode.display=false;s.invalidateResultRenderNodes(p.iBlur3Capture,400,800);check(s.records==records+1);
  p.viewPages[0].visibility=8;s.invalidateResultRenderNodes(p.iBlur3Capture,400,800);check(s.records==records+3);
 }
}'''.replace('HASH_RELATIVE',hash_relative).replace('RELATIVE',relative).replace('UPDATE',update).replace('CAPTURE',capture)})
