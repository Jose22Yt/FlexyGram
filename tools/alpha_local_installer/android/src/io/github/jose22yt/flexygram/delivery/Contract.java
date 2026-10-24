package io.github.jose22yt.flexygram.delivery.alpha2.iphone1266;

import android.content.Context;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import org.json.JSONObject;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.security.MessageDigest;

final class Contract {
    static final String APP = "io.github.jose22yt.flexygram.alpha";
    static final String APK = "FlexyGram-Alpha-arm64.apk";
    static final String HASH = "";
    static final String CIPHER_HASH = "";
    static final String CERTIFICATE = "c8f04cad685ca5757d35b25ea4b0b4613c7399909948d821e6ada61f9fb12b2c";
    static final String COMMIT = "1ff3053331656f7a32f3a093fb735abb61018770";
    static File directory(Context c) throws IOException {
        File d = new File(c.getNoBackupFilesDir(), "verified");
        if (!d.isDirectory() && !d.mkdir()) throw new IOException("private output unavailable");
        return d;
    }
    static String hash(File file) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] buffer = new byte[65536];
        try (FileInputStream in = new FileInputStream(file)) {
            int count;
            while ((count = in.read(buffer)) != -1) digest.update(buffer, 0, count);
        }
        return hex(digest.digest());
    }
    static String hex(byte[] value) {
        StringBuilder s = new StringBuilder(value.length * 2);
        for (byte b : value) s.append(String.format(java.util.Locale.ROOT, "%02x", b & 255));
        return s.toString();
    }
    static JSONObject requireVerified(Context c) throws Exception {
        File dir = directory(c), apk = new File(dir, APK), report = new File(dir, "verification.json");
        if (!apk.isFile() || !report.isFile() || report.length() > 262144 || !HASH.equals(hash(apk))) throw new IOException("integrity rejected");
        JSONObject r = new JSONObject(new String(Files.readAllBytes(report.toPath()), StandardCharsets.UTF_8));
        if (!CERTIFICATE.equals(r.getString("certificate_sha256")) || !HASH.equals(r.getString("sha256")) || !COMMIT.equals(r.getString("commit")) ||
                !"PASS_ARTIFACT_ONLY".equals(r.getString("status")) || !"NOT_TESTED".equals(r.getString("android_runtime")) ||
                !APP.equals(r.getString("application_id")) || r.getLong("version_code") != 1266 || r.getLong("bytes") != apk.length() || r.getInt("elf_count") != 96 || r.getJSONArray("elfs").length() != 96)
            throw new IOException("report rejected");
        PackageInfo p = c.getPackageManager().getPackageArchiveInfo(apk.getPath(), PackageManager.GET_SIGNING_CERTIFICATES);
        if (p == null || !APP.equals(p.packageName) || p.signingInfo == null || p.getLongVersionCode() != 1266) throw new IOException("APK identity rejected");
        Signature[] signers = p.signingInfo.getApkContentsSigners();
        if (signers.length != 1 || !r.getString("certificate_sha256").equals(hex(MessageDigest.getInstance("SHA-256").digest(signers[0].toByteArray()))))
            throw new IOException("certificate rejected");
        // Refuse a different installed signer or a downgrade before invoking Android.
        // PackageManager's installer performs its own signature verification too.
        try {
            requireCompatibleUpdate(c.getPackageManager().getPackageInfo(APP, PackageManager.GET_SIGNING_CERTIFICATES), p);
        } catch (PackageManager.NameNotFoundException firstInstallation) { }
        return r;
    }
    static void requireCompatibleUpdate(PackageInfo installed, PackageInfo candidate) throws IOException {
        if (installed == null || candidate == null || installed.signingInfo == null || candidate.signingInfo == null
                || installed.getLongVersionCode() > candidate.getLongVersionCode())
            throw new IOException("installed version rejected");
        Signature[] current = installed.signingInfo.getApkContentsSigners();
        Signature[] incoming = candidate.signingInfo.getApkContentsSigners();
        if (current.length != 1 || incoming.length != 1
                || !java.util.Arrays.equals(current[0].toByteArray(), incoming[0].toByteArray()))
            throw new IOException("installed certificate rejected");
    }
    static void clean(Context c) {
        try { deleteTree(directory(c)); } catch (IOException ignored) { }
        new File(c.getCacheDir(), "delivery.age").delete();
    }
    private static void deleteTree(File f) {
        File[] files = f.listFiles();
        if (files != null) for (File child : files) deleteTree(child);
        f.delete();
    }
}
