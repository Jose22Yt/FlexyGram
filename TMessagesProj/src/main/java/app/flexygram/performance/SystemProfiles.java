package app.flexygram.performance;

import android.content.Context;
import android.os.Build;
import android.util.Log;
import androidx.annotation.RequiresApi;
import java.util.*;
import java.util.function.Consumer;

/** System captures stay in private app storage. Testing overlay grants REQUEST_PROFILING only there. */
final class SystemProfiles {
    private Api35 impl;
    void start(Context context,boolean captureTrace){
        if(Build.VERSION.SDK_INT<35||impl!=null)return;
        try{impl=new Api35(context);impl.start(captureTrace);}catch(RuntimeException unavailable){stop();}
    }
    void stop(){if(impl!=null){impl.close();impl=null;}}
    @RequiresApi(35)
    private static final class Api35 {
        final android.os.ProfilingManager manager;
        final Consumer<android.os.ProfilingResult> callback=result->Log.i("FlexyPerformance","system_profile_result="+result.getErrorCode());
        boolean registered;
        android.os.CancellationSignal capture;
        Api35(Context context){manager=context.getSystemService(android.os.ProfilingManager.class);}
        void start(boolean captureTrace){
            if(manager==null)return;
            manager.registerForAllProfilingResults(Runnable::run,callback);registered=true;
            if(Build.VERSION.SDK_INT>=36)Api36.register(manager);
            if(captureTrace){
                capture=new android.os.CancellationSignal();
                manager.requestProfiling(android.os.ProfilingManager.PROFILING_TYPE_SYSTEM_TRACE,
                        null,"flexy_local",capture,Runnable::run,null);
            }
        }
        void close(){
            if(manager==null||!registered)return;
            if(capture!=null){try{capture.cancel();}catch(RuntimeException ignored){}capture=null;}
            try{if(Build.VERSION.SDK_INT>=36)Api36.remove(manager);}catch(RuntimeException ignored){}
            try{manager.unregisterForAllProfilingResults(callback);}catch(RuntimeException ignored){}
            registered=false;
        }
    }
    @RequiresApi(36)
    private static final class Api36 {
        static void register(android.os.ProfilingManager manager){
            List<android.os.ProfilingTrigger> triggers=new ArrayList<>();
            triggers.add(new android.os.ProfilingTrigger.Builder(android.os.ProfilingTrigger.TRIGGER_TYPE_ANR).setRateLimitingPeriodHours(1).build());
            if(Build.VERSION.SDK_INT>=37)Api37.add(triggers);
            manager.addProfilingTriggers(triggers);
        }
        static void remove(android.os.ProfilingManager manager){manager.removeProfilingTriggersByType(Build.VERSION.SDK_INT>=37
                ?new int[]{android.os.ProfilingTrigger.TRIGGER_TYPE_ANR,android.os.ProfilingTrigger.TRIGGER_TYPE_OOM}
                :new int[]{android.os.ProfilingTrigger.TRIGGER_TYPE_ANR});}
    }
    @RequiresApi(37)
    private static final class Api37 {
        static void add(List<android.os.ProfilingTrigger> triggers){triggers.add(new android.os.ProfilingTrigger.Builder(android.os.ProfilingTrigger.TRIGGER_TYPE_OOM).setRateLimitingPeriodHours(1).build());}
    }
}
