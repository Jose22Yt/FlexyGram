/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.studio;
import java.util.concurrent.*;
/** Provider I/O cannot stall Telegram's global/stage/render queues. Zero core threads, bounded backlog. */
public final class FlexyStudioIO {
    private static final ThreadPoolExecutor POOL=new ThreadPoolExecutor(0,1,1,TimeUnit.SECONDS,new ArrayBlockingQueue<>(1),r->{Thread t=new Thread(r,"FlexyStudioIO");t.setDaemon(true);return t;},new ThreadPoolExecutor.AbortPolicy());
    private FlexyStudioIO(){}
    public static Future<?> execute(Runnable task){POOL.purge();return POOL.submit(task);}
    public static void cancel(Future<?> future){if(future!=null)future.cancel(true);POOL.purge();}
}
