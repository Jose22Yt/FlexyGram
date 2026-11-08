package app.exteraless.player;

import android.text.TextUtils;

import org.telegram.SQLite.SQLiteCursor;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.FileLoader;
import org.telegram.messenger.FileLog;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.MediaController;
import org.telegram.messenger.MediaDataController;
import org.telegram.messenger.MessageObject;
import org.telegram.messenger.MessagesStorage;
import org.telegram.messenger.R;
import org.telegram.messenger.UserConfig;
import org.telegram.tgnet.NativeByteBuffer;
import org.telegram.tgnet.TLRPC;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.Components.BulletinFactory;

import java.io.File;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Locale;

public final class FlexyMusicLibrary {

    private FlexyMusicLibrary() {}

    public interface Callback {
        void onLoaded(ArrayList<MessageObject> music);
    }

    public static void loadAllDownloadedMusic(int account, Callback callback) {
        MessagesStorage storage = MessagesStorage.getInstance(account);
        storage.getStorageQueue().postRunnable(() -> {
            ArrayList<MessageObject> downloadedList = new ArrayList<>();
            HashSet<String> seenPaths = new HashSet<>();
            try {
                SQLiteCursor cursor = storage.getDatabase().queryFinalized(String.format(Locale.US,
                        "SELECT data, mid, uid FROM media_v4 WHERE mid > 0 AND type = %d ORDER BY date DESC LIMIT 500",
                        MediaDataController.MEDIA_MUSIC));
                while (cursor.next()) {
                    NativeByteBuffer data = cursor.byteBufferValue(0);
                    if (data != null) {
                        TLRPC.Message message = TLRPC.Message.TLdeserialize(data, data.readInt32(false), false);
                        data.reuse();
                        if (message != null && message.media != null && message.media.document != null) {
                            MessageObject mo = new MessageObject(account, message, false, false);
                            if (mo.isMusic()) {
                                File f = FileLoader.getInstance(account).getPathToMessage(message);
                                if (f != null && f.exists() && f.length() > 0) {
                                    downloadedList.add(mo);
                                    seenPaths.add(f.getAbsolutePath());
                                } else if (!TextUtils.isEmpty(message.attachPath)) {
                                    File af = new File(message.attachPath);
                                    if (af.exists() && af.length() > 0) {
                                        downloadedList.add(mo);
                                        seenPaths.add(af.getAbsolutePath());
                                    }
                                }
                            }
                        }
                    }
                }
                cursor.dispose();
            } catch (Throwable e) {
                FileLog.e(e);
            }

            try {
                File docDir = FileLoader.checkDirectory(FileLoader.MEDIA_DIR_DOCUMENT);
                scanDirectoryForAudio(account, docDir, downloadedList, seenPaths);
                File filesDir = FileLoader.checkDirectory(FileLoader.MEDIA_DIR_FILES);
                scanDirectoryForAudio(account, filesDir, downloadedList, seenPaths);
                File audioDir = FileLoader.checkDirectory(FileLoader.MEDIA_DIR_AUDIO);
                scanDirectoryForAudio(account, audioDir, downloadedList, seenPaths);
            } catch (Throwable e) {
                FileLog.e(e);
            }

            AndroidUtilities.runOnUIThread(() -> callback.onLoaded(downloadedList));
        });
    }

    private static void scanDirectoryForAudio(int account, File dir, ArrayList<MessageObject> list, HashSet<String> seenPaths) {
        if (dir == null || !dir.exists() || !dir.isDirectory()) return;
        File[] files = dir.listFiles();
        if (files == null) return;
        for (File f : files) {
            if (f.isFile() && f.length() > 1024) {
                String path = f.getAbsolutePath();
                if (seenPaths.contains(path)) continue;
                String name = f.getName().toLowerCase(Locale.ROOT);
                if (name.endsWith(".mp3") || name.endsWith(".m4a") || name.endsWith(".flac")
                        || name.endsWith(".ogg") || name.endsWith(".opus") || name.endsWith(".wav")) {
                    MessageObject mo = createMessageObjectForFile(account, f, list.size() + 1);
                    if (mo != null && mo.isMusic()) {
                        list.add(mo);
                        seenPaths.add(path);
                    }
                }
            }
        }
    }

    private static MessageObject createMessageObjectForFile(int account, File file, int id) {
        TLRPC.TL_message message = new TLRPC.TL_message();
        message.out = true;
        message.id = id;
        message.peer_id = new TLRPC.TL_peerUser();
        message.from_id = new TLRPC.TL_peerUser();
        message.peer_id.user_id = message.from_id.user_id = UserConfig.getInstance(account).getClientUserId();
        message.date = (int) (file.lastModified() / 1000);
        message.message = "";
        message.attachPath = file.getAbsolutePath();
        message.media = new TLRPC.TL_messageMediaDocument();
        message.media.flags |= 3;
        message.media.document = new TLRPC.TL_document();
        message.flags |= TLRPC.MESSAGE_FLAG_HAS_MEDIA | TLRPC.MESSAGE_FLAG_HAS_FROM_ID;
        message.dialog_id = 0;

        String ext = FileLoader.getFileExtension(file);
        message.media.document.id = 0;
        message.media.document.access_hash = 0;
        message.media.document.file_reference = new byte[0];
        message.media.document.date = message.date;
        message.media.document.mime_type = "audio/" + (!ext.isEmpty() ? ext : "mp3");
        message.media.document.size = file.length();
        message.media.document.dc_id = 0;

        TLRPC.TL_documentAttributeAudio attributeAudio = new TLRPC.TL_documentAttributeAudio();
        attributeAudio.voice = false;
        String baseName = file.getName();
        int dot = baseName.lastIndexOf('.');
        if (dot > 0) baseName = baseName.substring(0, dot);
        int dash = baseName.indexOf(" - ");
        if (dash > 0) {
            attributeAudio.performer = baseName.substring(0, dash).trim();
            attributeAudio.title = baseName.substring(dash + 3).trim();
            attributeAudio.flags |= 1 | 2;
        } else {
            attributeAudio.title = baseName.trim();
            attributeAudio.flags |= 1;
        }
        message.media.document.attributes.add(attributeAudio);
        return new MessageObject(account, message, false, false);
    }

    public static void openMusicTab(BaseFragment fragment, PlayerMiniView miniView) {
        if (fragment == null || fragment.getParentActivity() == null) return;
        MediaController mc = MediaController.getInstance();
        MessageObject playing = mc.getPlayingMessageObject();

        loadAllDownloadedMusic(fragment.getCurrentAccount(), list -> {
            if (fragment.getParentActivity() == null) return;
            if (list.isEmpty()) {
                if (playing != null && playing.isMusic()) {
                    Md3Player.open(fragment, miniView);
                } else {
                    BulletinFactory.of(fragment).createSimpleBulletin(
                            R.drawable.baseline_music_note_24,
                            LocaleController.getString(R.string.NoResult)
                    ).show();
                }
                return;
            }

            if (playing != null && playing.isMusic()) {
                MessageObject match = null;
                for (MessageObject mo : list) {
                    if (mo.getId() != 0 && mo.getId() == playing.getId() && mo.getDialogId() == playing.getDialogId()) {
                        match = mo;
                        break;
                    }
                }
                if (match == null) {
                    list.add(0, playing);
                    match = playing;
                }
                mc.setPlaylist(list, match, 0, false, null);
                Md3Player.open(fragment, miniView);
            } else {
                MessageObject first = list.get(0);
                mc.setPlaylist(list, first, 0, false, null);
                mc.playMessage(first);
                Md3Player.open(fragment, miniView);
            }
        });
    }
}
