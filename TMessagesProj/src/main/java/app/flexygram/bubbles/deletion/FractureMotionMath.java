/* Adapted from Bubble Fracture v1.0 by @larrat23, supplied with this change.
 * Original attribution retained; see CREDITS.md. */

package app.flexygram.bubbles.deletion;
/** Allocation-free motion curves; inputs are clamped at the native boundary. */
public final class FractureMotionMath {
    public static float unit(float t) {
        return Math.max(0f,Math.min(1f,t));
    }
    public static float smooth(float t) {
        t=unit(t);
        return t*t*(3f-2f*t);
    }
    public static float falling(float t,int gravity) {
        return (float)Math.pow(unit(t),1.35f+.65f*Math.max(.3f,Math.min(2f,gravity/100f)));
    }
    public static float spiralScale(float t,int squeeze) {
        return (float)Math.pow(1f-smooth(t),Math.max(.7f,Math.min(2.4f,squeeze/100f)));
    }
    public static float spiralAlpha(float t) {
        return 1f-smooth((t-.64f)/.36f);
    }
    public static float exitDistance(float y,float bottom,float width,float height) {
        return Math.max(1f,bottom-y+(float)Math.sqrt(width*width+height*height)+4f);
    }
}
