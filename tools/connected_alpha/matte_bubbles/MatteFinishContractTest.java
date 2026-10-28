/* SPDX-License-Identifier: GPL-3.0-or-later */
import app.flexygram.bubbles.SignatureMatteFinish;

public final class MatteFinishContractTest {
    private static int count;
    private static void check(boolean condition, String what) {
        count++;
        if (!condition) throw new AssertionError(what);
    }
    private static int chroma(int color) {
        int r = (color >>> 16) & 255, g = (color >>> 8) & 255, b = color & 255;
        return Math.max(r, Math.max(g,b)) - Math.min(r, Math.min(g,b));
    }
    public static void main(String[] ignored) {
        int[] palette = {0xff0088ff, 0xffe95a52, 0xfffafafa, 0xff080808, 0xff1a69a5,
                0x808eaabb, 0x00010203};
        for (int color : palette) {
            check(SignatureMatteFinish.color(color,0) == color, "disabled unchanged");
            check(SignatureMatteFinish.color(color,-100) == color, "negative clamps to 0");
            check(SignatureMatteFinish.color(color,101) == SignatureMatteFinish.color(color,100),
                    "high strength clamped");
            int lastChroma = chroma(color);
            for (int strength = 1; strength <= 100; strength++) {
                int result = SignatureMatteFinish.color(color,strength);
                check((result & 0xff000000) == (color & 0xff000000),
                        "alpha preserved");
                check(chroma(result) <= lastChroma, "saturation never increases");
                lastChroma = chroma(result);
            }
        }
        check(SignatureMatteFinish.color(0xff888888,100) == 0xff888888,
                "neutral gray stable");
        check(SignatureMatteFinish.color(0xffffffff,100) == 0xffffffff,
                "white stable");
        check(SignatureMatteFinish.color(0xff000000,100) == 0xff000000,
                "black stable");
        System.out.println("Signature Matte contracts: " + count + " checks passed");
    }
}
