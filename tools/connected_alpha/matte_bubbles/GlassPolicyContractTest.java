/* SPDX-License-Identifier: GPL-3.0-or-later */
import app.flexygram.bubbles.BubbleGlassPolicy;

/** Offline deterministic math checks; do not pretend this validates a phone renderer. */
public final class GlassPolicyContractTest {
    private static int assertions;
    private static void check(boolean valid, String reason) {
        assertions++;
        if (!valid) throw new AssertionError(reason);
    }
    public static void main(String[] args) {
        for (int strength = -20; strength <= 120; strength++) {
            int expected = BubbleGlassPolicy.clamp(strength);
            check(expected >= 0 && expected <= 100, "bounded intensity");
            int previous = -1;
            for (int alpha = -10; alpha <= 265; alpha++) {
                int value = BubbleGlassPolicy.opacity(alpha, strength);
                check(value >= 0 && value <= 255, "bounded blending alpha");
                check(value >= previous, "monotonic with native alpha");
                previous = value;
            }
        }
        check(BubbleGlassPolicy.opacity(255, 0) == 0, "0 glass does not paint");
        check(BubbleGlassPolicy.opacity(255, 100) == 255, "full strength retains source alpha");
        check(BubbleGlassPolicy.opacity(255, 70) == 179, "70% shared-wallpaper blend");
        check(BubbleGlassPolicy.opacity(128, 50) == 64, "preserves native transition opacity");
        System.out.println("Bubble Glass alpha blend checks: " + assertions);
    }
}
