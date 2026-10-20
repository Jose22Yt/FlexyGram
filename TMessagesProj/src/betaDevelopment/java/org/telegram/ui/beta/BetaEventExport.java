package org.telegram.ui.beta;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.nio.charset.StandardCharsets;

/** Called on one background executor, app-private synthetic observations only; no network/Logcat. */
final class BetaEventExport {
    private BetaEventExport() { }
    static boolean save(File files, NavigationEvents events, long exportId) {
        File folder = new File(new File(files, "beta-observer"), events.session() + "_" + exportId + ".partial");
        File complete = new File(folder.getParentFile(), events.session() + "_" + exportId);
        long count = 0;
        try {
            if (complete.exists() || !folder.mkdirs()) return false; // never overwrite an earlier observation
            try (Writer writer = new OutputStreamWriter(new FileOutputStream(new File(folder, "events.jsonl")), StandardCharsets.UTF_8)) {
                count = events.drainTo(writer);
            }
            try (Writer writer = new OutputStreamWriter(new FileOutputStream(new File(folder, "observer.json")), StandardCharsets.UTF_8)) {
                writer.write("{\"session_id\":\"" + events.session() + "\",\"export_id\":" + exportId + ",\"observer_lost_events\":" + events.lostEvents() + ",\"observer_abandoned_operations\":" + events.abandonedOperations() + ",\"records\":" + count
                        + ",\"event_endpoint\":\"beta_idle_predraw_frame_v1\",\"clock\":\"android_monotonic_ns\",\"source\":\"beta_local_synthetic_fixture\"}");
            }
            if (!folder.renameTo(complete))
                throw new java.io.IOException("Incomplete observation export");
            return true;
        } catch (Exception error) {
            events.exportFailed(count);
            // A .partial directory is never accepted as a completed export. No secret-bearing exceptions.
            return false;
        }
    }
}
