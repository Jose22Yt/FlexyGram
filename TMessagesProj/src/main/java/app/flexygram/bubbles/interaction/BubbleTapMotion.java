/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.os.SystemClock;
import android.view.View;

/** Cell-owned, frame-clock spring. No View property animator, bitmap or per-frame allocation.
 * Native hit testing decides eligibility before press(); RecyclerView owns gesture arbitration. */
public final class BubbleTapMotion implements Runnable {
    private final View owner;
    private float scale=1f, from=1f, compression, rebound;
    private long released, duration;
    private boolean pressed, running;
    public BubbleTapMotion(View owner){this.owner=owner;}
    public float scale(){return scale;}
    public boolean pressed(){return pressed;}
    public void press(float compression,float rebound,long duration){
        owner.removeCallbacks(this);
        this.compression=Math.max(0,Math.min(.065f,compression));
        this.rebound=Math.max(0,Math.min(1,rebound));this.duration=Math.max(140,Math.min(480,duration));
        pressed=true;running=false;scale=1f-this.compression;invalidate();
    }
    public void release(){
        if(!pressed)return;
        pressed=false;from=scale;released=SystemClock.uptimeMillis();running=true;
        owner.postOnAnimation(this);
    }
    public static float recovery(float t,float rebound){
        if(t>=1)return 1;
        // A bounded underdamped return, with an exact rest value at the end.
        float residual=(float)(Math.exp(-7*t)*Math.cos((1.5+rebound*1.5)*Math.PI*t));
        return 1-residual;
    }
    @Override public void run(){
        if(!running)return;
        float t=Math.min(1,(SystemClock.uptimeMillis()-released)/(float)duration);
        scale=from+(1-from)*recovery(t,rebound);
        if(t>=1){scale=1;running=false;}else owner.postOnAnimation(this);
        invalidate();
    }
    public void reset(){
        if(!pressed&&!running&&scale==1f)return;
        owner.removeCallbacks(this);pressed=running=false;scale=1;invalidate();
    }
    private void invalidate(){owner.invalidate();if(owner.getParent() instanceof View)((View)owner.getParent()).invalidate();}
}
