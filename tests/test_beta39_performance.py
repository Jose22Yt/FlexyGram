"""Production scheduling probes. Work counts/cancellation contracts, not device FPS."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_navigation_gate_rejects_late_account_and_owner_results(tmp_path):
    probe(tmp_path, {
        'org/telegram/messenger/UserConfig.java': 'package org.telegram.messenger;public class UserConfig{public static int selectedAccount;}',
        'org/telegram/ui/ActionBar/BaseFragment.java': '''package org.telegram.ui.ActionBar;public class BaseFragment{
            public boolean isFinished;public int account;public int getCurrentAccount(){return account;}public Object getArguments(){return this;}}''',
        'org/telegram/ui/ChatActivity.java': 'package org.telegram.ui;public class ChatActivity extends org.telegram.ui.ActionBar.BaseFragment{}',
        'app/flexygram/performance/ChatPeerPreloader.java': '''package app.flexygram.performance;public class ChatPeerPreloader{
            public interface Completion{void done(boolean found);}public static boolean cold=true;public static java.util.ArrayList<Completion> callbacks=new java.util.ArrayList<>();
            public static boolean prepare(int account,Object args,Completion completion){if(!cold)return false;callbacks.add(completion);return true;}}''',
        'Probe.java': '''import app.flexygram.performance.*;import org.telegram.ui.*;import org.telegram.ui.ActionBar.*;import org.telegram.messenger.UserConfig;
        public class Probe{
            static int opened,failed;static boolean valid=true;static void check(boolean b){if(!b)throw new AssertionError();}
            static boolean request(ChatNavigationGate g,BaseFragment f){return g.defer(f,()->valid,()->opened++,()->failed++);}
            static void complete(int n,boolean found){ChatPeerPreloader.callbacks.get(n).done(found);}
            public static void main(String[] args){
                ChatNavigationGate gate=new ChatNavigationGate();ChatActivity a=new ChatActivity(),b=new ChatActivity();
                check(request(gate,a));check(request(gate,b));complete(0,true);check(opened==0);complete(1,true);check(opened==1);
                request(gate,a);gate.cancel();complete(2,true);check(opened==1);
                request(gate,a);UserConfig.selectedAccount=1;complete(3,true);check(opened==1);UserConfig.selectedAccount=0;
                request(gate,a);a.account=1;complete(4,true);check(opened==1);a.account=0;
                request(gate,a);a.isFinished=true;complete(5,true);check(opened==1);a.isFinished=false;
                request(gate,a);valid=false;complete(6,true);check(opened==1);valid=true;
                request(gate,a);complete(7,false);check(opened==1&&failed==1);
                request(gate,a);check(!request(gate,new BaseFragment()));complete(8,true);check(opened==1);
                ChatPeerPreloader.cold=false;check(!request(gate,a));check(opened==1&&failed==1);
            }
        }''',
    }, [JAVA/'app/flexygram/performance/ChatNavigationGate.java'])


def test_queue_search_indexes_and_diffs_off_ui_and_publishes_only_latest(tmp_path):
    probe(tmp_path, {
        'org/telegram/messenger/MessageObject.java': '''package org.telegram.messenger;public class MessageObject{
            public static int reads;public int currentAccount,id;public long dialog;public String title,artist,file;
            public MessageObject(int id,long dialog,String title){this.id=id;this.dialog=dialog;this.title=title;artist="Éminem";file="music.mp3";}
            private void reading(){if(!Utilities.worker)throw new AssertionError("metadata on UI");reads++;}
            public String getMusicTitle(){reading();return title;}public String getMusicAuthor(){reading();return artist;}public String getFileName(){reading();return file;}
            public int getId(){return id;}public long getDialogId(){return dialog;}public boolean isMusic(){return true;}}''',
        'org/telegram/messenger/Utilities.java': '''package org.telegram.messenger;public class Utilities{
            public static boolean worker;public static final Queue searchQueue=new Queue();public static class Queue{
                public final java.util.ArrayList<Runnable> tasks=new java.util.ArrayList<>();
                public void postRunnable(Runnable r){tasks.add(r);}public void cancelRunnable(Runnable r){tasks.remove(r);}
                public void run(){Runnable r=tasks.remove(0);worker=true;try{r.run();}finally{worker=false;}}}}''',
        'org/telegram/messenger/AndroidUtilities.java': '''package org.telegram.messenger;public class AndroidUtilities{
            public static final java.util.ArrayList<Runnable> ui=new java.util.ArrayList<>();
            public static void runOnUIThread(Runnable r){ui.add(r);}public static void drain(){while(!ui.isEmpty())ui.remove(0).run();}}''',
        'androidx/recyclerview/widget/DiffUtil.java': '''package androidx.recyclerview.widget;public class DiffUtil{
            public abstract static class Callback{public abstract int getOldListSize();public abstract int getNewListSize();public abstract boolean areItemsTheSame(int a,int b);public abstract boolean areContentsTheSame(int a,int b);}
            public static class DiffResult{public Callback callback;DiffResult(Callback c){callback=c;}}
            public static DiffResult calculateDiff(Callback c){if(!org.telegram.messenger.Utilities.worker)throw new AssertionError("diff on UI");return new DiffResult(c);}}''',
        'app/exteraless/player/SearchProbe.java': '''package app.exteraless.player;import java.util.*;import org.telegram.messenger.*;
        public class SearchProbe{
            static int calls;static MusicQueueSearch.Result last;static void check(boolean b){if(!b)throw new AssertionError();}
            static void result(MusicQueueSearch.Result r){check(!Utilities.worker);calls++;last=r;}
            public static void run(){
                MusicQueueSearch engine=new MusicQueueSearch();ArrayList<MessageObject> source=new ArrayList<>();
                MessageObject a=new MessageObject(1,10,"Canción uno"),b=new MessageObject(1,20,"Other");source.add(a);source.add(b);
                engine.submit(source,1,List.of(),"cancion",SearchProbe::result);Utilities.searchQueue.run();check(calls==0);AndroidUtilities.drain();check(calls==1&&last.items.size()==1&&last.items.get(0)==a);
                int reads=MessageObject.reads;
                engine.submit(source,1,List.of(a),"EMINEM",SearchProbe::result);Utilities.searchQueue.run();AndroidUtilities.drain();check(calls==2&&last.items.size()==2&&MessageObject.reads==reads);
                check(!last.changes.callback.areItemsTheSame(0,1));check(last.changes.callback.areItemsTheSame(0,0));
                engine.submit(source,1,List.of(a),"other",SearchProbe::result);Utilities.searchQueue.run();
                engine.submit(source,1,List.of(a),"missing",SearchProbe::result);AndroidUtilities.drain();check(calls==2);
                Utilities.searchQueue.run();AndroidUtilities.drain();check(calls==3&&last.items.isEmpty());
                engine.submit(source,1,List.of(),"",SearchProbe::result);engine.cancel();check(Utilities.searchQueue.tasks.isEmpty());
                engine.submit(source,2,List.of(),"",SearchProbe::result);source.clear();Utilities.searchQueue.run();engine.cancel();AndroidUtilities.drain();check(calls==3);
                source.add(b);engine.submit(source,3,List.of(),"",SearchProbe::result);Utilities.searchQueue.run();AndroidUtilities.drain();check(calls==4&&last.items.size()==1&&last.items.get(0)==b);
                for(int i=0;i<5000;i++)source.add(new MessageObject(i+2,30,"t"+i));
                engine.submit(source,4,List.of(),"t4999",SearchProbe::result);Utilities.searchQueue.run();AndroidUtilities.drain();check(last.items.size()==1&&last.items.get(0).id==5001);
            }
        }''',
        'Probe.java': 'public class Probe{public static void main(String[] args){app.exteraless.player.SearchProbe.run();}}',
    }, [JAVA/'app/exteraless/player/MusicQueueSearch.java', JAVA/'app/exteraless/player/MusicQueueOrder.java'])


def test_profiler_classifies_flexygram_modules(tmp_path):
    source = (JAVA/'app/exteraless/debug/JankProfiler.java').read_text()
    prefixes = source[source.index('    private static final String[] APP_PACKAGES'):source.index('    private static JankProfiler instance;')]
    classifier = method(source, 'private static boolean isAppFrame(')
    probe(tmp_path, {'Probe.java': '''public class Probe {
        PREFIXES
        METHOD
        public static void main(String[] args){
            for(String name:new String[]{"app.flexygram.bubbles.BubbleFusion","app.flexygram.performance.ChatPeerPreloader","org.telegram.ui.ChatActivity","app.exteraless.player.MusicBlurCapture"})
                if(!isAppFrame(new StackTraceElement(name,"draw","",1)))throw new AssertionError(name);
            if(isAppFrame(new StackTraceElement("android.view.View","draw","",1)))throw new AssertionError();
        }
    }'''.replace('PREFIXES',prefixes).replace('METHOD',classifier)})


def test_shared_blur_captures_once_cancels_late_work_and_has_no_idle_loop(tmp_path):
    probe(tmp_path, {
        'android/graphics/Bitmap.java': '''package android.graphics;public class Bitmap{public boolean recycled;public void recycle(){recycled=true;}}''',
        'android/graphics/Rect.java': '''package android.graphics;public class Rect{
            public int left,top,right,bottom;public Rect(){}public Rect(Rect r){set(r.left,r.top,r.right,r.bottom);}
            public void set(int l,int t,int r,int b){left=l;top=t;right=r;bottom=b;}public void setEmpty(){set(0,0,0,0);}
            public boolean isEmpty(){return right<=left||bottom<=top;}public int width(){return right-left;}public int height(){return bottom-top;}
            public void union(Rect r){if(r.isEmpty())return;if(isEmpty()){set(r.left,r.top,r.right,r.bottom);return;}
                left=Math.min(left,r.left);top=Math.min(top,r.top);right=Math.max(right,r.right);bottom=Math.max(bottom,r.bottom);}}''',
        'android/os/SystemClock.java': 'package android.os;public class SystemClock{public static long time;public static long uptimeMillis(){return time;}}',
        'android/view/ViewTreeObserver.java': '''package android.view;public class ViewTreeObserver{
            public interface OnPreDrawListener{boolean onPreDraw();}public interface OnScrollChangedListener{void onScrollChanged();}public interface OnGlobalLayoutListener{void onGlobalLayout();}
            public int adds,removes;public boolean isAlive(){return true;}
            public void addOnPreDrawListener(OnPreDrawListener l){adds++;}public void addOnScrollChangedListener(OnScrollChangedListener l){adds++;}public void addOnGlobalLayoutListener(OnGlobalLayoutListener l){adds++;}
            public void removeOnPreDrawListener(OnPreDrawListener l){removes++;}public void removeOnScrollChangedListener(OnScrollChangedListener l){removes++;}public void removeOnGlobalLayoutListener(OnGlobalLayoutListener l){removes++;}}''',
        'android/view/View.java': '''package android.view;public class View{
            public final ViewTreeObserver observer=new ViewTreeObserver();public int invalidations;public long delay;
            public final java.util.ArrayList<Runnable> posted=new java.util.ArrayList<>();
            public ViewTreeObserver getViewTreeObserver(){return observer;}public void invalidate(){invalidations++;}
            public void removeCallbacks(Runnable r){posted.remove(r);}public void postDelayed(Runnable r,long delay){posted.add(r);this.delay=delay;}
            public void fire(){Runnable r=posted.remove(0);r.run();}}''',
        'org/telegram/messenger/LiteMode.java': '''package org.telegram.messenger;public class LiteMode{public static int FLAG_CHAT_BLUR=1;public static boolean enabled=true;public static boolean isEnabled(int flag){return enabled;}}''',
        'org/telegram/messenger/Utilities.java': 'package org.telegram.messenger;public class Utilities{public interface Callback<T>{void run(T value);}}',
        'org/telegram/messenger/AndroidUtilities.java': '''package org.telegram.messenger;import android.graphics.*;public class AndroidUtilities{
            public static Runnable ui;public static int calls;public static float scale;public static Rect region;
            public static java.util.ArrayList<Utilities.Callback<Bitmap>> completions=new java.util.ArrayList<>();
            public static void runOnUIThread(Runnable r){ui=r;}
            public static void makeGlobalBlurBitmap(Utilities.Callback<Bitmap> c,float s,int amount,android.view.View v,java.util.List<android.view.View> e,boolean async,Rect bounds){
                if(!app.exteraless.player.MusicBlurSurface.isCapturing()||!async)throw new AssertionError();calls++;scale=s;region=new Rect(bounds);completions.add(c);
            }
            public static void finish(int n,Bitmap b){completions.get(n).run(b);ui.run();ui=null;}}''',
        'app/exteraless/player/MusicBlurSurface.java': '''package app.exteraless.player;import android.graphics.*;public class MusicBlurSurface{
            public static boolean capturing,frozen;public static boolean isCapturing(){return capturing;}static boolean isFrozen(){return frozen;}
            boolean captureVisible=true,changed=true;final Rect screenBounds=new Rect();int accepts,clears;Bitmap bitmap;
            MusicBlurSurface(int y){screenBounds.set(-30,y,100,y+30);}boolean updateGeometry(){boolean value=changed;changed=false;return value;}
            void acceptCapture(Bitmap b,Rect region){bitmap=b;accepts++;}void clearCapture(){bitmap=null;clears++;}}''',
        'app/exteraless/player/BlurProbe.java': '''package app.exteraless.player;import android.graphics.*;import android.view.*;import android.os.SystemClock;import org.telegram.messenger.*;
        public class BlurProbe{
            static void check(boolean b){if(!b)throw new AssertionError();}
            public static void run(){
                View root=new View();MusicBlurCapture group=new MusicBlurCapture(root);
                MusicBlurSurface a=new MusicBlurSurface(20),b=new MusicBlurSurface(130),c=new MusicBlurSurface(250);
                group.add(a);group.add(b);group.add(c);check(root.observer.adds==3);
                group.onPreDraw();check(AndroidUtilities.calls==1&&!MusicBlurSurface.isCapturing());
                check(AndroidUtilities.region.left==-30&&AndroidUtilities.region.top==20&&AndroidUtilities.region.height()==260);
                for(int i=0;i<100;i++)group.onPreDraw();check(AndroidUtilities.calls==1);
                Bitmap first=new Bitmap();AndroidUtilities.finish(0,first);check(a.bitmap==first&&b.bitmap==first&&c.bitmap==first);
                for(int i=0;i<10000;i++)group.onPreDraw();check(AndroidUtilities.calls==1&&root.posted.isEmpty());
                SystemClock.time=40;group.onScrollChanged();group.onPreDraw();check(root.posted.size()==1&&root.delay==120);
                for(int i=0;i<1000;i++)group.onPreDraw();check(root.posted.size()==1);
                SystemClock.time=160;root.fire();group.onPreDraw();check(AndroidUtilities.calls==2);
                group.onGlobalLayout();Bitmap obsolete=new Bitmap();AndroidUtilities.finish(1,obsolete);check(obsolete.recycled&&a.bitmap==first);
                SystemClock.time=320;group.onPreDraw();check(AndroidUtilities.calls==3);Bitmap second=new Bitmap();AndroidUtilities.finish(2,second);check(a.bitmap==second&&!first.recycled);
                LiteMode.enabled=false;group.onPreDraw();check(a.bitmap==null&&b.bitmap==null&&c.bitmap==null);LiteMode.enabled=true;
                MusicBlurSurface.frozen=true;SystemClock.time=480;group.onPreDraw();check(AndroidUtilities.calls==3);MusicBlurSurface.frozen=false;
                group.onPreDraw();check(AndroidUtilities.calls==4);group.remove(a);group.remove(b);group.remove(c);
                check(root.observer.removes==3&&root.posted.isEmpty());Bitmap detached=new Bitmap();AndroidUtilities.finish(3,detached);check(detached.recycled);
                group.add(a);a.screenBounds.set(-100,0,3900,2000);a.changed=true;group.onPreDraw();
                check(AndroidUtilities.calls==5&&AndroidUtilities.scale>=4000f/384);check(AndroidUtilities.region.width()/AndroidUtilities.scale<=384.01f);
                Bitmap large=new Bitmap();AndroidUtilities.finish(4,large);check(a.bitmap==large);
                group.remove(a);check(!large.recycled&&root.posted.isEmpty());
            }
        }''',
        'Probe.java': 'public class Probe{public static void main(String[] args){app.exteraless.player.BlurProbe.run();}}',
    }, [JAVA/'app/exteraless/player/MusicBlurCapture.java'])


def test_shared_blur_crop_uses_screen_origin_and_preserves_each_surface(tmp_path):
    accept = method((JAVA/'app/exteraless/player/MusicBlurSurface.java').read_text(), 'void acceptCapture(')
    probe(tmp_path, {
        'Probe.java': '''public class Probe {
            static class Rect{int left,top,right,bottom;Rect(int l,int t,int r,int b){set(l,t,r,b);}void set(int l,int t,int r,int b){left=l;top=t;right=r;bottom=b;}int width(){return right-left;}int height(){return bottom-top;}}
            static class Bitmap{int getWidth(){return 50;}int getHeight(){return 100;}}
            static class RectF{float left,top,right,bottom;void set(float l,float t,float r,float b){left=l;top=t;right=r;bottom=b;}}
            Bitmap bitmap;Rect screenBounds=new Rect(20,140,100,220);RectF sourceRect=new RectF();int invalidations;
            void invalidateSelf(){invalidations++;}
            ACCEPT
            public static void main(String[] args){Probe p=new Probe();Bitmap shared=new Bitmap();p.acceptCapture(shared,new Rect(-20,100,380,900));
                if(p.bitmap!=shared||p.sourceRect.left!=5||p.sourceRect.top!=5||p.sourceRect.right!=15||p.sourceRect.bottom!=15||p.invalidations!=1)throw new AssertionError();
                p.screenBounds.set(21,143,101,223);p.acceptCapture(shared,new Rect(-20,100,380,900));
                if(p.sourceRect.left!=5.125f||p.sourceRect.top!=5.375f)throw new AssertionError("fractional crop lost");
                p.acceptCapture(null,new Rect(0,0,1,1));if(p.bitmap!=null||p.invalidations!=3)throw new AssertionError();
            }
        }'''.replace('ACCEPT',accept),
    })


def test_deferred_stack_insertion_preserves_native_position_and_lifecycle(tmp_path):
    # Compile the entire production insertion method, including its native mutable
    # position branch. This catches lambda capture/API mistakes missed by syntax parsing.
    source = (JAVA/'org/telegram/ui/ActionBar/ActionBarLayout.java').read_text()
    insertion = method(source, 'public boolean addFragmentToStack(BaseFragment fragment, int position)')
    probe(tmp_path, {'Probe.java': '''import java.util.*;import java.util.function.*;
    public class Probe {
        static final int VISIBLE=0;
        static class View {Object getParent(){return null;}void setVisibility(int v){}}
        static class ViewGroup extends View {void removeView(View v){}}
        static class ActionBar extends View {boolean shouldAddToContainer(){return false;}}
        static class BaseFragment {int created,resumed,paused;ActionBar actionBar;View fragmentView;
            boolean onFragmentCreate(){created++;return true;}void setParentLayout(Object layout){}void onPause(){paused++;}
            void onRemoveFromParent(){}void detachSheets(){}void onResume(){resumed++;}
            void onTransitionAnimationEnd(boolean a,boolean b){}void onBecomeFullyVisible(){}
        }
        static class INavigationLayout {static final int FORCE_NOT_ATTACH_VIEW=-2,FORCE_ATTACH_VIEW_AS_FIRST=-3;}
        interface Delegate {boolean needAddFragmentToStack(BaseFragment f,Probe p);}
        static class Gate {boolean cold=true;Runnable resume;BooleanSupplier valid;
            boolean defer(BaseFragment f,BooleanSupplier valid,Runnable resume,Runnable failed){if(!cold)return false;this.valid=valid;this.resume=resume;return true;}
            void finish(){cold=false;if(valid.getAsBoolean())resume.run();}
        }
        Gate chatNavigation=new Gate();Delegate delegate;ArrayList<BaseFragment> fragmentsStack=new ArrayList<>();
        boolean useAlphaAnimations;View backgroundView;int attached,attachedFirst,failures;
        BaseFragment getLastFragment(){return fragmentsStack.isEmpty()?null:fragmentsStack.get(fragmentsStack.size()-1);}
        boolean chatNavigationOwnerValid(BaseFragment anchor){return getLastFragment()==anchor;}
        void chatNavigationFailed(){failures++;}void attachView(BaseFragment f){attached++;}void attachViewTo(BaseFragment f,int position){attachedFirst++;}
        void onFragmentStackChanged(String s){}void setVisibility(int v){}
        INSERTION
        static void check(boolean b){if(!b)throw new AssertionError();}
        public static void main(String[] args){
            Probe p=new Probe();BaseFragment original=new BaseFragment(),next=new BaseFragment();p.fragmentsStack.add(original);
            check(p.addFragmentToStack(next,-1));check(next.created==0&&p.fragmentsStack.size()==1);
            p.chatNavigation.finish();check(next.created==1&&next.resumed==1&&p.attached==1&&p.getLastFragment()==next);
            BaseFragment first=new BaseFragment();p.chatNavigation.cold=true;p.addFragmentToStack(first,INavigationLayout.FORCE_ATTACH_VIEW_AS_FIRST);
            check(first.created==0);p.chatNavigation.finish();check(p.fragmentsStack.get(0)==first&&p.attachedFirst==1);
            BaseFragment detached=new BaseFragment();p.chatNavigation.cold=true;p.addFragmentToStack(detached,INavigationLayout.FORCE_NOT_ATTACH_VIEW);
            p.chatNavigation.finish();check(detached.created==1&&detached.resumed==0&&p.getLastFragment()==detached);
            BaseFragment stale=new BaseFragment();p.chatNavigation.cold=true;p.addFragmentToStack(stale,-1);p.fragmentsStack.clear();p.chatNavigation.finish();check(stale.created==0);
        }
    }'''.replace('INSERTION', insertion)})
