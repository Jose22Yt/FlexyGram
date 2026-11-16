// Explicit isolated host API; not shipped in the application.
package org.telegram.messenger;
public class LiteMode {
 public static final int FLAG_LIQUID_GLASS = 1 << 18;
 public static void addOnPowerSaverAppliedListener(Utilities.Callback<Boolean> listener) {}
 public static void removeOnPowerSaverAppliedListener(Utilities.Callback<Boolean> listener) {}
 public static boolean saver;
 public static boolean isPowerSaverApplied(){return saver;}
 public static boolean isEnabled(int flag) { return true; }
}
