package io.github.jose22yt.flexygram.delivery;

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
    static final String HASH = "579f70e6e90f4445b2fedfe747ad433392bc8a7f9beebebf98752e4b284194fb";
    static final String CIPHER_HASH = "33cd33d4e0d7da4733af0c02eb1b34288e8659886dc4df8c3d49d2f4e863147c";
    static final String COMMIT = "c4210911a048d4fde080c03c31aa98741336db2f";
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
        if (!HASH.equals(r.getString("sha256")) || !COMMIT.equals(r.getString("commit")) ||
                !"PASS_ARTIFACT_ONLY".equals(r.getString("status")) || !"NOT_TESTED".equals(r.getString("android_runtime")) ||
                r.getLong("bytes") != apk.length() || r.getInt("elf_count") != 96 || r.getJSONArray("elfs").length() != 96)
            throw new IOException("report rejected");
        PackageInfo p = c.getPackageManager().getPackageArchiveInfo(apk.getPath(), PackageManager.GET_SIGNING_CERTIFICATES);
        if (p == null || !APP.equals(p.packageName) || p.signingInfo == null) throw new IOException("APK identity rejected");
        Signature[] signers = p.signingInfo.getApkContentsSigners();
        if (signers.length != 1 || !r.getString("certificate_sha256").equals(hex(MessageDigest.getInstance("SHA-256").digest(signers[0].toByteArray()))))
            throw new IOException("certificate rejected");
        return r;
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
