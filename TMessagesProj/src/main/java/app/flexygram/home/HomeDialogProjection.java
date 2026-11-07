/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.home;

import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.function.ToLongFunction;

/** UI-thread snapshots for Home only. Never remove or reorder the controller's dialogs. */
public final class HomeDialogProjection<T> {
    private final IdentityHashMap<ArrayList<T>, ArrayList<T>> snapshots = new IdentityHashMap<>();
    private final ToLongFunction<T> id;
    private long hidden;
    private boolean initialized;

    public HomeDialogProjection(ToLongFunction<T> id) { this.id = id; }
    public void invalidate() { snapshots.clear(); }

    public ArrayList<T> without(ArrayList<T> source, long hiddenId) {
        if(!initialized||hidden!=hiddenId){invalidate();hidden=hiddenId;initialized=true;}
        ArrayList<T> cached = snapshots.get(source);
        if (cached != null) return cached;
        ArrayList<T> copy = new ArrayList<>(source.size());
        for (T item : source) if (id.applyAsLong(item) != hiddenId) copy.add(item);
        snapshots.put(source, copy);
        return copy;
    }
}
