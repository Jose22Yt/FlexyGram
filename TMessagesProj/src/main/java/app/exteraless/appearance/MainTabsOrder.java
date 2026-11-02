package app.exteraless.appearance;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import tw.nekomimi.nekogram.NekoConfig;
import tw.nekomimi.nekogram.helpers.MainTabsHelper;

/** Stable slots: Feed replaces Contacts, and Calls replaces Settings when enabled. */
public final class MainTabsOrder {
    public static final int CHATS = 0, CONTACTS = 1, SETTINGS = 2, PROFILE = 3;
    private static final String KEY = "FlexyMainTabsOrder";

    private MainTabsOrder() {}

    public static List<Integer> all() {
        ArrayList<Integer> order = new ArrayList<>();
        String saved = NekoConfig.getPreferences().getString(KEY, "0,1,2,3");
        for (String token : saved.split(",")) {
            try {
                int id = Integer.parseInt(token);
                if (id >= CHATS && id <= PROFILE && !order.contains(id)) order.add(id);
            } catch (NumberFormatException ignored) {}
        }
        for (int id = CHATS; id <= PROFILE; id++) if (!order.contains(id)) order.add(id);
        return order;
    }

    public static List<Integer> visible() {
        List<Integer> order = all();
        if (!MainTabsHelper.hasContactsOrFeedTab()) order.remove(Integer.valueOf(CONTACTS));
        if (MainTabsHelper.isProfileTabHidden()) order.remove(Integer.valueOf(PROFILE));
        return order;
    }

    public static int position(int slot) {
        return visible().indexOf(slot);
    }

    public static void swap(int first, int second) {
        List<Integer> order = all();
        int a = order.indexOf(first), b = order.indexOf(second);
        if (a < 0 || b < 0 || a == b) return;
        Collections.swap(order, a, b);
        StringBuilder saved = new StringBuilder();
        for (int id : order) {
            if (saved.length() > 0) saved.append(',');
            saved.append(id);
        }
        NekoConfig.getPreferences().edit().putString(KEY, saved.toString()).apply();
    }

    public static void reset() {
        NekoConfig.getPreferences().edit().remove(KEY).apply();
    }
}
