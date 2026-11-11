/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.camerapop;

/** Reusable, allocation-free sample of the capsule's absorption trajectory. */
public final class CameraPopMotion {
    public float scaleX,scaleY,x,y,alpha,contentAlpha,neck;
    public void update(float progress,boolean closing,float terminalX,float terminalY,
            float destinationX,float destinationY,boolean cutout) {
        float p=Math.max(0f,Math.min(1f,progress));
        // Horizontal contraction precedes vertical contraction: a short neck, no bounce.
        scaleX=terminalX+(1f-terminalX)*(float)Math.pow(p,1.55);
        scaleY=terminalY+(1f-terminalY)*(float)Math.pow(p,.82);
        x=destinationX*(1f-p);y=destinationY*(1f-p);
        // With real geometry, keep the surface opaque until it fits inside the hole.
        alpha=cutout?(p==0f?0f:1f):Math.min(1f,p*4f);
        contentAlpha=Math.max(0f,Math.min(1f,(p-.18f)/.65f));
        neck=(float)Math.sin(Math.PI*p)*(closing?.16f:.10f);
    }
}
