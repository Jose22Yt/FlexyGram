/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.exteraless.player;

import java.text.Normalizer;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.regex.Pattern;
import org.telegram.messenger.MessageObject;

/** Session-only edits in audible order. No preference, profile, disk or network writes. */
public final class MusicQueueOrder {
    public static final int MAX_TRACKS = 5000;
    private static final Pattern MARKS = Pattern.compile("\\p{M}+");
    private MusicQueueOrder() { }
    public static boolean same(MessageObject a, MessageObject b) {
        return a != null && b != null && (a == b || a.getId() != 0
                && a.currentAccount == b.currentAccount && a.getDialogId() == b.getDialogId()
                && a.getId() == b.getId());
    }
    public static int indexOf(List<MessageObject> list, MessageObject item) {
        for (int i = 0; i < list.size(); i++) if (same(list.get(i), item)) return i;
        return -1;
    }
    public static ArrayList<MessageObject> audible(List<MessageObject> source, boolean forward) {
        ArrayList<MessageObject> result = new ArrayList<>(source);
        if (!forward) java.util.Collections.reverse(result);
        return result;
    }
    public static boolean enqueue(ArrayList<MessageObject> order, MessageObject playing, MessageObject item, boolean next) {
        if (playing == null || item == null || !item.isMusic() || playing.currentAccount != item.currentAccount
                || same(playing, item)) return false;
        int current = indexOf(order, playing), previous = indexOf(order, item);
        if (current < 0 || previous < 0 && order.size() >= MAX_TRACKS) return false;
        if (previous >= 0) order.remove(previous);
        current = indexOf(order, playing);
        // 'At end' means after the remaining tracks, even if the current track was last.
        order.add(next ? current + 1 : order.size(), item);
        return true;
    }
    public static boolean remove(ArrayList<MessageObject> order, MessageObject playing, MessageObject item) {
        int index = indexOf(order, item);
        if (index < 0 || same(playing, item)) return false;
        order.remove(index); return true;
    }
    public static boolean move(ArrayList<MessageObject> order, MessageObject playing, MessageObject item, MessageObject target) {
        int from = indexOf(order, item), to = indexOf(order, target);
        if (from < 0 || to < 0 || from == to || same(playing, item) || same(playing, target)) return false;
        order.add(to, order.remove(from)); return true;
    }
    public static String normalize(String text) {
        if (text == null) return "";
        return MARKS.matcher(Normalizer.normalize(text, Normalizer.Form.NFD)).replaceAll("").toLowerCase(Locale.ROOT).trim();
    }
    public static boolean matches(String indexed, String query) {
        return matches(indexed, query.split("\\s+"));
    }
    public static boolean matches(String indexed, String[] tokens) {
        for (String token : tokens) if (!indexed.contains(token)) return false;
        return true;
    }
}
