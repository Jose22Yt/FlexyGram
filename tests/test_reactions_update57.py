"""Lifecycle/ownership regressions from the reaction and memory review; no device FPS claims."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_hw_emoji_owner_does_not_release_new_popup_and_reentrant_task_is_preserved(tmp_path):
    probe(tmp_path,{
      'android/view/View.java':'package android.view;public class View{public int invalidations;public void invalidate(){invalidations++;}}',
      'org/telegram/messenger/SharedConfig.java':'package org.telegram.messenger;public class SharedConfig{public static final int PERFORMANCE_CLASS_HIGH=2;public static int getDevicePerformanceClass(){return 1;}}',
      'org/telegram/messenger/ImageLoader.java':'package org.telegram.messenger;public class ImageLoader{static final ImageLoader i=new ImageLoader();public static ImageLoader getInstance(){return i;}public final Queue q=new Queue();public Queue getCacheOutQueue(){return q;}public static class Queue{public boolean paused;public void pause(){paused=true;}public void resume(){paused=false;}}}',
      'Probe.java':'''import org.telegram.ui.Components.Reactions.HwEmojis;import org.telegram.messenger.ImageLoader;import android.view.View;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){
 Object a=new Object(),b=new Object();int[]calls={0};View old=new View();
 HwEmojis.beforePreparing(a);HwEmojis.prepare(a,()->calls[0]++,true);HwEmojis.enableHw(a);check(HwEmojis.grab(old));
 HwEmojis.beforePreparing(b);check(old.invalidations==1&&!HwEmojis.isHwEnabled());HwEmojis.prepare(b,()->calls[0]+=10,false);HwEmojis.enableHw(b);
 HwEmojis.disableHw(a);check(HwEmojis.isHwEnabled()&&ImageLoader.getInstance().q.paused&&HwEmojis.isOwner(b));
 HwEmojis.exec();check(calls[0]==10);HwEmojis.disableHw(b);check(!HwEmojis.isHwEnabled()&&!ImageLoader.getInstance().q.paused);
 HwEmojis.prepare(a,()->HwEmojis.prepare(a,()->calls[0]++,false),false);HwEmojis.exec();HwEmojis.exec();check(calls[0]==11);
 HwEmojis.prepare(()->calls[0]++,false);HwEmojis.enableHw();HwEmojis.exec();HwEmojis.disableHw();check(calls[0]==12&&!ImageLoader.getInstance().q.paused);
 }}'''
    },[JAVA/'org/telegram/ui/Components/Reactions/HwEmojis.java'])


def test_transition_layers_release_cascade_children_after_mode_changes_and_detach(tmp_path):
    s=(JAVA/'org/telegram/ui/Components/Reactions/CustomEmojiReactionsWindow.java').read_text()
    methods='\n'.join(method(s,x) for x in ['private void promoteTransitionLayer(','private void switchLayerType(','private void releaseTransitionResources()'])
    probe(tmp_path,{'Probe.java':'''import java.util.*;
public class Probe{
 static class View{static final int LAYER_TYPE_HARDWARE=2,IMPORTANT_FOR_ACCESSIBILITY_AUTO=0;int layer;int getLayerType(){return layer;}void setLayerType(int n,Object p){layer=n;}}
 static class Group extends View{Group contentView;ArrayList<View>children=new ArrayList<>();int getChildCount(){return children.size();}View getChildAt(int n){return children.get(n);}}
 static class Dialog{View emojiGridView=new View(),searchBox=new View(),emojiTabsShadow=new View();Group emojiTabs=new Group();int endCalls;void setEnterAnimationInProgress(boolean b){endCalls++;}}
 static class ValueAnimator{boolean cancelled,removed,updatesRemoved;void removeAllListeners(){removed=true;}void removeAllUpdateListeners(){updatesRemoved=true;}void cancel(){if(!removed||!updatesRemoved)throw new AssertionError("reentrant callbacks possible");cancelled=true;}}
 static class HwEmojis{static Object owner;static void disableHw(Object o){if(owner==o)owner=null;}}
 static class Locker{int unlocks;void unlock(){unlocks++;}}
 static class Reactions{boolean skip=true;float progress=.5f;void setImportantForAccessibility(int n){}void setCustomEmojiEnterProgress(float f){progress=f;}void setSkipDraw(boolean b){skip=b;}}
 Reactions reactionsContainerLayout=new Reactions();int restoredScales;void setScaleForChild(View v,float s){if(s!=1)throw new AssertionError();restoredScales++;}
 Dialog selectAnimatedEmojiDialog=new Dialog();boolean cascadeAnimation=true,transition,transitionResourcesReleased;ValueAnimator valueAnimator;
 ArrayList<ValueAnimator>animators=new ArrayList<>();HashSet<View>animatingEnterChild=new HashSet<>();Locker notificationsLocker=new Locker();
 final IdentityHashMap<View,Integer>transitionLayers=new IdentityHashMap<>();METHODS
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();p.selectAnimatedEmojiDialog.emojiTabs.contentView=new Group();
 for(int i=0;i<20;i++)p.selectAnimatedEmojiDialog.emojiTabs.contentView.children.add(new View());
 p.selectAnimatedEmojiDialog.searchBox.layer=1;p.switchLayerType(true);check(p.transitionLayers.size()==18);
 View changed=p.selectAnimatedEmojiDialog.emojiTabs.contentView.children.get(0);changed.layer=1;
 p.cascadeAnimation=false;p.switchLayerType(true);check(p.transitionLayers.size()==20);
 ValueAnimator parent=new ValueAnimator(),child=new ValueAnimator();p.valueAnimator=parent;p.animators.add(child);p.animatingEnterChild.add(changed);
 Object newer=new Object();HwEmojis.owner=newer;p.releaseTransitionResources();
 check(parent.cancelled&&child.cancelled&&p.transitionLayers.isEmpty()&&p.animators.isEmpty()&&p.animatingEnterChild.isEmpty()&&p.valueAnimator==null);
 check(p.selectAnimatedEmojiDialog.searchBox.layer==1&&changed.layer==1&&HwEmojis.owner==newer);
 check(p.restoredScales==1&&!p.reactionsContainerLayout.skip&&p.reactionsContainerLayout.progress==0);
 for(int i=1;i<20;i++)check(p.selectAnimatedEmojiDialog.emojiTabs.contentView.children.get(i).layer==0);
 p.releaseTransitionResources();check(p.notificationsLocker.unlocks==1);
 }}'''.replace('METHODS',methods)})
    assert 'releaseTransitionResources();' in method(s,'public void removeView()')


def test_finished_chat_releases_pool_only_after_detach_and_outside_layout(tmp_path):
    s=(JAVA/'org/telegram/ui/ChatActivity.java').read_text()
    cleanup=method(s,'private void releaseFinishedChatRecycler()')
    probe(tmp_path,{'Probe.java':'''public class Probe{
 static class AndroidUtilities{static Runnable queued;static void cancelRunOnUIThread(Runnable r){if(queued==r)queued=null;}static void runOnUIThread(Runnable r){queued=r;}}
 static class View{boolean attached;boolean isAttachedToWindow(){return attached;}}
 static class RecyclerView{static class RecycledViewPool{int clears;void clear(){clears++;}}}
 static class ListView{boolean layout;int stops,adapters,animators,cache=-1;RecyclerView.RecycledViewPool pool=new RecyclerView.RecycledViewPool();boolean isComputingLayout(){return layout;}void stopScroll(){stops++;}void setItemAnimator(Object x){animators++;}void setAdapter(Object x){adapters++;}void setItemViewCacheSize(int n){cache=n;}RecyclerView.RecycledViewPool getRecycledViewPool(){return pool;}}
 boolean isFinished,chatRecyclerReleased;View contentView=new View();ListView chatListView=new ListView();final Runnable releaseChatRecycler=this::releaseFinishedChatRecycler;CLEANUP
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();p.releaseFinishedChatRecycler();check(p.chatListView.stops==0);
 p.isFinished=true;p.contentView.attached=true;p.releaseFinishedChatRecycler();check(p.chatListView.stops==0);
 p.contentView.attached=false;p.chatListView.layout=true;p.releaseFinishedChatRecycler();check(p.chatListView.stops==0&&AndroidUtilities.queued!=null);
 p.chatListView.layout=false;AndroidUtilities.queued.run();p.releaseFinishedChatRecycler();check(p.chatListView.stops==1&&p.chatListView.adapters==1&&p.chatListView.animators==1&&p.chatListView.cache==0&&p.chatListView.pool.clears==1);
 }}'''.replace('CLEANUP',cleanup)})


def test_particle_motion_uses_elapsed_time_and_same_timestamp_does_not_advance(tmp_path):
    s=(JAVA/'org/telegram/ui/Components/Premium/StarParticlesView.java').read_text()
    delta=method(s,'private static float frameDeltaMillis(')
    probe(tmp_path,{'Probe.java':'''public class Probe{DELTA
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){check(frameDeltaMillis(100,120,120)==20);check(frameDeltaMillis(100,100,120)==0);check(frameDeltaMillis(100,2000,120)==50);
 check(Math.abs(frameDeltaMillis(0,100,60)-1000f/60)<.01);check(Math.abs(frameDeltaMillis(0,100,Float.NaN)-1000f/60)<.01);
 float fast=0,slow=0;for(int i=0;i<120;i++)fast+=frameDeltaMillis(100,108,120);for(int i=0;i<48;i++)slow+=frameDeltaMillis(100,120,120);check(fast==slow);
 }}'''.replace('DELTA',delta)})
    assert 'lastColor = Theme.getColor(colorKey, resourcesProvider);' in method(s,'private void generateBitmaps()')
    draw=method(s,'public void onDraw(Canvas canvas, float alpha)')
    assert 'SystemClock.uptimeMillis()' in draw and 'dt = diff;' in draw


def test_miui_android14_uses_broadcast_without_loading_hidden_class(tmp_path):
    s=(JAVA/'org/telegram/messenger/NotificationBadge.java').read_text()
    body=method(s[s.index('public static class XiaomiHomeBadger'):],'public void executeBadge(int badgeCount)')
    probe(tmp_path,{
      'android/app/MiuiNotification.java':'package android.app;public class MiuiNotification{public static int creations;public Object messageCount;public MiuiNotification(){creations++;}}',
      'Probe.java':'''import java.lang.reflect.Field;import java.util.*;
public class Probe{
 static class Build{static class VERSION{static int SDK_INT=34;}}
 static class Intent{Map<String,String>extras=new HashMap<>();Intent(String a){}void putExtra(String k,String v){extras.put(k,v);}}
 static class Component{String getPackageName(){return "com.flexygram.messenger";}String getClassName(){return "Launcher";}}
 static class Context{int sends;Intent sent;void sendBroadcast(Intent i){sends++;sent=i;}}
 static class ApplicationLoader{static Context applicationContext=new Context();}
 static class AndroidUtilities{static void runOnUIThread(Runnable r){r.run();}}
 static class FileLog{static void e(Throwable t){}}
 static final String INTENT_ACTION="badge",EXTRA_UPDATE_APP_COMPONENT_NAME="component",EXTRA_UPDATE_APP_MSG_TEXT="count";
 Component componentName=new Component();boolean resolve=true;boolean canResolveBroadcast(Intent i){return resolve;}
 BODY
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();for(int sdk:new int[]{34,35,36,37}){Build.VERSION.SDK_INT=sdk;p.executeBadge(5);check(android.app.MiuiNotification.creations==0);}check(ApplicationLoader.applicationContext.sends==4);
 p.executeBadge(0);check(ApplicationLoader.applicationContext.sent.extras.get("count").equals(""));
 p.resolve=false;p.executeBadge(9);check(ApplicationLoader.applicationContext.sends==5);Build.VERSION.SDK_INT=33;p.executeBadge(4);check(android.app.MiuiNotification.creations==1&&ApplicationLoader.applicationContext.sends==5);
 }}'''.replace('BODY',body)
    })


def test_async_blur_is_bounded_and_transfers_only_accepted_captures(tmp_path):
    probe(tmp_path,{
      'android/graphics/Bitmap.java':'package android.graphics;public class Bitmap{public int recycled;public boolean fail;public void recycle(){recycled++;}}',
      'android/os/Process.java':'package android.os;public class Process{public static final int THREAD_PRIORITY_BACKGROUND=10;public static void setThreadPriority(int p){}}',
      'android/os/Trace.java':'package android.os;public class Trace{public static void beginSection(String n){}public static void endSection(){}}',
      'org/telegram/messenger/AndroidUtilities.java':'package org.telegram.messenger;public class AndroidUtilities{public static final java.util.concurrent.ConcurrentLinkedQueue<Runnable> ui=new java.util.concurrent.ConcurrentLinkedQueue<>();public static void runOnUIThread(Runnable r){ui.add(r);}}',
      'org/telegram/messenger/Utilities.java':'''package org.telegram.messenger;public class Utilities{public static volatile boolean block=true;public static java.util.concurrent.CountDownLatch entered=new java.util.concurrent.CountDownLatch(1),release=new java.util.concurrent.CountDownLatch(1);public static void stackBlurBitmap(android.graphics.Bitmap b,int radius){if(Thread.currentThread().getName().equals("main"))throw new AssertionError("UI blur");if(block){entered.countDown();try{release.await();}catch(InterruptedException e){throw new RuntimeException(e);}}if(b.fail)throw new RuntimeException("failed blur");}}''',
      'Probe.java':'''import app.flexygram.performance.AsyncBitmapBlur;import android.graphics.Bitmap;import org.telegram.messenger.*;import java.util.concurrent.*;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}static void await(int n)throws Exception{long end=System.nanoTime()+TimeUnit.SECONDS.toNanos(3);while(AndroidUtilities.ui.size()<n&&System.nanoTime()<end)Thread.sleep(1);check(AndroidUtilities.ui.size()==n);while(!AndroidUtilities.ui.isEmpty())AndroidUtilities.ui.remove().run();}
 public static void main(String[]args)throws Exception{Bitmap a=new Bitmap(),b=new Bitmap(),rejected=new Bitmap();int[] delivered={0};
 check(AsyncBitmapBlur.submit(a,10,result->{check(result==a);delivered[0]++;}));check(Utilities.entered.await(3,TimeUnit.SECONDS));
 check(AsyncBitmapBlur.submit(b,10,result->{check(result==b);delivered[0]++;}));check(!AsyncBitmapBlur.submit(rejected,10,result->{throw new AssertionError();}));check(rejected.recycled==0&&delivered[0]==0);
 Utilities.block=false;Utilities.release.countDown();await(2);check(delivered[0]==2&&a.recycled==0&&b.recycled==0);
 Bitmap failed=new Bitmap();failed.fail=true;check(AsyncBitmapBlur.submit(failed,10,result->{check(result==null);delivered[0]++;}));await(1);check(failed.recycled==1&&delivered[0]==3);
 }}'''
    },[JAVA/'app/flexygram/performance/AsyncBitmapBlur.java'])


def test_popup_capture_coalesces_layouts_and_discards_resized_or_closed_results(tmp_path):
    s=(JAVA/'org/telegram/ui/SelectAnimatedEmojiDialog.java').read_text()
    nested=s[s.index('private class SelectStatusDurationDialog'):]
    prepare=method(nested,'private void prepareBlurBitmap()')
    assert 'blurBitmapWidth != parentView.getMeasuredWidth()' in nested
    assert 'blurBitmap.getWidth() != parentView.getMeasuredWidth()' not in nested
    probe(tmp_path,{
      'android/graphics/Bitmap.java':'''package android.graphics;public class Bitmap{public static int allocations;public int width,height,recycled;public enum Config{ARGB_8888}public static Bitmap createBitmap(int w,int h,Config c){if(w<=0||h<=0)throw new AssertionError();Bitmap b=new Bitmap();b.width=w;b.height=h;allocations++;return b;}public void recycle(){recycled++;}}''',
      'android/graphics/Canvas.java':'package android.graphics;public class Canvas{public Canvas(Bitmap b){}public void scale(float x,float y){}public void drawColor(int c){}public void save(){}public void translate(float x,float y){}public void restore(){}}',
      'android/graphics/Paint.java':'package android.graphics;public class Paint{public static final int ANTI_ALIAS_FLAG=1;public Paint(int f){}}',
      'app/flexygram/performance/AsyncBitmapBlur.java':'''package app.flexygram.performance;import android.graphics.Bitmap;public class AsyncBitmapBlur{public interface Callback{void done(Bitmap b);}public static boolean accept=true;public static java.util.ArrayDeque<Runnable> queue=new java.util.ArrayDeque<>();public static Bitmap last;public static boolean submit(Bitmap b,int radius,Callback callback){last=b;if(!accept)return false;queue.add(()->callback.done(b));return true;}public static void complete(){queue.remove().run();}}''',
      'Probe.java':'''import android.graphics.*;import app.flexygram.performance.AsyncBitmapBlur;
public class Probe{
 static class View{int width=1080,height=2400,draws,invalidates;int getMeasuredWidth(){return width;}int getMeasuredHeight(){return height;}void draw(Canvas c){draws++;}void getLocationOnScreen(int[]n){}void invalidate(){invalidates++;}}
 static class Window{View decor=new View();View getDecorView(){return decor;}}
 static class Activity{Window window=new Window();Window getWindow(){return window;}}
 static class Dialog{Window getWindow(){return new Window();}}
 static class Fragment{Dialog getVisibleDialog(){return null;}}
 static class Layout{Fragment getLastFragment(){return new Fragment();}}
 static class LaunchActivity extends Activity{Layout getActionBarLayout(){return new Layout();}}
 static class Theme{static final int key_windowBackgroundWhite=1;static int getColor(int key){return 1;}}
 static class SelectStatusDurationDialog{
  Activity parent=new Activity();Activity getParentActivity(){return parent;}
  int blurBitmapWidth,blurBitmapHeight,blurGeneration;boolean blurInFlight,blurClosed;Bitmap blurBitmap;Paint blurBitmapPaint;View contentView=new View(),parentDialogView;int[]tempLocation=new int[2];PREPARE
 }
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){SelectStatusDurationDialog d=new SelectStatusDurationDialog();d.prepareBlurBitmap();
 check(Bitmap.allocations==1&&AsyncBitmapBlur.queue.size()==1&&d.blurBitmap==null);Bitmap first=AsyncBitmapBlur.last;check(first.width==90&&first.height==200);
 for(int i=0;i<10000;i++)d.prepareBlurBitmap();check(Bitmap.allocations==1&&AsyncBitmapBlur.queue.size()==1);
 AsyncBitmapBlur.complete();check(d.blurBitmap==first&&d.blurBitmapWidth==1080&&d.blurBitmapHeight==2400);
 for(int i=0;i<10000;i++)d.prepareBlurBitmap();check(Bitmap.allocations==1&&AsyncBitmapBlur.queue.isEmpty());
 d.parent.window.decor.width=1200;d.prepareBlurBitmap();Bitmap outdated=AsyncBitmapBlur.last;d.parent.window.decor.height=2600;
 for(int i=0;i<10000;i++)d.prepareBlurBitmap();check(Bitmap.allocations==2);
 AsyncBitmapBlur.complete();check(outdated.recycled==1&&Bitmap.allocations==3&&AsyncBitmapBlur.queue.size()==1&&first.recycled==0);
 AsyncBitmapBlur.complete();check(d.blurBitmapWidth==1200&&d.blurBitmapHeight==2600&&!d.blurInFlight);
 d.parent.window.decor.width=1300;d.prepareBlurBitmap();Bitmap closed=AsyncBitmapBlur.last;d.blurClosed=true;d.blurGeneration++;d.blurInFlight=false;AsyncBitmapBlur.complete();check(closed.recycled==1&&!d.blurInFlight);
 d.blurClosed=false;d.parent.window.decor.width=0;int before=Bitmap.allocations;d.prepareBlurBitmap();check(Bitmap.allocations==before);
 d.parent.window.decor.width=1;d.parent.window.decor.height=1;AsyncBitmapBlur.accept=false;d.prepareBlurBitmap();check(AsyncBitmapBlur.last.width==1&&AsyncBitmapBlur.last.height==1&&AsyncBitmapBlur.last.recycled==1&&!d.blurInFlight);
 }
}'''.replace('PREPARE',prepare)
    })


def test_detached_chat_does_not_remove_another_fragments_reaction_overlay():
    s=(JAVA/'org/telegram/ui/ChatActivity.java').read_text()
    view=s[s.index('public class ChatActivityFragmentView extends SizeNotifierFrameLayout'):]
    detach=method(view,'protected void onDetachedFromWindow()')
    assert 'ReactionsEffectOverlay.dismissByFragment(ChatActivity.this)' in detach
    assert 'ReactionsEffectOverlay.removeCurrent(true)' not in detach
