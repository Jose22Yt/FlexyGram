/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.files;
import java.util.concurrent.*;
import java.io.Closeable;
/** Instance-owned scope, constructed only on explicit open. No static pool, idle observer or service. */
final class FilesWork implements Closeable {
    private final ThreadPoolExecutor pool=new ThreadPoolExecutor(0,1,1,TimeUnit.SECONDS,new ArrayBlockingQueue<>(2),r->{Thread t=new Thread(r,"FlexyFiles");t.setDaemon(true);return t;},new ThreadPoolExecutor.DiscardPolicy());
    private final Object lock=new Object();
    private Future<?> future;
    private Runnable pending;
    private volatile boolean closed;
    private volatile int generation;
    int token(){return generation;}
    boolean current(int token){return !closed&&generation==token;}
    void submit(Runnable work){
        if(closed||work==null)return;
        synchronized(lock){
            if(closed)return;
            generation++;
            pending=work;
            if(future!=null)future.cancel(true);
            pool.purge();
            future=pool.submit(this::drainPending);
        }
    }
    private void drainPending(){
        while(!closed){
            Runnable next;
            synchronized(lock){
                if(closed||pending==null)return;
                next=pending;
                pending=null;
            }
            if(Thread.currentThread().isInterrupted())Thread.interrupted();
            next.run();
        }
    }
    void cancel(){
        synchronized(lock){
            generation++;
            pending=null;
            if(future!=null)future.cancel(true);
            pool.purge();
        }
    }
    @Override public void close(){
        synchronized(lock){
            closed=true;
            generation++;
            pending=null;
            if(future!=null)future.cancel(true);
            pool.shutdownNow();
        }
    }
}
