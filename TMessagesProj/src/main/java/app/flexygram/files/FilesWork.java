/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.files;
import java.util.concurrent.*;
import java.io.Closeable;
/** Instance-owned scope, constructed only on explicit open. No static pool, idle observer or service. */
final class FilesWork implements Closeable {
    private final ThreadPoolExecutor pool=new ThreadPoolExecutor(0,1,1,TimeUnit.SECONDS,new ArrayBlockingQueue<>(1),r->{Thread t=new Thread(r,"FlexyFiles");t.setDaemon(true);return t;},new ThreadPoolExecutor.AbortPolicy());
    private Future<?> future;private volatile boolean closed;private int generation;
    int token(){return generation;}
    boolean current(int token){return !closed&&generation==token;}
    void submit(Runnable work){if(closed)return;if(future!=null)future.cancel(true);pool.purge();generation++;future=pool.submit(work);}
    @Override public void close(){closed=true;generation++;if(future!=null)future.cancel(true);pool.shutdownNow();}
}
