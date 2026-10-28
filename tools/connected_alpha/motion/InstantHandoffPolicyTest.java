import org.telegram.ui.ActionBar.FlexyNavigationHandoffPolicy;

/**
 * Real production policy, compiled and executed without Android test doubles.
 * javac -d /tmp/flexy-handoff .../FlexyNavigationHandoffPolicy.java \
 *     tools/connected_alpha/motion/InstantHandoffPolicyTest.java
 * java -cp /tmp/flexy-handoff InstantHandoffPolicyTest
 */
public final class InstantHandoffPolicyTest {
    private static int cases;

    private static void check(String name, boolean expected,
                              boolean active, boolean blocked, boolean visible, boolean attached,
                              float x, float y, float outgoingX, float width, float height, float margin) {
        boolean actual = FlexyNavigationHandoffPolicy.canHandoffClosingDown(
                active, blocked, visible, attached, x, y, outgoingX, width, height, margin);
        cases++;
        if (actual != expected) {
            throw new AssertionError(name + " expected=" + expected + ", actual=" + actual);
        }
    }

    private static void sample(String name, boolean expected,
                               boolean active, boolean blocked, boolean visible, boolean attached,
                               float x, float y, float outgoingX) {
        check(name, expected, active, blocked, visible, attached,
                x, y, outgoingX, 400f, 800f, 16f);
    }

    private static void timed(String name, boolean expected, boolean ready, boolean blocked, boolean attached,
                               float alpha, float x, float y, float width, float height, float inset) {
        cases++;
        boolean actual=FlexyNavigationHandoffPolicy.canHandoffRenderedTimedCloseDown(ready,blocked,attached,alpha,x,y,width,height,inset);
        if(actual!=expected)throw new AssertionError(name+" expected="+expected+", actual="+actual);
    }

    public static void main(String[] args) {
        sample("exposed middle of outgoing close", true, true, false, true, true, 80f, 200f, 220f);
        sample("exposed near left", true, true, false, true, true, 16f, 200f, 220f);
        sample("exposed just before border", true, true, false, true, true, 203.99f, 200f, 220f);
        sample("no active closing", false, false, false, true, true, 80f, 200f, 220f);
        sample("preview, modal or gesture", false, true, true, true, true, 80f, 200f, 220f);
        sample("outgoing hidden", false, true, false, false, true, 80f, 200f, 220f);
        sample("background detached", false, true, false, true, false, 80f, 200f, 220f);
        sample("touch inside outgoing", false, true, false, true, true, 240f, 200f, 220f);
        sample("outgoing boundary inset", false, true, false, true, true, 204f, 200f, 220f);
        sample("left edge outside safe region", false, true, false, true, true, 15.99f, 200f, 220f);
        sample("top edge outside safe region", false, true, false, true, true, 80f, 15.99f, 220f);
        sample("bottom edge outside safe region", false, true, false, true, true, 80f, 784f, 220f);
        sample("top boundary inside safe region", true, true, false, true, true, 80f, 16f, 220f);
        sample("bottom boundary inside safe region", true, true, false, true, true, 80f, 783.99f, 220f);
        sample("no exposed area yet", false, true, false, true, true, 16f, 200f, 0f);
        sample("exposure below minimum", false, true, false, true, true, 16f, 200f, 31.99f);
        sample("exposure exactly minimum", false, true, false, true, true, 16f, 200f, 32f);
        sample("invalid overshoot beyond view", false, true, false, true, true, 80f, 200f, 401f);
        sample("NaN touch x", false, true, false, true, true, Float.NaN, 200f, 220f);
        sample("NaN touch y", false, true, false, true, true, 80f, Float.NaN, 220f);
        sample("NaN translation", false, true, false, true, true, 80f, 200f, Float.NaN);
        sample("Infinity translation", false, true, false, true, true, 80f, 200f, Float.POSITIVE_INFINITY);
        sample("Infinity touch", false, true, false, true, true, Float.NEGATIVE_INFINITY, 200f, 220f);
        check("zero width", false, true, false, true, true, 80f, 200f, 220f, 0f, 800f, 16f);
        check("zero height", false, true, false, true, true, 80f, 200f, 220f, 400f, 0f, 16f);
        check("negative inset", false, true, false, true, true, 80f, 200f, 220f, 400f, 800f, -1f);
        check("NaN width", false, true, false, true, true, 80f, 200f, 220f, Float.NaN, 800f, 16f);
        check("Infinity inset", false, true, false, true, true, 80f, 200f, 220f, 400f, 800f, Float.POSITIVE_INFINITY);
        check("tiny screen", false, true, false, true, true, 80f, 200f, 220f, 12f, 12f, 16f);
        check("zero inset at x zero", true, true, false, true, true, 0f, 20f, 100f, 400f, 800f, 0f);
        timed("rendered timed body",true,true,false,true,0,120,240,300,600,16);
        timed("running timed",false,false,false,true,0,120,240,300,600,16);
        timed("visible outgoing",false,true,false,true,.001f,120,240,300,600,16);
        timed("modal",false,true,true,true,0,120,240,300,600,16);
        timed("detached",false,true,false,false,0,120,240,300,600,16);
        timed("NaN alpha",false,true,false,true,Float.NaN,120,240,300,600,16);
        timed("infinite x",false,true,false,true,0,Float.POSITIVE_INFINITY,240,300,600,16);
        timed("outside right",false,true,false,true,0,284,240,300,600,16);
        timed("outside bottom",false,true,false,true,0,120,584,300,600,16);
        timed("negative inset",false,true,false,true,0,120,240,300,600,-1);
        timed("invalid dimensions",false,true,false,true,0,120,240,Float.NaN,600,16);
        timed("too small",false,true,false,true,0,16,16,32,32,16);
        System.out.println("Instant navigation handoff policy: " + cases + " PASS");
    }
}
