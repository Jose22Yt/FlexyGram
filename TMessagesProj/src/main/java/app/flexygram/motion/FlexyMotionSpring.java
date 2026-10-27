/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.motion;

/** Closed-form damped oscillator. No integration substeps, allocations or refresh-rate assumption. */
public final class FlexyMotionSpring {
    private double value, velocity, target, stiffness, dampingRatio;
    private double omega, alpha, frequency, pole1, pole2;
    private boolean critical;
    public FlexyMotionSpring(float initial) { configure(FlexyMotionProfile.FLOW); snapTo(initial); }
    public float value(){return (float)value;}
    public float velocity(){return (float)velocity;}
    public float target(){return (float)target;}
    public void configure(FlexyMotionProfile profile){if(profile==null)throw new IllegalArgumentException("profile");configure(Math.max(1,profile.stiffness),profile.dampingRatio);}
    public void configure(float stiffness,float damping){
        if(!Float.isFinite(stiffness)||!Float.isFinite(damping)||stiffness<1||stiffness>4000||damping<.2f||damping>2)throw new IllegalArgumentException("physics");
        if (this.stiffness == stiffness && dampingRatio == damping) return;
        this.stiffness=stiffness;dampingRatio=damping;
        omega=Math.sqrt(stiffness);alpha=damping*omega;
        critical=Math.abs(damping-1)<.00001;
        frequency=omega*Math.sqrt(Math.abs(1-dampingRatio*dampingRatio));
        pole1=-alpha+frequency;pole2=-alpha-frequency;
    }
    public void target(float next){if(!Float.isFinite(next))throw new IllegalArgumentException("target");target=next;}
    public void snapTo(float next){target(next);value=next;velocity=0;}
    public boolean settled(){return Math.abs(value-target)<=.0006&&Math.abs(velocity)<=.004;}
    public float advance(float seconds){
        if(!(seconds>0)||!Float.isFinite(seconds))return value();
        if(settled()||seconds>=.25f){snapTo(target());return value();}
        double x=value-target,v=velocity,w=omega,z=dampingRatio,t=seconds;
        if(critical){double b=v+w*x,e=Math.exp(-w*t);value=target+(x+b*t)*e;velocity=(v-w*b*t)*e;}
        else if(z<1){double a=alpha,d=frequency,c=Math.cos(d*t),s=Math.sin(d*t),b=(v+a*x)/d,e=Math.exp(-a*t);double y=x*c+b*s;value=target+e*y;velocity=e*(-a*y-x*d*s+b*d*c);}
        else {double r1=pole1,r2=pole2,a=(v-r2*x)/(r1-r2),b=x-a;double e1=Math.exp(r1*t),e2=Math.exp(r2*t);value=target+a*e1+b*e2;velocity=a*r1*e1+b*r2*e2;}
        if(settled())snapTo(target());return value();
    }
}
