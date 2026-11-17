package app.flexygram.performance;

import android.view.View;
import java.util.function.BooleanSupplier;

/** Reports usable content after its draw, without polling or persistent frame callbacks. */
public final class StartupDrawReporter {
    private final View owner;
    private final BooleanSupplier ready;
    private final Runnable callback;
    private boolean scheduled, complete;
    public StartupDrawReporter(View owner, BooleanSupplier ready, Runnable report) {
        this.owner = owner; this.ready = ready;
        callback = () -> {
            scheduled = false;
            if (complete || !this.ready.getAsBoolean()) return;
            complete = true;
            report.run();
        };
    }
    public void afterDraw() {
        if (complete || scheduled || !ready.getAsBoolean()) return;
        scheduled = true;
        if (!owner.post(callback)) scheduled = false;
    }
    public void close() { complete = true; scheduled = false; owner.removeCallbacks(callback); }
}
