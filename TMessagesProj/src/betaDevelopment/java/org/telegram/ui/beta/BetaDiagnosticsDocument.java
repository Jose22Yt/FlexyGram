package org.telegram.ui.beta;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

/** Explicit background export only. Never reads sessions, preferences, Logcat or arbitrary files. */
final class BetaDiagnosticsDocument {
    private static final long MAX_TOTAL = 16L * 1024 * 1024;
    private static final Pattern SESSION = Pattern.compile("b[0-9a-z]+_[0-9a-z]+");
    private static final Pattern NAME = Pattern.compile("b[0-9a-z]+_[0-9a-z]+_[1-9][0-9]*\\.zip");
    private static final Pattern HEADER = Pattern.compile(
        "\\{\"session_id\":\"(b[0-9a-z]+_[0-9a-z]+)\",\"export_id\":([1-9][0-9]*),"
        + "\"observer_lost_events\":([0-9]+),\"observer_abandoned_operations\":([0-9]+),\"records\":([0-9]+),"
        + "\"event_endpoint\":\"beta_idle_predraw_frame_v1\",\"clock\":\"android_monotonic_ns\","
        + "\"source\":\"beta_local_synthetic_fixture\"\\}");
    private static final Pattern EVENT = Pattern.compile(
        "\\{\"id\":\"(b[0-9a-z]+_[0-9a-z]+)_[0-9a-z]+\","
        + "\"op\":\"(?:startup|chat_open|chat_close|rapid_tap|transition_interrupt|theme_light|theme_dark)\","
        + "\"phase\":\"(?:request|accepted|presented|cancelled|timeout)\","
        + "\"timestamp_ns\":([0-9]+),\"clock\":\"android_monotonic_ns\"\\}");

    private BetaDiagnosticsDocument() { }

    static boolean validName(String name) {
        return name != null && name.length() <= 100 && NAME.matcher(name).matches();
    }

    private static void require(boolean value) throws IOException {
        if (!value) throw new IOException("Synthetic diagnostic export unavailable");
    }

    private static File child(File parent, String name) throws IOException {
        File result = new File(parent.getCanonicalFile(), name);
        require(result.getAbsoluteFile().equals(result.getCanonicalFile()));
        return result;
    }

    private static byte[] read(File file, int limit) throws IOException {
        require(file.isFile() && file.length() <= limit);
        try (FileInputStream input = new FileInputStream(file);
             ByteArrayOutputStream bytes = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int count;
            while ((count = input.read(buffer)) != -1) {
                require(bytes.size() + (long) count <= limit);
                bytes.write(buffer, 0, count);
            }
            return bytes.toByteArray();
        }
    }

    private static long number(String text) throws IOException {
        try {
            long value = Long.parseLong(text);
            require(value >= 0);
            return value;
        } catch (NumberFormatException invalid) {
            throw new IOException("Synthetic diagnostic counter invalid");
        }
    }

    private static void entry(ZipOutputStream zip, String name, byte[] bytes) throws IOException {
        ZipEntry item = new ZipEntry(name);
        item.setTime(0); // no wall-clock/device/owner metadata
        zip.putNextEntry(item);
        zip.write(bytes);
        zip.closeEntry();
    }

    /** First persist through the existing consumer; failed/cancelled external saves cannot drain again. */
    static File prepare(File files, NavigationEvents events, long id,
                        ProbeState.Value probe, ProbeState.Outcome outcome) throws IOException {
        require(SESSION.matcher(events.session()).matches() && id >= 1 && id <= 100);
        require(BetaEventExport.save(files, events, id));
        File root = files.getCanonicalFile();
        File observations = child(root, "beta-observer");
        File directory = child(root, "beta-mobile-export");
        require(directory.isDirectory() || directory.mkdir());
        File complete = child(directory, events.session() + "_" + id + ".zip");
        File partial = child(directory, complete.getName() + ".partial");
        require(!complete.exists() && partial.createNewFile());
        boolean done = false;
        try {
            long total = 0, previousTime = -1, previousLost = -1, previousAbandoned = -1;
            try (FileOutputStream file = new FileOutputStream(partial);
                 ZipOutputStream zip = new ZipOutputStream(file)) {
                for (long batch = 1; batch <= id; batch++) {
                    String name = events.session() + "_" + batch;
                    File folder = child(observations, name);
                    byte[] header = read(child(folder, "observer.json"), 4096);
                    byte[] records = read(child(folder, "events.jsonl"), 2 * 1024 * 1024);
                    Matcher match = HEADER.matcher(new String(header, StandardCharsets.UTF_8));
                    require(match.matches() && events.session().equals(match.group(1))
                            && number(match.group(2)) == batch);
                    long lost = number(match.group(3)), abandoned = number(match.group(4));
                    require(lost >= previousLost && abandoned >= previousAbandoned);
                    previousLost = lost; previousAbandoned = abandoned;
                    String text = new String(records, StandardCharsets.UTF_8);
                    String[] lines = text.isEmpty() ? new String[0] : text.split("\n", -1);
                    long count = text.isEmpty() ? 0 : lines.length - 1;
                    require(text.isEmpty() || lines[lines.length - 1].isEmpty());
                    require(number(match.group(5)) == count && count <= 4096);
                    for (int index = 0; index < count; index++) {
                        Matcher event = EVENT.matcher(lines[index]);
                        require(event.matches() && events.session().equals(event.group(1)));
                        long stamp = number(event.group(2));
                        require(stamp >= previousTime);
                        previousTime = stamp;
                    }
                    total += header.length + (long) records.length;
                    require(total <= MAX_TOTAL);
                    entry(zip, name + "/observer.json", header);
                    entry(zip, name + "/events.jsonl", records);
                }
                // Only enums defined by the existing local probe: never exception text or module output.
                String probeName = probe == null ? "UNKNOWN" : probe.name();
                String outcomeName = outcome == null ? "UNKNOWN" : outcome.name();
                String metadata = "{\"schema\":1,\"kind\":\"beta_mobile_synthetic_observations\","
                        + "\"probe\":\"" + probeName + "\",\"probe_outcome\":\"" + outcomeName + "\","
                        + "\"runtime_certified\":false}";
                entry(zip, "diagnostic.json", metadata.getBytes(StandardCharsets.UTF_8));
                zip.finish(); zip.flush(); file.getFD().sync();
            }
            require(partial.length() <= MAX_TOTAL + 1024 * 1024 && partial.renameTo(complete));
            done = true;
            return complete;
        } finally {
            if (!done) partial.delete(); // never delete source batches or completed/cancelled snapshots
        }
    }

    /** Copies only a completed snapshot; caller owns/closes the user-selected stream. */
    static void copy(File files, String name, OutputStream output) throws IOException {
        require(validName(name) && output != null);
        File archive = child(child(files.getCanonicalFile(), "beta-mobile-export"), name);
        require(archive.isFile() && archive.length() > 0 && archive.length() <= MAX_TOTAL + 1024 * 1024);
        try (FileInputStream input = new FileInputStream(archive)) {
            byte[] buffer = new byte[16384];
            int count;
            while ((count = input.read(buffer)) != -1) {
                require(!Thread.currentThread().isInterrupted());
                output.write(buffer, 0, count);
            }
        }
    }
}
