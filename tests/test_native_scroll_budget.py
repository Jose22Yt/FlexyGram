"""Run shared scrolling work with counted probes; no device FPS claim."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_prefetch_budget_tracks_display_changes_and_stays_thread_owned(tmp_path):
    source=(JAVA/'androidx/recyclerview/widget/RecyclerView.java').read_text()
    update=method(source,'public static void updatePrefetchFrameInterval(')
    probe(tmp_path,{'Probe.java':'''public class Probe{
 static class GapWorker{static ThreadLocal<GapWorker>sGapWorker=new ThreadLocal<>();long mFrameIntervalNs=16666666;}
 UPDATE
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a)throws Exception{
  updatePrefetchFrameInterval(120);check(GapWorker.sGapWorker.get()==null);
  GapWorker worker=new GapWorker();GapWorker.sGapWorker.set(worker);
  for(float hz:new float[]{60,90,120,144,30,60}){updatePrefetchFrameInterval(hz);check(worker.mFrameIntervalNs==(long)(1000000000d/hz));}
  long before=worker.mFrameIntervalNs;
  for(float hz:new float[]{0,-1,29,1001,Float.NaN,Float.POSITIVE_INFINITY})updatePrefetchFrameInterval(hz);
  check(worker.mFrameIntervalNs==before);
  long[] otherBudget={0};Thread t=new Thread(()->{GapWorker other=new GapWorker();GapWorker.sGapWorker.set(other);updatePrefetchFrameInterval(120);otherBudget[0]=other.mFrameIntervalNs;});t.start();t.join();
  check(worker.mFrameIntervalNs==before&&otherBudget[0]==8333333);
 }
}'''.replace('UPDATE',update)})
    monitor=(JAVA/'app/flexygram/performance/RefreshRateMonitor.java').read_text()
    assert 'RecyclerView.updatePrefetchFrameInterval(rate);' in method(monitor,'private void update()')


def test_segmented_rows_share_two_neighbor_queries_and_keep_all_corner_cases(tmp_path):
    source=(JAVA/'org/telegram/ui/Components/RecyclerListView.java').read_text()
    actual='\n'.join(method(source,signature) for signature in [
        'private int segmentedSectionNeighbors(',
        'private float getSegmentedSectionTopRadius(',
        'private float getSegmentedSectionBottomRadius(',
    ])
    probe(tmp_path,{'Probe.java':'''public class Probe{
 static final int NO_POSITION=-1;static class RectF{}
 static class View{int position;boolean round;}
 static class Adapter{int count,types,counts;boolean[]section;
  int getItemCount(){counts++;return count;}int getItemViewType(int p){types++;if(p<0||p>=count)throw new AssertionError();return section[p]?1:0;}}
 static class Predicate{boolean run(int type){return type==1;}}
 Adapter adapter=new Adapter();Predicate isViewTypeSection=new Predicate();int positionReads;
 float sectionRadius=20;Adapter getAdapter(){return adapter;}int getChildAdapterPosition(View v){positionReads++;return v.position;}
 boolean isRoundSectionView(View v){return v.round;}float getSingleSectionRadius(RectF r){return 24;}float segmentInnerRadius(){return 6;}
 ACTUAL
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){Probe p=new Probe();View v=new View();RectF r=new RectF();
  for(int count=1;count<8;count++)for(int mask=0;mask<(1<<count);mask++)for(int pos=0;pos<count;pos++)for(boolean round:new boolean[]{false,true}){
   p.adapter.count=count;p.adapter.section=new boolean[count];for(int i=0;i<count;i++)p.adapter.section[i]=(mask&(1<<i))!=0;v.position=pos;v.round=round;
   int reads=p.positionReads,types=p.adapter.types,counts=p.adapter.counts;
   int neighbors=p.segmentedSectionNeighbors(v);boolean above=pos>0&&p.adapter.section[pos-1],below=pos+1<count&&p.adapter.section[pos+1];
   float top=!above&&!below&&round?24:above?6:20,bottom=!above&&!below&&round?24:below?6:20;
   check(p.getSegmentedSectionTopRadius(v,r,neighbors)==top&&p.getSegmentedSectionBottomRadius(v,r,neighbors)==bottom);
   check(p.positionReads-reads==1&&p.adapter.counts-counts==1&&p.adapter.types-types<=2);
  }
  for(int pos:new int[]{-1,-2,999}){v.position=pos;check(p.segmentedSectionNeighbors(v)==0);}
  p.adapter=null;check(p.segmentedSectionNeighbors(v)==0);check(p.segmentedSectionNeighbors(null)==0);
 }
}'''.replace('ACTUAL',actual)})
    for signature in ['private void drawSegmentedSectionBackground(', 'private void clipChildWithSegmentedSection(', 'public Drawable getClipBackground(View child, boolean forceRound)']:
        body=method(source,signature)
        assert body.count('segmentedSectionNeighbors(child)')==1


def test_shared_media_active_scroll_updates_section_progress_once(tmp_path):
    source=(JAVA/'org/telegram/ui/Components/SharedMediaLayout.java').read_text()
    listener=source[source.index('mediaPages[a].listView.setOnScrollListener'):]
    scrolled=method(listener,'public void onScrolled(')
    probe(tmp_path,{'Probe.java':'''import java.util.*;
public class Probe{
 static final int TAB_PHOTOVIDEO=0,TAB_GIF=5;
 static class RecyclerView{}static class RecyclerListView extends RecyclerView{boolean scrollingByUser;int checks,forced;void checkSection(boolean force){if(force)forced++;if(force||scrollingByUser)checks++;}}
 static class MediaPage{int selectedType;RecyclerListView listView=new RecyclerListView();Object fastScrollHintView;void invalidate(){}}
 static class Data{List<Object>messages=new ArrayList<>(List.of(new Object()));}
 MediaPage mediaPage=new MediaPage();MediaPage[]mediaPages={mediaPage};Data[]sharedMediaData={new Data()};Object layoutManager=new Object();int loads,blurs;
 void checkLoadMoreScroll(Object page,Object list,Object manager){loads++;}void showFloatingDateView(){}void showFastScrollHint(Object page,Object data,boolean value){}boolean isAnyStoryPageType(int t){return false;}void invalidateBlur(){blurs++;}
 SCROLLED
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]a){Probe p=new Probe();RecyclerListView list=p.mediaPage.listView;
  list.scrollingByUser=true;for(int i=0;i<10000;i++){p.onScrolled(list,0,3);list.checkSection(false);}
  check(list.forced==0&&list.checks==10000&&p.loads==10000&&p.blurs==10000);
  list.scrollingByUser=false;p.onScrolled(list,0,3);list.checkSection(false);check(list.forced==1&&list.checks==10001);
 }
}'''.replace('SCROLLED',scrolled)})


def test_scroll_frame_hint_uses_supported_apis_and_releases_its_own_vote(tmp_path):
    probe(tmp_path,{
        'android/os/Build.java':'package android.os;public class Build{public static class VERSION{public static int SDK_INT;}}',
        'android/view/View.java':'''package android.view;public class View{
 public static final float REQUESTED_FRAME_RATE_CATEGORY_HIGH=-4;public float rate=60,velocity;public int gets,sets,velocities;
 public float getRequestedFrameRate(){gets++;return rate;}public void setRequestedFrameRate(float r){sets++;rate=r;}
 public void setFrameContentVelocity(float v){velocities++;if(android.os.Build.VERSION.SDK_INT<35)throw new NoSuchMethodError();velocity=v;}}''',
        'Probe.java':'''import android.os.Build;import android.view.View;import app.flexygram.performance.ScrollFrameRateHint;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]a){
 for(int sdk:new int[]{23,29,30,34}){Build.VERSION.SDK_INT=sdk;View v=new View();ScrollFrameRateHint hint=new ScrollFrameRateHint(v);hint.setScrolling(true);hint.setScrolling(false);check(v.gets==0&&v.sets==0&&v.velocities==0);}
 Build.VERSION.SDK_INT=35;View v=new View();ScrollFrameRateHint hint=new ScrollFrameRateHint(v);
 for(int i=0;i<10000;i++)hint.setScrolling(true);check(v.sets==1&&v.velocities==1&&v.rate==View.REQUESTED_FRAME_RATE_CATEGORY_HIGH);
 hint.setScrolling(false);check(v.rate==60&&v.velocity==0&&v.sets==2);hint.setScrolling(false);check(v.sets==2);
 hint.setScrolling(true);v.rate=90;hint.setScrolling(false);check(v.rate==90&&v.velocity==0);
}}'''
    },[JAVA/'app/flexygram/performance/ScrollFrameRateHint.java'])


def test_display_monitor_updates_all_shared_prefetch_work_without_frame_polling(tmp_path):
    probe(tmp_path,{
        'android/content/Context.java':'package android.content;public class Context{public static final String DISPLAY_SERVICE="display";}',
        'android/app/Activity.java':'''package android.app;public class Activity extends android.content.Context{
 public android.hardware.display.DisplayManager manager=new android.hardware.display.DisplayManager();public android.view.WindowManager window=new android.view.WindowManager();
 public Object getSystemService(String name){return manager;}public android.view.WindowManager getWindowManager(){return window;}}''',
        'android/view/WindowManager.java':'package android.view;public class WindowManager{public Display display=new Display();public Display getDefaultDisplay(){return display;}}',
        'android/view/Display.java':'package android.view;public class Display{public float rate=60;public float getRefreshRate(){return rate;}public int getDisplayId(){return 1;}}',
        'android/hardware/display/DisplayManager.java':'''package android.hardware.display;public class DisplayManager{
 public int registrations,removals;public interface DisplayListener{void onDisplayChanged(int id);void onDisplayAdded(int id);void onDisplayRemoved(int id);}
 public void registerDisplayListener(DisplayListener l,android.os.Handler h){registrations++;}public void unregisterDisplayListener(DisplayListener l){removals++;}}''',
        'android/os/Handler.java':'package android.os;public class Handler{public Handler(Looper l){}}',
        'android/os/Looper.java':'package android.os;public class Looper{public static Looper getMainLooper(){return new Looper();}}',
        'org/telegram/messenger/AndroidUtilities.java':'package org.telegram.messenger;public class AndroidUtilities{public static float screenRefreshRate,screenRefreshTime;}',
        'androidx/recyclerview/widget/RecyclerView.java':'package androidx.recyclerview.widget;public class RecyclerView{public static int updates;public static float hz;public static void updatePrefetchFrameInterval(float rate){updates++;hz=rate;}}',
        'Probe.java':'''import app.flexygram.performance.RefreshRateMonitor;import androidx.recyclerview.widget.RecyclerView;import android.app.Activity;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]a){
 Activity activity=new Activity();RefreshRateMonitor monitor=new RefreshRateMonitor(activity);monitor.start();monitor.start();check(activity.manager.registrations==1&&RecyclerView.updates==1&&RecyclerView.hz==60);
 activity.window.display.rate=120;monitor.onDisplayChanged(2);check(RecyclerView.updates==1);monitor.onDisplayChanged(1);check(RecyclerView.updates==2&&RecyclerView.hz==120);
 activity.window.display.rate=Float.NaN;monitor.onDisplayChanged(1);check(RecyclerView.updates==2);
 monitor.stop();activity.window.display.rate=90;monitor.onDisplayChanged(1);check(RecyclerView.updates==2&&activity.manager.removals==1);
 monitor.start();check(RecyclerView.hz==90&&RecyclerView.updates==3);
}}'''
    },[JAVA/'app/flexygram/performance/RefreshRateMonitor.java'])
