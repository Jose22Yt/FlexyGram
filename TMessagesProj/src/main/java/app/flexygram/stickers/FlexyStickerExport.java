/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.stickers;

import android.app.Activity;
import android.content.ContentResolver;
import android.content.Intent;
import android.net.Uri;
import android.provider.DocumentsContract;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.ApplicationLoader;
import org.telegram.messenger.FileLog;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.Components.BulletinFactory;
import java.io.*;
import java.lang.ref.WeakReference;
import java.util.concurrent.*;

/** One pending SAF export per fragment. The worker owns the source after a successful pick. */
public final class FlexyStickerExport {
    public static final int REQUEST_CODE = 0x4658;
    private static final ThreadPoolExecutor WORKER = new ThreadPoolExecutor(0, 1, 1, TimeUnit.SECONDS,
            new ArrayBlockingQueue<>(2), task -> {
                Thread thread = new Thread(task, "FlexyStickerExport");
                thread.setDaemon(true);
                return thread;
            }, new ThreadPoolExecutor.AbortPolicy());
    private File pending;

    /** True transfers ownership; a failed launch leaves the preview usable. */
    public boolean begin(BaseFragment owner, File source) {
        if (pending != null || source == null || !source.isFile() || owner.isFinished
                || owner.getParentActivity() == null || owner.getParentLayout() == null) return false;
        Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT)
                .addCategory(Intent.CATEGORY_OPENABLE).setType(FlexyStickerSpec.MIME)
                .putExtra(Intent.EXTRA_TITLE, "FlexySticker_" + System.currentTimeMillis() + ".webp");
        pending = source;
        try {
            owner.startActivityForResult(intent, REQUEST_CODE);
            return true;
        } catch (RuntimeException unavailable) {
            pending = null;
            FileLog.e(unavailable);
            report(owner, false);
            return false;
        }
    }

    public boolean onActivityResult(BaseFragment owner, int code, int result, Intent data) {
        if (code != REQUEST_CODE) return false;
        File source = pending;
        pending = null;
        if (source == null) return true;
        if (result != Activity.RESULT_OK || data == null || data.getData() == null) {
            source.delete();
            return true;
        }
        Uri destination = data.getData();
        if (!"content".equals(destination.getScheme())) {
            source.delete();
            report(owner, false);
            return true;
        }
        ContentResolver resolver = ApplicationLoader.applicationContext.getContentResolver();
        WeakReference<BaseFragment> reference = new WeakReference<>(owner);
        try {
            WORKER.execute(() -> {
                boolean ok = false;
                try {
                    copy(resolver, source, destination);
                    ok = true;
                } catch (Exception failed) {
                    FileLog.e(failed);
                    try { DocumentsContract.deleteDocument(resolver, destination); }
                    catch (Exception cleanupFailed) { FileLog.e(cleanupFailed); }
                } finally {
                    source.delete();
                }
                boolean success = ok;
                AndroidUtilities.runOnUIThread(() -> {
                    BaseFragment current = reference.get();
                    if (current != null) report(current, success);
                });
            });
        } catch (RejectedExecutionException busy) {
            source.delete();
            report(owner, false);
        }
        return true;
    }

    public void cancel() {
        if (pending != null) {
            pending.delete();
            pending = null;
        }
    }

    private static void copy(ContentResolver resolver, File source, Uri destination) throws IOException {
        try (InputStream input = new FileInputStream(source);
             OutputStream output = open(resolver, destination)) {
            if (output == null) throw new IOException("Document provider returned no output stream");
            byte[] buffer = new byte[8192];
            int read;
            while ((read = input.read(buffer)) != -1) output.write(buffer, 0, read);
            output.flush();
        }
    }

    private static OutputStream open(ContentResolver resolver, Uri destination) throws IOException {
        try {
            OutputStream output = resolver.openOutputStream(destination, "wt");
            if (output != null) return output;
        } catch (FileNotFoundException | IllegalArgumentException unsupportedMode) {
            // Some document providers support only write mode.
        }
        return resolver.openOutputStream(destination, "w");
    }

    private static void report(BaseFragment owner, boolean ok) {
        if (owner.isFinished || owner.getParentActivity() == null || !BulletinFactory.canShowBulletin(owner)) return;
        if (ok) {
            BulletinFactory.of(owner).createSimpleBulletin(R.drawable.msg_sticker_remix,
                    LocaleController.getString(R.string.FlexyStickerExported)).show();
        } else {
            BulletinFactory.of(owner).createErrorBulletin(LocaleController.getString(R.string.ErrorOccurred)).show();
        }
    }
}
