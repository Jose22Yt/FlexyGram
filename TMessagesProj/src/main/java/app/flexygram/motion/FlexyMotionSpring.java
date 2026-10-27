/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.motion;

/** Closed-form damped oscillator. No integration substeps, allocations or refresh-rate assumption. */
public final class FlexyMotionSpring {
    private double value, velocity, target, stiffness=560, dampingRatio=.92;
    public FlexyMotionSpring(float initial) { snapTo(initial); }
    public float value(){return (float)value;}
    public float velocity(){return (float)velocity;}
    public float target(){return (float)target;}
    public void configure(FlexyMotionProfile profile){if(profile==null)throw new IllegalArgumentException("profile");configure(Math.max(1,profile.stiffness),profile.dampingRatio);}
    public void configure(float stiffness,float damping){
        if(!Float.isFinite(stiffness)||!Float.isFinite(damping)||stiffness<1||stiffness>4000||damping<.2f||damping>2)throw new IllegalArgumentException("physics");
        this.stiffness=stiffness;dampingRatio=damping;
    }
    public void target(float next){if(!Float.isFinite(next))throw new IllegalArgumentException("target");target=next;}
    public void snapTo(float next){target(next);value=next;velocity=0;}
    public boolean settled(){return Math.abs(value-target)<=.0006&&Math.abs(velocity)<=.004;}
    public float advance(float seconds){
        if(!(seconds>0)||!Float.isFinite(seconds))return value();
        if(settled()||seconds>=.25f){snapTo(target());return value();}
        double x=value-target,v=velocity,w=Math.sqrt(stiffness),z=dampingRatio,t=seconds;
        if(Math.abs(z-1)<.00001){double b=v+w*x,e=Math.exp(-w*t);value=target+(x+b*t)*e;velocity=(v-w*b*t)*e;}
        else if(z<1){double a=z*w,d=w*Math.sqrt(1-z*z),c=Math.cos(d*t),s=Math.sin(d*t),b=(v+a*x)/d,e=Math.exp(-a*t);double y=x*c+b*s;value=target+e*y;velocity=e*(-a*y-x*d*s+b*d*c);}
        else {double d=w*Math.sqrt(z*z-1),r1=-z*w+d,r2=-z*w-d,a=(v-r2*x)/(r1-r2),b=x-a;double e1=Math.exp(r1*t),e2=Math.exp(r2*t);value=target+a*e1+b*e2;velocity=a*r1*e1+b*r2*e2;}
        if(settled())snapTo(target());return value();
    }
}
