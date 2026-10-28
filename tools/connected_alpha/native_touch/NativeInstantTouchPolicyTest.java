/* SPDX-License-Identifier: GPL-3.0-or-later */
import app.flexygram.navigation.NativeInstantTouchPolicy;

public final class NativeInstantTouchPolicyTest {
    private static int passed;
    private static void test(boolean value, String name) {
        passed++;
        if (!value) throw new AssertionError(name);
    }
    private static boolean admit(boolean down, boolean root, boolean close,
            boolean dialogs, boolean cell, boolean covered, boolean modal,
            boolean ime, boolean gesture) {
        return NativeInstantTouchPolicy.canFinishNativeCloseForDown(down,root,close,
                dialogs,cell,covered,modal,ime,gesture);
    }
    public static void main(String[] args) {
        test(admit(true,true,true,true,true,false,false,false,false),"one real down");
        test(!admit(false,true,true,true,true,false,false,false,false),"no move/up/new event");
        test(!admit(true,false,true,true,true,false,false,false,false),"background root");
        test(!admit(true,true,false,true,true,false,false,false,false),"not closing");
        test(!admit(true,true,true,false,true,false,false,false,false),"non-dialog destination");
        test(!admit(true,true,true,true,false,false,false,false,false),"no visible row");
        test(!admit(true,true,true,true,true,true,false,false,false),"outgoing covers target");
        test(!admit(true,true,true,true,true,false,true,false,false),"modal/preview");
        test(!admit(true,true,true,true,true,false,false,true,false),"keyboard/sheet");
        test(!admit(true,true,true,true,true,false,false,false,true),"swipe/selection");
        System.out.println("Native Instant Touch: "+passed+" policies passed");
    }
}
