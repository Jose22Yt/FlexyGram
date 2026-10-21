package io.github.jose22yt.flexygram.login.local;
/** View lifecycle ticket only; not an animation engine or timer. */
public final class LocalTransitionFence {
    private long epoch;private boolean alive=true;
    public synchronized long next(){if(!alive)throw new IllegalStateException("LOCAL_VIEW_DESTROYED");return ++epoch;}
    public synchronized boolean current(long ticket){return alive&&ticket==epoch;}
    public synchronized void destroy(){alive=false;++epoch;}
}
