package app.flexygram.performance;

import android.app.Activity;
import android.util.Log;
import androidx.metrics.performance.*;
import org.telegram.messenger.BuildConfig;
import java.lang.ref.WeakReference;

/** Opt-in performance builds only. No identifiers, message text, uploads or per-frame logging. */
public final class FrameDiagnostics {
    private static WeakReference<FrameDiagnostics> active=new WeakReference<>(null);
    private final WeakReference<Activity> owner;
    private final FrameWindowStats stats=new FrameWindowStats();
    private final JankStats jank;
    private final PerformanceMetricsState.Holder state;
    private volatile boolean accepting;
    private final SystemProfiles profiles=new SystemProfiles();
    private MemoryBudgetBridge memory;
    private String transition;
    private int transitionCookie;
    private static int nextTransition;
    private static final java.util.Set<FrameDiagnostics> pendingServices=java.util.concurrent.ConcurrentHashMap.newKeySet();
    private static final java.util.concurrent.atomic.AtomicBoolean draining=new java.util.concurrent.atomic.AtomicBoolean();
    private static final java.util.concurrent.ThreadPoolExecutor services=new java.util.concurrent.ThreadPoolExecutor(0,1,1,java.util.concurrent.TimeUnit.SECONDS,
            new java.util.concurrent.ArrayBlockingQueue<>(1),r->{Thread t=new Thread(r,"FlexyDiagnostics");t.setDaemon(true);return t;},new java.util.concurrent.ThreadPoolExecutor.AbortPolicy());
    private static void schedule(FrameDiagnostics current){
        pendingServices.add(current);
        if(!draining.compareAndSet(false,true))return;
        try{services.execute(FrameDiagnostics::drainServices);}catch(java.util.concurrent.RejectedExecutionException busy){draining.set(false);}
    }
    private static void drainServices(){
        do{
            for(FrameDiagnostics current:pendingServices){pendingServices.remove(current);current.syncServices();}
            draining.set(false);
        }while(!pendingServices.isEmpty()&&draining.compareAndSet(false,true));
    }
    private void syncServices(){
        Activity activity=owner.get();
        if(accepting&&activity!=null){
            android.content.Context app=activity.getApplicationContext();
            profiles.start(app,BuildConfig.FLEXY_SYSTEM_TRACE);
            if(memory==null)memory=MemoryBudgetBridge.start(app,()->{
                if(org.telegram.messenger.ApplicationLoader.applicationLoaderInstance!=null)
                    org.telegram.messenger.ApplicationLoader.applicationLoaderInstance.onTrimMemory(15);
            });
        }
        if(!accepting||activity==null){profiles.stop();if(memory!=null){memory.close();memory=null;}}
    }
    private FrameDiagnostics(Activity activity){
        owner=new WeakReference<>(activity);
        state=PerformanceMetricsState.getHolderForHierarchy(activity.getWindow().getDecorView());
        jank=JankStats.createAndTrack(activity.getWindow(),frame->{
            if(!accepting)return;
            String screen="other";boolean scrolling=false;
            for(StateInfo item:frame.getStates()){
                if("screen".equals(item.getKey()))screen=item.getValue();
                else if("scrolling".equals(item.getKey()))scrolling="yes".equals(item.getValue());
            }
            stats.record(FrameWindowStats.state(screen,scrolling),frame.getFrameDurationUiNanos(),frame.isJank());
        });
    }
    public static FrameDiagnostics resume(Activity activity,FrameDiagnostics previous){
        if(!BuildConfig.FLEXY_FRAME_DIAGNOSTICS)return null;
        try{
            FrameDiagnostics current=previous==null?new FrameDiagnostics(activity):previous;
            current.accepting=true;current.jank.setTrackingEnabled(true);active=new WeakReference<>(current);
            schedule(current);
            return current;
        }catch(RuntimeException unavailable){return previous;}
    }
    public static void screen(Activity activity,String className){
        if(!BuildConfig.FLEXY_FRAME_DIAGNOSTICS)return;
        FrameDiagnostics current=active.get();
        if(current!=null&&current.owner.get()==activity&&current.state.getState()!=null){
            current.state.getState().putState("screen",FrameWindowStats.screen(className));
            current.state.getState().putState("scrolling","no");
        }
    }
    public static void scrolling(Activity activity,boolean scrolling){
        if(!BuildConfig.FLEXY_FRAME_DIAGNOSTICS)return;
        FrameDiagnostics current=active.get();
        if(current!=null&&current.owner.get()==activity&&current.state.getState()!=null)
            current.state.getState().putState("scrolling",scrolling?"yes":"no");
    }
    public static int transitionStart(Activity activity,boolean opening){
        if(!BuildConfig.FLEXY_FRAME_DIAGNOSTICS||android.os.Build.VERSION.SDK_INT<29)return 0;
        FrameDiagnostics current=active.get();
        if(current==null||current.owner.get()!=activity)return 0;
        current.endTransition(current.transitionCookie);
        current.transition=opening?"Flexy.chat.open":"Flexy.chat.close";current.transitionCookie=++nextTransition;
        android.os.Trace.beginAsyncSection(current.transition,current.transitionCookie);
        return current.transitionCookie;
    }
    private void endTransition(int cookie){
        if(android.os.Build.VERSION.SDK_INT>=29&&transition!=null&&cookie==transitionCookie){
            android.os.Trace.endAsyncSection(transition,transitionCookie);transition=null;
        }
    }
    public static void transitionEnd(Activity activity,int cookie){
        if(!BuildConfig.FLEXY_FRAME_DIAGNOSTICS||android.os.Build.VERSION.SDK_INT<29)return;
        FrameDiagnostics current=active.get();
        if(current!=null&&current.owner.get()==activity)current.endTransition(cookie);
    }
    public static void pause(FrameDiagnostics current){
        if(current==null)return;
        current.endTransition(current.transitionCookie);
        current.accepting=false;current.jank.setTrackingEnabled(false);
        schedule(current);
        if(active.get()==current)active.clear();
        Log.i("FlexyPerformance",current.stats.drain());
    }
}
