package app.exteraless.speech;

import android.content.SharedPreferences;
import android.text.TextUtils;

import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.ApplicationLoader;
import org.telegram.messenger.FileLog;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

import okhttp3.OkHttpClient;
import okhttp3.Call;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.ResponseBody;
import tw.nekomimi.nekogram.NekoConfig;
import tw.nekomimi.nekogram.utils.HttpClient;

public final class VoskManager {

    public interface DownloadListener {
        void onProgress(long done, long total);

        void onFinished(VoskModel model, Throwable error);

        default void onSizeChanged(String code) { }
    }

    private static final String KEY_LANGUAGE = "OEVoskLanguage";
    private static final String READY_MARKER = ".ready";
    private static final int BUFFER_SIZE = 64 * 1024;

    private static final ExecutorService executor = Executors.newSingleThreadExecutor();
    private static final ArrayList<DownloadListener> listeners = new ArrayList<>();

    private static volatile String downloadingCode;
    private static volatile long downloadedBytes;
    private static volatile long totalBytes;
    private static volatile AtomicBoolean cancelled = new AtomicBoolean();
    private static volatile Call activeDownload;
    private static final Map<String, Long> installedSizes = new HashMap<>();
    private static final Set<String> sizePending = new HashSet<>();
    private static long sizesGeneration;
    private static final Set<String> deletingCodes = java.util.concurrent.ConcurrentHashMap.newKeySet();

    private VoskManager() {
    }

    private static SharedPreferences preferences() {
        return NekoConfig.getPreferences();
    }

    public static String getLanguage() {
        String stored = preferences().getString(KEY_LANGUAGE, null);
        if (!TextUtils.isEmpty(stored)) {
            return stored;
        }
        Locale locale = Locale.getDefault();
        VoskModel guessed = VoskModels.forCurrentLocale(locale.getLanguage(), locale.getCountry());
        return guessed != null ? guessed.code : "en-us";
    }

    public static void setLanguage(String code) {
        preferences().edit().putString(KEY_LANGUAGE, code).apply();
        VoskTranscriber.releaseModel();
    }

    public static File getModelsDir() {
        return ApplicationLoader.getFilesDirFixed("vosk");
    }

    public static File getModelDir(String code) {
        File root = getModelsDir();
        return root == null ? null : new File(root, code);
    }

    public static boolean isInstalled(String code) {
        File dir = getModelDir(code);
        return dir != null && new File(dir, READY_MARKER).exists();
    }

    public static boolean hasAnyModel() {
        for (VoskModel model : VoskModels.all()) {
            if (isInstalled(model.code)) {
                return true;
            }
        }
        return false;
    }

    /** -1 means a coalesced worker scan is pending; row binding never walks the directory. */
    public static long installedSize(String code) {
        synchronized (installedSizes) {
            Long known = installedSizes.get(code);
            if (known != null) return known;
            if (!sizePending.add(code)) return -1;
            final long generation = sizesGeneration;
            try {
                executor.execute(() -> {
                    long size = 0;
                    try {
                        File dir = getModelDir(code);
                        if (dir != null) size = directorySize(dir);
                    } catch (RuntimeException failed) { FileLog.e(failed); }
                    synchronized (installedSizes) {
                        if (generation == sizesGeneration) installedSizes.put(code, size);
                        sizePending.remove(code);
                    }
                    AndroidUtilities.runOnUIThread(() -> notifySizeChanged(code));
                });
            } catch (java.util.concurrent.RejectedExecutionException unavailable) {
                sizePending.remove(code);
                FileLog.e(unavailable);
            }
            return -1;
        }
    }

    private static void invalidateInstalledSizes() {
        synchronized (installedSizes) {
            sizesGeneration++;
            installedSizes.clear();
        }
    }

    public static boolean isDeleting(String code) {
        return code != null && deletingCodes.contains(code);
    }

    public static String getDownloadingCode() {
        return downloadingCode;
    }

    public static long getDownloadedBytes() {
        return downloadedBytes;
    }

    public static long getTotalBytes() {
        return totalBytes;
    }

    public static void addListener(DownloadListener listener) {
        if (listener != null && !listeners.contains(listener)) {
            listeners.add(listener);
        }
    }

    public static void removeListener(DownloadListener listener) {
        listeners.remove(listener);
    }

    public static synchronized void cancelDownload() {
        cancelled.set(true);
        Call call = activeDownload;
        if (call != null) call.cancel(); // Unblock a body read, not merely the next read-loop check.
    }

    public static synchronized void download(VoskModel model) {
        if (model == null || downloadingCode != null || isDeleting(model.code) || isInstalled(model.code)) {
            return;
        }
        invalidateInstalledSizes();
        downloadingCode = model.code;
        downloadedBytes = 0;
        totalBytes = model.size;
        cancelled = new AtomicBoolean();
        final AtomicBoolean cancelFlag = cancelled;
        executor.submit(() -> {
            Throwable error = null;
            try {
                downloadInternal(model, cancelFlag);
            } catch (Throwable e) {
                error = cancelFlag.get() ? new InterruptedException("cancelled") : e;
                if (!(error instanceof InterruptedException)) {
                    FileLog.e(error);
                }
            }
            invalidateInstalledSizes();
            final Throwable result = error;
            downloadingCode = null;
            AndroidUtilities.runOnUIThread(() -> notifyFinished(model, result));
        });
    }

    private static void downloadInternal(VoskModel model, AtomicBoolean cancelFlag) throws Exception {
        File root = getModelsDir();
        if (root == null) {
            throw new IOException("no models dir");
        }
        File archive = new File(root, model.code + ".zip");
        File target = new File(root, model.code);
        File staging = new File(root, model.code + ".tmp");
        try {
            deleteRecursive(staging);
            archive.delete();

            OkHttpClient client = HttpClient.INSTANCE.getInstance().newBuilder()
                    .callTimeout(0, java.util.concurrent.TimeUnit.SECONDS)
                    .readTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
                    .build();
            Request request = new Request.Builder().url(model.url).build();
            MessageDigest digest = MessageDigest.getInstance("MD5");
            Call call = client.newCall(request);
            activeDownload = call;
            if (cancelFlag.get()) call.cancel();
            try (Response response = call.execute()) {
                if (!response.isSuccessful()) {
                    throw new IOException("http " + response.code());
                }
                ResponseBody body = response.body();
                if (body == null) {
                    throw new IOException("empty body");
                }
                long contentLength = body.contentLength();
                if (contentLength > 0) {
                    totalBytes = contentLength;
                }
                byte[] buffer = new byte[BUFFER_SIZE];
                long done = 0;
                long lastPublished = 0;
                try (InputStream input = body.byteStream();
                     OutputStream output = new FileOutputStream(archive)) {
                    int read;
                    while ((read = input.read(buffer)) != -1) {
                        if (cancelFlag.get()) {
                            throw new InterruptedException("cancelled");
                        }
                        output.write(buffer, 0, read);
                        digest.update(buffer, 0, read);
                        done += read;
                        downloadedBytes = done;
                        if (done - lastPublished > 512 * 1024) {
                            lastPublished = done;
                            final long published = done;
                            final long total = totalBytes;
                            AndroidUtilities.runOnUIThread(() -> notifyProgress(published, total));
                        }
                    }
                }
            } finally {
                if (activeDownload == call) activeDownload = null;
            }

            if (!TextUtils.isEmpty(model.md5)) {
                StringBuilder hash = new StringBuilder();
                for (byte b : digest.digest()) {
                    hash.append(String.format(Locale.US, "%02x", b));
                }
                if (!model.md5.equalsIgnoreCase(hash.toString())) {
                    archive.delete();
                    throw new IOException("checksum mismatch");
                }
            }

            unzipStripRoot(archive, staging, cancelFlag);
            archive.delete();
            VoskTranscriber.afterModelRelease(model.code, () -> {
                if (cancelFlag.get()) throw new InterruptedException("cancelled");
                deleteRecursive(target);
                if (!staging.renameTo(target)) throw new IOException("cannot move model");
                boolean ready = false;
                try {
                    new File(target, READY_MARKER).createNewFile();
                    ready = true;
                } finally {
                    if (!ready) deleteRecursive(target);
                }
                return null;
            }).get();
        } finally {
            archive.delete();
            deleteRecursive(staging);
        }
    }

    private static void unzipStripRoot(File archive, File target, AtomicBoolean cancelFlag) throws Exception {
        target.mkdirs();
        String canonicalTarget = target.getCanonicalPath() + File.separator;
        byte[] buffer = new byte[BUFFER_SIZE];
        try (ZipInputStream zip = new ZipInputStream(new java.io.BufferedInputStream(
                new java.io.FileInputStream(archive), BUFFER_SIZE))) {
            ZipEntry entry;
            while ((entry = zip.getNextEntry()) != null) {
                if (cancelFlag.get()) {
                    throw new InterruptedException("cancelled");
                }
                String name = stripRoot(entry.getName());
                if (TextUtils.isEmpty(name)) {
                    continue;
                }
                File out = new File(target, name);
                if (!out.getCanonicalPath().startsWith(canonicalTarget)) {
                    throw new IOException("bad entry " + entry.getName());
                }
                if (entry.isDirectory()) {
                    out.mkdirs();
                    continue;
                }
                File parent = out.getParentFile();
                if (parent != null) {
                    parent.mkdirs();
                }
                try (OutputStream output = new FileOutputStream(out)) {
                    int read;
                    while ((read = zip.read(buffer)) != -1) {
                        if (cancelFlag.get()) throw new InterruptedException("cancelled");
                        output.write(buffer, 0, read);
                    }
                }
            }
        }
    }

    private static String stripRoot(String name) {
        if (name == null) {
            return null;
        }
        int slash = name.indexOf('/');
        if (slash < 0) {
            return "";
        }
        return name.substring(slash + 1);
    }

    public static void delete(String code) {
        delete(code, null);
    }

    public static synchronized void delete(String code, Runnable completion) {
        if (code == null || code.isEmpty() || !deletingCodes.add(code)) {
            if (completion != null) AndroidUtilities.runOnUIThread(completion);
            return;
        }
        if (code.equals(downloadingCode)) cancelDownload();
        invalidateInstalledSizes();
        try {
            VoskTranscriber.afterModelRelease(code, () -> {
                try {
                    File dir = getModelDir(code);
                    if (dir != null) deleteRecursive(dir);
                } catch (RuntimeException failed) {
                    FileLog.e(failed);
                } finally {
                    deletingCodes.remove(code);
                    invalidateInstalledSizes();
                    if (completion != null) AndroidUtilities.runOnUIThread(completion);
                }
                return null;
            });
        } catch (java.util.concurrent.RejectedExecutionException unavailable) {
            deletingCodes.remove(code);
            if (completion != null) AndroidUtilities.runOnUIThread(completion);
            FileLog.e(unavailable);
        }
    }

    private static void deleteRecursive(File file) {
        if (file == null || !file.exists()) {
            return;
        }
        File[] children = file.listFiles();
        if (children != null) {
            for (File child : children) {
                deleteRecursive(child);
            }
        }
        file.delete();
    }

    private static long directorySize(File file) {
        if (file == null || !file.exists()) {
            return 0;
        }
        if (file.isFile()) {
            return file.length();
        }
        long size = 0;
        File[] children = file.listFiles();
        if (children != null) {
            for (File child : children) {
                size += directorySize(child);
            }
        }
        return size;
    }

    private static void notifySizeChanged(String code) {
        for (DownloadListener listener : listeners.toArray(new DownloadListener[0])) {
            if (!listeners.contains(listener)) continue;
            try { listener.onSizeChanged(code); }
            catch (RuntimeException failed) { FileLog.e(failed); }
        }
    }

    private static void notifyProgress(long done, long total) {
        for (DownloadListener listener : listeners.toArray(new DownloadListener[0])) {
            if (!listeners.contains(listener)) continue;
            try { listener.onProgress(done, total); }
            catch (RuntimeException failed) { FileLog.e(failed); }
        }
    }

    private static void notifyFinished(VoskModel model, Throwable error) {
        for (DownloadListener listener : listeners.toArray(new DownloadListener[0])) {
            if (!listeners.contains(listener)) continue;
            try { listener.onFinished(model, error); }
            catch (RuntimeException failed) { FileLog.e(failed); }
        }
    }
}
