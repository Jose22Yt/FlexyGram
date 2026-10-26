/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.files.core;

import java.io.*;
import java.nio.ByteBuffer;
import java.nio.CharBuffer;
import java.nio.charset.*;
import java.util.*;
import java.util.zip.*;

/** A read-only capability for ONE selected local document. Construct/use on a cancellable worker.
 * No directory scanning, threads, services, native decoder or static file/cache initialization. */
public final class SelectedDocument implements Closeable {
    public static final long MAX_ARCHIVE = 128L * 1024 * 1024;
    public static final int MAX_ENTRIES = 10000, MAX_ENTRY = 8 * 1024 * 1024, MAX_TEXT = 256 * 1024;
    private static final long MAX_SESSION_BYTES = 64L * 1024 * 1024;
    private final File selected;
    private final LinkedHashMap<String, ZipEntry> zipEntries = new LinkedHashMap<>();
    private ZipFile zip;
    private volatile boolean closed;
    private long decoded;
    private final boolean archive;

    public static final class Entry {
        public final String path;
        public final boolean directory;
        public final long size, compressedSize;
        private Entry(String path, boolean directory, long size, long compressed) {
            this.path = path; this.directory = directory; this.size = size; this.compressedSize = compressed;
        }
    }
    public static final class Rejected extends IOException {
        public final String code;
        public Rejected(String code) { super(code); this.code = code; }
    }
    public SelectedDocument(File exactFile) throws IOException {
        if (Thread.currentThread().isInterrupted()) throw new InterruptedIOException("CANCELED");
        selected = exactFile.getCanonicalFile();
        if (!selected.isFile()) throw new Rejected("NOT_LOCAL");
        if (selected.length() > MAX_ARCHIVE) throw new Rejected("FILE_LIMIT");
        int magic;
        try (DataInputStream input = new DataInputStream(new FileInputStream(selected))) {
            magic = selected.length() >= 4 ? input.readInt() : 0;
        }
        archive = magic == 0x504b0304 || magic == 0x504b0506 || magic == 0x504b0708;
        if (archive) {
            // Validate the central directory budget BEFORE ZipFile allocates its index.
            preflightZip(selected);
            ZipFile opened = new ZipFile(selected);
            try {
                Enumeration<? extends ZipEntry> entries = opened.entries();
                long deadline = System.nanoTime() + 10_000_000_000L;
                while (entries.hasMoreElements()) {
                    check(deadline);
                    if (zipEntries.size() >= MAX_ENTRIES) throw new Rejected("ENTRY_LIMIT");
                    ZipEntry entry = entries.nextElement();
                    String path = safePath(entry.getName());
                    if (zipEntries.put(path, entry) != null) throw new Rejected("DUPLICATE_PATH");
                    if (entry.getSize() > Math.max(1, entry.getCompressedSize()) * 200L)
                        throw new Rejected("COMPRESSION_LIMIT");
                }
                zip = opened;
            } catch (IOException | RuntimeException failure) { opened.close(); throw failure; }
        }
    }
    public boolean isArchive() { return archive; }
    public String name() { return selected.getName(); }
    public long size() { return selected.length(); }
    public List<Entry> entries() throws IOException {
        requireOpen();
        ArrayList<Entry> result = new ArrayList<>(zipEntries.size());
        long deadline = System.nanoTime() + 10_000_000_000L;
        for (Map.Entry<String, ZipEntry> item : zipEntries.entrySet()) {
            check(deadline); ZipEntry e = item.getValue();
            result.add(new Entry(item.getKey(), e.isDirectory(), e.getSize(), e.getCompressedSize()));
        }
        return Collections.unmodifiableList(result);
    }
    public byte[] read(String entryPath, int limit) throws IOException {
        requireOpen();
        if (limit < 0 || limit > MAX_ENTRY) throw new Rejected("READ_LIMIT");
        if (!archive) {
            if (entryPath != null) throw new Rejected("UNKNOWN_ENTRY");
            try (InputStream input = new FileInputStream(selected)) { return bounded(input, selected.length(), -1, limit); }
        }
        ZipEntry entry = zipEntries.get(entryPath);
        if (entry == null || entry.isDirectory()) throw new Rejected("UNKNOWN_ENTRY");
        ZipFile reader = zip;
        if (reader == null) throw new Rejected("CLOSED");
        try (InputStream input = reader.getInputStream(entry)) { return bounded(input, entry.getSize(), entry.getCrc(), limit); }
        catch (IllegalStateException disposed) { throw new Rejected("CLOSED"); }
    }
    private byte[] bounded(InputStream input, long expected, long crc, int limit) throws IOException {
        if (expected > limit) throw new Rejected("READ_LIMIT");
        ByteArrayOutputStream output = new ByteArrayOutputStream((int) Math.max(0, Math.min(32768, expected)));
        byte[] buffer = new byte[8192]; CRC32 checksum = new CRC32();
        long deadline = System.nanoTime() + 10_000_000_000L;
        int count, total = 0;
        while ((count = input.read(buffer)) != -1) {
            check(deadline);
            if (count > limit - total || count > MAX_SESSION_BYTES - decoded) throw new Rejected("READ_LIMIT");
            total += count; decoded += count; checksum.update(buffer, 0, count); output.write(buffer, 0, count);
        }
        check(deadline);
        if (expected >= 0 && expected != total || crc >= 0 && checksum.getValue() != crc) throw new Rejected("CORRUPT");
        return output.toByteArray();
    }
    /** Writes a NEW archive to a caller-owned destination; never opens the selected file for writing.
     * Entries become ordinary files/directories; no filesystem links or executable actions are created. */
    public void writeZipCopy(OutputStream destination, String updatedEntry, byte[] replacement) throws IOException {
        requireOpen();
        ZipEntry updated = zipEntries.get(updatedEntry);
        if (!archive || updated == null || updated.isDirectory()) throw new Rejected("UNKNOWN_ENTRY");
        if (replacement.length > MAX_ENTRY) throw new Rejected("READ_LIMIT");
        long deadline = System.nanoTime() + 30_000_000_000L;
        // The caller retains ownership of its SAF stream, including cleanup/transaction failure.
        ZipOutputStream output = new ZipOutputStream(new FilterOutputStream(destination) {
            @Override public void close() throws IOException { flush(); }
        });
        try {
            for (Map.Entry<String, ZipEntry> item : zipEntries.entrySet()) {
                check(deadline); ZipEntry original = item.getValue();
                String name = item.getKey() + (original.isDirectory() ? "/" : "");
                ZipEntry copy = new ZipEntry(name);
                if (original.getTime() >= 0) copy.setTime(original.getTime());
                output.putNextEntry(copy);
                if (!original.isDirectory()) {
                    byte[] bytes = item.getKey().equals(updatedEntry) ? replacement : read(item.getKey(), MAX_ENTRY);
                    output.write(bytes);
                }
                output.closeEntry();
            }
            output.finish();
        } finally { output.close(); }
    }
    public static String safePath(String name) throws Rejected {
        if (name == null || name.isEmpty() || name.length() > 1024 || name.indexOf('\0') >= 0
                || name.startsWith("/") || name.startsWith("\\") || name.indexOf('\\') >= 0 || name.indexOf(':') >= 0)
            throw new Rejected("UNSAFE_PATH");
        String path = name.endsWith("/") ? name.substring(0, name.length() - 1) : name;
        String[] segments = path.split("/", -1);
        if (segments.length > 16) throw new Rejected("PATH_DEPTH");
        for (String segment : segments) if (segment.isEmpty() || segment.equals(".") || segment.equals("..")) throw new Rejected("UNSAFE_PATH");
        return path;
    }
    private static int u16(byte[] data, int i) { return (data[i] & 255) | (data[i + 1] & 255) << 8; }
    private static long u32(byte[] data, int i) { return (long) u16(data, i) | (long) u16(data, i + 2) << 16; }
    private static void preflightZip(File file) throws IOException {
        try (RandomAccessFile input = new RandomAccessFile(file, "r")) {
            long size = input.length();
            byte[] tail = new byte[(int) Math.min(65557, size)];
            input.seek(size - tail.length); input.readFully(tail);
            for (int i = tail.length - 22; i >= 0; i--) {
                if (u32(tail, i) != 0x06054b50L || i + 22 + u16(tail, i + 20) != tail.length) continue;
                if (u16(tail, i + 4) != 0 || u16(tail, i + 6) != 0
                        || u16(tail, i + 8) != u16(tail, i + 10)) throw new Rejected("MULTI_DISK");
                int count = u16(tail, i + 10); long central = u32(tail, i + 12), offset = u32(tail, i + 16);
                if (count > MAX_ENTRIES || central > 4 * 1024 * 1024L || offset + central > size - tail.length + i)
                    throw new Rejected("INDEX_LIMIT");
                return;
            }
            throw new Rejected("CORRUPT");
        }
    }
    private void requireOpen() throws IOException { if (closed) throw new Rejected("CLOSED"); }
    private void check(long deadline) throws IOException {
        requireOpen();
        if (Thread.currentThread().isInterrupted()) throw new InterruptedIOException("CANCELED");
        if (System.nanoTime() > deadline) throw new Rejected("TIME_LIMIT");
    }
    @Override public void close() throws IOException {
        if (closed) return;
        closed = true;
        ZipFile previous = zip; zip = null;
        if (previous != null) previous.close();
        // Immutable after construction. An in-flight worker may still be iterating; its
        // next cancellation check stops it, and the session then releases this bounded index.
    }

    public static final class Text {
        public final String value, encoding, newline;
        private final Charset charset;
        private final byte[] bom;
        private Text(String value, Charset charset, byte[] bom) {
            this.value = value; this.charset = charset; this.encoding = charset.name(); this.bom = bom;
            int crlf = 0, lf = 0, cr = 0;
            for (int i = 0; i < value.length(); i++) {
                char c = value.charAt(i);
                if (c == '\r') { if (i + 1 < value.length() && value.charAt(i + 1) == '\n') { crlf++; i++; } else cr++; }
                else if (c == '\n') lf++;
            }
            newline = (crlf > 0 ? 1 : 0) + (lf > 0 ? 1 : 0) + (cr > 0 ? 1 : 0) > 1 ? "MIXED" : crlf > 0 ? "CRLF" : cr > 0 ? "CR" : "LF";
        }
        public byte[] encode(String edited) throws IOException {
            if (edited.length() > MAX_TEXT) throw new Rejected("TEXT_LIMIT");
            ByteBuffer encoded;
            try { encoded = charset.newEncoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).encode(CharBuffer.wrap(edited)); }
            catch (CharacterCodingException invalid) { throw new Rejected("ENCODING"); }
            if (encoded.remaining() > MAX_TEXT - bom.length) throw new Rejected("TEXT_LIMIT");
            byte[] result = new byte[bom.length + encoded.remaining()]; System.arraycopy(bom, 0, result, 0, bom.length); encoded.get(result, bom.length, encoded.remaining());
            return result;
        }
    }
    public static Text text(byte[] bytes) throws IOException {
        if (bytes.length > MAX_TEXT) throw new Rejected("TEXT_LIMIT");
        Charset charset = StandardCharsets.UTF_8; int skip = 0;
        if (bytes.length >= 3 && bytes[0] == (byte) 0xef && bytes[1] == (byte) 0xbb && bytes[2] == (byte) 0xbf) skip = 3;
        else if (bytes.length >= 2 && bytes[0] == (byte) 0xff && bytes[1] == (byte) 0xfe) { charset = StandardCharsets.UTF_16LE; skip = 2; }
        else if (bytes.length >= 2 && bytes[0] == (byte) 0xfe && bytes[1] == (byte) 0xff) { charset = StandardCharsets.UTF_16BE; skip = 2; }
        String value;
        try { value = charset.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes, skip, bytes.length - skip)).toString(); }
        catch (CharacterCodingException invalid) { throw new Rejected("ENCODING"); }
        if (value.indexOf('\0') >= 0) throw new Rejected("BINARY");
        int lines = 1; for (int i = 0; i < value.length(); i++) if (value.charAt(i) == '\n' && ++lines > 20000) throw new Rejected("LINE_LIMIT");
        return new Text(value, charset, Arrays.copyOf(bytes, skip));
    }
}
