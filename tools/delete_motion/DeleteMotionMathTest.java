import app.flexygram.bubbles.deletion.DeleteMotionMath;

/** Host-side tests: deterministic endpoints, no NaNs, monotonic particle travel. */
public final class DeleteMotionMathTest {
    public static void main(String[] args) {
        check(DeleteMotionMath.smooth(-1)==0 && DeleteMotionMath.smooth(2)==1,"clamp");
        check(DeleteMotionMath.smooth(0)==0 && DeleteMotionMath.smooth(1)==1,"smooth endpoints");
        check(DeleteMotionMath.fade(.3f,.6f)==1 && DeleteMotionMath.fade(1f,.6f)==0,"fade");
        check(DeleteMotionMath.preCompression(0)==1 && DeleteMotionMath.preCompression(.12f)==1,"press");
        float previous=0;
        for(int i=0;i<=10000;i++) {
            float t=i/10000f;
            float x=DeleteMotionMath.scatter(t);
            check(Float.isFinite(x)&&x>=previous-1e-6f&&x>=0&&x<=1,"scatter monotonic");
            previous=x;
            check(Float.isFinite(DeleteMotionMath.hash(i)),"hash finite");
            check(Float.isFinite(DeleteMotionMath.smooth(t)),"smooth finite");
        }
        System.out.println("DeleteMotionMathTest PASS (10001 samples)");
    }
    private static void check(boolean ok,String message) { if(!ok)throw new AssertionError(message); }
}
