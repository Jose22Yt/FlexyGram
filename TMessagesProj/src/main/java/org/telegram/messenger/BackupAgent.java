package org.telegram.messenger;

import android.app.backup.BackupAgentHelper;
import android.app.backup.BackupDataInput;
import android.app.backup.FullBackupDataOutput;
import android.app.backup.FullRestoreDataInput;
import android.os.ParcelFileDescriptor;
import java.io.EOFException;
import java.io.IOException;
import java.io.InputStream;

/** Legacy class retained for binary compatibility, never registered by the diagnostic manifest.
 * No helpers are installed: framework key/value restore skips unknown helpers without writing
 * tokens, session files or preferences. Never reuse this agent for an authenticated variant;
 * a future settings-only transport must use SettingsBackupPolicy and a new helper identity.
 */
public class BackupAgent extends BackupAgentHelper {
    @Override
    public void onCreate() {
        if (DiagnosticPolicy.isIsolated()) return;
        // Deliberately no SharedPreferencesBackupHelper (including legacy token stores).
    }

    @Override
    public void onRestore(BackupDataInput data, int version, ParcelFileDescriptor state) {
        // Reject legacy key/value entities, even if this dormant agent is invoked directly.
    }

    @Override
    public void onRestoreFile(ParcelFileDescriptor data, long size, java.io.File destination,
                              int type, long mode, long mtime) throws IOException {
        discardEntity(data, size);
    }

    // API 36.1+ has a separate public callback. Do not rely on its default writer
    // or introduce app-side calls to this API on older Android versions.
    @android.annotation.SuppressLint("NewApi")
    @Override
    public void onRestoreFile(FullRestoreDataInput input) throws IOException {
        if (input == null) throw new IOException("Missing restore entity");
        discardEntity(input.getData(), input.getSize());
    }

    private static void discardEntity(ParcelFileDescriptor data, long size) throws IOException {
        if (size < 0) throw new IOException("Invalid restore entity size");
        // Directories and empty files have no payload; do not touch the descriptor.
        if (size == 0) return;
        if (data == null) throw new IOException("Missing restore entity data");
        // dup shares the stream position but has independent ownership. Closing the
        // stream closes ONLY our duplicate, never the framework's original descriptor.
        try (InputStream input = new ParcelFileDescriptor.AutoCloseInputStream(
                ParcelFileDescriptor.dup(data.getFileDescriptor()))) {
            byte[] buffer = new byte[8192];
            long remaining = size;
            while (remaining > 0) {
                int read = input.read(buffer, 0, (int) Math.min(buffer.length, remaining));
                if (read < 0) throw new EOFException("Truncated restore entity");
                if (read == 0) throw new IOException("Restore entity made no progress");
                remaining -= read;
            }
        }
    }

    @Override
    public void onFullBackup(FullBackupDataOutput data) {
        // No automatic filesystem backup, including session databases and native auth keys.
    }

    public static void requestBackup() {
        if (DiagnosticPolicy.isIsolated()) return;
        // No credential backup scheduling, independently of DiagnosticPolicy.
    }
}
