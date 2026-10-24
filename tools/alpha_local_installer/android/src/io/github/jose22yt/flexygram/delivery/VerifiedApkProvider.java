package io.github.jose22yt.flexygram.delivery.alpha2.home2v1268;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;
import java.io.File;
import java.io.FileNotFoundException;

public final class VerifiedApkProvider extends ContentProvider {
    static final Uri URI = Uri.parse("content://io.github.jose22yt.flexygram.delivery.alpha2.home2v1268.files/verified/FlexyGram-Alpha-arm64.apk");
    private void requireUri(Uri uri) {
        if (!URI.equals(uri)) throw new SecurityException("Unsupported file");
    }
    @Override public boolean onCreate() { return true; }
    @Override public String getType(Uri uri) { requireUri(uri); return "application/vnd.android.package-archive"; }
    @Override public ParcelFileDescriptor openFile(Uri uri, String mode) throws FileNotFoundException {
        requireUri(uri);
        if (!"r".equals(mode)) throw new SecurityException("Read only");
        try {
            Contract.requireVerified(getContext());
            return ParcelFileDescriptor.open(new File(Contract.directory(getContext()), Contract.APK), ParcelFileDescriptor.MODE_READ_ONLY);
        } catch (Exception e) { throw new FileNotFoundException("Verified APK unavailable"); }
    }
    @Override public Cursor query(Uri uri, String[] projection, String selection, String[] args, String order) {
        requireUri(uri);
        String[] columns = projection == null ? new String[]{OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE} : projection;
        MatrixCursor cursor = new MatrixCursor(columns);
        Object[] values = new Object[columns.length];
        long size = 0;
        try { size = new File(Contract.directory(getContext()), Contract.APK).length(); } catch (Exception ignored) { }
        for (int i = 0; i < columns.length; i++) {
            if (OpenableColumns.DISPLAY_NAME.equals(columns[i])) values[i] = Contract.APK;
            if (OpenableColumns.SIZE.equals(columns[i])) values[i] = size;
        }
        cursor.addRow(values);
        return cursor;
    }
    @Override public Uri insert(Uri u, ContentValues v) { throw new SecurityException("Read only"); }
    @Override public int update(Uri u, ContentValues v, String s, String[] a) { throw new SecurityException("Read only"); }
    @Override public int delete(Uri u, String s, String[] a) { throw new SecurityException("Read only"); }
}
