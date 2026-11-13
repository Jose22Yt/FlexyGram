/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.performance;

import java.util.Iterator;
import java.util.LinkedHashMap;

/** Storage-queue owned, single-use snapshots. The byte limit is serialized payload, not heap size. */
public final class WarmHistoryCache<T> {
    public static final long TTL_MS = 5000;
    private static final int MAX_ENTRIES = 2, MAX_BYTES = 512 * 1024;
    public static final class Revision {
        private final Object database;
        private final long changes, external, owner;
        public Revision(Object database, long changes, long external) {
            this(database, changes, external, 0);
        }
        public Revision(Object database, long changes, long external, long owner) {
            this.database = database; this.changes = changes; this.external = external; this.owner = owner;
        }
        public boolean same(Revision other) {
            return other != null && database == other.database && changes == other.changes && external == other.external && owner == other.owner;
        }
    }
    private static final class Entry<T> {
        T value; int count, bytes; long created; Revision revision;
    }
    private final LinkedHashMap<Long, Entry<T>> entries = new LinkedHashMap<>();
    private int bytes;
    public void trim(long now) {
        Iterator<Entry<T>> iterator = entries.values().iterator();
        while (iterator.hasNext()) {
            Entry<T> e = iterator.next();
            if (now < e.created || now - e.created >= TTL_MS) { bytes -= e.bytes; iterator.remove(); }
        }
    }
    public boolean contains(long dialog, int count, long now, Revision revision) {
        trim(now);
        Entry<T> e = entries.get(dialog);
        if (e != null && !e.revision.same(revision)) { clear(); return false; }
        return e != null && e.count == count;
    }
    public T take(long dialog, int count, long now, Revision revision) {
        if (!contains(dialog, count, now, revision)) return null;
        Entry<T> e = entries.remove(dialog); bytes -= e.bytes;
        return e.value;
    }
    public void put(long dialog, int count, long now, Revision revision, int cost, T value) {
        trim(now);
        if (revision == null || value == null || cost <= 0 || cost > MAX_BYTES / MAX_ENTRIES) return;
        Entry<T> old = entries.remove(dialog);
        if (old != null) bytes -= old.bytes;
        while (entries.size() >= MAX_ENTRIES || bytes + cost > MAX_BYTES) {
            Long first = entries.keySet().iterator().next(); bytes -= entries.remove(first).bytes;
        }
        Entry<T> e = new Entry<>(); e.value = value; e.count = count; e.created = now; e.revision = revision; e.bytes = cost;
        entries.put(dialog, e); bytes += cost;
    }
    public boolean isEmpty() { return entries.isEmpty(); }
    public void clear() { entries.clear(); bytes = 0; }
}
