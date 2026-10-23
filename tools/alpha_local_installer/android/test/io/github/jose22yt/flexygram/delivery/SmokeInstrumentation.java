package io.github.jose22yt.flexygram.delivery.alpha2;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.os.ParcelFileDescriptor;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.FrameLayout;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;

// No real identity or decrypted Alpha APK is present in this test APK.
public final class SmokeInstrumentation extends Instrumentation {
    private void check(boolean value) { if (!value) throw new AssertionError("helper smoke assertion"); }
    @Override public void onCreate(Bundle arguments) { super.onCreate(arguments); start(); }
    @Override public void onStart() {
        Bundle result = new Bundle();
        try {
            Context c = getTargetContext();
            check(c.getPackageManager().checkPermission("android.permission.INTERNET", c.getPackageName()) == PackageManager.PERMISSION_DENIED);
            check(c.getPackageManager().checkPermission("android.permission.READ_EXTERNAL_STORAGE", c.getPackageName()) == PackageManager.PERMISSION_DENIED);
            MainActivity activity = (MainActivity) startActivitySync(new Intent(c, MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
            runOnMainSync(() -> {
                // Isolated Android measure-cache regression, no Telegram state.
                final int[] measurements = {0};
                FrameLayout parent = new FrameLayout(c);
                FrameLayout hook = new FrameLayout(c) {
                    @Override protected void onMeasure(int w, int h) {
                        measurements[0]++;
                        super.onMeasure(w, h);
                    }
                };
                parent.addView(hook, new FrameLayout.LayoutParams(300, 60));
                int width = View.MeasureSpec.makeMeasureSpec(400, View.MeasureSpec.EXACTLY);
                int height = View.MeasureSpec.makeMeasureSpec(100, View.MeasureSpec.EXACTLY);
                parent.measure(width, height); parent.layout(0, 0, 400, 100);
                int first = measurements[0];
                parent.requestLayout();
                parent.measure(width, height); parent.layout(0, 0, 400, 100);
                result.putBoolean("parent_only_skips_child_measure", measurements[0] == first);
                int beforeChildRequest = measurements[0];
                hook.requestLayout();
                parent.measure(width, height); parent.layout(0, 0, 400, 100);
                check(measurements[0] > beforeChildRequest);
                result.putString("isolated_child_measure_contract", "PASS");
                View root = activity.getWindow().getDecorView();
                check(button(root, "1. Seleccionar archivo cifrado").isEnabled());
                check(!button(root, "3. Descifrar y comprobar").isEnabled());
                check(!button(root, "4. Actualizar FlexyGram Alpha 2").isEnabled());
            });
            File cipher = new File(c.getCacheDir(), "test-cipher"), identity = new File(c.getCacheDir(), "test-identity");
            Files.write(cipher.toPath(), "invalid encrypted test bytes".getBytes(StandardCharsets.UTF_8));
            Files.write(identity.toPath(), "this is NOT an age private key".getBytes(StandardCharsets.UTF_8));
            try (ParcelFileDescriptor cf = ParcelFileDescriptor.open(cipher, ParcelFileDescriptor.MODE_READ_ONLY);
                 ParcelFileDescriptor kf = ParcelFileDescriptor.open(identity, ParcelFileDescriptor.MODE_READ_ONLY)) {
                check(MainActivity.decryptNative(cf.detachFd(), kf.detachFd(), Contract.directory(c).getPath()) == 1);
            }
            cipher.delete(); identity.delete();
            boolean rejected = false;
            try { c.getContentResolver().openFileDescriptor(VerifiedApkProvider.URI, "rw"); } catch (Exception e) { rejected = true; }
            check(rejected);
            rejected = false;
            try { c.getContentResolver().openFileDescriptor(Uri.parse("content://io.github.jose22yt.flexygram.delivery.alpha2.files/../identity"), "r"); } catch (Exception e) { rejected = true; }
            check(rejected);
            File fake = new File(Contract.directory(c), Contract.APK);
            Files.write(fake.toPath(), new byte[]{1,2,3});
            rejected = false;
            try { Contract.requireVerified(c); } catch (Exception e) { rejected = true; }
            check(rejected);
            rejected = false;
            try { c.getContentResolver().openFileDescriptor(VerifiedApkProvider.URI, "r"); } catch (Exception e) { rejected = true; }
            check(rejected);
            Contract.clean(c);
            runOnMainSync(activity::finish);
            result.putString("helper_smoke", "PASS");
            result.putString("scope", "Android emulator: helper only. FlexyGram/Poco physical runtime NOT_TESTED.");
            finish(Activity.RESULT_OK, result);
        } catch (Throwable e) {
            result.putString("helper_smoke", "FAIL");
            result.putString("failure_type", e.getClass().getSimpleName());
            finish(Activity.RESULT_CANCELED, result);
        }
    }
    private Button button(View v, String label) {
        Button found = find(v, label);
        if (found == null) throw new AssertionError("button missing");
        return found;
    }
    private Button find(View v, String label) {
        if (v instanceof Button && label.contentEquals(((Button)v).getText())) return (Button)v;
        if (v instanceof ViewGroup) for (int i=0; i<((ViewGroup)v).getChildCount(); i++) {
            Button b = find(((ViewGroup)v).getChildAt(i), label); if (b != null) return b;
        }
        return null;
    }
}
