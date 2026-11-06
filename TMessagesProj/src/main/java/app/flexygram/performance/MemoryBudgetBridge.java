package app.flexygram.performance;

import android.content.Context;
import android.os.Build;
import android.os.Looper;
import android.os.SystemClock;
import java.lang.reflect.*;

/** Optional public API37.2 bridge. No hidden API access or invented system budget.
 * Older systems use ComponentCallbacks2; this adapter is attached only in performance builds. */
final class MemoryBudgetBridge implements AutoCloseable {
    private Object manager,listener;
    private Method unregister;
    private long lastTrim=-1;
    private volatile boolean registered;
    static MemoryBudgetBridge start(Context context,Runnable trim){
        if(Build.VERSION.SDK_INT<37)return null;
        MemoryBudgetBridge bridge=new MemoryBudgetBridge();
        try{
            Class<?> type=Class.forName("android.app.MemoryBudgetManager");
            Class<?> callback=Class.forName("android.app.MemoryBudgetManager$OnOverBudgetListener");
            bridge.manager=context.getSystemService(type);
            if(bridge.manager==null)return null;
            bridge.unregister=type.getMethod("unregisterProcessOverBudgetListener",callback);
            bridge.listener=Proxy.newProxyInstance(MemoryBudgetBridge.class.getClassLoader(),new Class<?>[]{callback},(proxy,method,args)->{
                if(method.getDeclaringClass()==Object.class){
                    if(method.getName().equals("hashCode"))return System.identityHashCode(proxy);
                    if(method.getName().equals("equals"))return proxy==args[0];
                    return "FlexyMemoryListener";
                }
                if(!bridge.registered)return null;
                long now=SystemClock.uptimeMillis();
                if(bridge.lastTrim<0||now-bridge.lastTrim>=5000){bridge.lastTrim=now;trim.run();}
                return null;
            });
            bridge.registered=true;
            type.getMethod("registerProcessOverBudgetListener",Looper.class,callback).invoke(bridge.manager,Looper.getMainLooper(),bridge.listener);
            return bridge;
        }catch(ReflectiveOperationException|RuntimeException|LinkageError unsupported){bridge.close();return null;}
    }
    @Override public void close(){
        registered=false;
        if(manager!=null&&listener!=null&&unregister!=null)try{unregister.invoke(manager,listener);}catch(ReflectiveOperationException|RuntimeException ignored){}
        manager=listener=null;unregister=null;
    }
}
