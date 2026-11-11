/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.camerapop;

import android.content.SharedPreferences;
import java.util.HashSet;
import java.util.Set;
import org.telegram.messenger.MessagesController;
import org.telegram.messenger.UserConfig;

/** Uses the existing account preferences; no eager app-wide storage or new service. */
public final class CameraPopConfig {
    private static final String PREFIX = "flexy_camera_pop_";
    public final SharedPreferences prefs;
    public final boolean enabled, immediate, reminders, names, respectMuted, quiet;
    public final int intervalMinutes, durationSeconds, quietStart, quietEnd;
    public final Set<Long> selected = new HashSet<>();
    public CameraPopConfig(int account) {
        prefs = MessagesController.getMainSettings(account);
        long owner=UserConfig.getInstance(account).getClientUserId();
        long previous=prefs.getLong(PREFIX+"owner",0);
        if(owner!=0 && previous!=owner) {
            SharedPreferences.Editor edit=prefs.edit().putLong(PREFIX+"owner",owner);
            if(previous!=0) edit.putBoolean(PREFIX+"enabled",false).remove(PREFIX+"selected").remove(PREFIX+"pending");
            edit.apply();
        }
        enabled = prefs.getBoolean(PREFIX+"enabled", false);
        immediate = prefs.getBoolean(PREFIX+"immediate", true);
        reminders = prefs.getBoolean(PREFIX+"reminders", true);
        names = prefs.getBoolean(PREFIX+"names", true);
        respectMuted = prefs.getBoolean(PREFIX+"respect_muted", true);
        quiet = prefs.getBoolean(PREFIX+"quiet", false);
        int minutes = prefs.getInt(PREFIX+"interval", 15);
        intervalMinutes = minutes == 5 || minutes == 30 ? minutes : 15;
        durationSeconds = Math.max(2, Math.min(10, prefs.getInt(PREFIX+"duration", 4)));
        quietStart = Math.floorMod(prefs.getInt(PREFIX+"quiet_start", 22*60), 1440);
        quietEnd = Math.floorMod(prefs.getInt(PREFIX+"quiet_end", 8*60), 1440);
        for (String id : prefs.getStringSet(PREFIX+"selected", java.util.Collections.emptySet())) {
            try { selected.add(Long.parseLong(id)); } catch (NumberFormatException ignored) {}
        }
    }
    public static boolean enabled(int account) { return MessagesController.getMainSettings(account).getBoolean(PREFIX+"enabled", false); }
    public static boolean interested(int account,long dialog,boolean nativeAllowed) {
        SharedPreferences prefs=MessagesController.getMainSettings(account);
        return prefs.getBoolean(PREFIX+"enabled",false)
                && (nativeAllowed || !prefs.getBoolean(PREFIX+"respect_muted",true))
                && prefs.getStringSet(PREFIX+"selected",java.util.Collections.emptySet()).contains(Long.toString(dialog));
    }
    public long interval() { return intervalMinutes * 60_000L; }
    public void set(String key, boolean value) { prefs.edit().putBoolean(PREFIX+key,value).apply(); }
    public void set(String key, int value) { prefs.edit().putInt(PREFIX+key,value).apply(); }
    public void select(Set<Long> dialogs) {
        Set<String> saved = new HashSet<>();
        for (long id : dialogs) saved.add(Long.toString(id));
        prefs.edit().putStringSet(PREFIX+"selected",saved).apply();
    }
    public void load(CameraPopState state) { state.restore(prefs.getStringSet(PREFIX+"pending",java.util.Collections.emptySet()),selected); }
    public void save(CameraPopState state) { prefs.edit().putStringSet(PREFIX+"pending",state.save()).apply(); }
    public void clearPending() { prefs.edit().remove(PREFIX+"pending").apply(); }
}
