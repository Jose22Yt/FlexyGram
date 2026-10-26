import app.flexygram.header.fusion.SignatureFusionGeometry;
import app.flexygram.header.fusion.SignatureFusionGeometry.Layout;
import app.flexygram.header.fusion.SignatureFusionGeometry.Rect;

/** Host-only geometry contract. Run with javac/java; no Android dependencies. */
public final class SignatureFusionGeometryTest {
    private static int assertions = 0;
    private static void yes(boolean condition, String message) {
        assertions++;
        if (!condition) throw new AssertionError(message);
    }
    private static void close(float a,float b,String message) {
        yes(Math.abs(a-b) <= .02f,message+" actual="+a+" target="+b);
    }
    private static void test(int widthDp, float density, boolean rtl, boolean calling) {
        float width=widthDp*density;
        Layout g = SignatureFusionGeometry.calculate(width,density,rtl,calling);
        yes(g.back.left >= 0 && g.back.right <= width,"back inside screen");
        yes(g.actions.left >= 0 && g.actions.right <= width,"actions inside screen");
        yes(g.center.left >= 0 && g.center.right <= width,"center inside screen");
        yes(g.center.width() >= 0,"center valid");
        close(g.center.height(),50*density,"center height");
        close(g.back.height(),46*density,"back height");
        close(g.actions.height(),46*density,"action height");
        yes(g.center.height()>g.back.height(),"center only slightly taller");
        close(g.back.width(),46*density,"back width");
        close(g.actions.width(),(calling?96:48)*density,"right action width");
        if (g.fits) {
            if (!rtl) {
                yes(g.center.left-g.back.right>=9.99f*density,"left 10dp gap");
                yes(g.actions.left-g.center.right>=9.99f*density,"right 10dp gap");
            } else {
                yes(g.back.left-g.center.right>=9.99f*density,"right 10dp gap rtl");
                yes(g.center.left-g.actions.right>=9.99f*density,"left 10dp gap rtl");
            }
            yes(g.text.left>=g.center.left && g.text.right<=g.center.right,"text in card");
            yes(g.portrait.left>=g.center.left && g.portrait.right<=g.center.right,"portrait in card");
            yes(g.text.width()>=48*density,"minimum text area");
            yes(g.portrait.width()>0,"nonempty portrait");
            close(g.call.width(),calling?48*density:0f,"call hit width");
            close(g.more.width(),48*density,"menu hit width");
        }
        Layout gOther = SignatureFusionGeometry.calculate(width,density,rtl,calling);
        close(g.back.left,gOther.back.left,"deterministic back");
        close(g.actions.left,gOther.actions.left,"deterministic action");
    }
    private static void testSymmetry(int w,boolean calls) {
        Layout l=SignatureFusionGeometry.calculate(w,1f,false,calls);
        Layout r=SignatureFusionGeometry.calculate(w,1f,true,calls);
        close(l.back.left,w-r.back.right,"mirrored back");
        close(l.actions.left,w-r.actions.right,"mirrored actions");
        close(l.center.left,w-r.center.right,"mirrored card");
    }
    public static void main(String[] args) {
        for (int w:new int[]{240,280,320,360,393,412,600,800}) {
            for(float d:new float[]{1f,1.5f,3f}) {
                for(boolean rtl:new boolean[]{false,true}) {
                    for(boolean calling:new boolean[]{false,true}) test(w,d,rtl,calling);
                }
            }
            testSymmetry(w,true);testSymmetry(w,false);
        }
        // Too-narrow viewports should NOT have overlapping hit targets.
        yes(!SignatureFusionGeometry.calculate(240,1f,false,true).fits,"narrow fallback");
        for(int w:new int[]{360,393,412}) yes(SignatureFusionGeometry.calculate(w,1f,false,true).fits,"typical phone support");
        System.out.println("PASS: "+assertions+" Signature Fusion geometry assertions");
    }
}
