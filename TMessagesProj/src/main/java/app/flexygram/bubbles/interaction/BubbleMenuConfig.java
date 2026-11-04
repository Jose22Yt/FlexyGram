package app.flexygram.bubbles.interaction;

import android.content.Context;
import android.content.SharedPreferences;
import java.util.EnumSet;
import java.util.HashSet;
import java.util.Set;
import app.flexygram.bubbles.interaction.BubbleActionPanelView.Action;

/** Presentation preferences only. Telegram still decides which actions a message permits. */
public final class BubbleMenuConfig {
    public static final int LIST = 0, GRID = 1, GROUPS = 2, TOOLBAR = 3;
    public static final String FILE = "flexy_bubble_interaction", STYLE = "menu_layout", ACTIONS = "menu_actions";
    private BubbleMenuConfig() {}
    private static SharedPreferences prefs(Context context) {
        return context.getApplicationContext().getSharedPreferences(FILE, Context.MODE_PRIVATE);
    }
    public static int layout(Context context) { return Math.max(LIST, Math.min(TOOLBAR, prefs(context).getInt(STYLE, LIST))); }
    public static void layout(Context context, int style) {
        prefs(context).edit().putInt(STYLE, Math.max(LIST, Math.min(TOOLBAR, style))).apply();
        BubbleInteractionSettings.setStyle(context, BubbleInteractionSettings.STYLE_SIGNATURE);
    }
    public static EnumSet<Action> defaults() {
        return EnumSet.of(Action.REPLY, Action.COPY, Action.STICKER, Action.FORWARD, Action.PIN, Action.DELETE);
    }
    public static EnumSet<Action> actions(Context context) {
        SharedPreferences preferences = prefs(context);
        if (!preferences.contains(ACTIONS)) return defaults();
        EnumSet<Action> result = EnumSet.noneOf(Action.class);
        for (String key : preferences.getStringSet(ACTIONS, java.util.Collections.emptySet())) {
            try { Action action = Action.valueOf(key); if (action != Action.MORE) result.add(action); }
            catch (IllegalArgumentException ignored) { /* Newer/removed actions do not grant permissions. */ }
        }
        return result;
    }
    public static void actions(Context context, EnumSet<Action> actions) {
        Set<String> keys = new HashSet<>();
        for (Action action : actions) if (action != Action.MORE) keys.add(action.name());
        prefs(context).edit().putStringSet(ACTIONS, keys).apply();
    }
    public static EnumSet<Action> visible(EnumSet<Action> permitted, EnumSet<Action> chosen) {
        EnumSet<Action> result = permitted.clone(); result.retainAll(chosen); result.remove(Action.MORE); return result;
    }
}
