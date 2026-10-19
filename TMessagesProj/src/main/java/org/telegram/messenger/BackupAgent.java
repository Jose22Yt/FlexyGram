package org.telegram.messenger;

import android.app.backup.BackupAgentHelper;
import android.app.backup.BackupDataInput;
import android.app.backup.FullBackupDataOutput;
import android.os.ParcelFileDescriptor;
import java.io.IOException;

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
        // Consume/discard the entity instead of restoring any filesystem path.
        super.onRestoreFile(data, size, (java.io.File) null, type, mode, mtime);
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
