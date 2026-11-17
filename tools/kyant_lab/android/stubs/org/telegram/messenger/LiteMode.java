// Explicit isolated host API; not shipped in the application.
package org.telegram.messenger;
public class LiteMode {
 public static boolean isPowerSaverApplied() { return false; }
 public static void addOnPowerSaverAppliedListener(Utilities.Callback<Boolean> listener) {}
 public static void removeOnPowerSaverAppliedListener(Utilities.Callback<Boolean> listener) {}
 public static boolean isEnabled(int flag) { return true; }
}
