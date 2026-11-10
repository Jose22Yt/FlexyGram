/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.exteraless.player;

import android.content.Context;
import android.widget.Toast;
import android.view.View;
import android.view.ViewGroup;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.MediaController;
import org.telegram.messenger.MessageObject;
import org.telegram.messenger.R;
import org.telegram.ui.Components.ItemOptions;

public final class MusicQueueActions {
    public static final int NEXT = 154, LAST = 155;
    private MusicQueueActions() { }
    public static boolean eligible(MessageObject item) {
        if (item == null || !item.isMusic() || item.scheduled || item.isVoiceOnce() || item.isRoundOnce()) return false;
        MessageObject playing = MediaController.getInstance().getPlayingMessageObject();
        return (playing == null || playing.isMusic() && playing.currentAccount == item.currentAccount)
                && !MusicQueueOrder.same(item, playing);
    }
    public static void enqueue(Context context, MessageObject item, boolean next) {
        boolean ok = eligible(item) && MediaController.getInstance().enqueueMusic(item, next);
        Toast.makeText(context, LocaleController.getString(ok ? R.string.FlexyQueueAdded : R.string.FlexyQueueEditFailed), Toast.LENGTH_SHORT).show();
    }
    public static void add(ItemOptions options, Context context, MessageObject item) {
        if (!eligible(item)) return;
        options.add(R.drawable.player_new_order, LocaleController.getString(R.string.FlexyQueueNext), () -> enqueue(context, item, true));
        options.add(R.drawable.msg_add, LocaleController.getString(R.string.FlexyQueueLast), () -> enqueue(context, item, false));
    }
    public static boolean showRowMenu(Context context, ViewGroup host, View anchor, MessageObject item) {
        if (item == null || MusicQueueOrder.same(item,MediaController.getInstance().getPlayingMessageObject())) return false;
        ItemOptions options=ItemOptions.makeOptions(host,null,anchor,true);
        add(options,context,item);
        options.add(R.drawable.msg_delete,LocaleController.getString(R.string.FlexyQueueRemove),()->MediaController.getInstance().removeMusicFromQueue(item));
        options.show();return true;
    }
}
