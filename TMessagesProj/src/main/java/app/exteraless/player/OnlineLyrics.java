package app.exteraless.player;

import android.text.TextUtils;
import android.util.LruCache;

import org.json.JSONArray;
import org.json.JSONObject;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.ApplicationLoader;
import org.telegram.messenger.BuildVars;
import org.telegram.messenger.DispatchQueue;
import org.telegram.messenger.FileLog;
import org.telegram.messenger.Utilities;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import android.os.SystemClock;
import android.util.AtomicFile;
import java.text.Normalizer;
import java.util.Locale;
import java.util.regex.Pattern;

public final class OnlineLyrics {

    public static final int OK = 0;
    public static final int NOT_FOUND = 1;
    public static final int ERROR = 2;

    public static final class Request {
        private volatile Callback callback;
        private Request(Callback callback) { this.callback = callback; }
        public void cancel() { callback = null; }
        private void deliver(Lyrics lyrics, int status) {
            Callback value = callback; callback = null;
            if (value != null) value.onResult(lyrics, status);
        }
    }

    public interface Callback {
        void onResult(Lyrics lyrics, int status);
    }

    public static final class Query {
        public final String artist;
        public final String title;
        public final String album;
        public final int duration;

        public Query(String artist, String title, String album, int duration) {
            String a = clean(artist);
            String t = clean(title);
            if (t != null) {
                t = AUDIO_EXT.matcher(t).replaceFirst("").replace('_', ' ').trim();
            }
            if (TextUtils.isEmpty(a) && t != null) {
                int dash = t.indexOf(" - ");
                if (dash > 0) {
                    a = t.substring(0, dash).trim();
                    t = t.substring(dash + 3).trim();
                }
            }
            this.artist = a;
            this.title = stripDecorations(t);
            this.album = clean(album);
            this.duration = duration;
        }

        public String key() {
            return (artist == null ? "" : artist.toLowerCase(Locale.ROOT)) + "\u0001" + (title == null ? "" : title.toLowerCase(Locale.ROOT)) + "\u0001" + (album == null ? "" : album.toLowerCase(Locale.ROOT)) + "\u0001" + duration;
        }

        public boolean valid() {
            return !TextUtils.isEmpty(title);
        }
    }

    private static final class Found {
        final Lyrics lyrics;

        Found(Lyrics lyrics) {
            this.lyrics = lyrics;
        }
    }

    private static final String LRCLIB = "https://lrclib.net/api/";
    private static final String LRCMUX = "https://api.lrcmux.dev/get";
    private static final String LRCLIB_NAME = "LRCLIB";
    private static final int CACHE_VERSION = 4;
    private static final int MAX_RESPONSE_BYTES = 1024 * 1024;
    private static final long MISSING_TTL_MS = 15 * 60_000L;
    private static final int MAX_DURATION_DIFF = 3;
    private static final int MAX_FALLBACK_DURATION_DIFF = 5;
    private static final int ALIGN_WINDOW = 4;
    private static final float MIN_ALIGNED = 0.9f;
    private static final Pattern NOT_WORD = Pattern.compile("[^\\p{L}\\p{N}]+");
    private static final Pattern AUDIO_EXT = Pattern.compile("\\.(mp3|m4a|flac|ogg|oga|opus|wav|aac|alac|wma)$", Pattern.CASE_INSENSITIVE);
    private static final Pattern DECORATION = Pattern.compile("\\s*[(\\[][^)\\]]*(official|lyric|video|audio|visualizer|remaster|hq|hd)[^)\\]]*[)\\]]", Pattern.CASE_INSENSITIVE);
    private static final DispatchQueue queue = new DispatchQueue("lyrics");
    private static final LruCache<String, Lyrics> memory = new LruCache<>(24);
    private static final LruCache<String, Long> missing = new LruCache<>(64);
    private static final ThreadLocal<String> currentRequest = new ThreadLocal<>();
    private static final HashMap<String, ArrayList<Request>> pending = new HashMap<>();

    private OnlineLyrics() {
    }

    private static String clean(String s) {
        if (s == null) {
            return null;
        }
        s = s.trim();
        return s.isEmpty() ? null : s;
    }

    private static String stripDecorations(String s) {
        if (s == null) {
            return null;
        }
        String out = DECORATION.matcher(s).replaceAll("").trim();
        return out.isEmpty() ? s : out;
    }

    public static Lyrics cached(Query query) {
        return memory.get(query.key());
    }

    public static boolean knownMissing(Query query) {
        Long until = missing.get(query.key());
        if (until == null) return false;
        if (SystemClock.elapsedRealtime() < until) return true;
        missing.remove(query.key()); return false;
    }

    public static void loadCached(Query query, Callback callback) {
        String key = query.key();
        Lyrics hit = memory.get(key);
        if (hit != null) {
            callback.onResult(hit, OK);
            return;
        }
        queue.postRunnable(() -> {
            Lyrics disk = readDisk(key);
            AndroidUtilities.runOnUIThread(() -> {
                if (disk != null) {
                    memory.put(key, disk);
                }
                callback.onResult(disk, disk != null ? OK : NOT_FOUND);
            });
        });
    }

    public static Request fetch(Query query, Callback callback) {
        Request request = new Request(callback);
        if (query == null || !query.valid()) { AndroidUtilities.runOnUIThread(() -> request.deliver(null, NOT_FOUND)); return request; }
        String key = query.key();
        Lyrics hit = memory.get(key);
        if (hit != null) { AndroidUtilities.runOnUIThread(() -> request.deliver(hit, OK)); return request; }
        synchronized (pending) {
            ArrayList<Request> listeners = pending.get(key);
            if (listeners != null) { listeners.add(request); return request; }
            listeners = new ArrayList<>(); listeners.add(request); pending.put(key, listeners);
        }
        queue.postRunnable(() -> {
            synchronized (pending) {
                ArrayList<Request> listeners = pending.get(key);
                boolean active = false;
                if (listeners != null) for (Request listener : listeners) active |= listener.callback != null;
                if (!active) { pending.remove(key); return; }
            }
            currentRequest.set(key);
            try {
                Lyrics result = readDisk(key);
                int status = OK;
                if (result == null) {
                    boolean failed = false;
                    Found primary = null;
                    try {
                        primary = requestLrclib(query);
                    } catch (Throwable e) {
                        FileLog.e(e);
                        failed = true;
                    }
                    if (primary != null && (primary.lyrics.synced || primary.lyrics.instrumental)) {
                        result = primary.lyrics;
                    } else {
                        Found fallback = null;
                        try {
                            fallback = requestLrcmux(query);
                        } catch (Throwable e) {
                            FileLog.e(e);
                            failed = true;
                        }
                        if (fallback != null && (fallback.lyrics.synced || primary == null)) {
                            result = fallback.lyrics;
                            if (primary != null && fallback.lyrics.synced) {
                                Lyrics punctuated = punctuate(fallback.lyrics, primary.lyrics);
                                if (punctuated != null) {
                                    result = punctuated;
                                }
                            }
                        } else if (primary != null) {
                            result = primary.lyrics;
                        }
                    }
                    if (result != null) {
                        writeDisk(key, result);
                    } else {
                        status = failed ? ERROR : NOT_FOUND;
                    }
                }
                final Lyrics lyrics = result;
                final int finalStatus = status;
                AndroidUtilities.runOnUIThread(() -> {
                    if (lyrics != null) {
                        memory.put(key, lyrics);
                        missing.remove(key);
                    } else if (finalStatus == NOT_FOUND) {
                        missing.put(key, SystemClock.elapsedRealtime() + MISSING_TTL_MS);
                    }
                    ArrayList<Request> listeners;
                    synchronized (pending) { listeners = pending.remove(key); }
                    if (listeners != null) for (Request listener : listeners) listener.deliver(lyrics, finalStatus);
                });
            } finally { currentRequest.remove(); }
        });
        return request;
    }

    private static Found requestLrclib(Query q) throws Exception {
        if (!TextUtils.isEmpty(q.artist)) {
            try {
                StringBuilder url = new StringBuilder(LRCLIB).append("get?artist_name=").append(enc(q.artist))
                        .append("&track_name=").append(enc(q.title));
                if (!TextUtils.isEmpty(q.album)) {
                    url.append("&album_name=").append(enc(q.album));
                }
                if (q.duration > 0) {
                    url.append("&duration=").append(q.duration);
                }
                String body = get(url.toString());
                if (body != null) {
                    JSONObject candidate = new JSONObject(body);
                    Found found = matches(q.title, q.artist, q.duration, candidate, "trackName", "artistName") ? fromLrclib(candidate) : null;
                    if (found != null) {
                        return found;
                    }
                }
            } catch (Throwable ignore) {
            }
        }
        StringBuilder url = new StringBuilder(LRCLIB).append("search?track_name=").append(enc(q.title));
        if (!TextUtils.isEmpty(q.artist)) {
            url.append("&artist_name=").append(enc(q.artist));
        }
        String body = get(url.toString());
        if (body == null && !TextUtils.isEmpty(q.artist)) {
            url = new StringBuilder(LRCLIB).append("search?q=").append(enc(q.artist + " " + q.title));
            body = get(url.toString());
        }
        if (body == null) {
            url = new StringBuilder(LRCLIB).append("search?q=").append(enc(q.title));
            body = get(url.toString());
        }
        if (body == null) {
            return null;
        }
        JSONArray arr = new JSONArray(body);
        Found best = null;
        int bestScore = Integer.MIN_VALUE;
        for (int i = 0; i < arr.length(); i++) {
            JSONObject o = arr.optJSONObject(i);
            if (o == null || !matches(q.title, q.artist, q.duration, o, "trackName", "artistName")) continue;
            Found found = fromLrclib(o);
            if (found == null) continue;
            int score = found.lyrics.synced ? 40 : 0;
            if (q.duration > 0 && o.has("duration")) {
                int diff = (int) Math.abs(Math.round(o.optDouble("duration", 0)) - q.duration);
                score -= diff <= MAX_DURATION_DIFF ? diff : 20 + Math.min(diff, 60);
            }
            if (score > bestScore) {
                bestScore = score;
                best = found;
            }
        }
        return best;
    }

    private static String identity(String value) {
        if (value == null) return "";
        String normalized = Normalizer.normalize(stripDecorations(value), Normalizer.Form.NFKD);
        return NOT_WORD.matcher(normalized.replaceAll("\\p{M}+", "").toLowerCase(Locale.ROOT)).replaceAll("");
    }

    static boolean matches(String title, String artist, int duration, JSONObject candidate, String titleKey, String artistKey) {
        if (candidate == null) return false;
        String candTitle = optString(candidate, titleKey);
        if (candTitle == null && "trackName".equals(titleKey)) {
            candTitle = optString(candidate, "name");
        }
        if (candTitle == null || !identity(title).equals(identity(candTitle))) return false;
        if (!TextUtils.isEmpty(artist)) {
            String candArtist = optString(candidate, artistKey);
            if (candArtist == null || !identity(artist).equals(identity(candArtist))) return false;
        }
        double actual = candidate.optDouble("duration", 0);
        return Double.isFinite(actual) && (duration <= 0 || actual <= 0 || Math.abs(actual - duration) <= MAX_FALLBACK_DURATION_DIFF);
    }

    private static String optString(JSONObject o, String name) {
        if (o == null || o.isNull(name)) {
            return null;
        }
        String s = o.optString(name, null);
        return TextUtils.isEmpty(s) ? null : s;
    }

    private static Found fromLrclib(JSONObject o) {
        if (o.optBoolean("instrumental", false)) {
            return new Found(Lyrics.instrumental(Lyrics.SOURCE_ONLINE, LRCLIB_NAME));
        }
        Lyrics synced = Lyrics.parse(optString(o, "syncedLyrics"), Lyrics.SOURCE_ONLINE, LRCLIB_NAME);
        if (synced != null && synced.synced) {
            return new Found(synced);
        }
        Lyrics plain = Lyrics.parse(optString(o, "plainLyrics"), Lyrics.SOURCE_ONLINE, LRCLIB_NAME);
        if (plain != null) {
            return new Found(plain);
        }
        return synced != null ? new Found(synced) : null;
    }

    private static Found requestLrcmux(Query q) throws Exception {
        StringBuilder url = new StringBuilder(LRCMUX).append("?title=").append(enc(q.title)).append("&level=line&format=json");
        if (!TextUtils.isEmpty(q.artist)) {
            url.append("&artist=").append(enc(q.artist));
        }
        if (!TextUtils.isEmpty(q.album)) {
            url.append("&album=").append(enc(q.album));
        }
        if (q.duration > 0) {
            url.append("&duration=").append(q.duration);
        }
        String body = get(url.toString());
        if (body == null) {
            return null;
        }
        JSONObject o = new JSONObject(body);
        JSONObject track = o.optJSONObject("track");
        JSONObject meta = o.optJSONObject("meta");
        if (track == null || !matches(q.title, q.artist, q.duration, track, "title", "artist")) return null;
        if (q.duration > 0 && track != null) {
            int duration = track.optInt("duration", 0);
            if (duration > 0 && Math.abs(duration - q.duration) > MAX_FALLBACK_DURATION_DIFF) {
                return null;
            }
        }
        JSONObject source = meta != null ? meta.optJSONObject("source") : null;
        String sourceName = source != null ? optString(source, "name") : null;
        String provider = sourceName != null ? "lrcmux · " + sourceName : "lrcmux";
        if (meta != null && meta.optBoolean("instrumental", false)) {
            return new Found(Lyrics.instrumental(Lyrics.SOURCE_ONLINE, provider));
        }
        JSONArray lines = o.optJSONArray("lines");
        if (lines == null || lines.length() == 0) {
            return null;
        }
        boolean synced = meta != null && !"none".equals(meta.optString("level"));
        StringBuilder text = new StringBuilder();
        for (int i = 0; i < lines.length(); i++) {
            JSONObject line = lines.optJSONObject(i);
            if (line == null) {
                continue;
            }
            if (synced) {
                long start = Math.max(0, line.optLong("start", 0));
                text.append(String.format(Locale.US, "[%02d:%02d.%02d]", start / 60000, start / 1000 % 60, start % 1000 / 10));
            }
            text.append(line.optString("text", "")).append('\n');
        }
        Lyrics lyrics = Lyrics.parse(text.toString(), Lyrics.SOURCE_ONLINE, provider);
        return lyrics == null ? null : new Found(lyrics);
    }

    private static String wordKey(String word) {
        return NOT_WORD.matcher(word.toLowerCase(Locale.ROOT)).replaceAll("");
    }

    private static int firstLetter(String s) {
        for (int i = 0; i < s.length(); i++) {
            if (Character.isLetter(s.charAt(i))) {
                return i;
            }
        }
        return -1;
    }

    private static String withCase(String token, String original) {
        int t = firstLetter(token);
        int o = firstLetter(original);
        if (t < 0 || o < 0) {
            return token;
        }
        boolean upper = Character.isUpperCase(original.charAt(o));
        char c = token.charAt(t);
        if (Character.isUpperCase(c) == upper) {
            return token;
        }
        return token.substring(0, t) + (upper ? Character.toUpperCase(c) : Character.toLowerCase(c)) + token.substring(t + 1);
    }

    private static void appendWord(StringBuilder sb, String word) {
        if (word.isEmpty()) {
            return;
        }
        if (sb.length() > 0) {
            sb.append(' ');
        }
        sb.append(word);
    }

    private static Lyrics punctuate(Lyrics timed, Lyrics plain) {
        ArrayList<String> tokens = new ArrayList<>();
        ArrayList<String> keys = new ArrayList<>();
        for (Lyrics.Line line : plain.lines) {
            for (String word : line.text.split("\\s+")) {
                String key = wordKey(word);
                if (!key.isEmpty()) {
                    tokens.add(word);
                    keys.add(key);
                }
            }
        }
        if (keys.isEmpty()) {
            return null;
        }
        int pos = 0;
        int total = 0;
        int matched = 0;
        ArrayList<Lyrics.Line> out = new ArrayList<>(timed.lines.size());
        for (Lyrics.Line line : timed.lines) {
            StringBuilder sb = new StringBuilder();
            for (String word : line.text.split("\\s+")) {
                String key = wordKey(word);
                if (key.isEmpty()) {
                    appendWord(sb, word);
                    continue;
                }
                total++;
                int hit = -1;
                for (int j = pos, end = Math.min(pos + ALIGN_WINDOW, keys.size()); j < end; j++) {
                    if (keys.get(j).equals(key)) {
                        hit = j;
                        break;
                    }
                }
                if (hit < 0) {
                    appendWord(sb, word);
                    continue;
                }
                matched++;
                appendWord(sb, withCase(tokens.get(hit), word));
                pos = hit + 1;
            }
            out.add(new Lyrics.Line(line.time, sb.toString()));
        }
        if (total == 0 || matched < total * MIN_ALIGNED) {
            return null;
        }
        return Lyrics.synced(out, timed.source, timed.provider + " + " + LRCLIB_NAME);
    }

    private static String enc(String s) throws Exception {
        return URLEncoder.encode(s, "UTF-8").replace("+", "%20");
    }

    private static void ensureActiveRequest() throws java.io.InterruptedIOException {
        String key = currentRequest.get(); if (key == null) return;
        synchronized (pending) {
            ArrayList<Request> requests = pending.get(key);
            if (requests != null) for (Request request : requests) if (request.callback != null) return;
        }
        throw new java.io.InterruptedIOException("lyrics request cancelled");
    }

    private static String get(String url) throws Exception {
        ensureActiveRequest();
        HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
        try {
            connection.setConnectTimeout(5_000);
            connection.setReadTimeout(6_000);
            connection.setRequestProperty("User-Agent", "FlexyGram/" + BuildVars.BUILD_VERSION_STRING + " (Android; +https://github.com/Jose22Yt/FlexyGram)");
            connection.setRequestProperty("Accept", "application/json");
            int code = connection.getResponseCode();
            if (code == 404) {
                return null;
            }
            if (code < 200 || code >= 300) {
                throw new IllegalStateException("lyrics http " + code);
            }
            try (InputStream in = connection.getInputStream()) {
                return readAll(in);
            }
        } finally {
            connection.disconnect();
        }
    }

    private static String readAll(InputStream in) throws Exception {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buf = new byte[8192];
        int n;
        while ((n = in.read(buf)) > 0) {
            ensureActiveRequest();
            if (out.size() + n > MAX_RESPONSE_BYTES) throw new java.io.IOException("lyrics response too large");
            out.write(buf, 0, n);
        }
        return out.toString("UTF-8");
    }

    private static File cacheFile(String key) {
        File dir = new File(ApplicationLoader.applicationContext.getCacheDir(), "lrclib");
        if (!dir.exists() && !dir.mkdirs()) {
            return null;
        }
        return new File(dir, Utilities.MD5(key) + ".json");
    }

    private static Lyrics readDisk(String key) {
        try {
            File f = cacheFile(key);
            if (f == null || !f.exists()) {
                return null;
            }
            JSONObject o;
            try (FileInputStream in = new FileInputStream(f)) {
                o = new JSONObject(readAll(in));
            }
            int version = o.optInt("v", 1);
            if (version != CACHE_VERSION) return null;
            String provider = optString(o, "provider");
            if (provider == null) provider = LRCLIB_NAME;
            if (o.optBoolean("instrumental", false)) {
                return Lyrics.instrumental(Lyrics.SOURCE_ONLINE, provider);
            }
            return Lyrics.parse(optString(o, "text"), Lyrics.SOURCE_ONLINE, provider);
        } catch (Throwable e) {
            FileLog.e(e);
            return null;
        }
    }

    private static void writeDisk(String key, Lyrics lyrics) {
        try {
            File f = cacheFile(key);
            if (f == null) {
                return;
            }
            JSONObject o = new JSONObject();
            o.put("v", CACHE_VERSION);
            o.put("provider", lyrics.provider);
            o.put("instrumental", lyrics.instrumental);
            o.put("text", lyrics.toText());
            AtomicFile atomic = new AtomicFile(f);
            FileOutputStream out = null;
            try {
                out = atomic.startWrite();out.write(o.toString().getBytes(StandardCharsets.UTF_8));atomic.finishWrite(out);
            } catch (Exception error) { atomic.failWrite(out); throw error; }
        } catch (Throwable e) {
            FileLog.e(e);
        }
    }
}
