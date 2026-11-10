/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.exteraless.player;

import androidx.recyclerview.widget.DiffUtil;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.MessageObject;
import org.telegram.messenger.Utilities;

/** Serial background index/filter/diff. UI only snapshots and publishes the latest request. */
final class MusicQueueSearch {
    static final class Result {
        final ArrayList<MessageObject> items;
        final DiffUtil.DiffResult changes;
        Result(ArrayList<MessageObject> items, DiffUtil.DiffResult changes) {
            this.items = items; this.changes = changes;
        }
    }
    private volatile int generation;
    private Runnable task;
    // Owned exclusively by searchQueue; never modified from UI.
    private long indexedVersion = -1;
    private ArrayList<String> index = new ArrayList<>();

    void cancel() {
        generation++;
        if (task != null) Utilities.searchQueue.cancelRunnable(task);
        task = null;
    }

    void submit(List<MessageObject> source, long version, List<MessageObject> oldItems,
                String query, Consumer<Result> publish) {
        cancel();
        final int ticket = generation;
        final ArrayList<MessageObject> snapshot = new ArrayList<>(source);
        final ArrayList<MessageObject> previous = new ArrayList<>(oldItems);
        task = () -> {
            if (ticket != generation) return;
            if (indexedVersion != version) {
                ArrayList<String> nextIndex = new ArrayList<>(snapshot.size());
                for (MessageObject item : snapshot) {
                    if (ticket != generation) return;
                    nextIndex.add(MusicQueueOrder.normalize(item.getMusicTitle()+"\n"+item.getMusicAuthor()+"\n"+item.getFileName()));
                }
                index = nextIndex; indexedVersion = version;
            }
            String[] tokens = MusicQueueOrder.normalize(query).split("\\s+");
            ArrayList<MessageObject> matches = new ArrayList<>();
            for (int i = 0; i < snapshot.size(); i++) {
                if (ticket != generation) return;
                if (MusicQueueOrder.matches(index.get(i), tokens)) matches.add(snapshot.get(i));
            }
            DiffUtil.DiffResult changes = DiffUtil.calculateDiff(new DiffUtil.Callback() {
                @Override public int getOldListSize() { return previous.size(); }
                @Override public int getNewListSize() { return matches.size(); }
                @Override public boolean areItemsTheSame(int oldPosition, int newPosition) {
                    return MusicQueueOrder.same(previous.get(oldPosition), matches.get(newPosition));
                }
                @Override public boolean areContentsTheSame(int oldPosition, int newPosition) {
                    return previous.get(oldPosition) == matches.get(newPosition);
                }
            });
            if (ticket != generation) return;
            AndroidUtilities.runOnUIThread(() -> {
                if (ticket != generation) return;
                task = null;
                publish.accept(new Result(matches, changes));
            });
        };
        Utilities.searchQueue.postRunnable(task);
    }
}
