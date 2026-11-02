/* SPDX-License-Identifier: GPL-3.0-or-later */
import app.flexygram.composer.ComposerStyle;

/** Pure color policy: source/Android integration is verified separately. */
public final class GlassUiPolicyContractTest {
    private static int assertions;
    private static void check(boolean valid, String message) {
        assertions++;
        if (!valid) throw new AssertionError(message);
    }
    public static void main(String[] args) {
        int[] input = {0xff000000, 0xff222b35, 0xffffffff, 0xffe3c6ad, 0x006699ff};
        for (int source : input) {
            int tint = ComposerStyle.nativeGlassTint(source);
            check((tint & 0x00ffffff) == (source & 0x00ffffff),
                    "preserve native color RGB");
            check(((tint >>> 24) & 255) == 0x9a, "bounded frosted alpha");
            check(((tint >>> 24) & 255) < 255, "never hide native blur behind solid fill");
        }
        for (boolean dark : new boolean[]{false,true}) {
            int circle = ComposerStyle.nativeGlassButton(dark);
            check(((circle >>> 24) & 255) == 0xa6, "bounded action circle alpha");
            check(((circle >>> 24) & 255) < 255, "action circle remains translucent");
        }
        // Existing compact geometry and hit size must remain independent of glass.
        check(ComposerStyle.diameter(0) == 44, "native target default");
        check(ComposerStyle.position(100) == ComposerStyle.MAX_POSITION, "position policy unchanged");
        System.out.println("Native conversation glass tint contracts passed: " + assertions);
    }
}
