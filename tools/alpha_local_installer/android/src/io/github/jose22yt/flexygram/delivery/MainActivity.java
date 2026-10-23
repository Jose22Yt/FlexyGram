package io.github.jose22yt.flexygram.delivery.alpha2;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.Intent;
import android.graphics.Insets;
import android.net.Uri;
import android.os.Bundle;
import android.os.ParcelFileDescriptor;
import android.provider.Settings;
import android.view.WindowInsets;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.concurrent.atomic.AtomicBoolean;

public final class MainActivity extends Activity {
    static native int decryptNative(int encryptedFD, int identityFD, String directory);
    private static final AtomicBoolean RUNNING = new AtomicBoolean();
    private Uri encrypted, identity;
    private Button cipherButton, keyButton, decryptButton, installButton, reportButton, clearButton;
    private TextView status;
    private boolean verified, nativeReady;
    private static final int PICK_CIPHER = 1, PICK_IDENTITY = 2, SAVE_REPORT = 3;

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        getWindow().addFlags(android.view.WindowManager.LayoutParams.FLAG_SECURE);
        try { System.loadLibrary("deliveryjni"); nativeReady = true; } catch (UnsatisfiedLinkError e) { nativeReady = false; }
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        int pad = (int)(20 * getResources().getDisplayMetrics().density);
        root.setPadding(pad, pad, pad, pad);
        ScrollView scroll = new ScrollView(this); scroll.addView(root); setContentView(scroll);
        scroll.setOnApplyWindowInsetsListener((v, insets) -> {
            Insets bars = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
            v.setPadding(bars.left, bars.top, bars.right, bars.bottom); return insets;
        });
        TextView title = text(root, "Actualizar FlexyGram Alpha 2"); title.setTextSize(25);
        text(root, "Todo el descifrado ocurre en este teléfono. La identidad privada no se guarda ni se transmite.");
        text(root, "Abre tu ZIP de recuperación en el teléfono. Selecciona únicamente el archivo de identidad age original que contiene la clave privada. El archivo delivery-public-recipient.txt no sirve para descifrar.");
        cipherButton = button(root, "1. Seleccionar archivo cifrado", () -> pick(PICK_CIPHER));
        keyButton = button(root, "2. Seleccionar identidad original", () -> pick(PICK_IDENTITY));
        decryptButton = button(root, "3. Descifrar y comprobar", this::startDecrypt);
        status = text(root, nativeReady ? "Selecciona FlexyGram-Alpha-arm64.tar.age y tu identidad original." : "No se pudo cargar el componente local. No se ha leído tu identidad.");
        status.setTextIsSelectable(true);
        installButton = button(root, "4. Actualizar FlexyGram Alpha 2", this::startInstall);
        reportButton = button(root, "Ver informe de verificación", this::showReport);
        clearButton = button(root, "Borrar archivos temporales", () -> {
            Contract.clean(this); verified = false; encrypted = identity = null;
            cipherButton.setText("1. Seleccionar archivo cifrado"); keyButton.setText("2. Seleccionar identidad original");
            status.setText("Archivos temporales borrados. Tu ZIP y tus aplicaciones siguen en su lugar."); refresh();
        });
        refresh();
    }
    private TextView text(LinearLayout root, String message) {
        TextView v = new TextView(this); v.setText(message); v.setTextSize(16); v.setPadding(0, 10, 0, 10); root.addView(v); return v;
    }
    private Button button(LinearLayout root, String label, Runnable action) {
        Button b = new Button(this); b.setText(label); b.setAllCaps(false); b.setOnClickListener(v -> action.run()); root.addView(b); return b;
    }
    private void refresh() {
        boolean idle = !RUNNING.get();
        cipherButton.setEnabled(idle); keyButton.setEnabled(idle);
        decryptButton.setEnabled(idle && nativeReady && encrypted != null && identity != null);
        installButton.setEnabled(idle && verified); reportButton.setEnabled(idle && verified); clearButton.setEnabled(idle);
    }
    private void pick(int request) {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("*/*");
        intent.putExtra(Intent.EXTRA_LOCAL_ONLY, true);
        startActivityForResult(intent, request);
    }
    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (result != RESULT_OK || data == null || data.getData() == null || RUNNING.get()) return;
        if (request == SAVE_REPORT) { saveReport(data.getData()); return; }
        if (request == PICK_CIPHER) { encrypted = data.getData(); cipherButton.setText("1. Archivo cifrado seleccionado"); }
        if (request == PICK_IDENTITY) { identity = data.getData(); keyButton.setText("2. Identidad seleccionada (solo esta operación)"); }
        verified = false; refresh();
    }
    private void startDecrypt() {
        if (encrypted == null || identity == null || !RUNNING.compareAndSet(false, true)) return;
        final Uri selectedCipher = encrypted, selectedIdentity = identity;
        identity = null; verified = false;
        status.setText("Descifrando y comprobando… Mantén abierta esta aplicación."); refresh();
        new Thread(() -> {
            String message;
            File copy = new File(getCacheDir(), "delivery.age");
            try {
                Contract.clean(this);
                try (InputStream in = getContentResolver().openInputStream(selectedCipher); FileOutputStream out = new FileOutputStream(copy)) {
                    if (in == null) throw new java.io.IOException();
                    byte[] buffer = new byte[65536]; long total = 0; int count;
                    while ((count = in.read(buffer)) != -1) {
                        total += count; if (total > 128L * 1024 * 1024) throw new java.io.IOException(); out.write(buffer, 0, count);
                    }
                }
                if (!Contract.CIPHER_HASH.equals(Contract.hash(copy))) throw new SecurityException();
                int code;
                try (ParcelFileDescriptor cf = ParcelFileDescriptor.open(copy, ParcelFileDescriptor.MODE_READ_ONLY);
                     ParcelFileDescriptor kf = getContentResolver().openFileDescriptor(selectedIdentity, "r")) {
                    if (kf == null) throw new java.io.IOException();
                    // Native owns these two descriptors and closes them on every result.
                    code = decryptNative(cf.detachFd(), kf.detachFd(), Contract.directory(this).getPath());
                }
                if (code == 1) message = "La identidad no corresponde a tu destinatario original. Selecciona el archivo privado correcto; no el archivo público. Instalación bloqueada.";
                else if (code != 0) message = "No se pudo autenticar la entrega. Instalación bloqueada. Comprueba los dos archivos originales.";
                else {
                    Contract.requireVerified(this); verified = true;
                    message = "APK verificada. SHA-256 correcto, firma original, identidad independiente y 96 bibliotecas según el informe. Ya puedes pulsar Instalar.\n\nConserva instalada tu Alpha actual y acepta Actualizar. La barra compacta y su fluidez quedan pendientes de tu prueba.";
                }
            } catch (Exception | LinkageError e) {
                message = "Comprobación fallida. No se instalará ningún archivo. Vuelve a seleccionar los archivos originales.";
            } finally {
                copy.delete(); if (!verified) Contract.clean(this);
            }
            final String result = message;
            RUNNING.set(false);
            runOnUiThread(() -> { status.setText(result); keyButton.setText("2. Seleccionar identidad original"); refresh(); });
        }, "local-decryption").start();
    }
    private void startInstall() {
        if (!verified || !RUNNING.compareAndSet(false, true)) return;
        refresh(); status.setText("Comprobando de nuevo la APK antes de abrir el instalador…");
        new Thread(() -> {
            boolean ok;
            try { Contract.requireVerified(this); ok = true; } catch (Exception e) { ok = false; }
            final boolean checked = ok; RUNNING.set(false);
            runOnUiThread(() -> {
                if (!checked) { verified = false; status.setText("La integridad cambió. Instalación bloqueada."); refresh(); return; }
                refresh();
                if (!getPackageManager().canRequestPackageInstalls()) {
                    status.setText("Android necesita tu autorización para instalar desde este auxiliar. Activa el permiso, vuelve aquí y pulsa Instalar otra vez.");
                    try { startActivity(new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, Uri.parse("package:" + getPackageName()))); }
                    catch (Exception e) { status.setText("Abre Ajustes > Instalar aplicaciones desconocidas y autoriza este auxiliar. Luego vuelve a pulsar Instalar."); }
                    return;
                }
                Intent intent = new Intent(Intent.ACTION_VIEW).setDataAndType(VerifiedApkProvider.URI, "application/vnd.android.package-archive");
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                intent.setClipData(ClipData.newRawUri("FlexyGram Alpha verificada", VerifiedApkProvider.URI));
                try { startActivity(intent); status.setText("Confirma la instalación en Android. Después abre FlexyGram Alpha desde su icono. Este auxiliar no inicia sesión por ti."); }
                catch (Exception e) { status.setText("No se pudo abrir el instalador de Android. La APK permanece verificada dentro de este auxiliar."); }
            });
        }, "verify-before-install").start();
    }
    private void showReport() {
        try {
            // This view shows only the public, fixed verification summary. No identity content.
            new AlertDialog.Builder(this).setTitle("Informe de la entrega")
                .setMessage("Paquete: " + Contract.APP + "\nCommit: " + Contract.COMMIT + "\nSHA-256: " + Contract.HASH + "\nBibliotecas ELF: 96\nFirma: coincide con el informe cifrado\nPrueba física: PENDIENTE\n\nverification.json se ha extraído en el almacenamiento privado del auxiliar.")
                .setNeutralButton("Guardar informe", (dialog, which) -> {
                    Intent save = new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("application/json");
                    save.putExtra(Intent.EXTRA_TITLE, "FlexyGram-Alpha2-verification.json"); save.putExtra(Intent.EXTRA_LOCAL_ONLY, true);
                    startActivityForResult(save, SAVE_REPORT);
                })
                .setPositiveButton("Cerrar", null).show();
        } catch (Exception ignored) { }
    }
    private void saveReport(Uri destination) {
        if (!verified || !RUNNING.compareAndSet(false, true)) return;
        refresh();
        new Thread(() -> {
            String message;
            try {
                Contract.requireVerified(this);
                byte[] report = java.nio.file.Files.readAllBytes(new File(Contract.directory(this), "verification.json").toPath());
                try (java.io.OutputStream out = getContentResolver().openOutputStream(destination, "wt")) {
                    if (out == null) throw new java.io.IOException(); out.write(report);
                }
                message = "Informe guardado en la ubicación local que elegiste. Ya puedes actualizar FlexyGram Alpha 2.";
            } catch (Exception e) { message = "No se pudo guardar el informe. Puedes seguir instalando la APK verificada o volver a intentarlo."; }
            final String result = message; RUNNING.set(false);
            runOnUiThread(() -> { status.setText(result); refresh(); });
        }, "save-local-report").start();
    }
}
