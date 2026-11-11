/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.camerapop;

/** Exact critically damped motion. Retargeting preserves position and velocity. */
public final class CameraPopSpring {
    public float value,velocity,target;
    public void target(float target) {this.target=Math.max(0f,Math.min(1f,target));}
    public void snap(float value) {this.value=this.target=value;velocity=0;}
    public boolean step(float dt) {
        float t=Math.max(0f,Math.min(.05f,dt)),omega=19f;
        float a=value-target,b=velocity+omega*a,decay=(float)Math.exp(-omega*t);
        value=target+(a+b*t)*decay;velocity=(velocity-omega*b*t)*decay;
        if(value<0f || value>1f) {value=Math.max(0f,Math.min(1f,value));velocity=0;}
        if(Math.abs(value-target)<.001f && Math.abs(velocity)<.015f) {snap(target);return false;}
        return true;
    }
}
