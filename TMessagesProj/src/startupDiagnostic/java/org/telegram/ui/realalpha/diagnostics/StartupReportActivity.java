package org.telegram.ui.realalpha.diagnostics;

import android.app.*;
import android.content.*;
import android.os.*;
import android.widget.*;
import org.telegram.messenger.StartupTrace;
import org.telegram.ui.realalpha.RealAlphaActivity;
import java.util.List;

/** Phone-only report. No READ_LOGS, bugreport, trace stream, account data or external export. */
public final class StartupReportActivity extends Activity {
    private TextView report;
    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        if (!StartupTrace.enabled()) { finish(); return; }
        LinearLayout body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(20,20,20,20);
        TextView title = new TextView(this);
        title.setText("FlexyGram — diagnóstico offline de arranque\nPaquete independiente. No borres la app anterior.\nSin cuentas, red ni restauración.");
        body.addView(title);
        Button run = new Button(this); run.setText("Ejecutar un arranque nativo"); body.addView(run);
        run.setOnClickListener(v -> {
            if (probeRunning()) { refresh(); return; }
            getPreferences(MODE_PRIVATE).edit().putLong("requested", System.currentTimeMillis()).commit();
            StartupTrace.begin(StartupTrace.Stage.PROBE_REQUESTED);
            startActivity(new Intent(this, RealAlphaActivity.class));
        });
        Button update = new Button(this); update.setText("Actualizar informe"); body.addView(update);
        update.setOnClickListener(v -> refresh());
        Button copy = new Button(this); copy.setText("Copiar informe sanitizado"); body.addView(copy);
        copy.setOnClickListener(v -> {
            refresh();
            ((ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(
                    ClipData.newPlainText("FlexyGram startup", report.getText()));
        });
        report = new TextView(this); report.setTextIsSelectable(true); report.setTextSize(13);
        ScrollView scroll = new ScrollView(this); scroll.addView(report);
        body.addView(scroll, new LinearLayout.LayoutParams(-1,0,1));
        setContentView(body); refresh();
    }
    @Override protected void onResume() { super.onResume(); if (report != null) refresh(); }
    private boolean probeRunning() {
        ActivityManager manager = (ActivityManager)getSystemService(ACTIVITY_SERVICE);
        if (manager == null || manager.getRunningAppProcesses() == null) return false;
        for (ActivityManager.RunningAppProcessInfo info : manager.getRunningAppProcesses()) {
            if (info.uid == android.os.Process.myUid() && (getPackageName()+":startup_probe").equals(info.processName)) return true;
        }
        return false;
    }
    private void refresh() {
        StringBuilder text = new StringBuilder("STARTUP_REPORT_V1\nAPI=").append(Build.VERSION.SDK_INT)
            .append("\nPACKAGE=io.github.jose22yt.flexygram.realalpha.startupdiagnostic\n")
            .append(StartupTrace.read()).append("\n");
        if (Build.VERSION.SDK_INT >= 30) ownExit(text);
        else text.append("EXIT_INFO_UNAVAILABLE_BELOW_API30\n");
        text.append("PROBE_RUNNING=").append(probeRunning()).append("\n");
        report.setText(text.toString());
    }
    @android.annotation.TargetApi(30)
    private void ownExit(StringBuilder text) {
        try {
            ActivityManager manager = (ActivityManager)getSystemService(ACTIVITY_SERVICE);
            List<ApplicationExitInfo> exits = manager.getHistoricalProcessExitReasons(getPackageName(),0,8);
            long requested = getPreferences(MODE_PRIVATE).getLong("requested",Long.MAX_VALUE);
            for (ApplicationExitInfo exit : exits) {
                if (!(getPackageName()+":startup_probe").equals(exit.getProcessName()) || exit.getTimestamp() < requested) continue;
                text.append("OWN_PROBE_EXIT_REASON=").append(exit.getReason())
                    .append("\nOWN_PROBE_EXIT_STATUS=").append(exit.getStatus()).append("\n");
                return;
            }
            text.append("NO_MATCHING_PROBE_EXIT_RECORD\n");
        } catch (RuntimeException ignored) { text.append("OWN_EXIT_INFO_UNAVAILABLE\n"); }
    }
}
