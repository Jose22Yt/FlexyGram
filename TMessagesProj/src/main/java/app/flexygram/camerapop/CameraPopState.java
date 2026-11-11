/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.camerapop;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

/** Account-local, UI-thread state. Stores no message text or peer names. */
public final class CameraPopState {
    public static final int QUEUE_LIMIT = 3;
    public static final class Pending {
        public final long dialog;
        public int message, received;
        public long topic, due;
        Pending(long dialog, int message, long topic, long due) {
            this.dialog = dialog; this.message = message; this.received = message; this.topic = topic; this.due = due;
        }
    }
    private final Map<Long, Pending> entries = new HashMap<>();
    private final ArrayList<Long> queue = new ArrayList<>();

    public boolean incoming(long dialog, int message, long topic, long now, long interval) {
        if (dialog == 0 || message <= 0) return false;
        Pending old = entries.get(dialog);
        if (old != null && old.received >= message) return false;
        // New messages do not postpone the first pending reminder indefinitely.
        long due = old != null && old.due > 0 ? old.due : now + interval;
        Pending next=new Pending(dialog, old==null?message:Math.max(message,old.message), topic, due);
        next.received=message;entries.put(dialog,next);
        return true;
    }
    /** Restoring native unread state must not consume a live arrival's dedup token. */
    public boolean seed(long dialog,int message,long now,long interval) {
        if(dialog==0 || message<=0)return false;
        Pending old=entries.get(dialog);
        if(old!=null && old.message>=message)return false;
        Pending next=new Pending(dialog,message,old==null?0:old.topic,
                old!=null && old.due>0?old.due:now+interval);
        next.received=old==null?0:old.received;entries.put(dialog,next);return true;
    }
    public Pending get(long dialog) { return entries.get(dialog); }
    public ArrayList<Pending> pending() { return new ArrayList<>(entries.values()); }
    public void read(long dialog) {
        Pending p = entries.get(dialog);
        if (p != null) {p.due = 0;p.received=Math.max(p.received,p.message);} // Retain dedup after reading.
        queue.remove(dialog);
    }
    public void defer(long dialog, long due) {
        Pending p = entries.get(dialog);
        if (p != null && p.due > 0) p.due = due;
    }
    public void retain(Set<Long> selected) {
        entries.keySet().retainAll(selected); queue.retainAll(selected);
    }
    public void enqueue(long dialog) {
        if (queue.contains(dialog)) return;
        if (queue.size() == QUEUE_LIMIT) queue.remove(0);
        queue.add(dialog);
    }
    public long poll() { return queue.isEmpty() ? 0 : queue.remove(0); }
    public void clearQueue() { queue.clear(); }
    public void clear() { entries.clear(); queue.clear(); }
    public long nextDue() {
        long next = Long.MAX_VALUE;
        for (Pending p : entries.values()) if (p.due > 0) next = Math.min(next, p.due);
        return next;
    }
    public Set<String> save() {
        int read=0;for(Pending p:entries.values())if(p.due==0)read++;
        if(read>512) {
            java.util.Iterator<Pending> it=entries.values().iterator();
            while(it.hasNext() && read>512)if(it.next().due==0){it.remove();read--;}
        }
        Set<String> saved = new HashSet<>();
        for (Pending p : entries.values()) saved.add(p.dialog + ":" + p.message + ":" + p.topic + ":" + p.due + ":" + p.received);
        return saved;
    }
    public void restore(Set<String> saved, Set<Long> selected) {
        restore(saved,selected,false);
    }
    public void restore(Set<String> saved, Set<Long> selected,boolean all) {
        clear();
        for (String value : saved) {
            try {
                String[] fields = value.split(":");
                if (fields.length != 4 && fields.length != 5) continue;
                long dialog = Long.parseLong(fields[0]); int message = Integer.parseInt(fields[1]);
                long topic = Long.parseLong(fields[2]), due = Long.parseLong(fields[3]);
                int received=fields.length==5?Integer.parseInt(fields[4]):message;
                if ((all || selected.contains(dialog)) && message > 0 && due >= 0 && received>=0 && received<=message) {
                    Pending p=new Pending(dialog,message,topic,due);p.received=received;entries.put(dialog,p);
                }
            } catch (NumberFormatException ignored) { /* Discard corrupt persisted records. */ }
        }
    }
    public static boolean quiet(int minute, int start, int end) {
        return start == end || (start < end ? minute >= start && minute < end : minute >= start || minute < end);
    }
}
